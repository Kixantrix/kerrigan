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
   * Message options for sending to the SDK
   */
  export interface MessageOptions {
    prompt: string;
    attachments?: Array<{type: string; path?: string; content?: string}>;
  }

  /**
   * Assistant message event data
   */
  export interface AssistantMessageData {
    content: string;
    role: string;
  }

  /**
   * Assistant message event
   */
  export interface AssistantMessageEvent {
    type: 'assistant.message';
    data: AssistantMessageData;
  }

  /**
   * Session interface for interacting with Copilot
   */
  export interface Session {
    /**
     * Send a message to the SDK (non-blocking)
     * Returns immediately without waiting for response
     */
    send(options: MessageOptions): Promise<void>;
    
    /**
     * Send a message and wait for completion
     */
    sendAndWait(options: MessageOptions, timeout?: number): Promise<AssistantMessageEvent | undefined>;
    
    /**
     * Subscribe to session events
     */
    on(handler: (event: any) => void): void;
    
    /**
     * Destroy the session
     */
    destroy(): Promise<void>;
  }

  /**
   * Client options
   */
  export interface CopilotClientOptions {
    logLevel?: string;
    cliPath?: string;
    autoStart?: boolean;
  }

  /**
   * Main Copilot SDK Client
   */
  export class CopilotClient {
    constructor(options?: CopilotClientOptions);
    
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
