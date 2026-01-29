/**
 * Unit tests for SwarmDispatcher
 */

import { SwarmDispatcher } from '../src/swarm-dispatcher';
import { AgentContext, SessionState } from '../src/types';
import { Octokit } from '@octokit/rest';

// Mock the SDK
const mockStart = jest.fn().mockResolvedValue(undefined);
const mockStop = jest.fn().mockResolvedValue(undefined);
const mockSend = jest.fn().mockResolvedValue(undefined);
const mockOn = jest.fn();
const mockCreateSession = jest.fn().mockResolvedValue({
  send: mockSend,
  on: mockOn,
});

jest.mock('@github/copilot-sdk', () => {
  return {
    CopilotClient: jest.fn().mockImplementation(() => {
      return {
        start: mockStart,
        stop: mockStop,
        createSession: mockCreateSession,
      };
    }),
  };
}, { virtual: true });

describe('SwarmDispatcher', () => {
  let mockOctokit: jest.Mocked<Octokit>;
  let dispatcher: SwarmDispatcher;
  let mockContext: AgentContext;

  beforeEach(() => {
    jest.clearAllMocks();

    mockOctokit = {
      repos: {
        get: jest.fn().mockResolvedValue({
          data: { default_branch: 'main' },
        }),
      },
      issues: {
        get: jest.fn().mockResolvedValue({
          data: {
            number: 123,
            title: 'Test Issue',
            body: 'Test body',
            labels: [],
          },
        }),
      },
    } as any;

    dispatcher = new SwarmDispatcher(mockOctokit, 'test-token');

    mockContext = {
      issue: {
        number: 123,
        title: 'Test Issue',
        body: 'Test issue body',
        labels: ['role:swe', 'agent:go'],
      },
      repository: {
        owner: 'test-owner',
        name: 'test-repo',
        defaultBranch: 'main',
      },
      role: 'swe',
      artifacts: {},
      prompt: 'Test prompt',
    };
  });

  afterEach(async () => {
    // Cleanup
    await dispatcher.stop();
  });

  describe('dispatchIssue', () => {
    it('should dispatch a single issue successfully', async () => {
      const result = await dispatcher.dispatchIssue(mockContext);

      expect(result.dispatched).toBe(true);
      expect(result.issueNumber).toBe(123);
      expect(result.sessionId).toBeTruthy();
      expect(result.error).toBeUndefined();

      // Verify SDK methods were called
      expect(mockStart).toHaveBeenCalled();
      expect(mockCreateSession).toHaveBeenCalledWith({ model: 'gpt-4o' });
      expect(mockSend).toHaveBeenCalled();
    });

    it('should register session in manager', async () => {
      const result = await dispatcher.dispatchIssue(mockContext);

      const sessionManager = dispatcher.getSessionManager();
      const session = sessionManager.getSession(result.sessionId);

      expect(session).toBeDefined();
      expect(session?.issueNumber).toBe(123);
      expect(session?.state).toBe(SessionState.DISPATCHED);
    });

    it('should subscribe to session events', async () => {
      await dispatcher.dispatchIssue(mockContext);

      expect(mockOn).toHaveBeenCalled();
    });

    it('should handle dispatch errors', async () => {
      // Mock createSession to throw an error
      mockCreateSession.mockRejectedValueOnce(new Error('Session creation failed'));

      const result = await dispatcher.dispatchIssue(mockContext);

      expect(result.dispatched).toBe(false);
      expect(result.error).toContain('Session creation failed');
    });

    it('should respect max concurrent sessions limit', async () => {
      // Create dispatcher with limit of 2
      const limitedDispatcher = new SwarmDispatcher(mockOctokit, 'test-token', {
        maxConcurrentSessions: 2,
      });

      // Dispatch 2 issues successfully
      await limitedDispatcher.dispatchIssue(mockContext);
      await limitedDispatcher.dispatchIssue({ ...mockContext, issue: { ...mockContext.issue, number: 124 } });

      // Third dispatch should fail due to limit
      const result = await limitedDispatcher.dispatchIssue({ ...mockContext, issue: { ...mockContext.issue, number: 125 } });

      expect(result.dispatched).toBe(false);
      expect(result.error).toContain('Max concurrent sessions');

      await limitedDispatcher.stop();
    });
  });

  describe('dispatchBatch', () => {
    it('should dispatch multiple issues in parallel', async () => {
      const contexts: AgentContext[] = [
        mockContext,
        { ...mockContext, issue: { ...mockContext.issue, number: 124 } },
        { ...mockContext, issue: { ...mockContext.issue, number: 125 } },
      ];

      const result = await dispatcher.dispatchBatch(contexts);

      expect(result.total).toBe(3);
      expect(result.successful.length).toBe(3);
      expect(result.failed.length).toBe(0);
    });

    it('should handle partial failures in batch', async () => {
      // Mock to fail on second call
      let callCount = 0;
      mockCreateSession.mockImplementation(() => {
        callCount++;
        if (callCount === 2) {
          return Promise.reject(new Error('Failed'));
        }
        return Promise.resolve({
          send: mockSend,
          on: mockOn,
        });
      });

      const contexts: AgentContext[] = [
        mockContext,
        { ...mockContext, issue: { ...mockContext.issue, number: 124 } },
        { ...mockContext, issue: { ...mockContext.issue, number: 125 } },
      ];

      const result = await dispatcher.dispatchBatch(contexts);

      expect(result.total).toBe(3);
      expect(result.successful.length).toBe(2);
      expect(result.failed.length).toBe(1);
    });

    it('should return empty results for empty batch', async () => {
      const result = await dispatcher.dispatchBatch([]);

      expect(result.total).toBe(0);
      expect(result.successful.length).toBe(0);
      expect(result.failed.length).toBe(0);
    });
  });

  describe('getActiveSessionCount', () => {
    it('should return count of active sessions', async () => {
      expect(dispatcher.getActiveSessionCount()).toBe(0);

      await dispatcher.dispatchIssue(mockContext);

      expect(dispatcher.getActiveSessionCount()).toBe(1);

      await dispatcher.dispatchIssue({ ...mockContext, issue: { ...mockContext.issue, number: 124 } });

      expect(dispatcher.getActiveSessionCount()).toBe(2);
    });
  });

  describe('getAllSessions', () => {
    it('should return all sessions', async () => {
      await dispatcher.dispatchIssue(mockContext);
      await dispatcher.dispatchIssue({ ...mockContext, issue: { ...mockContext.issue, number: 124 } });

      const sessions = dispatcher.getAllSessions();

      expect(sessions.length).toBe(2);
    });
  });

  describe('stop', () => {
    it('should stop the SDK client', async () => {
      await dispatcher.dispatchIssue(mockContext);

      await dispatcher.stop();

      expect(mockStop).toHaveBeenCalled();
    });

    it('should cleanup completed sessions on stop', async () => {
      await dispatcher.dispatchIssue(mockContext);

      // Manually mark as completed
      const sessionManager = dispatcher.getSessionManager();
      const sessions = sessionManager.getAllSessions();
      sessionManager.updateSessionState(sessions[0].sessionId, SessionState.COMPLETED);

      await dispatcher.stop();

      // Should be cleaned up
      expect(dispatcher.getActiveSessionCount()).toBe(0);
    });
  });

  describe('configuration', () => {
    it('should use default config values', () => {
      const defaultDispatcher = new SwarmDispatcher(mockOctokit, 'test-token');
      
      // Defaults should be applied (tested indirectly through behavior)
      expect(defaultDispatcher).toBeDefined();
    });

    it('should use custom config values', async () => {
      const customDispatcher = new SwarmDispatcher(mockOctokit, 'test-token', {
        maxConcurrentSessions: 5,
        sessionTimeoutMs: 60000,
        retryAttempts: 5,
        retryDelayMs: 2000,
      });

      // Test that custom limit is respected
      for (let i = 0; i < 5; i++) {
        await customDispatcher.dispatchIssue({ ...mockContext, issue: { ...mockContext.issue, number: 100 + i } });
      }

      expect(customDispatcher.getActiveSessionCount()).toBe(5);

      // Sixth should fail
      const result = await customDispatcher.dispatchIssue({ ...mockContext, issue: { ...mockContext.issue, number: 200 } });
      expect(result.dispatched).toBe(false);

      await customDispatcher.stop();
    });
  });
});
