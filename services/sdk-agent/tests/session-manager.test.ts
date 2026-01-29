/**
 * Unit tests for SessionManager
 */

import { SessionManager } from '../src/session-manager';
import { SessionInfo, SessionState, AgentContext } from '../src/types';
import * as fs from 'fs';

// Mock fs for persistence tests
jest.mock('fs');

describe('SessionManager', () => {
  let manager: SessionManager;
  let mockSessionInfo: SessionInfo;

  beforeEach(() => {
    jest.clearAllMocks();
    manager = new SessionManager();

    mockSessionInfo = {
      sessionId: 'test-session-123',
      issueNumber: 42,
      issueContext: {
        issue: {
          number: 42,
          title: 'Test Issue',
          body: 'Test body',
          labels: ['role:swe'],
        },
        repository: {
          owner: 'test-owner',
          name: 'test-repo',
          defaultBranch: 'main',
        },
        role: 'swe',
        artifacts: {},
        prompt: 'Test prompt',
      },
      state: SessionState.CREATED,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
  });

  describe('registerSession', () => {
    it('should register a new session', () => {
      manager.registerSession(mockSessionInfo);

      const session = manager.getSession('test-session-123');
      expect(session).toBeDefined();
      expect(session?.sessionId).toBe('test-session-123');
      expect(session?.issueNumber).toBe(42);
    });

    it('should track multiple sessions', () => {
      manager.registerSession(mockSessionInfo);
      
      const secondSession: SessionInfo = {
        ...mockSessionInfo,
        sessionId: 'test-session-456',
        issueNumber: 43,
      };
      manager.registerSession(secondSession);

      expect(manager.getSessionCount()).toBe(2);
    });
  });

  describe('updateSessionState', () => {
    beforeEach(() => {
      manager.registerSession(mockSessionInfo);
    });

    it('should update session state', () => {
      manager.updateSessionState('test-session-123', SessionState.RUNNING);

      const session = manager.getSession('test-session-123');
      expect(session?.state).toBe(SessionState.RUNNING);
    });

    it('should update error when provided', () => {
      manager.updateSessionState('test-session-123', SessionState.FAILED, 'Test error');

      const session = manager.getSession('test-session-123');
      expect(session?.state).toBe(SessionState.FAILED);
      expect(session?.error).toBe('Test error');
    });

    it('should set completedAt for completed states', () => {
      manager.updateSessionState('test-session-123', SessionState.COMPLETED);

      const session = manager.getSession('test-session-123');
      expect(session?.completedAt).toBeDefined();
    });

    it('should handle non-existent session gracefully', () => {
      expect(() => {
        manager.updateSessionState('non-existent', SessionState.RUNNING);
      }).not.toThrow();
    });
  });

  describe('getSession', () => {
    beforeEach(() => {
      manager.registerSession(mockSessionInfo);
    });

    it('should retrieve session by ID', () => {
      const session = manager.getSession('test-session-123');
      expect(session).toBeDefined();
      expect(session?.sessionId).toBe('test-session-123');
    });

    it('should return undefined for non-existent session', () => {
      const session = manager.getSession('non-existent');
      expect(session).toBeUndefined();
    });
  });

  describe('getSessionByIssue', () => {
    beforeEach(() => {
      manager.registerSession(mockSessionInfo);
    });

    it('should retrieve session by issue number', () => {
      const session = manager.getSessionByIssue(42);
      expect(session).toBeDefined();
      expect(session?.issueNumber).toBe(42);
    });

    it('should return undefined for non-existent issue', () => {
      const session = manager.getSessionByIssue(999);
      expect(session).toBeUndefined();
    });
  });

  describe('getActiveSessions', () => {
    it('should return only active sessions', () => {
      // Register multiple sessions with different states
      manager.registerSession(mockSessionInfo);
      
      const runningSession: SessionInfo = {
        ...mockSessionInfo,
        sessionId: 'running-session',
        issueNumber: 43,
        state: SessionState.RUNNING,
      };
      manager.registerSession(runningSession);

      const completedSession: SessionInfo = {
        ...mockSessionInfo,
        sessionId: 'completed-session',
        issueNumber: 44,
        state: SessionState.COMPLETED,
      };
      manager.registerSession(completedSession);

      const activeSessions = manager.getActiveSessions();
      expect(activeSessions.length).toBe(2); // CREATED and RUNNING
      expect(activeSessions.find(s => s.state === SessionState.COMPLETED)).toBeUndefined();
    });
  });

  describe('removeSession', () => {
    beforeEach(() => {
      manager.registerSession(mockSessionInfo);
    });

    it('should remove a session', () => {
      expect(manager.getSessionCount()).toBe(1);
      
      manager.removeSession('test-session-123');
      
      expect(manager.getSessionCount()).toBe(0);
      expect(manager.getSession('test-session-123')).toBeUndefined();
    });
  });

  describe('cleanupCompletedSessions', () => {
    it('should remove completed and failed sessions', () => {
      manager.registerSession(mockSessionInfo);

      const completedSession: SessionInfo = {
        ...mockSessionInfo,
        sessionId: 'completed-session',
        issueNumber: 43,
        state: SessionState.COMPLETED,
      };
      manager.registerSession(completedSession);

      const failedSession: SessionInfo = {
        ...mockSessionInfo,
        sessionId: 'failed-session',
        issueNumber: 44,
        state: SessionState.FAILED,
      };
      manager.registerSession(failedSession);

      expect(manager.getSessionCount()).toBe(3);

      manager.cleanupCompletedSessions();

      expect(manager.getSessionCount()).toBe(1);
      expect(manager.getSession('test-session-123')).toBeDefined();
      expect(manager.getSession('completed-session')).toBeUndefined();
      expect(manager.getSession('failed-session')).toBeUndefined();
    });
  });

  describe('clear', () => {
    it('should clear all sessions', () => {
      manager.registerSession(mockSessionInfo);
      
      const secondSession: SessionInfo = {
        ...mockSessionInfo,
        sessionId: 'test-session-456',
        issueNumber: 43,
      };
      manager.registerSession(secondSession);

      expect(manager.getSessionCount()).toBe(2);

      manager.clear();

      expect(manager.getSessionCount()).toBe(0);
    });
  });

  describe('persistence', () => {
    it('should attempt to persist state when path is provided', () => {
      const persistManager = new SessionManager('/tmp/test-sessions.json');
      
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      (fs.mkdirSync as jest.Mock).mockReturnValue(undefined);
      (fs.writeFileSync as jest.Mock).mockReturnValue(undefined);

      persistManager.registerSession(mockSessionInfo);

      expect(fs.writeFileSync).toHaveBeenCalled();
    });

    it('should not persist when no path is provided', () => {
      manager.registerSession(mockSessionInfo);

      expect(fs.writeFileSync).not.toHaveBeenCalled();
    });
  });
});
