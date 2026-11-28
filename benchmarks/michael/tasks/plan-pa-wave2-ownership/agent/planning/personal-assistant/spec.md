# Personal Assistant Platform Specification

**Feature Branch**: `kixantrix-local-obsidian-agent`  
**Created**: 2026-09-10  
**Status**: Draft  
**Input**: Build an Android-first, self-hostable personal assistant that preserves conversational continuity, performs bounded everyday actions, safely uses Obsidian as durable knowledge, and delegates independent workstreams to constrained asynchronous workers.

## Goal

Deliver a calm, fast, context-rich personal assistant that remains available for conversation while deeper work runs independently. The first usable release must work through an Android phone without smart-glasses hardware, keep personal knowledge under the user's control, and prove all vault behavior against artificial data before any personal vault can be connected.

## Scope

- One persistent logical assistant identity with resumable conversation context.
- Android voice and text interaction using the phone's microphone, speaker, camera, notifications, and supported device actions.
- Dynamic device capability registration and routing rather than platform-name assumptions.
- Fast, bounded actions for retrieval, capture, personal productivity, and supported phone operations.
- Explicit delegation of independent workstreams to specialist workers.
- Durable task lifecycle, completion events, notification queuing, and concise result summaries.
- Semantic Obsidian operations for search, read, quick capture, append, todo, and property updates.
- Capability-based authorization, consequence-aware confirmation, audit records, and revocation.
- Inspectable hot, warm, and cold context with explicit memory capture and deletion.
- A synthetic-vault environment and automated promotion gate that prevent accidental personal-vault access during development and validation.
- Portable contracts that can later support VIVE Eagle, Windows, web, alternate model providers, and alternate worker runtimes.

## Non-goals

- VIVE Eagle integration in the first usable release.
- Autonomous unsolicited project work.
- Generic shell or unrestricted filesystem access for the interactive assistant.
- Continuous camera capture or passive surveillance.
- Full local model inference or offline parity.
- Multi-user SaaS administration.
- iOS or Windows clients before the Android experience and core boundaries are proven.
- Replacing Obsidian as the user's explicit durable knowledge workspace.
- Using Obsidian files as the live task queue or event bus.
- Connecting to or mutating the user's personal vault during automated development or test runs.

## User Scenarios & Testing

### User Story 1 - Continue a natural assistant conversation (Priority: P1)

The user invokes the assistant on Android by voice or text, asks follow-up questions, interrupts speech, and resumes later without starting from a blank conversational state.

**Why this priority**: The product must first feel like one continuing assistant rather than a collection of commands.

**Independent Test**: Run a scripted multi-turn conversation through the Android test client and verify referents, interruption, reconnection, and resumption against deterministic providers.

**Acceptance Scenarios**:

1. **Given** a prior conversation with an active topic, **When** the user reconnects and asks a contextual follow-up, **Then** the assistant resolves the reference from retained session context.
2. **Given** the assistant is speaking, **When** the user begins speaking, **Then** playback yields promptly and the new turn is accepted.
3. **Given** the realtime connection sleeps while idle, **When** the user invokes the assistant again, **Then** the logical assistant state resumes without exposing transport details.

### User Story 2 - Use personal knowledge safely (Priority: P1)

The user searches and reads notes, captures information, appends a small update, or adds a todo through semantic vault actions whose effects are understandable.

**Why this priority**: Personal context and safe capture are the main advantage over generic assistants.

**Independent Test**: Exercise every supported vault action against a generated synthetic vault, inspect the exact proposed and applied changes, and prove that paths outside the synthetic root are inaccessible.

**Acceptance Scenarios**:

1. **Given** a generated synthetic vault, **When** the user asks a question answered by its notes, **Then** the assistant retrieves only relevant content and cites the source note.
2. **Given** a bounded capture request, **When** the user approves any required confirmation, **Then** only the intended synthetic note or section changes.
3. **Given** a path outside the authorized vault scope, **When** any component attempts to read or write it, **Then** the operation is rejected and audited.
4. **Given** no explicit promotion has occurred, **When** the system starts in development or test mode, **Then** it cannot select a personal vault path.

### User Story 3 - Delegate deeper work without blocking (Priority: P1)

The user assigns substantial research, coding, synthesis, or multi-note work to a specialist and immediately continues talking to the assistant.

**Why this priority**: The assistant/worker boundary is the defining product behavior.

**Independent Test**: Use a deterministic worker that remains pending while the user completes another assistant turn, then emits a normalized completion and notification.

