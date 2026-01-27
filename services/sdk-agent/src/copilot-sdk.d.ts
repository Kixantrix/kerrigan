/**
 * Type definitions for @github/copilot-sdk
 * 
 * These types define the expected interface for the GitHub Copilot SDK.
 * Package: @github/copilot-sdk
 */

declare module '@github/copilot-sdk' {
  /**
   * Session configuration options
   */
  export interface SessionConfig {
    model?: string;
    temperature?: number;
    maxTokens?: number;
  }

  /**
   * Message to send to the SDK
   */
  export interface Message {
    prompt: string;
    context?: Record<string, any>;
  }

  /**
   * Response from the SDK
   */
  export interface Response {
    content: string;
    usage?: {
      promptTokens: number;
      completionTokens: number;
      totalTokens: number;
    };
  }

  /**
   * Session interface for interacting with Copilot
   */
  export interface Session {
    /**
     * Send a message to the SDK and get a response
     */
    send(message: Message): Promise<Response>;
    
    /**
     * Close the session
     */
    close?(): Promise<void>;
  }

  /**
   * Main Copilot SDK Client
   */
  export class CopilotClient {
    /**
     * Start the Copilot client
     */
    start(): Promise<void>;

    /**
     * Stop the Copilot client
     */
    stop(): Promise<void>;

    /**
     * Create a new session
     */
    createSession(config?: SessionConfig): Promise<Session>;
  }
}
