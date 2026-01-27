/**
 * Unit tests for SDK Client
 */

import { SDKClient } from '../src/sdk-client';
import { AgentContext } from '../src/types';
import { Octokit } from '@octokit/rest';

// Create mock for CopilotClient
const mockStart = jest.fn().mockResolvedValue(undefined);
const mockStop = jest.fn().mockResolvedValue(undefined);
const mockSend = jest.fn().mockResolvedValue({
  content: 'SDK generated response',
});
const mockCreateSession = jest.fn().mockResolvedValue({
  send: mockSend,
});

// Mock the @github/copilot-sdk module
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

describe('SDKClient', () => {
  let mockOctokit: jest.Mocked<Octokit>;
  let sdkClient: SDKClient;
  let mockContext: AgentContext;

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Mock Octokit
    mockOctokit = {
      users: {
        getAuthenticated: jest.fn().mockResolvedValue({
          data: { login: 'test-user' },
        }),
      },
    } as any;

    sdkClient = new SDKClient(mockOctokit, 'test-token', '/test/repo');

    // Mock agent context
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
      artifacts: {
        constitution: 'Test constitution',
      },
      prompt: 'Test prompt',
    };
  });

  describe('executeAgent', () => {
    it('should successfully execute agent with SDK', async () => {
      const result = await sdkClient.executeAgent(mockContext);

      expect(result.success).toBe(true);
      expect(result.output).toBe('SDK generated response');
      expect(result.logs).toContain('SDK execution completed');
      expect(result.error).toBeUndefined();
      
      // Verify SDK methods were called
      expect(mockStart).toHaveBeenCalled();
      expect(mockCreateSession).toHaveBeenCalledWith({ model: 'gpt-5.2-codex' });
      expect(mockSend).toHaveBeenCalled();
      expect(mockStop).toHaveBeenCalled();
    });

    it('should handle SDK execution errors', async () => {
      // Mock start to throw an error
      mockStart.mockRejectedValueOnce(new Error('SDK connection failed'));

      const result = await sdkClient.executeAgent(mockContext);

      expect(result.success).toBe(false);
      expect(result.error).toContain('SDK connection failed');
      expect(result.logs).toContain('SDK execution failed');
    });

    it('should build prompt with issue context', async () => {
      await sdkClient.executeAgent(mockContext);

      // Verify the prompt was built correctly
      const sendCall = mockSend.mock.calls[0][0];
      expect(sendCall.prompt).toContain('Test Issue');
      expect(sendCall.prompt).toContain('Test issue body');
      expect(sendCall.prompt).toContain('Test constitution');
    });

    it('should cleanup SDK client on error', async () => {
      // Mock send to throw an error
      mockSend.mockRejectedValueOnce(new Error('Session error'));

      await sdkClient.executeAgent(mockContext);

      // Verify stop was called for cleanup
      expect(mockStop).toHaveBeenCalled();
    });
  });

  describe('validate', () => {
    it('should validate SDK client successfully', async () => {
      const result = await sdkClient.validate();

      expect(result).toBe(true);
      expect(mockOctokit.users.getAuthenticated).toHaveBeenCalled();
    });

    it('should fail validation with invalid token', async () => {
      const client = new SDKClient(mockOctokit, '', '/test/repo');
      const result = await client.validate();

      expect(result).toBe(false);
    });

    it('should fail validation with authentication error', async () => {
      const errorClient = {
        users: {
          getAuthenticated: jest.fn().mockRejectedValue(
            new Error('Authentication failed')
          ),
        },
      } as any;

      const client = new SDKClient(errorClient, 'test-token', '/test/repo');
      const result = await client.validate();

      expect(result).toBe(false);
    });
  });
});
