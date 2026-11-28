# Runbook: Personal Assistant Platform

## Operating modes

| Mode | Allowed workspaces | Credentials | Intended use |
|---|---|---|---|
| `test` | Generated `synthetic` only | Ephemeral fixture credentials | Unit/integration/CI |
| `development` | Fresh generated `synthetic` only | Ephemeral local development credentials | Manual synthetic testing |
| `production-readonly` | Explicitly `promoted` read-only workspace | Distinct scoped secret-store reference | User-approved retrieval |
| `production-write` | Separately promoted structural-write scopes | Distinct scoped secret-store reference | Future, not implied by initial promotion |

The service must refuse to start if test/development mode is configured with a promoted workspace or raw vault path.

## Synthetic environment

1. Start the documented local backing services.
2. Generate a fresh synthetic vault and manifest.
3. Run unit, integration, adversarial path, deterministic E2E, and smoke tests.
4. Inspect the I/O manifest; zero operations may appear outside the generated root.
5. Run the smoke test twice to verify idempotency.

No step scans home directories, Obsidian configuration, recent files, mounted drives, or environment variables for a vault.

## Secrets

Store server signing keys, database credentials, provider credentials, adapter credentials, and LiveKit keys in the deployment secret store. Clients receive short-lived scoped tokens only.

Never place in source, logs, test fixtures, or promotion receipts:

- model/provider secrets;
- Obsidian adapter keys;
- raw personal vault roots;
- contact or message content;
- note bodies or images.

Approved task envelopes may contain the minimum selected note excerpts or attachments required by the worker contract. That content uses an encrypted, access-scoped channel with explicit workspace binding and retention; it is never copied into logs, receipts, diagnostics, or unrestricted provider metadata.

## Observability

Default telemetry includes:

- correlation IDs and redacted user/device/task identities;
- state transitions and authorization decisions;
- adapter/provider/version;
- timing for invocation, speech end, first token/audio, capability execution, worker dispatch/completion, and notification delivery;
- retry counts and stable error codes.

Diagnostic content capture is opt-in, time-limited, clearly visible, and separately purged.

## Failure handling

### Task dispatcher unavailable

- Durable tasks and outbox events remain pending.
- Assistant acknowledgment is allowed only after the task transaction commits.
- Restarted dispatchers scan available outbox rows before relying on notifications.

### Duplicate or out-of-order events

- Deduplicate by idempotency key.
- Reject state regression.
- Retain redacted diagnostic evidence.
- Do not create another inbox item or repeat an external effect.

### Device disconnect

- Expire its capability leases.
- Mark in-flight requests unavailable or reconcile by idempotency key on reconnect.
- Keep assistant/task/inbox state durable.

### Vault stale revision

- Apply no write.
- Return `vault.stale_revision`.
- Re-read, regenerate an exact diff, and require renewed confirmation when consequence changes.

### Vault adapter unavailable

- Do not fall back to arbitrary filesystem access.
- Keep proposed changes pending or fail clearly.
- Existing personal data remains untouched.

### Worker provider failure

- Normalize the failure and preserve available progress/details.
- Queue one failure inbox item according to policy.
- Retry only when the task policy and idempotency guarantees permit it.

## Backup and recovery

- Back up PostgreSQL and attachment storage using deployment-native encrypted backups.
- Treat Obsidian as canonical for explicit notes; derived indexes are rebuildable.
- Promotion requires a rollback/backup checkpoint before issuing access.
- Restore tests use synthetic data.
- Memory deletion tombstones are restored with backups so a rebuild cannot resurrect deleted records.

## Personal-vault promotion gate

This procedure is intentionally unavailable to unattended agents.

Preconditions:

1. All cloud synthetic gates pass at the target commit.
2. The synthetic fixture revision and result hash are recorded.
3. The adapter/version is pinned and has passed concurrency, traversal, stale-version, and failure tests.
4. The user explicitly selects the target vault and read scopes.
5. A rollback/backup checkpoint exists.

Promotion records a redacted receipt with the approver and expiry, then issues a distinct read-only credential. Verify read scope and revocation using non-sensitive test notes chosen by the user. Do not enable writes.

Structural-write promotion, if requested later, requires a new decision and attestation. Permanent delete, arbitrary command execution, plugin installation, and generic raw-path tools remain disabled.

## Android attestation

Test API 31, 34, 35, 36, and 37 where available, including Pixel and Samsung hardware, Bluetooth routing, call interruption, Doze, process death, reboot, network handoff, camera/microphone privacy toggles, and permission revocation.

Record only device class, OS/app versions, test IDs, timestamps, outcomes, and redacted evidence.

## Rollback

- Server: deploy the previous known-good container and run schema-compatible health checks.
- Android: disable affected capability flags/server grants; do not depend solely on app rollback.
- Adapter: revoke the credential and workspace immediately, then restore from the required checkpoint if a verified write occurred.
- Provider: switch the adapter off; durable domain state remains authoritative.
