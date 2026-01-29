/**
 * Type definitions for SDK Agent Service
 */

export interface ServiceConfig {
  githubAppId: string;
  githubAppPrivateKey: string;
  githubToken?: string;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  retryAttempts: number;
  retryDelayMs: number;
  sdkTimeoutMs: number;
}

export interface IssueEvent {
  action: string;
  issue: {
    number: number;
    title: string;
    body: string;
    labels: Array<{ name: string }>;
    user: {
      login: string;
    };
    state: string;
  };
  repository: {
    name: string;
    owner: {
      login: string;
    };
    default_branch: string;
  };
}

export interface AgentRole {
  name: string;
  label: string;
  promptFile: string;
  description: string;
}

export interface AgentContext {
  issue: {
    number: number;
    title: string;
    body: string;
    labels: string[];
  };
  repository: {
    owner: string;
    name: string;
    defaultBranch: string;
  };
  role: string;
  artifacts: {
    constitution?: string;
    spec?: string;
    architecture?: string;
    plan?: string;
  };
  prompt: string;
}

export interface AgentResult {
  success: boolean;
  output?: string;
  prNumber?: number;
  branchName?: string;
  error?: string;
  logs?: string[];
}

export interface PRCreationOptions {
  owner: string;
  repo: string;
  issueNumber: number;
  branchName: string;
  title: string;
  body: string;
  labels?: string[];
}

export enum AgentStatus {
  STARTED = 'started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface StatusUpdate {
  status: AgentStatus;
  message: string;
  timestamp: Date;
  prNumber?: number;
  error?: string;
}

/**
 * Session state for tracking execution status
 */
export enum SessionState {
  CREATED = 'created',
  DISPATCHED = 'dispatched',
  RUNNING = 'running',
  IDLE = 'idle',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * Session information for tracking
 */
export interface SessionInfo {
  sessionId: string;
  issueNumber: number;
  issueContext: AgentContext;
  state: SessionState;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
  error?: string;
  prNumber?: number;
}

/**
 * Configuration for SwarmDispatcher
 */
export interface SwarmDispatcherConfig {
  maxConcurrentSessions: number;
  sessionTimeoutMs: number;
  retryAttempts: number;
  retryDelayMs: number;
}

/**
 * Dispatch result containing session ID
 */
export interface DispatchResult {
  sessionId: string;
  issueNumber: number;
  dispatched: boolean;
  error?: string;
}

/**
 * Batch dispatch result
 */
export interface BatchDispatchResult {
  successful: DispatchResult[];
  failed: DispatchResult[];
  total: number;
}
