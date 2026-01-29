/**
 * CompletionHandler
 * Handles session completion events and triggers PR creation
 */

import { Octokit } from '@octokit/rest';
import { SessionManager } from './session-manager';
import { SessionState, AgentResult } from './types';
import { PRCreator } from './pr-creator';
import { StatusReporter } from './status-reporter';

export interface SessionEvent {
  type: string;
  sessionId: string;
  data?: any;
}

export class CompletionHandler {
  private octokit: Octokit;
  private sessionManager: SessionManager;
  private prCreator: PRCreator;

  constructor(octokit: Octokit, sessionManager: SessionManager) {
    this.octokit = octokit;
    this.sessionManager = sessionManager;
    this.prCreator = new PRCreator(octokit);
  }

  /**
   * Subscribe to session events
   * @param session SDK session to monitor
   * @param sessionId Session ID for tracking
   */
  subscribeToSession(session: any, sessionId: string): void {
    console.log(`👂 Subscribing to events for session: ${sessionId}`);

    session.on((event: any) => {
      this.handleEvent({
        type: event.type,
        sessionId,
        data: event.data,
      });
    });
  }

  /**
   * Handle session events
   */
  private async handleEvent(event: SessionEvent): Promise<void> {
    console.log(`📨 Event received: ${event.type} for session ${event.sessionId}`);

    try {
      switch (event.type) {
        case 'session.idle':
          await this.handleIdle(event);
          break;
        case 'assistant.message':
          await this.handleMessage(event);
          break;
        case 'error':
          await this.handleError(event);
          break;
        default:
          console.log(`  ℹ️  Unhandled event type: ${event.type}`);
      }
    } catch (error: any) {
      console.error(`❌ Error handling event: ${error.message}`);
      // Log the error but don't call handleError to avoid infinite recursion
      // Instead, directly update the session state
      this.sessionManager.updateSessionState(
        event.sessionId,
        SessionState.FAILED,
        `Event handler error: ${error.message}`
      );
    }
  }

  /**
   * Handle session.idle event - session is complete
   */
  private async handleIdle(event: SessionEvent): Promise<void> {
    console.log(`✅ Session idle: ${event.sessionId}`);

    const sessionInfo = this.sessionManager.getSession(event.sessionId);
    if (!sessionInfo) {
      console.warn(`⚠️  Session info not found: ${event.sessionId}`);
      return;
    }

    // Update session state to idle
    this.sessionManager.updateSessionState(event.sessionId, SessionState.IDLE);

    // Trigger PR creation
    await this.createPR(event.sessionId);
  }

  /**
   * Handle assistant.message event - collect response content
   */
  private async handleMessage(event: SessionEvent): Promise<void> {
    const sessionInfo = this.sessionManager.getSession(event.sessionId);
    if (!sessionInfo) {
      return;
    }

    // Update session state to running if not already
    if (sessionInfo.state === SessionState.DISPATCHED) {
      this.sessionManager.updateSessionState(event.sessionId, SessionState.RUNNING);
    }

    // Log message preview
    const content = event.data?.content || '';
    if (content.length > 0) {
      console.log(`  📝 Content preview: ${content.substring(0, 100)}...`);
    }
  }

  /**
   * Handle error event
   */
  private async handleError(event: SessionEvent): Promise<void> {
    console.error(`❌ Session error: ${event.sessionId}`);
    console.error(`   Error: ${JSON.stringify(event.data)}`);

    const sessionInfo = this.sessionManager.getSession(event.sessionId);
    if (!sessionInfo) {
      console.warn(`⚠️  Session info not found: ${event.sessionId}`);
      return;
    }

    const errorMessage = event.data?.error || event.data?.message || 'Unknown error';
    this.sessionManager.updateSessionState(event.sessionId, SessionState.FAILED, errorMessage);

    // Report failure to issue
    await this.reportFailure(event.sessionId, errorMessage);
  }

