/**
 * Unit tests for CompletionHandler
 */

import { CompletionHandler } from '../src/completion-handler';
import { SessionManager } from '../src/session-manager';
import { SessionInfo, SessionState } from '../src/types';
import { Octokit } from '@octokit/rest';

// Mock PRCreator
jest.mock('../src/pr-creator', () => {
  return {
    PRCreator: jest.fn().mockImplementation(() => {
      return {
        createBranch: jest.fn().mockResolvedValue(undefined),
        commitFile: jest.fn().mockResolvedValue(undefined),
        createPR: jest.fn().mockResolvedValue(123),
      };
    }),
  };
});

// Mock StatusReporter
jest.mock('../src/status-reporter', () => {
  return {
    StatusReporter: jest.fn().mockImplementation(() => {
      return {
        reportSuccess: jest.fn().mockResolvedValue(undefined),
        reportFailure: jest.fn().mockResolvedValue(undefined),
      };
    }),
  };
});

describe('CompletionHandler', () => {
  let mockOctokit: jest.Mocked<Octokit>;
  let sessionManager: SessionManager;
  let completionHandler: CompletionHandler;
  let mockSessionInfo: SessionInfo;
  let mockCreateBranch: jest.Mock;
  let mockCommitFile: jest.Mock;
  let mockCreatePR: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup mocks for PRCreator
    mockCreateBranch = jest.fn().mockResolvedValue(undefined);
    mockCommitFile = jest.fn().mockResolvedValue(undefined);
    mockCreatePR = jest.fn().mockResolvedValue(123);

    const { PRCreator } = require('../src/pr-creator');
    PRCreator.generateBranchName = jest.fn().mockReturnValue('test-branch');
    PRCreator.generatePRBody = jest.fn().mockReturnValue('Test PR body');
    PRCreator.mockImplementation(() => ({
      createBranch: mockCreateBranch,
      commitFile: mockCommitFile,
      createPR: mockCreatePR,
    }));

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

    sessionManager = new SessionManager();
    completionHandler = new CompletionHandler(mockOctokit, sessionManager);

    mockSessionInfo = {
      sessionId: 'test-session-123',
      issueNumber: 123,
      issueContext: {
        issue: {
          number: 123,
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
      state: SessionState.DISPATCHED,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
  });

  describe('subscribeToSession', () => {
    it('should subscribe to session events', () => {
      const mockSession = {
        on: jest.fn(),
      };

      completionHandler.subscribeToSession(mockSession, 'test-session-123');

      expect(mockSession.on).toHaveBeenCalled();
    });
  });

  describe('event handling', () => {
    beforeEach(() => {
      sessionManager.registerSession(mockSessionInfo);
    });

    it('should handle session.idle event', async () => {
      const mockSession = {
        on: jest.fn((handler) => {
          // Simulate idle event
          setTimeout(() => {
            handler({ type: 'session.idle', data: {} });
          }, 10);
        }),
      };

      completionHandler.subscribeToSession(mockSession, 'test-session-123');

      // Wait for event to be processed
      await new Promise((resolve) => setTimeout(resolve, 50));

      const session = sessionManager.getSession('test-session-123');
      expect(session?.state).toBe(SessionState.COMPLETED);
    });

    it('should handle assistant.message event', async () => {
      const mockSession = {
        on: jest.fn((handler) => {
          // Simulate message event
          setTimeout(() => {
            handler({
              type: 'assistant.message',
              data: { content: 'Test response content' },
            });
          }, 10);
        }),
      };

      completionHandler.subscribeToSession(mockSession, 'test-session-123');

      // Wait for event to be processed
      await new Promise((resolve) => setTimeout(resolve, 50));

      const session = sessionManager.getSession('test-session-123');
      expect(session?.state).toBe(SessionState.RUNNING);
    });

    it('should handle error event', async () => {
      const mockSession = {
        on: jest.fn((handler) => {
          // Simulate error event
          setTimeout(() => {
            handler({
              type: 'error',
              data: { error: 'Test error message' },
            });
          }, 10);
        }),
      };

      completionHandler.subscribeToSession(mockSession, 'test-session-123');

      // Wait for event to be processed
      await new Promise((resolve) => setTimeout(resolve, 50));

      const session = sessionManager.getSession('test-session-123');
      expect(session?.state).toBe(SessionState.FAILED);
      expect(session?.error).toBe('Test error message');
    });

    it('should handle events for non-existent session gracefully', async () => {
      const mockSession = {
        on: jest.fn((handler) => {
          setTimeout(() => {
            handler({ type: 'session.idle', data: {} });
          }, 10);
        }),
      };

      // Subscribe with non-existent session ID
      completionHandler.subscribeToSession(mockSession, 'non-existent-session');

      // Wait for event to be processed - should not throw
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
  });

  describe('PR creation on idle', () => {
    beforeEach(() => {
      sessionManager.registerSession(mockSessionInfo);
    });

    it('should create PR when session becomes idle', async () => {
      const mockSession = {
        on: jest.fn((handler) => {
          setTimeout(() => {
            handler({ type: 'session.idle', data: {} });
          }, 10);
        }),
      };

      completionHandler.subscribeToSession(mockSession, 'test-session-123');

      // Wait for PR creation
      await new Promise((resolve) => setTimeout(resolve, 100));

      const session = sessionManager.getSession('test-session-123');
      expect(session?.state).toBe(SessionState.COMPLETED);
      expect(session?.prNumber).toBe(123);
    });

    it('should update session on PR creation failure', async () => {
      // Mock PR creation to fail
      const { PRCreator } = require('../src/pr-creator');
      PRCreator.mockImplementationOnce(() => {
        return {
          createBranch: jest.fn().mockRejectedValue(new Error('Branch creation failed')),
        };
      });

      const mockSession = {
        on: jest.fn((handler) => {
          setTimeout(() => {
            handler({ type: 'session.idle', data: {} });
          }, 10);
        }),
      };

      completionHandler.subscribeToSession(mockSession, 'test-session-123');

      // Wait for PR creation attempt
      await new Promise((resolve) => setTimeout(resolve, 100));

      const session = sessionManager.getSession('test-session-123');
      expect(session?.state).toBe(SessionState.FAILED);
    });
  });

  describe('status reporting', () => {
    beforeEach(() => {
      sessionManager.registerSession(mockSessionInfo);
    });

    it('should report success after PR creation', async () => {
      const { StatusReporter } = require('../src/status-reporter');
      const mockReportSuccess = jest.fn().mockResolvedValue(undefined);
      StatusReporter.mockImplementationOnce(() => {
        return {
          reportSuccess: mockReportSuccess,
          reportFailure: jest.fn(),
        };
      });

      const mockSession = {
        on: jest.fn((handler) => {
          setTimeout(() => {
            handler({ type: 'session.idle', data: {} });
          }, 10);
        }),
      };

      completionHandler.subscribeToSession(mockSession, 'test-session-123');

      await new Promise((resolve) => setTimeout(resolve, 100));

      expect(mockReportSuccess).toHaveBeenCalled();
    });

    it('should report failure on error event', async () => {
      const { StatusReporter } = require('../src/status-reporter');
      const mockReportFailure = jest.fn().mockResolvedValue(undefined);
      StatusReporter.mockImplementationOnce(() => {
        return {
          reportSuccess: jest.fn(),
          reportFailure: mockReportFailure,
        };
      });

      const mockSession = {
        on: jest.fn((handler) => {
          setTimeout(() => {
            handler({ type: 'error', data: { error: 'Test error' } });
          }, 10);
        }),
      };

      completionHandler.subscribeToSession(mockSession, 'test-session-123');

      await new Promise((resolve) => setTimeout(resolve, 100));

      expect(mockReportFailure).toHaveBeenCalled();
    });
  });
});
