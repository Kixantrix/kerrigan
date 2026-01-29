/**
 * Prompt loader utility
 * Loads agent prompts from markdown files
 */

import * as fs from 'fs';
import * as path from 'path';

/**
 * Load prompt content from a markdown file
 * 
 * @param promptFile - Name of the prompt file (e.g., 'kickoff-spec.md')
 * @param repoPath - Repository root path (defaults to cwd)
 * @returns Prompt content as string
 */
export function loadPrompt(promptFile: string, repoPath: string = process.cwd()): string {
  const promptPath = path.join(repoPath, 'prompts', promptFile);
  
  try {
    if (fs.existsSync(promptPath)) {
      return fs.readFileSync(promptPath, 'utf-8');
    }
    
    // Fall back to .github/agents if prompts/ doesn't exist
    const agentsPath = path.join(repoPath, '.github/agents', promptFile);
    if (fs.existsSync(agentsPath)) {
      return fs.readFileSync(agentsPath, 'utf-8');
    }
    
    console.warn(`⚠️  Prompt file not found: ${promptFile}`);
    return `# ${promptFile}\n\nPrompt file not found.`;
  } catch (error: any) {
    console.error(`❌ Failed to load prompt ${promptFile}:`, error.message);
    return `# ${promptFile}\n\nError loading prompt: ${error.message}`;
  }
}

/**
 * Build system message content with agent role and context
 * 
 * @param role - Agent role name
 * @param promptContent - Base prompt content
 * @param constitution - Constitution content (optional)
 * @returns Formatted system message content
 */
export function buildSystemMessage(
  role: string,
  promptContent: string,
  constitution?: string
): string {
  let systemMessage = `<kerrigan_agent role="${role}">\n`;
  systemMessage += promptContent;
  
  if (constitution) {
    systemMessage += `\n\n<constitution>\n${constitution}\n</constitution>`;
  }
  
  systemMessage += `\n</kerrigan_agent>`;
  
  return systemMessage;
}
