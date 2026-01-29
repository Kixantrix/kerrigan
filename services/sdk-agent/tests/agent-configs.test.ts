/**
 * Tests for agent configurations
 */

import { KERRIGAN_AGENTS, getAgentConfig, getAllAgentConfigs } from '../src/agents';

describe('Agent Configurations', () => {
  describe('KERRIGAN_AGENTS', () => {
    it('should have 6 agent configurations', () => {
      const configs = Object.keys(KERRIGAN_AGENTS);
      expect(configs).toHaveLength(6);
      expect(configs).toContain('spec');
      expect(configs).toContain('architect');
      expect(configs).toContain('swe');
      expect(configs).toContain('deploy');
      expect(configs).toContain('security');
      expect(configs).toContain('triage');
    });

    it('should have spec agent with correct configuration', () => {
      const spec = KERRIGAN_AGENTS.spec;
      expect(spec.name).toBe('kerrigan-spec');
      expect(spec.displayName).toBe('Kerrigan Spec Agent');
      expect(spec.promptFile).toBe('kickoff-spec.md');
      expect(spec.label).toBe('role:spec');
      expect(spec.tools).toBeDefined();
      expect(spec.tools.length).toBeGreaterThan(0);
    });

    it('should have architect agent with correct configuration', () => {
      const architect = KERRIGAN_AGENTS.architect;
      expect(architect.name).toBe('kerrigan-architect');
      expect(architect.displayName).toBe('Kerrigan Architect Agent');
      expect(architect.promptFile).toBe('architecture-design.md');
      expect(architect.label).toBe('role:architect');
      expect(architect.tools).toBeDefined();
    });

    it('should have swe agent with correct configuration', () => {
      const swe = KERRIGAN_AGENTS.swe;
      expect(swe.name).toBe('kerrigan-swe');
      expect(swe.displayName).toBe('Kerrigan SWE Agent');
      expect(swe.promptFile).toBe('implementation-swe.md');
      expect(swe.label).toBe('role:swe');
      expect(swe.tools).toBeDefined();
    });

    it('should have deploy agent with correct configuration', () => {
      const deploy = KERRIGAN_AGENTS.deploy;
      expect(deploy.name).toBe('kerrigan-deploy');
      expect(deploy.displayName).toBe('Kerrigan Deploy Agent');
      expect(deploy.promptFile).toBe('deployment-ops.md');
      expect(deploy.label).toBe('role:deploy');
      expect(deploy.tools).toBeDefined();
    });

    it('should have security agent with correct configuration', () => {
      const security = KERRIGAN_AGENTS.security;
      expect(security.name).toBe('kerrigan-security');
      expect(security.displayName).toBe('Kerrigan Security Agent');
      expect(security.promptFile).toBe('security-review.md');
      expect(security.label).toBe('role:security');
      expect(security.tools).toBeDefined();
    });

    it('should have triage agent with correct configuration', () => {
      const triage = KERRIGAN_AGENTS.triage;
      expect(triage.name).toBe('kerrigan-triage');
      expect(triage.displayName).toBe('Kerrigan Triage Agent');
      expect(triage.promptFile).toBe('triage-analysis.md');
      expect(triage.label).toBe('role:triage');
      expect(triage.tools).toBeDefined();
    });

    it('should assign appropriate tools to each agent', () => {
      // All agents should have read_constitution tool
      Object.values(KERRIGAN_AGENTS).forEach(agent => {
        const toolNames = agent.tools.map(t => t.name);
        expect(toolNames).toContain('read_constitution');
      });

      // Architect, SWE, Deploy, Security should have read_spec
      ['architect', 'swe', 'deploy', 'security'].forEach(role => {
        const toolNames = KERRIGAN_AGENTS[role].tools.map(t => t.name);
        expect(toolNames).toContain('read_spec');
      });

      // All agents should have list_artifacts
      Object.values(KERRIGAN_AGENTS).forEach(agent => {
        const toolNames = agent.tools.map(t => t.name);
        expect(toolNames).toContain('list_artifacts');
      });
    });
  });

  describe('getAgentConfig', () => {
    it('should return config for valid role', () => {
      const config = getAgentConfig('spec');
      expect(config).toBeDefined();
      expect(config?.name).toBe('kerrigan-spec');
    });

    it('should return undefined for invalid role', () => {
      const config = getAgentConfig('invalid-role');
      expect(config).toBeUndefined();
    });
  });

  describe('getAllAgentConfigs', () => {
    it('should return array of all agent configs', () => {
      const configs = getAllAgentConfigs();
      expect(configs).toHaveLength(6);
      expect(configs[0]).toHaveProperty('name');
      expect(configs[0]).toHaveProperty('displayName');
      expect(configs[0]).toHaveProperty('tools');
    });
  });
});
