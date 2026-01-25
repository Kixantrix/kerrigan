/**
 * Status Reporter
 * Posts status updates to GitHub issues
 */

import { Octokit } from '@octokit/rest';
import { AgentStatus, StatusUpdate } from './types';

export class StatusReporter {
  private octokit: Octokit;
  private owner: string;
  private repo: string;
  private issueNumber: number;

  constructor(octokit: Octokit, owner: string, repo: string, issueNumber: number) {
    this.octokit = octokit;
    this.owner = owner;
    this.repo = repo;
    this.issueNumber = issueNumber;
  }

  /**
   * Post a status comment to the issue
   */
  async postComment(body: string): Promise<void> {
    try {
      await this.octokit.issues.createComment({
        owner: this.owner,
        repo: this.repo,
        issue_number: this.issueNumber,
        body,
      });
      console.log(`💬 Posted comment to issue #${this.issueNumber}`);
    } catch (error) {
      console.error('❌ Failed to post comment:', error);
      throw error;
    }
  }

  /**
   * Report that agent has started working
   */
  async reportStarted(role: string): Promise<void> {
    const body = `🤖 **SDK Agent Started**

The **${role}** agent has been triggered and is now working on this issue.

- **Triggered by**: SDK Agent Service (GitHub Actions)
- **Started at**: ${new Date().toISOString()}
- **Status**: In Progress

I'll update this issue when the work is complete.`;

    await this.postComment(body);
  }

  /**
   * Report successful PR creation
   */
  async reportSuccess(prNumber: number, branchName: string): Promise<void> {
    const body = `✅ **Work Complete**

I've created a pull request with the proposed changes:

- **Pull Request**: #${prNumber}
- **Branch**: \`${branchName}\`
- **Completed at**: ${new Date().toISOString()}

Please review the PR and provide feedback!`;

    await this.postComment(body);
  }

  /**
   * Report failure
   */
  async reportFailure(error: string, logs?: string[]): Promise<void> {
    let body = `❌ **Agent Failed**

The SDK agent encountered an error while processing this issue:

\`\`\`
${error}
\`\`\`

**Failed at**: ${new Date().toISOString()}

`;

    if (logs && logs.length > 0) {
      body += `\n**Recent logs**:\n\n\`\`\`\n${logs.slice(-10).join('\n')}\n\`\`\`\n`;
    }

    body += `\n---\n\n**Retry Instructions**:\n`;
    body += `1. Check the error message above\n`;
    body += `2. Fix any issues in the repository or configuration\n`;
    body += `3. Remove and re-add the \`agent:go\` label to retry\n`;

    await this.postComment(body);
  }

  /**
   * Report progress update
   */
  async reportProgress(message: string): Promise<void> {
    const body = `🔄 **Progress Update**

${message}

_Updated at: ${new Date().toISOString()}_`;

    await this.postComment(body);
  }
}
