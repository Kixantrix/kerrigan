# Worker Provider Contract

## Interface

```text
submit(TaskEnvelope) -> SubmissionAcknowledgement
cancel(taskId, reason) -> CancellationResult
inspect(providerRunId) -> ProviderRunState
subscribe(providerRunId, cursor?) -> WorkerEvent stream
resume(providerRunId) -> ProviderRun when supported
```

`submit` durably enqueues and returns an acknowledgment without waiting for provider startup. Startup and the provider run identity arrive as lifecycle events. Adapters declare optional capabilities such as `resume`, `interactive_questions`, and `artifact_streaming`. The assistant domain never branches on a provider name.

Cancellation is keyed by the durable task ID so it is valid before a provider run exists. The task service records cancellation intent atomically; if startup has not occurred the adapter must not start the task, and if a provider run appears concurrently the adapter forwards cancellation using its private run ID and reconciles the terminal event idempotently.

## Task envelope

```json
{
  "task_id": "task-id",
  "vault_workspace_id": "server-resolved-workspace-id",
  "agent": {
    "id": "home-projects",
    "instructions_ref": "agent-definition-revision",
    "model_preference": "provider-neutral-tier"
  },
  "request": "Reconcile the supplied synthetic project notes.",
  "expected_deliverable": "Updated plan and unresolved-question list",
  "recent_turns": [],
  "context_items": [
    {
      "type": "vault_excerpt",
      "id": "scoped-context-reference",
      "revision": "content-hash",
      "content_ref": "encrypted-access-scoped-content-reference"
    }
  ],
  "attachments": [],
  "permissions": {
    "tools": ["web.search"],
    "vault_read": ["Home/**"],
    "vault_write": ["Home/**"],
    "shell": false,
    "phone": false
  },
  "notification_policy": "normal"
}
```

The envelope is immutable after submission. `vault_workspace_id` is resolved and authorized by the server before the task is committed; every vault context item and path scope is interpreted only within that immutable workspace. Before every worker search, read, content-reference resolution, proposal, or mutation, the vault gateway revalidates the current workspace, credential, and grant state. Expiry or revocation takes effect immediately despite the frozen envelope and denies subsequent operations. `content_ref` resolves only through an encrypted, access-scoped channel with task/worker authorization, bounded retention, and audit; resolved note/image content is prohibited from ordinary provider metadata, logs, diagnostics, and results. Follow-up input becomes a new correlated event. Credentials and unrestricted roots are never included.

## Normalized events

Every provider event maps to:

```json
{
  "event_id": "event-id",
  "idempotency_key": "provider-stable-key",
  "task_id": "task-id",
  "provider_run_id": "opaque-provider-run",
  "sequence": 1,
  "type": "started",
  "occurred_at": "RFC3339 timestamp",
  "payload": {}
}
```

Allowed types are `created`, `started`, `progress`, `completed`, `failed`, and `cancelled`. A completed payload follows the result contract in `protocol.md`.

## Correctness rules

- `submit` must be idempotent for a task ID.
- A terminal task cannot return to a non-terminal state.
- Unknown or duplicate provider events are retained for diagnostics but do not repeat effects.
- Cancellation records intent even if the provider cannot stop immediately.
- Provider errors are normalized into stable codes; raw traces remain in restricted diagnostics.
- Adapter permission hooks deny tools outside the envelope before execution.
- Vault changes are proposals/results through the vault gateway, not direct personal filesystem writes.
- The assistant can answer and accept new tasks while a provider run is active.

## Copilot adapter

The initial adapter reuses the existing Copilot SDK runner and agent definitions, then maps SDK session/tool/lifecycle events to this contract. Authentication, SDK session IDs, hook shapes, and model IDs remain adapter-private.

Migration proceeds without changing stable `services/obsidian-agent` behavior:

1. Add contract tests around a fake `WorkerProvider`.
2. Wrap current `runAgent` behavior behind the interface.
3. Normalize pending file operations as vault change proposals.
4. Map lifecycle and cancellation where supported.
5. Route one synthetic specialist task through the adapter.
6. Only then consider replacing the legacy queue/API path.