**Acceptance Scenarios**:

1. **Given** a request that creates an independent workstream, **When** the assistant delegates it, **Then** it returns a task identifier and remains available without waiting for worker startup.
2. **Given** a worker is running, **When** the user asks an unrelated quick question, **Then** the assistant responds without worker interference.
3. **Given** a worker completes during an active turn, **When** interruption policy defers ordinary results, **Then** completion is queued and surfaced after a safe pause.
4. **Given** a completed worker result, **When** the user asks for details, **Then** the assistant answers from the normalized completion payload without restarting the worker.

### User Story 4 - Understand and control capabilities (Priority: P2)

The user can see which devices and services are connected, which capabilities are available, what consequential actions were requested, and what actually happened.

**Why this priority**: The assistant handles sensitive personal actions and must remain predictable.

**Independent Test**: Register synthetic phone and desktop devices, vary their advertised capabilities, and verify routing, confirmation, denial, revocation, and audit behavior.

**Acceptance Scenarios**:

1. **Given** multiple connected devices, **When** an action requires a capability, **Then** the system selects an authorized provider advertising that capability rather than assuming the interaction device can execute it.
2. **Given** a consequential action, **When** policy requires confirmation, **Then** no side effect occurs until confirmation succeeds.
3. **Given** a revoked capability, **When** the assistant attempts to use it, **Then** the action is denied with an understandable explanation.

### User Story 5 - Capture visual context explicitly (Priority: P2)

The user explicitly asks the phone camera to inspect or remember something and can continue the conversation using that visual referent.

**Why this priority**: Phone vision proves the interaction model before wearable hardware exists.

**Independent Test**: Supply fixture images through a synthetic camera capability and verify explicit activation, contextual follow-up, durable capture, and absence of passive capture.

**Acceptance Scenarios**:

1. **Given** the camera is inactive, **When** the user has not explicitly requested visual input, **Then** no image is captured or transmitted.
2. **Given** an explicit visual request, **When** an image is captured, **Then** the result remains available for contextual follow-up in the current conversation.
3. **Given** an explicit "remember this" request, **When** persistence succeeds, **Then** the user can inspect and delete the resulting memory and linked artifact.

### Edge Cases

- A device disconnects after accepting a capability request but before returning a result.
- Duplicate or out-of-order task events arrive after reconnect.
- A worker crashes, times out, is cancelled, or completes more than once.
- A vault note changes between read and write.
- A requested path uses traversal, aliases, case differences, encoded separators, or symlinks.
- A proposed change exceeds the granted scope or targets several files when only one was authorized.
- An ordinary completion arrives while the user is speaking, on a phone call, or in quiet mode.
- Realtime media is unavailable but text and notifications still work.
- Derived memory conflicts with explicit user-authored knowledge.
- The assistant cannot confidently decide whether a request is a quick action or independent workstream.

## Requirements

### Functional requirements

