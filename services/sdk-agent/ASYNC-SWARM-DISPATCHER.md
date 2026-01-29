# Async Swarm Dispatcher

The Async Swarm Dispatcher enables parallel processing of multiple GitHub issues using the Copilot SDK's non-blocking `send()` API.

## Architecture

The dispatcher consists of three main components:

1. **SwarmDispatcher** - Orchestrates parallel issue dispatching
2. **SessionManager** - Manages session lifecycle and state
3. **CompletionHandler** - Handles session events and triggers PR creation

```
                    ┌─→ Session 1 (Issue #1) ─→ idle event ─→ PR #1
Dispatcher ─────────┼─→ Session 2 (Issue #2) ─→ idle event ─→ PR #2  
  (6ms each)        └─→ Session 3 (Issue #3) ─→ idle event ─→ PR #3
```

## Installation

The dispatcher is part of the SDK Agent service:

```bash
cd services/sdk-agent
npm install
```

## Usage

### Basic Usage - Single Issue

```typescript
import { SwarmDispatcher } from './swarm-dispatcher';
import { AgentContext } from './types';
import { Octokit } from '@octokit/rest';

// Initialize
const octokit = new Octokit({ auth: 'your-token' });
const dispatcher = new SwarmDispatcher(octokit, 'github-token');

// Prepare issue context
const context: AgentContext = {
  issue: {
    number: 123,
    title: 'Implement feature X',
    body: 'Feature description...',
    labels: ['role:swe', 'agent:go'],
  },
  repository: {
    owner: 'your-org',
    name: 'your-repo',
    defaultBranch: 'main',
  },
  role: 'swe',
  artifacts: {},
  prompt: 'Your agent prompt here...',
};

// Dispatch (returns immediately)
const result = await dispatcher.dispatchIssue(context);
console.log(`Dispatched: ${result.sessionId}`);

// Sessions run in background, PRs created on completion
```

### Batch Processing - Multiple Issues

```typescript
// Prepare multiple contexts
const contexts: AgentContext[] = [
  { /* issue 1 */ },
  { /* issue 2 */ },
  { /* issue 3 */ },
];

// Dispatch all in parallel
const batchResult = await dispatcher.dispatchBatch(contexts);

console.log(`Successful: ${batchResult.successful.length}`);
console.log(`Failed: ${batchResult.failed.length}`);
```

### Configuration

```typescript
const dispatcher = new SwarmDispatcher(octokit, token, {
  maxConcurrentSessions: 10,      // Max parallel sessions
  sessionTimeoutMs: 300000,        // 5 minute timeout
  retryAttempts: 3,                // Retry failed dispatches
  retryDelayMs: 1000,              // Delay between retries
});
```

### Monitoring Sessions

```typescript
// Get active session count
const count = dispatcher.getActiveSessionCount();

// Get all sessions
const sessions = dispatcher.getAllSessions();

// Get session manager for direct access
const manager = dispatcher.getSessionManager();
const session = manager.getSession('session-id');
console.log(`State: ${session?.state}`);
```

### Cleanup

```typescript
// Stop dispatcher and cleanup
await dispatcher.stop();
```

## Session Lifecycle

Sessions progress through the following states:

1. **CREATED** - Session initialized
2. **DISPATCHED** - Prompt sent (non-blocking)
3. **RUNNING** - Agent is processing
4. **IDLE** - Agent completed, PR creation triggered
5. **COMPLETED** - PR created successfully
6. **FAILED** - Error occurred

## Event Handling

The CompletionHandler subscribes to SDK session events:

- `session.idle` - Agent completed, triggers PR creation
- `assistant.message` - Response content received
- `error` - Error occurred, marks session as failed

## State Persistence

Sessions are persisted to `/tmp/swarm-sessions.json` for recovery:

```typescript
// Custom persistence path
const manager = new SessionManager('/path/to/sessions.json');
```

## Testing

Run the test suite:

```bash
npm test
```

Run specific tests:

