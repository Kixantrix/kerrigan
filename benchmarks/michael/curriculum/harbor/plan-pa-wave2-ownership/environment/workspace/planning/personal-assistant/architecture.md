# Architecture: Personal Assistant Platform

## Overview

The platform is an Android-first personal assistant built as a **modular monolith plus an isolated worker process**. The assistant owns conversational continuity, bounded actions, capability policy, task state, notifications, and context selection. Specialist workers own independent workstreams and report provider-neutral lifecycle events.

The first implementation deliberately avoids a service mesh:

```text
Android client
  - text / push-to-talk / camera
  - device capability providers
  - completion notifications
          |
          | HTTPS + active-session WebRTC
          v
Assistant runtime (modular monolith)
  - session/context
  - capability router and confirmation policy
  - task/outbox/inbox
  - semantic vault gateway
  - provider interfaces
          |
          +--> PostgreSQL + pgvector
          |
          +--> Copilot worker process
          |
          +--> local Obsidian adapter
```

LiveKit carries active realtime media and interaction data. It does not own durable assistant state. PostgreSQL owns assistant sessions, tasks, capability grants, inbox items, memories, audit records, and a transactional event outbox. Server-sent events deliver durable task and inbox updates to clients; mobile background delivery uses platform notifications.

All development begins in **synthetic mode**. A vault workspace is not an arbitrary path: it is a typed identity with `synthetic` or `promoted` trust. Only generated synthetic workspaces are accepted by normal development and CI configuration. Personal access requires a separate administrative promotion procedure after all synthetic gates pass, starts read-only, and records redacted evidence.

## Components & interfaces

### Android client

A native Kotlin/Jetpack Compose application provides:

- text and push-to-talk interaction without requiring default-assistant status;
- a user-visible active-conversation foreground service for microphone and playback;
- one-shot CameraX capture with explicit activation;
- dynamic capability advertisements with leases and current permission state;
- user-mediated compose-message, dial, and navigation actions;
- task/inbox notifications and a redacted diagnostics screen;
- optional, separately revocable default-assistant, wake-word, and notification-listener capabilities.

The always-running `VoiceInteractionService`, when enabled, remains lightweight. Realtime media starts only for an active user-visible conversation. A LiveKit room may disappear during sleep, process death, reboot, or extended network loss; the client resumes from durable server state.

### Assistant runtime

The runtime is organized into domain modules with no provider-specific objects in their public contracts:

| Module | Responsibility |
|---|---|
| Session | Logical assistant identity, recent turns, summaries, active topics |
| Context | Hot context assembly and warm/cold retrieval |
| Capability | Advertisements, grants, routing, confirmations, correlated results |
| Task | Delegation decision, lifecycle state machine, context package, cancellation |
| Inbox | Interruption policy, deferred delivery, catch-up summaries |
| Vault | Semantic operations, workspace trust, structural diffs, concurrency |
| Memory | Inspectable durable records, retrieval, export, deletion |
| Audit | Redacted consequential-action and authorization evidence |
| Provider | Replaceable conversation, vision, worker, embedding, and delivery adapters |

Initial APIs use boring versioned HTTP for bootstrap, settings, history, task browsing, memory administration, and capability requests. SSE streams durable outbox events using event IDs for reconnect. LiveKit handles audio/video and low-latency active-session data only.

### Protocol package

The protocol package defines versioned schemas for:

- `DeviceHello` and `DeviceCapabilitiesChanged`;
- `InteractionStarted` and `InteractionEnded`;
- `CapabilityRequest` and `CapabilityResult`;
- `TaskDelegated` and `TaskStatusChanged`;
- `NotificationQueued` and `NotificationDelivered`;
- `MemoryCaptured`;
- normalized errors and correlation/idempotency keys.

Capability advertisements include device instance, schema version, expiry, heartbeat, availability, permission state, and confirmation class. Advertisements describe current availability; authorization remains server-side.

### Durable task and event backbone

PostgreSQL is the Stage 1 source of truth. A domain update and immutable outbox event are committed in one transaction. Dispatchers claim rows with `FOR UPDATE SKIP LOCKED`; optional `LISTEN/NOTIFY` wakes them but never replaces durable polling.

External side effects use idempotency keys. Consumers tolerate duplicate and out-of-order delivery. SSE event IDs map to durable outbox IDs so a reconnect can resume from `Last-Event-ID`.

NATS JetStream is deferred until independently deployed consumers, multi-language fan-out, replay volume, or availability needs justify another operational dependency.

### Worker provider

The worker boundary is asynchronous and provider-neutral:

```text
WorkerProvider
  submit(taskEnvelope) -> submissionAcknowledgement
  cancel(taskId, reason)
  inspect(providerRunId)
  subscribe(providerRunId) -> normalized lifecycle events
  resume(providerRunId) -> optional provider capability
```

The task envelope contains the explicit request, selected specialist, relevant recent turns, selected vault excerpts, attachments, expected deliverable, tool scopes, vault read/write scopes, and notification policy. It never contains unrestricted credentials or the entire assistant context.

