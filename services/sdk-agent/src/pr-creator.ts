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
      // Sanitize checklist items to prevent markdown injection
      const sanitizedChecklist = checklist.map(item => this.sanitizeChecklistItem(item));
      body += sanitizedChecklist.map(item => `- [ ] ${item}`).join('\n');
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
   * Sanitize checklist item to prevent markdown injection
   */
  private static sanitizeChecklistItem(item: string): string {
    // Remove dangerous markdown patterns
    return item
      .replace(/[`*_[\]()]/g, '') // Remove markdown formatting characters
      .replace(/https?:\/\/[^\s]+/g, '[URL]') // Replace URLs with placeholder
      .substring(0, 100); // Limit length
  }

  /**
   * Generate branch name from issue number
   */
  static generateBranchName(issueNumber: number, role: string): string {
    return `sdk-agent/${role}/issue-${issueNumber}`;
  }

  /**
   * Commit a file to a branch
   */
  async commitFile(
    owner: string,
    repo: string,
    branchName: string,
    filePath: string,
    content: string,
    message: string
  ): Promise<void> {
    // Get the current commit SHA for the branch
    const { data: ref } = await this.octokit.git.getRef({
      owner,
      repo,
      ref: `heads/${branchName}`,
    });

    // Get the tree SHA
    const { data: commit } = await this.octokit.git.getCommit({
      owner,
      repo,
      commit_sha: ref.object.sha,
    });

    // Create a blob for the file content
    const { data: blob } = await this.octokit.git.createBlob({
      owner,
      repo,
      content: Buffer.from(content).toString('base64'),
      encoding: 'base64',
    });

    // Create a new tree with the file
    const { data: newTree } = await this.octokit.git.createTree({
      owner,
      repo,
      base_tree: commit.tree.sha,
      tree: [
        {
          path: filePath,
          mode: '100644',
          type: 'blob',
          sha: blob.sha,
        },
      ],
    });

    // Create a new commit
    const { data: newCommit } = await this.octokit.git.createCommit({
      owner,
      repo,
      message,
      tree: newTree.sha,
      parents: [ref.object.sha],
    });

    // Update the branch reference
    await this.octokit.git.updateRef({
      owner,
      repo,
      ref: `heads/${branchName}`,
      sha: newCommit.sha,
    });

    console.log(`✅ Committed file: ${filePath}`);
  }
}