```bash
npm test -- session-manager.test.ts
npm test -- swarm-dispatcher.test.ts
npm test -- completion-handler.test.ts
```

## API Reference

### SwarmDispatcher

#### `dispatchIssue(context: AgentContext): Promise<DispatchResult>`

Dispatches a single issue for processing. Returns immediately after sending the prompt.

**Returns:**
```typescript
{
  sessionId: string;      // Unique session identifier
  issueNumber: number;    // Issue number
  dispatched: boolean;    // Success indicator
  error?: string;         // Error message if failed
}
```

#### `dispatchBatch(contexts: AgentContext[]): Promise<BatchDispatchResult>`

Dispatches multiple issues in parallel.

**Returns:**
```typescript
{
  successful: DispatchResult[];  // Successfully dispatched
  failed: DispatchResult[];      // Failed to dispatch
  total: number;                 // Total count
}
```

#### `getActiveSessionCount(): number`

Returns the number of active (non-completed) sessions.

#### `getAllSessions(): SessionInfo[]`

Returns all registered sessions.

#### `stop(): Promise<void>`

Stops the dispatcher, cleans up SDK client, and removes completed sessions.

### SessionManager

#### `registerSession(sessionInfo: SessionInfo): void`

Registers a new session in the manager.

#### `updateSessionState(sessionId: string, state: SessionState, error?: string): void`

Updates a session's state.

#### `getSession(sessionId: string): SessionInfo | undefined`

Retrieves a session by ID.

#### `getSessionByIssue(issueNumber: number): SessionInfo | undefined`

Retrieves a session by issue number.

#### `getActiveSessions(): SessionInfo[]`

Returns all active sessions.

#### `cleanupCompletedSessions(): void`

Removes completed and failed sessions.

### CompletionHandler

#### `subscribeToSession(session: any, sessionId: string): void`

Subscribes to events from an SDK session.

## Examples

### Example 1: Process Multiple Issues from GitHub Search

```typescript
import { Octokit } from '@octokit/rest';
import { SwarmDispatcher } from './swarm-dispatcher';
import { AgentOrchestrator } from './agent-orchestrator';

const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
const dispatcher = new SwarmDispatcher(octokit, process.env.GITHUB_TOKEN!);

// Search for issues with agent:go label
const { data: issues } = await octokit.issues.listForRepo({
  owner: 'your-org',
  repo: 'your-repo',
  labels: 'agent:go',
  state: 'open',
});

// Prepare contexts
const contexts = issues.map(issue => ({
  issue: {
    number: issue.number,
    title: issue.title,
    body: issue.body || '',
    labels: issue.labels.map(l => typeof l === 'string' ? l : l.name || ''),
  },
  repository: {
    owner: 'your-org',
    name: 'your-repo',
    defaultBranch: 'main',
  },
  role: AgentOrchestrator.determineRole(issue.labels).name,
  artifacts: {},
  prompt: 'Your prompt...',
}));

// Dispatch all in parallel
const result = await dispatcher.dispatchBatch(contexts);
console.log(`Processing ${result.successful.length} issues in parallel...`);

// PRs will be created automatically as sessions complete
```

### Example 2: Monitor Session Progress

```typescript
const dispatcher = new SwarmDispatcher(octokit, token);

// Dispatch issues
await dispatcher.dispatchIssue(context1);
await dispatcher.dispatchIssue(context2);

// Poll for completion
const checkInterval = setInterval(() => {
  const active = dispatcher.getActiveSessionCount();
  console.log(`Active sessions: ${active}`);
  
  if (active === 0) {
    console.log('All sessions completed!');
    clearInterval(checkInterval);
    dispatcher.stop();
  }
}, 5000);
```

## Performance

- **Dispatch time**: ~6ms per issue (non-blocking)
- **Concurrent limit**: Configurable (default: 10)
- **Session timeout**: Configurable (default: 5 minutes)

## Limitations

- Requires Copilot CLI installed and authenticated
- Depends on infrastructure setup from Issue #160
- Sessions must complete within timeout period
- Maximum concurrent sessions enforced

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT
