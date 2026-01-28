/**
 * SDK Agent Service - Main Entry Point
 * 
 * This service handles autonomous agent triggering via GitHub Actions.
 * It processes issues labeled with agent:go and creates PRs automatically.
 */

import * as dotenv from 'dotenv';
import { GitHubAppAuth } from './github-app-auth';
import { AgentOrchestrator } from './agent-orchestrator';
import { StatusReporter } from './status-reporter';
import { PRCreator } from './pr-creator';
import { SDKClient } from './sdk-client';
import { AgentContext, ServiceConfig } from './types';

// Load environment variables
dotenv.config();

export class SDKAgentService {
  private config: ServiceConfig;
  private githubAuth: GitHubAppAuth;

  constructor(config: ServiceConfig) {
    this.config = config;
    this.githubAuth = new GitHubAppAuth(config.githubAppId, config.githubAppPrivateKey);
  }

  /**
   * Main entry point - process an issue event
   */
  async processIssue(
    owner: string,
    repo: string,
    issueNumber: number,
    eventType: string
  ): Promise<void> {
    console.log('🚀 SDK Agent Service Starting...');
    console.log(`  Repository: ${owner}/${repo}`);
    console.log(`  Issue: #${issueNumber}`);
    console.log(`  Event Type: ${eventType}`);

    try {
      // Validate GitHub App credentials
      const isValid = await this.githubAuth.validate();
      if (!isValid) {
        throw new Error('GitHub App credentials are invalid');
      }

      // Create authenticated Octokit client
      const octokit = await this.githubAuth.createOctokitClient(owner, repo);

      // Fetch issue details
      const { data: issue } = await octokit.issues.get({
        owner,
        repo,
        issue_number: issueNumber,
      });

      console.log(`📋 Issue: ${issue.title}`);
      const labels = issue.labels.map((l) => (typeof l === 'string' ? l : l.name || ''));
      console.log(`🏷️  Labels: ${labels.join(', ')}`);

      // Check autonomy gates
      const { allowed, reason: gateReason } = AgentOrchestrator.shouldProcess(labels);
      if (!allowed) {
        console.log(`⛔ Autonomy gate blocked: ${gateReason}`);
        return;
      }
      console.log(`✅ Autonomy gate passed: ${gateReason}`);

      // Check for blocking status
      const { blocked, reason: statusReason } = await AgentOrchestrator.checkStatus(
        octokit,
        owner,
        repo,
        issueNumber
      );
      if (blocked) {
        console.log(`⏸️  Work blocked: ${statusReason}`);
        return;
      }

      // Determine agent role
      const role = AgentOrchestrator.determineRole(labels);
      console.log(`🎯 Agent Role: ${role.name} - ${role.description}`);

      // Initialize status reporter
      const reporter = new StatusReporter(octokit, owner, repo, issueNumber);

      // Report that agent has started
      await reporter.reportStarted(role.name);

      // Get installation token for SDK
      const token = await this.githubAuth.getInstallationToken(owner, repo);

      // Initialize SDK client
      const sdkClient = new SDKClient(octokit, token);
      const sdkValid = await sdkClient.validate();
      if (!sdkValid) {
        throw new Error('SDK client validation failed');
      }

      // Get repository default branch
      const { data: repository } = await octokit.repos.get({
        owner,
        repo,
      });

      // Prepare agent context
      const context: AgentContext = {
        issue: {
          number: issueNumber,
          title: issue.title,
          body: issue.body || '',
          labels,
        },
        repository: {
          owner,
          name: repo,
          defaultBranch: repository.default_branch,
        },
        role: role.name,
        artifacts: {},
        prompt: '', // Will be loaded by SDK client
      };

      // Execute agent with SDK
      console.log('🤖 Executing agent...');
      const result = await sdkClient.executeAgent(context);

      if (!result.success) {
        console.error(`❌ Agent execution failed: ${result.error}`);
        await reporter.reportFailure(result.error || 'Unknown error', result.logs);
        process.exit(1);
      }

      // Create PR with results
      console.log('📝 Creating pull request...');
      const prCreator = new PRCreator(octokit);
      
      const branchName = PRCreator.generateBranchName(issueNumber, role.name);
      
      // Get default branch
      const { data: repoData } = await octokit.repos.get({ owner, repo });
      const baseBranch = repoData.default_branch;
      
      // Create branch first
      await prCreator.createBranch(owner, repo, branchName, baseBranch);
      
      // Commit the agent's response as a research document
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const outputPath = `docs/research/issue-${issueNumber}-${role.name}-${timestamp}.md`;
      const outputContent = `# Agent Response: Issue #${issueNumber}\n\n**Role**: ${role.description}\n**Generated**: ${new Date().toISOString()}\n\n---\n\n${result.output}`;
      
      await prCreator.commitFile(
        owner,
        repo,
        branchName,
        outputPath,
        outputContent,
        `docs: add ${role.name} agent research for issue #${issueNumber}`
      );
      
      const prTitle = `${role.description}: ${issue.title}`;
      const prBody = PRCreator.generatePRBody(
        issueNumber,
        role.description,
        ['Changes implemented', 'Tests added', 'Documentation updated']
      );

      const prNumber = await prCreator.createPR({
        owner,
        repo,
        issueNumber,
        branchName,
        title: prTitle,
        body: prBody,
        labels: labels.filter(l => l.startsWith('role:')),
      });

      // Report success
      await reporter.reportSuccess(prNumber, branchName);

      console.log('✅ SDK Agent Service completed successfully');
      console.log(`   PR #${prNumber} created`);
    } catch (error: any) {
      console.error('❌ SDK Agent Service failed:', error);
      
      try {
        const octokit = await this.githubAuth.createOctokitClient(owner, repo);
        const reporter = new StatusReporter(octokit, owner, repo, issueNumber);
        await reporter.reportFailure(error.message || 'Unknown error');
      } catch (reportError) {
        console.error('❌ Failed to report error to issue:', reportError);
      }

      throw error;
    }
  }
}

/**
 * CLI entry point
 */
async function main() {
  // Parse command line arguments
  const args = process.argv.slice(2);
  const getArg = (name: string): string => {
    const index = args.indexOf(name);
    if (index === -1 || index === args.length - 1) {
      throw new Error(`Missing required argument: ${name}`);
    }
    return args[index + 1];
  };

  const eventType = getArg('--event-type');
  const issueNumber = parseInt(getArg('--issue-number'), 10);
  const repository = getArg('--repository');
  const [owner, repo] = repository.split('/');

  // Load configuration from environment
  const config: ServiceConfig = {
    githubAppId: process.env.GITHUB_APP_ID || '',
    githubAppPrivateKey: process.env.GITHUB_APP_PRIVATE_KEY || '',
    githubToken: process.env.GITHUB_TOKEN,
    logLevel: (process.env.LOG_LEVEL as any) || 'info',
    retryAttempts: parseInt(process.env.RETRY_ATTEMPTS || '3', 10),
    retryDelayMs: parseInt(process.env.RETRY_DELAY_MS || '1000', 10),
    sdkTimeoutMs: parseInt(process.env.SDK_TIMEOUT_MS || '300000', 10),
  };

  // Validate configuration
  if (!config.githubAppId || !config.githubAppPrivateKey) {
    throw new Error(
      'Missing required environment variables: GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY'
    );
  }

  // Create and run service
  const service = new SDKAgentService(config);
  await service.processIssue(owner, repo, issueNumber, eventType);
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default SDKAgentService;