- **FR-001**: The system MUST maintain one logical assistant identity whose recent context, active tasks, and pending notifications survive transport reconnects.
- **FR-002**: The system MUST keep the interactive assistant available while delegated workers execute.
- **FR-003**: The system MUST classify requests into bounded action, confirmation-required action, delegated task, or clarification without creating autonomous unsolicited work.
- **FR-004**: The system MUST represent each connected client as an independently authenticated device with dynamically advertised input, output, and action capabilities.
- **FR-005**: The system MUST route each capability request using current availability, user policy, and required capability rather than platform-name checks.
- **FR-006**: The system MUST expose semantic, narrowly scoped vault operations instead of unrestricted filesystem or generic remote-control access.
- **FR-007**: The system MUST enforce worker-specific read and write scopes independently from interactive-assistant permissions.
- **FR-008**: The system MUST require consequence-aware confirmation before sensitive, destructive, multi-recipient, or otherwise policy-governed actions.
- **FR-009**: The system MUST record the requested action, authorization decision, execution status, and affected resource for consequential writes and actions without logging personal content by default.
- **FR-010**: The system MUST normalize worker lifecycle into created, started, progress, completed, failed, and cancelled events.
- **FR-011**: The system MUST persist task state durably and process duplicate lifecycle events idempotently.
- **FR-012**: The system MUST normalize worker results into a summary, artifact list, unresolved questions, and details pointer independent of worker provider.
- **FR-013**: The system MUST queue and route completion notifications according to urgency, conversation state, quiet mode, call state, and available output surfaces.
- **FR-014**: The system MUST support an assistant inbox that summarizes deferred completions, failures, reminders, confirmations, and important device notifications.
- **FR-015**: The system MUST distinguish transient hot context, retrievable context, explicit durable knowledge, derived memory, and worker history.
- **FR-016**: The user MUST be able to inspect, delete, disable, and export persistent assistant memory.
- **FR-017**: Camera access MUST require an explicit user interaction and remain visibly active for the full capture period; one-shot capture is the initial default.
- **FR-018**: Provider-specific objects and event schemas MUST NOT cross the product-domain contracts for conversation, capabilities, tasks, memory, or vault operations.
- **FR-019**: Development and automated tests MUST use generated synthetic application identities, devices, credentials, content, and vaults. An explicitly declared provider-adapter integration environment MAY use a repository-managed, non-personal, least-privilege test credential only with synthetic data, secret-store injection, egress controls, redacted logs, and revocation.
- **FR-020**: Personal-vault connectivity MUST be absent by default and require a separately documented, explicit promotion step after all synthetic-vault gates pass.
- **FR-021**: The promotion mechanism MUST reject repository paths, temporary test paths, ambiguous roots, and unapproved vault identifiers.
- **FR-022**: No automated test, CI workflow, or unattended worker MUST require or discover a personal vault path.
- **FR-023**: The system MUST remain usable through text when realtime audio, camera, or a model provider is unavailable.
- **FR-024**: The Android-first release MUST remain useful without VIVE Eagle hardware.
- **FR-025**: The system MUST expose redacted diagnostics for connection state, active session, capabilities, task status, queued notifications, routing, and latency.
- **FR-026**: Core text, push-to-talk, capture, and safe user-mediated actions MUST work without making the application the device's default assistant.
- **FR-027**: Optional wake-word behavior MUST be disabled by default, processed on-device, visibly indicate microphone use, provide an immediate stop control, and remain independently revocable.
- **FR-028**: Logical assistant continuity MUST survive process death, extended network loss, device sleep, and reboot without relying on a permanently connected media session.
- **FR-029**: System-notification ingestion MUST be optional, package/category scoped, redact sensitive content, and expose reply only when the source notification provides a supported reply action.
- **FR-030**: Initial messaging, calling, and navigation actions MUST prefer user-mediated compose, dial, and navigation flows; direct send or call requires a separately granted and audited capability.

### Request classification precedence

| Precedence | Condition | Classification | Rule |
|---|---|---|---|
| 1 | Required goal, referent, target, or consequence is materially ambiguous | `clarification` | Ask only for the missing decision; do not route, execute, or create a task |
| 2 | The request creates work that should continue independently while conversation remains available: substantial research, coding, multi-file reconciliation, iterative debugging, or a long tool loop | `delegated_task` | Durably create a scoped task; worker writes/actions still obey their own capability and confirmation policies |
| 3 | The request is bounded but its side effect, sensitivity, recipient count, destructiveness, or policy requires approval | `confirmation_required_action` | Prepare the canonical action and obtain valid confirmation before provider inspection or execution |
| 4 | The request is bounded, sufficiently specified, within a live grant, and does not require confirmation | `bounded_action` | Execute directly within the active turn |

Ambiguity always wins. Independent-workstream classification is based on separable work, not tool count or whether the request writes. Consequence policy governs bounded actions and every worker side effect independently. No category permits unsolicited work.

### Key entities

- **Assistant Session**: The logical conversation identity, summary, recent turns, active topics, context references, and pending notifications.
- **Device**: An authenticated client, its presence, modality state, and currently advertised capabilities.
- **Capability Grant**: User policy describing who may invoke a semantic action, with scope, confirmation level, and revocation state.
- **Capability Request**: A versioned request for a bounded action and its correlated result.
- **Task**: A delegated independent workstream with origin, worker, status, context package, permission envelope, notification policy, and timestamps.
- **Worker Result**: A provider-neutral task outcome containing summary, artifacts, questions, and a details pointer.
- **Assistant Inbox Item**: Deferred information requiring later delivery or user attention.
- **Memory Record**: Inspectable durable personal context with provenance, retention category, and deletion state.
- **Vault Workspace**: An explicitly identified synthetic or promoted knowledge root with allowed semantic operations and concurrency metadata.
- **Audit Record**: Redacted evidence of authorization and consequential execution.

## Acceptance criteria

