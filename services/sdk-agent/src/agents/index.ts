/**
 * Kerrigan Agent Configurations
 * SDK-compatible agent personas with role-specific tools
 */

import { AgentConfig } from './types';
import { readConstitutionTool, readSpecTool, listArtifactsTool } from '../tools';

/**
 * KERRIGAN_AGENTS - SDK-compatible agent configurations
 * 
 * Each agent has:
 * - name: Unique identifier for the agent
 * - displayName: Human-readable name
 * - description: Agent's purpose and responsibilities
 * - promptFile: Markdown file containing agent instructions
 * - label: GitHub label for agent selection (e.g., 'role:spec')
 * - tools: Array of custom tools the agent can invoke
 */
export const KERRIGAN_AGENTS: { [key: string]: AgentConfig } = {
  spec: {
    name: 'kerrigan-spec',
    displayName: 'Kerrigan Spec Agent',
    description: 'Creates project specifications following Kerrigan conventions',
    promptFile: 'kickoff-spec.md',
    label: 'role:spec',
    tools: [
      readConstitutionTool,
      listArtifactsTool,
    ],
  },
  
  architect: {
    name: 'kerrigan-architect',
    displayName: 'Kerrigan Architect Agent',
    description: 'Designs systems following architecture patterns',
    promptFile: 'architecture-design.md',
    label: 'role:architect',
    tools: [
      readConstitutionTool,
      readSpecTool,
      listArtifactsTool,
    ],
  },
  
  swe: {
    name: 'kerrigan-swe',
    displayName: 'Kerrigan SWE Agent',
    description: 'Implements code with tests following test-first development',
    promptFile: 'implementation-swe.md',
    label: 'role:swe',
    tools: [
      readConstitutionTool,
      readSpecTool,
      listArtifactsTool,
    ],
  },
  
  deploy: {
    name: 'kerrigan-deploy',
    displayName: 'Kerrigan Deploy Agent',
    description: 'Creates runbooks and cost estimates',
    promptFile: 'deployment-ops.md',
    label: 'role:deploy',
    tools: [
      readConstitutionTool,
      readSpecTool,
      listArtifactsTool,
    ],
  },
  
  security: {
    name: 'kerrigan-security',
    displayName: 'Kerrigan Security Agent',
    description: 'Reviews for security vulnerabilities',
    promptFile: 'security-review.md',
    label: 'role:security',
    tools: [
      readConstitutionTool,
      readSpecTool,
      listArtifactsTool,
    ],
  },
  
  triage: {
    name: 'kerrigan-triage',
    displayName: 'Kerrigan Triage Agent',
    description: 'Categorizes and prioritizes issues',
    promptFile: 'triage-analysis.md',
    label: 'role:triage',
    tools: [
      readConstitutionTool,
      listArtifactsTool,
    ],
  },
};

/**
 * Get agent configuration by role name
 */
export function getAgentConfig(role: string): AgentConfig | undefined {
  return KERRIGAN_AGENTS[role];
}

/**
 * Get all agent configurations
 */
export function getAllAgentConfigs(): AgentConfig[] {
  return Object.values(KERRIGAN_AGENTS);
}
