/**
 * Agent Orchestrator
 * Routes issues to appropriate agent roles based on labels
 */

import { AgentRole } from './types';

export class AgentOrchestrator {
  private static readonly AGENT_ROLES: AgentRole[] = [
    {
      name: 'spec',
      label: 'role:spec',
      promptFile: 'kickoff-spec.md',
      description: 'Spec Agent - Define project goals and acceptance criteria',
    },
    {
      name: 'architect',
      label: 'role:architect',
      promptFile: 'architecture-design.md',
      description: 'Architect Agent - Design system architecture and create implementation plan',
    },
    {
      name: 'swe',
      label: 'role:swe',
      promptFile: 'implementation-swe.md',
      description: 'SWE Agent - Implement features with tests',
    },
    {
      name: 'deploy',
      label: 'role:deploy',
      promptFile: 'deployment-ops.md',
      description: 'Deploy Agent - Create operational runbooks',
    },
    {
      name: 'security',
      label: 'role:security',
      promptFile: 'security-review.md',
      description: 'Security Agent - Security review and hardening',
    },
    {
      name: 'triage',
      label: 'role:triage',
      promptFile: 'triage-analysis.md',
      description: 'Triage Agent - Analyze and categorize issues',
    },
  ];

  /**
   * Determine which agent role should handle this issue
   */
  static determineRole(labels: string[]): AgentRole {
    // Check for explicit role labels
    for (const role of this.AGENT_ROLES) {
      if (labels.includes(role.label)) {
        console.log(`🎯 Matched role: ${role.name} (${role.label})`);
        return role;
      }
    }

    // Default to SWE agent if no role specified
    console.log('🎯 No explicit role found, defaulting to SWE agent');
    return this.AGENT_ROLES.find((r) => r.name === 'swe')!;
  }

  /**
   * Check if issue should be processed by SDK agent
   */
  static shouldProcess(labels: string[]): { allowed: boolean; reason: string } {
    // Check for autonomy gate labels
    const hasAgentGo = labels.includes('agent:go');
    const hasAgentSprint = labels.includes('agent:sprint');
    const hasAutonomyOverride = labels.includes('autonomy:override');

    if (hasAutonomyOverride) {
      return { allowed: true, reason: 'autonomy:override label present' };
    }

    if (hasAgentGo) {
      return { allowed: true, reason: 'agent:go label present' };
    }

    if (hasAgentSprint) {
      return { allowed: true, reason: 'agent:sprint label present' };
    }

    return {
      allowed: false,
      reason: 'No autonomy gate label found (agent:go, agent:sprint, or autonomy:override)',
    };
  }

  /**
   * Check if issue has blocking status
   */
  static async checkStatus(
    octokit: any,
    owner: string,
    repo: string,
    issueNumber: number
  ): Promise<{ blocked: boolean; reason: string }> {
    try {
      // Try to fetch status.json from the repository
      // This is a placeholder - actual implementation would check project-specific status
      // For now, we'll assume not blocked
      return { blocked: false, reason: 'No blocking status found' };
    } catch (error) {
      // If status.json doesn't exist or can't be read, assume not blocked
      console.log('ℹ️  No status.json found, assuming not blocked');
      return { blocked: false, reason: 'No status file found' };
    }
  }

  /**
   * Get all available roles
   */
  static getAvailableRoles(): AgentRole[] {
    return this.AGENT_ROLES;
  }
}
