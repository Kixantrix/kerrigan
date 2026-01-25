/**
 * Basic unit tests for Agent Orchestrator
 */

import { AgentOrchestrator } from '../src/agent-orchestrator';

describe('AgentOrchestrator', () => {
  describe('determineRole', () => {
    it('should detect spec role', () => {
      const role = AgentOrchestrator.determineRole(['role:spec', 'agent:go']);
      expect(role.name).toBe('spec');
      expect(role.promptFile).toBe('kickoff-spec.md');
    });

    it('should detect architect role', () => {
      const role = AgentOrchestrator.determineRole(['role:architect', 'agent:go']);
      expect(role.name).toBe('architect');
      expect(role.promptFile).toBe('architecture-design.md');
    });

    it('should detect swe role', () => {
      const role = AgentOrchestrator.determineRole(['role:swe', 'agent:go']);
      expect(role.name).toBe('swe');
      expect(role.promptFile).toBe('implementation-swe.md');
    });

    it('should default to swe when no role specified', () => {
      const role = AgentOrchestrator.determineRole(['agent:go']);
      expect(role.name).toBe('swe');
    });

    it('should detect deploy role', () => {
      const role = AgentOrchestrator.determineRole(['role:deploy', 'agent:go']);
      expect(role.name).toBe('deploy');
      expect(role.promptFile).toBe('deployment-ops.md');
    });

    it('should detect security role', () => {
      const role = AgentOrchestrator.determineRole(['role:security', 'agent:go']);
      expect(role.name).toBe('security');
      expect(role.promptFile).toBe('security-review.md');
    });

    it('should detect triage role', () => {
      const role = AgentOrchestrator.determineRole(['role:triage', 'agent:go']);
      expect(role.name).toBe('triage');
      expect(role.promptFile).toBe('triage-analysis.md');
    });
  });

  describe('shouldProcess', () => {
    it('should allow with agent:go label', () => {
      const result = AgentOrchestrator.shouldProcess(['agent:go']);
      expect(result.allowed).toBe(true);
      expect(result.reason).toContain('agent:go');
    });

    it('should allow with agent:sprint label', () => {
      const result = AgentOrchestrator.shouldProcess(['agent:sprint']);
      expect(result.allowed).toBe(true);
      expect(result.reason).toContain('agent:sprint');
    });

    it('should allow with autonomy:override label', () => {
      const result = AgentOrchestrator.shouldProcess(['autonomy:override']);
      expect(result.allowed).toBe(true);
      expect(result.reason).toContain('autonomy:override');
    });

    it('should block without autonomy labels', () => {
      const result = AgentOrchestrator.shouldProcess(['role:swe']);
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('No autonomy gate label');
    });

    it('should prioritize autonomy:override', () => {
      const result = AgentOrchestrator.shouldProcess([
        'agent:go',
        'agent:sprint',
        'autonomy:override',
      ]);
      expect(result.allowed).toBe(true);
      expect(result.reason).toContain('autonomy:override');
    });
  });

  describe('getAvailableRoles', () => {
    it('should return all roles', () => {
      const roles = AgentOrchestrator.getAvailableRoles();
      expect(roles.length).toBe(6);
      
      const roleNames = roles.map(r => r.name);
      expect(roleNames).toContain('spec');
      expect(roleNames).toContain('architect');
      expect(roleNames).toContain('swe');
      expect(roleNames).toContain('deploy');
      expect(roleNames).toContain('security');
      expect(roleNames).toContain('triage');
    });
  });
});
