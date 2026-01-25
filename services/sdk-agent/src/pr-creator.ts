/**
 * PR Creator
 * Creates pull requests with proper linking to issues
 */

import { Octokit } from '@octokit/rest';
import { PRCreationOptions } from './types';

export class PRCreator {
  private octokit: Octokit;

  constructor(octokit: Octokit) {
    this.octokit = octokit;
  }

  /**
   * Create a branch for the PR
   */
  async createBranch(
    owner: string,
    repo: string,
    branchName: string,
    baseBranch: string
  ): Promise<void> {
    try {
      // Get the SHA of the base branch
      const { data: ref } = await this.octokit.git.getRef({
        owner,
        repo,
        ref: `heads/${baseBranch}`,
      });

      // Create new branch
      await this.octokit.git.createRef({
        owner,
        repo,
        ref: `refs/heads/${branchName}`,
        sha: ref.object.sha,
      });

      console.log(`✅ Created branch: ${branchName}`);
    } catch (error: any) {
      if (error.status === 422) {
        console.log(`ℹ️  Branch ${branchName} already exists, will use it`);
      } else {
        throw error;
      }
    }
  }

  /**
   * Create a pull request
   */
  async createPR(options: PRCreationOptions): Promise<number> {
    const { owner, repo, issueNumber, branchName, title, body, labels } = options;

    try {
      // Get default branch
      const { data: repository } = await this.octokit.repos.get({ owner, repo });
      const baseBranch = repository.default_branch;

      // Create branch if it doesn't exist
      await this.createBranch(owner, repo, branchName, baseBranch);

      // Create PR
      const { data: pr } = await this.octokit.pulls.create({
        owner,
        repo,
        title,
        body,
        head: branchName,
        base: baseBranch,
      });

      console.log(`✅ Created PR #${pr.number}: ${title}`);

      // Add labels if provided
      if (labels && labels.length > 0) {
        await this.octokit.issues.addLabels({
          owner,
          repo,
          issue_number: pr.number,
          labels,
        });
        console.log(`🏷️  Added labels to PR: ${labels.join(', ')}`);
      }

      return pr.number;
    } catch (error) {
      console.error('❌ Failed to create PR:', error);
      throw error;
    }
  }

  /**
   * Generate PR body with issue reference
   */
  static generatePRBody(issueNumber: number, roleDescription: string, checklist: string[]): string {
    let body = `## Summary\n\n`;
    body += `This PR addresses issue #${issueNumber}.\n\n`;
    body += `**Agent Role**: ${roleDescription}\n\n`;
    body += `## Changes\n\n`;
    
    if (checklist.length > 0) {
      body += checklist.map(item => `- [ ] ${item}`).join('\n');
      body += '\n\n';
    }
    
    body += `## Testing\n\n`;
    body += `- [ ] CI passes\n`;
    body += `- [ ] Manual testing completed\n`;
    body += `- [ ] Documentation updated if needed\n\n`;
    
    body += `---\n\n`;
    body += `Closes #${issueNumber}\n`;
    
    return body;
  }

  /**
   * Generate branch name from issue number
   */
  static generateBranchName(issueNumber: number, role: string): string {
    return `sdk-agent/${role}/issue-${issueNumber}`;
  }
}
