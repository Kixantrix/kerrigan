/**
 * Agent configuration types for SDK integration
 */

/**
 * SDK-compatible agent configuration
 */
export interface AgentConfig {
  name: string;
  displayName: string;
  description: string;
  promptFile: string;
  label: string;
  tools: any[];  // Tool definitions - using any to avoid type complexity
  systemPrompt?: string;
}

/**
 * Role-specific tool assignments
 */
export interface RoleTools {
  common: any[];      // Tools available to all agents
  roleSpecific: {
    [roleName: string]: any[];
  };
}