- **AC-001**: A scripted three-turn interaction retains referents across reconnect without exposing transport or provider details.
- **AC-002**: A quick synthetic-vault capture completes without creating a worker task and changes only the expected note fragment.
- **AC-003**: A substantial multi-note request creates a worker task, acknowledges delegation before worker startup completes, and leaves the assistant able to answer another turn.
- **AC-004**: Worker completion produces one normalized result and one policy-routed notification even when duplicate completion events are delivered.
- **AC-005**: An unauthorized, traversal-based, or out-of-root vault operation is denied and produces a redacted audit record.
- **AC-006**: Fresh development and CI runs can complete all tests without a personal vault path, personal content, or personal service credential.
- **AC-007**: No personal vault can be selected until a separate promotion command verifies an explicit approved root and records user consent.
- **AC-008**: A capability request routes to the authorized connected device advertising the required capability and fails clearly when no provider is available.
- **AC-009**: Consequential actions cannot execute before their required confirmation state is satisfied.
- **AC-010**: Notification routing distinguishes urgent from ordinary events across active speech, quiet mode, call state, and available output surfaces without losing deferred items.
- **AC-011**: Explicit camera capture supports one contextual follow-up; no image is acquired when camera activation was not requested.
- **AC-012**: Persistent memories can be listed, disabled, re-enabled, exported, and deleted, including provenance for each record.
- **AC-013**: A deterministic request corpus is classified as bounded action, confirmation-required action, delegated task, or clarification according to the independent-workstream and consequence rules.
- **AC-014**: Contract tests prove that conversation, capability, task, memory, and vault domain messages serialize without provider-specific types or fields.
- **AC-015**: Diagnostics report connection, session, capability, task, inbox, routing, and latency state while redacting personal content and credentials.
- **AC-016**: Every core assistant scenario has a working text path when realtime audio is unavailable.
- **AC-017**: Optional notification ingestion and direct communication actions remain scoped, redacted, separately granted, audited, and immediately revocable.
- **AC-018**: The foundation package builds, validates its schemas, passes its protocol/policy/path tests, and completes two idempotent synthetic smoke runs with zero instrumented out-of-root vault I/O.
- **AC-019**: One existing Copilot specialist runs through the provider adapter against a synthetic workspace, stays within its permission envelope, and emits one normalized terminal result.
- **AC-020**: A timed clean-checkout quickstart completes the available synthetic scenarios within ten minutes without personal credentials.
- **AC-021**: The isolated Obsidian adapter passes generated-vault concurrency, stale-revision, mode, preview, revocation, traversal, and failure attestations without discovering a personal vault.
- **AC-022**: Context assembly preserves distinct lifecycle, provenance, retrieval, and deletion semantics for hot context, retrievable context, explicit durable knowledge, derived memory, and worker history.

## Success Criteria

### Measurable outcomes

- **SC-001**: In scripted interaction tests, at least 95% of follow-up references across a reconnect resolve to the intended prior subject.
- **SC-002**: The assistant acknowledges a delegated task within one second of durable task creation without waiting for worker execution.
- **SC-003**: A user can complete a bounded vault capture in one conversational turn, with the exact affected note and change visible afterward.
- **SC-004**: All automated development and CI scenarios run exclusively on generated synthetic data and demonstrate zero reads or writes outside their authorized roots.
- **SC-005**: Duplicate and out-of-order worker events never create duplicate user notifications or regress a task to an earlier state.
- **SC-006**: A disconnected or incapable device never receives an action it did not advertise and authorize.
- **SC-007**: In interruption scenarios, ordinary notifications never overlap active user speech and are recoverable from the assistant inbox.
- **SC-008**: A new contributor can start the synthetic end-to-end environment and complete the primary quick-action and delegation scenarios in under ten minutes without personal credentials.
- **SC-009**: The first Android release supports text fallback for every core assistant scenario when realtime audio is unavailable.
- **SC-010**: Personal-vault enablement remains a separate, auditable operator action and is not exercised by automated tests.

## Assumptions

- The initial product has one owner, while protocols retain explicit user and device identity for future expansion.
- Cloud model providers are acceptable initially when personal data exposure is explicit and provider boundaries remain replaceable.
- Android is the first interaction client; smart-glasses support begins only after the phone experience and protocol boundaries are proven.
- Obsidian remains canonical for explicit project knowledge, while transient conversation state and live task state use purpose-built storage.
- Existing Obsidian agent definitions and Copilot-based worker behavior should be adapted rather than discarded.
- The first implementation may use deterministic fake providers to prove product boundaries before connecting realtime media, worker, calendar, messaging, or vault integrations.
- Human attestation is required for final Android hardware behavior and for any future personal-vault promotion.