The existing `services/obsidian-agent` Copilot SDK runner, agent definitions, permission scopes, queue lifecycle, and normalized file-operation results are migration inputs. A new Copilot adapter wraps them rather than exposing Copilot session events to the assistant domain. Existing behavior remains available while slices move behind the new interface.

### Vault capability gateway

The gateway exposes semantic operations:

```text
vault.search
vault.read
vault.quick_capture
vault.append
vault.add_todo
vault.update_property
vault.propose_patch
vault.apply_approved_patch
```

Stage 1 reuses the official Obsidian Plugin API and `coddingtonbear/markdown-patch` for structural edits. Patch computation and version verification execute inside `Vault.process()` for atomic read-modify-write behavior. A wrapped `obsidian-local-rest-api` 5.1.0+ may be used as local read/REST prior art, but raw REST/MCP, arbitrary commands, and permanent deletion are never exposed to a model.

Search indexing is a separate derived projection with note/section identity, content hash, provenance, and embeddings. Obsidian remains canonical for explicit knowledge; the index can be rebuilt.

### Memory

Stage 1 stores inspectable memory records and embeddings in PostgreSQL/pgvector. Explicit facts, derived text, provenance, extractor/model version, confidence, consent state, and deletion state remain queryable and exportable.

Mem0 may be evaluated later behind `MemoryProvider`, with telemetry disabled and outbound providers explicitly configured. It will not become the only copy of memory, provenance, or consent.

### Synthetic-vault promotion gate

Synthetic mode creates a physically separate generated vault and credential. Every operation is:

1. resolved against a typed synthetic workspace;
2. checked against semantic operation and path scopes;
3. dry-run to an exact structural diff;
4. confirmed when policy requires;
5. serialized per note;
6. version-checked atomically;
7. applied and re-read for hash/invariant verification;
8. recorded in a redacted audit trail.

Promotion is not an environment-variable toggle. A separate administrative command records adapter version, synthetic suite revision, target vault identity, allowed folders/types/operations, expiry, approving principal, and rollback checkpoint. It issues a distinct read-only credential. Structural writes are enabled only through another explicit approval; permanent delete and arbitrary commands remain disabled.

## Tradeoffs

| Decision | Chosen | Alternative | Rationale |
|---|---|---|---|
| Initial process topology | Modular monolith + worker | Many microservices | Preserves boundaries without premature deployment complexity |
| Active realtime transport | Self-hosted LiveKit | Pipecat/SmallWebRTC/direct provider | Strongest maintained native Android SDK, reconnection, media, data, and interruption ecosystem |
| Durable state | PostgreSQL | LiveKit state, files, NATS-only | Transactions, inspection, backup, and one operational source of truth |
| Task/event delivery | Transactional outbox + SSE | NATS JetStream initially | Sufficient for Stage 1 and avoids dual-write and cluster operations |
| Vector retrieval | pgvector | Dedicated vector database | Keeps provenance and vectors transactional until scale requires separation |
| Vault writes | Custom semantic gateway + atomic structural patch | Raw filesystem or generic REST/MCP | Narrow authorization, understandable diffs, concurrency safety |
| Worker runtime | Copilot SDK adapter | Rebuild workers immediately | Reuses existing agents and tested implementation while preserving replaceability |
| Android actions | User-mediated intents first | Direct privileged actions | Lower permission and consequence risk; direct actions can be added as explicit grants |
| Wake word | Optional, on-device, off by default | Mandatory always-listening | Battery, Android lifecycle, privacy, and portability constraints |
| Memory | Explicit records first | Mem0 as foundation | Inspectability, deletion, provenance, and provider independence |

## Security & privacy notes

- Each device and adapter receives a distinct revocable identity; no shared universal credential is placed in prompts.
- Tool authorization is capability- and scope-based. Device advertisements never grant authority.
- The realtime assistant has no generic shell, arbitrary filesystem, raw REST, plugin-management, or permanent-delete tool.
- Consequential actions require policy-specific confirmation and idempotency keys.
- Vault workers receive independent allow/deny scopes and only selected context.
- Personal note bodies, prompts, messages, contacts, images, and tokens are excluded from default logs.
- Camera and microphone activity remain user-visible and are activated only for supported interaction states.
- Notification ingestion is opt-in, package/category scoped, redacts sensitive content, and does not assume OTP or work-profile access.
- Tests and CI reject discovered Obsidian settings, home-directory vault paths, personal credentials, and non-generated workspace identities.
- The initial promoted personal credential is read-only, time/scoped, and separately revocable.
- Provider egress is explicit in configuration and diagnostics so "self-hosted" does not conceal external model, TURN, notification, or speech dependencies.

## Architecture decision records

1. **ADR-001**: Android/Compose + LiveKit for active interaction; logical state is durable outside LiveKit.
2. **ADR-002**: PostgreSQL transactional outbox and SSE precede NATS JetStream.
3. **ADR-003**: Official Obsidian API + atomic `markdown-patch` gateway precede generic REST exposure.
4. **ADR-004**: Copilot SDK remains the first worker provider behind normalized contracts.
5. **ADR-005**: Explicit PostgreSQL memory records precede Mem0 adoption.
6. **ADR-006**: Synthetic-vault-only defaults and administrative promotion are non-bypassable trust boundaries.