  /**
   * Create PR from session results
   */
  private async createPR(sessionId: string): Promise<void> {
    const sessionInfo = this.sessionManager.getSession(sessionId);
    if (!sessionInfo) {
      console.warn(`⚠️  Session info not found: ${sessionId}`);
      return;
    }

    const { issueContext, issueNumber } = sessionInfo;
    const { repository, role } = issueContext;

    console.log(`📝 Creating PR for issue #${issueNumber}...`);

    try {
      // Generate branch name
      const branchName = PRCreator.generateBranchName(issueNumber, role);

      // Get repository default branch
      const { data: repoData } = await this.octokit.repos.get({
        owner: repository.owner,
        repo: repository.name,
      });
      const baseBranch = repoData.default_branch;

      // Create branch
      await this.prCreator.createBranch(
        repository.owner,
        repository.name,
        branchName,
        baseBranch
      );

      // Create a placeholder commit (actual implementation would use agent output)
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const outputPath = `docs/research/issue-${issueNumber}-${role}-${timestamp}.md`;
      const outputContent = `# Agent Response: Issue #${issueNumber}\n\n**Role**: ${role}\n**Generated**: ${new Date().toISOString()}\n**Session**: ${sessionId}\n\n---\n\n[Agent output placeholder - implementation would include actual response]`;

      await this.prCreator.commitFile(
        repository.owner,
        repository.name,
        branchName,
        outputPath,
        outputContent,
        `docs: add ${role} agent research for issue #${issueNumber}`
      );

      // Fetch issue details for PR
      const { data: issue } = await this.octokit.issues.get({
        owner: repository.owner,
        repo: repository.name,
        issue_number: issueNumber,
      });

      // Create PR
      const prTitle = `[${role}] ${issue.title}`;
      const prBody = PRCreator.generatePRBody(
        issueNumber,
        role,
        ['Changes implemented', 'Agent executed via async swarm dispatcher']
      );

      const prNumber = await this.prCreator.createPR({
        owner: repository.owner,
        repo: repository.name,
        issueNumber,
        branchName,
        title: prTitle,
        body: prBody,
        labels: issueContext.issue.labels.filter((l) => l.startsWith('role:')),
      });

      console.log(`✅ PR #${prNumber} created for issue #${issueNumber}`);

      // Update session with PR number
      sessionInfo.prNumber = prNumber;
      this.sessionManager.updateSessionState(sessionId, SessionState.COMPLETED);

      // Report success to issue
      await this.reportSuccess(sessionId, prNumber, branchName);
    } catch (error: any) {
      console.error(`❌ Failed to create PR: ${error.message}`);
      this.sessionManager.updateSessionState(sessionId, SessionState.FAILED, error.message);
      await this.reportFailure(sessionId, error.message);
    }
  }

  /**
   * Report success to issue
   */
  private async reportSuccess(
    sessionId: string,
    prNumber: number,
    branchName: string
  ): Promise<void> {
    const sessionInfo = this.sessionManager.getSession(sessionId);
    if (!sessionInfo) {
      return;
    }

    const { issueContext, issueNumber } = sessionInfo;
    const { repository } = issueContext;
    const reporter = new StatusReporter(
      this.octokit,
      repository.owner,
      repository.name,
      issueNumber
    );

    await reporter.reportSuccess(prNumber, branchName);
  }

  /**
   * Report failure to issue
   */
  private async reportFailure(sessionId: string, error: string): Promise<void> {
    const sessionInfo = this.sessionManager.getSession(sessionId);
    if (!sessionInfo) {
      return;
    }

    const { issueContext, issueNumber } = sessionInfo;
    const { repository } = issueContext;
    const reporter = new StatusReporter(
      this.octokit,
      repository.owner,
      repository.name,
      issueNumber
    );

    await reporter.reportFailure(error, [`Session: ${sessionId}`, `Error: ${error}`]);
  }
}
