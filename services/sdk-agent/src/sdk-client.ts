/**
 * SDK Client Wrapper
 * Interface with GitHub Copilot SDK
 */

// Dynamic import for ESM-only SDK package
type CopilotClientType = import('@github/copilot-sdk').CopilotClient;

import { Octokit } from '@octokit/rest';
import { AgentContext, AgentResult } from './types';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Interface for SDK client behavior.
 * This documents the expected contract for SDK integration.
 */
export interface ISDKClient {
  /**
   * Execute agent with SDK
   * @param context Agent execution context
   * @returns Result of agent execution
   */
  executeAgent(context: AgentContext): Promise<AgentResult>;

  /**
   * Validate SDK prerequisites
   * @returns True if SDK is ready to use
   */
  validate(): Promise<boolean>;
}

export class SDKClient implements ISDKClient {
  private octokit: Octokit;
  private token: string;
  private repoPath: string;
  private copilotClient?: CopilotClientType;

  constructor(octokit: Octokit, token: string, repoPath: string = process.cwd()) {
    this.octokit = octokit;
    this.token = token;
    this.repoPath = repoPath;
  }

  /**
   * Execute agent with SDK
   */
  async executeAgent(context: AgentContext): Promise<AgentResult> {
    console.log('🤖 Executing agent with SDK...');
    console.log(`  Role: ${context.role}`);
    console.log(`  Issue: #${context.issue.number} - ${context.issue.title}`);

    try {
      // Dynamic import for ESM-only SDK package
      // Use Function constructor to prevent TypeScript from converting import() to require()
      const dynamicImport = new Function('specifier', 'return import(specifier)');
      const { CopilotClient } = await dynamicImport('@github/copilot-sdk');
      
      // Initialize Copilot SDK client
      this.copilotClient = new CopilotClient();
      await this.copilotClient.start();
      
      console.log('✅ Copilot SDK client started');

      // Create SDK session with configured model
      const session = await this.copilotClient.createSession({
        model: 'gpt-5.2-codex',  // or configured model
      });

      console.log('✅ SDK session created');

      // Build prompt with full context
      const prompt = this.buildPrompt(context);

      // Execute agent with SDK
      const response = await session.send({
        prompt,
      });

      console.log('✅ SDK execution completed');

      // Stop the SDK client
      await this.copilotClient.stop();
      this.copilotClient = undefined;

      return {
        success: true,
        output: response.content,
        logs: [
          'SDK client initialized',
          'Session created successfully',
          'Agent executed with SDK',
          'Response received',
          'SDK execution completed',
        ],
      };
    } catch (error: any) {
      console.error('❌ SDK execution failed:', error);
      
      // Cleanup on error
      if (this.copilotClient) {
        try {
          await this.copilotClient.stop();
        } catch (stopError) {
          console.error('Error stopping SDK client:', stopError);
        }
        this.copilotClient = undefined;
      }

      return {
        success: false,
        error: error.message || 'Unknown SDK error',
        logs: ['SDK execution failed', `Error: ${error.message}`],
      };
    }
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
   * Load agent prompt from file
   */
  private async loadPrompt(promptFile: string): Promise<string> {
    const promptPath = path.join(this.repoPath, 'prompts', promptFile);
    
    try {
      if (fs.existsSync(promptPath)) {
        return fs.readFileSync(promptPath, 'utf-8');
      }
      
      // Fall back to .github/agents if prompts/ doesn't exist
      const agentsPath = path.join(this.repoPath, '.github/agents', promptFile);
      if (fs.existsSync(agentsPath)) {
        return fs.readFileSync(agentsPath, 'utf-8');
      }
      
      throw new Error(`Prompt file not found: ${promptFile}`);
    } catch (error) {
      console.error(`❌ Failed to load prompt: ${error}`);
      throw error;
    }
  }

  /**
   * Load artifact files for context
   */
  private async loadArtifacts(owner: string, repo: string): Promise<any> {
    const artifacts: any = {};

    try {
      // Load constitution
      const { data: constitution } = await this.octokit.repos.getContent({
        owner,
        repo,
        path: 'specs/constitution.md',
      });
      
      if ('content' in constitution) {
        artifacts.constitution = Buffer.from(constitution.content, 'base64').toString('utf-8');
      }
    } catch (error) {
      console.log('ℹ️  Constitution not found, skipping');
    }

    // TODO: Load other artifacts (spec.md, architecture.md, plan.md) based on issue context

    return artifacts;
  }

  /**
   * Validate SDK prerequisites
   */
  async validate(): Promise<boolean> {
    try {
      console.log('🔍 Validating SDK client...');
      
      // Check token is valid
      if (!this.token || this.token === '') {
        console.error('❌ Invalid token');
        return false;
      }

      // Check token works by making a simple API call
      // For GitHub App installation tokens, we verify we can access the repo
      const rateLimit = await this.octokit.rateLimit.get();
      console.log(`✅ Token valid - Rate limit remaining: ${rateLimit.data.rate.remaining}`);
      
      return true;
    } catch (error) {
      console.error('❌ SDK client validation failed:', error);
      return false;
    }
  }
}
