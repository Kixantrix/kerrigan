/**
 * Mock implementation of @github/copilot-cli-sdk
 */

export class CopilotClient {
  async start(): Promise<void> {
    return Promise.resolve();
  }

  async stop(): Promise<void> {
    return Promise.resolve();
  }

  async createSession(config?: any): Promise<any> {
    return {
      send: async (message: any) => {
        return {
          content: 'SDK generated response',
        };
      },
    };
  }
}
