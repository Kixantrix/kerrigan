/**
 * SwarmDispatcher
 * Dispatches multiple issues to SDK sessions in parallel using non-blocking send()
 */

import { Octokit } from '@octokit/rest';
import {
  AgentContext,
  SwarmDispatcherConfig,
  DispatchResult,
  BatchDispatchResult,
  SessionInfo,
  SessionState,
} from './types';
import { SessionManager } from './session-manager';
import { CompletionHandler } from './completion-handler';

// Dynamic import type for CopilotClient
type CopilotClientType = import('@github/copilot-sdk').CopilotClient;
type SessionType = import('@github/copilot-sdk').Session;

export class SwarmDispatcher {
  private octokit: Octokit;
  private token: string;
  private config: SwarmDispatcherConfig;
  private sessionManager: SessionManager;
  private completionHandler: CompletionHandler;
  private copilotClient?: CopilotClientType;

  constructor(
    octokit: Octokit,
    token: string,
    config: Partial<SwarmDispatcherConfig> = {}
  ) {
    this.octokit = octokit;
    this.token = token;
    this.config = {
      maxConcurrentSessions: config.maxConcurrentSessions || 10,
      sessionTimeoutMs: config.sessionTimeoutMs || 300000, // 5 minutes
      retryAttempts: config.retryAttempts || 3,
      retryDelayMs: config.retryDelayMs || 1000,
    };

    // Initialize managers
    this.sessionManager = new SessionManager('/tmp/swarm-sessions.json');
    this.completionHandler = new CompletionHandler(octokit, this.sessionManager);
  }

  /**
   * Initialize the Copilot SDK client
   */
  private async initializeCopilotClient(): Promise<CopilotClientType> {
    if (this.copilotClient) {
      return this.copilotClient;
    }

    console.log('🚀 Initializing Copilot SDK client for swarm mode...');

    // Dynamic import for ESM-only SDK package
    const dynamicImport = new Function('specifier', 'return import(specifier)');
    const { CopilotClient } = await dynamicImport('@github/copilot-sdk');

    // Set the GitHub token for SDK authentication
    process.env.COPILOT_GITHUB_TOKEN = this.token;

    // Initialize Copilot SDK client
    const client = new CopilotClient({
      logLevel: 'info',
    });
    this.copilotClient = client;

    await client.start();
    console.log('✅ Copilot SDK client started in swarm mode');

    return client;
  }

  /**
   * Dispatch a single issue for processing
   * Returns immediately after sending the prompt (non-blocking)
   */
  async dispatchIssue(context: AgentContext): Promise<DispatchResult> {
    console.log(`🚀 Dispatching issue #${context.issue.number}...`);

    try {
      // Check if we've hit the concurrent session limit
      const activeSessions = this.sessionManager.getActiveSessions();
      if (activeSessions.length >= this.config.maxConcurrentSessions) {
        return {
          sessionId: '',
          issueNumber: context.issue.number,
          dispatched: false,
          error: `Max concurrent sessions (${this.config.maxConcurrentSessions}) reached`,
        };
      }

      // Initialize SDK client if not already done
      const client = await this.initializeCopilotClient();

      // Create SDK session
      const session: SessionType = await client.createSession({
        model: 'gpt-4o',
      });

      // Generate a unique session ID
      const sessionId = `session-${context.issue.number}-${Date.now()}`;

      // Register session in manager
      const sessionInfo: SessionInfo = {
        sessionId,
        issueNumber: context.issue.number,
        issueContext: context,
        state: SessionState.CREATED,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      this.sessionManager.registerSession(sessionInfo);

      // Subscribe to session events
      this.completionHandler.subscribeToSession(session, sessionId);

      // Build prompt
      const prompt = this.buildPrompt(context);

      // Send prompt (non-blocking) - returns immediately
      console.log(`📤 Sending prompt for issue #${context.issue.number} (non-blocking)...`);
      const startTime = Date.now();
      
      // Use send() instead of sendAndWait() for non-blocking execution
      session.send({ prompt }).catch((error: any) => {
        console.error(`❌ Error sending prompt: ${error.message}`);
        this.sessionManager.updateSessionState(sessionId, SessionState.FAILED, error.message);
      });
      
      const elapsed = Date.now() - startTime;
      console.log(`✅ Dispatch completed in ${elapsed}ms for issue #${context.issue.number}`);

      // Update session state to dispatched
      this.sessionManager.updateSessionState(sessionId, SessionState.DISPATCHED);

      return {
        sessionId,
        issueNumber: context.issue.number,
        dispatched: true,
      };
    } catch (error: any) {
      console.error(`❌ Failed to dispatch issue #${context.issue.number}: ${error.message}`);
      return {
        sessionId: '',
        issueNumber: context.issue.number,
        dispatched: false,
        error: error.message,
      };
    }
  }

  /**
   * Dispatch multiple issues in parallel
   */
  async dispatchBatch(contexts: AgentContext[]): Promise<BatchDispatchResult> {
    console.log(`🚀 Dispatching batch of ${contexts.length} issues...`);

    const results: DispatchResult[] = [];

    // Dispatch all issues in parallel
    const dispatchPromises = contexts.map((context) => this.dispatchIssue(context));
    const dispatchResults = await Promise.all(dispatchPromises);

    const successful = dispatchResults.filter((r) => r.dispatched);
    const failed = dispatchResults.filter((r) => !r.dispatched);

    console.log(`✅ Batch dispatch complete:`);
    console.log(`   Successful: ${successful.length}`);
    console.log(`   Failed: ${failed.length}`);

    return {
      successful,
      failed,
      total: contexts.length,
    };
  }

  /**
   * Build prompt from agent context
   */
  private buildPrompt(context: AgentContext): string {
    let prompt = context.prompt;

    // Append issue context
    prompt += `\n\n## Issue Context\n`;
    prompt += `Issue #${context.issue.number}: ${context.issue.title}\n`;
    prompt += `\n${context.issue.body}\n`;

    // Append artifacts if available
    if (context.artifacts.constitution) {
      prompt += `\n## Constitution\n${context.artifacts.constitution}\n`;
    }
    if (context.artifacts.spec) {
      prompt += `\n## Specification\n${context.artifacts.spec}\n`;
    }
    if (context.artifacts.architecture) {
      prompt += `\n## Architecture\n${context.artifacts.architecture}\n`;
    }
    if (context.artifacts.plan) {
      prompt += `\n## Implementation Plan\n${context.artifacts.plan}\n`;
    }

    return prompt;
  }

  /**
   * Get session manager for external access
   */
  getSessionManager(): SessionManager {
    return this.sessionManager;
  }

  /**
   * Get completion handler for external access
   */
  getCompletionHandler(): CompletionHandler {
    return this.completionHandler;
  }

  /**
   * Stop the dispatcher and cleanup
   */
  async stop(): Promise<void> {
    console.log('🛑 Stopping swarm dispatcher...');

    if (this.copilotClient) {
      try {
        await this.copilotClient.stop();
        console.log('✅ Copilot SDK client stopped');
      } catch (error) {
        console.error('❌ Error stopping SDK client:', error);
      }
      this.copilotClient = undefined;
    }

    // Cleanup completed sessions
    this.sessionManager.cleanupCompletedSessions();
  }

  /**
   * Get active session count
   */
  getActiveSessionCount(): number {
    return this.sessionManager.getActiveSessions().length;
  }

  /**
   * Get all sessions
   */
  getAllSessions(): SessionInfo[] {
    return this.sessionManager.getAllSessions();
  }
}
