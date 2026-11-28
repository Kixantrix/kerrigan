# Acceptance Tests: Personal Assistant Platform

Every criterion is assigned one primary test level and one execution environment. Automated tests use generated identities, devices, credentials, content, and vault roots.

## Foundation scenarios

### AT-001 - Conversation continuity

- **Covers**: AC-001
- **Level**: integration
- **Environment**: cloud-linux
- **Given** a deterministic corpus of at least 100 multi-turn conversations with labeled follow-up referents
- **When** every conversation disconnects and reconnects before its labeled follow-up
- **Then** at least 95% resolve the intended referent without creating a new logical assistant identity
- **And** failures identify corpus case IDs without logging personal content

### AT-002 - Quick capture stays bounded

- **Covers**: AC-002
- **Level**: integration
- **Environment**: cloud-linux
- **Given** a generated vault fixture and a `vault.quick_capture` grant restricted to its Inbox
- **When** the user searches and reads cited content, then proposes quick capture, append, todo, and typed-property updates
- **Then** retrieval cites stable note/section identities and each mutation produces an exact revision-bound diff
- **And** approved changes affect only the addressed structure while stale revisions, ambiguous targets, and unapproved proposals make no change
- **And** the quick-capture request creates no task record, invokes no worker provider, and completes entirely through the bounded vault capability

### AT-003 - Deep work delegates asynchronously

- **Covers**: AC-003
- **Level**: integration
- **Environment**: cloud-linux
- **Given** a deterministic worker whose startup is held pending
- **When** the user requests reconciliation of several project notes
- **Then** a durable task/outbox transaction commits and acknowledgment is observed within one second on a monotonic clock, before worker startup completes
- **And** the same assistant session answers an unrelated follow-up while the worker remains pending

### AT-004 - Completion is idempotent

- **Covers**: AC-004
- **Level**: integration
- **Environment**: cloud-linux
- **Given** a running task
- **When** completed events with the same idempotency key arrive twice, followed by separately keyed lower-sequence progress and failure events
- **Then** the task remains completed, exactly one provider-neutral result is persisted, and exactly one notification is routed according to the task's notification policy

### AT-005 - Vault boundary enforcement

- **Covers**: AC-005
- **Level**: integration
- **Environment**: cloud-linux
- **Given** a generated vault with a path-scoped credential
- **When** encoded traversal, absolute paths, sibling roots, symlink escapes, case variants, and denied prefixes are requested
- **Then** every request is denied before I/O and a redacted audit record identifies the denial reason

### AT-006 - Clean synthetic verification suite

- **Covers**: AC-006
- **Level**: integration
- **Environment**: cloud-linux
- **Given** a clean checkout with no personal credentials or machine paths
- **When** CI runs build/type-check, unit, integration, adversarial path, schema, deterministic E2E, and smoke gates
- **Then** every gate passes without discovering a personal path or credential
- **And** each vault-capable process emits an I/O manifest proving all instrumented vault reads and writes stayed under its generated root

### AT-007 - Explicit vault promotion

- **Covers**: AC-007
- **Level**: scenario
- **Environment**: local-attested-personal-vault
- **Given** promotion is not approved, **When** a personal, repository, temporary-test, ambiguous, or unapproved target is selected, **Then** access is denied and no credential is issued
- **Given** all automated synthetic-vault gates are green
- **When** an authorized operator runs the documented promotion procedure against an explicitly selected vault identity
- **Then** the procedure records consent, adapter version, approved scopes, test evidence, expiry, and rollback checkpoint
- **And** initial access is read-only
- **When** the promoted workspace or credential is revoked, **Then** subsequent reads are denied immediately
- **Evidence required**: redacted promotion receipt and synthetic-suite revision; no personal note content

### AT-008 - Dynamic capability routing

- **Covers**: AC-008
- **Level**: integration
- **Environment**: cloud-linux
- **Given** synthetic phone and desktop devices with different advertised capabilities
- **When** a clipboard action is requested
- **Then** only the authorized connected desktop receives the request
- **And** the request fails clearly if that capability disappears before dispatch

### AT-009 - Confirmation gate

- **Covers**: AC-009
- **Level**: integration
- **Environment**: cloud-linux
- **Given** a multi-recipient message capability requiring confirmation
- **When** the action is prepared but confirmation is absent, rejected, expired, or mismatched
- **Then** the capability provider records no side effect
- **Given** a revoked grant, **When** the same action is requested with otherwise valid confirmation, **Then** routing is denied as unauthorized and no side effect occurs

### AT-010 - Notification interruption matrix

- **Covers**: AC-010
- **Level**: integration
- **Environment**: cloud-linux
- **Given** the matrix of active speech, quiet mode, active call, no interactive output, phone-only output, and glasses-selected output
- **When** ordinary, requested-high-priority, timer, and incoming-call events arrive
- **Then** ordinary events defer during speech, quiet mode, and calls; urgent allowed events use the selected available surface; unavailable surfaces fall back to a persisted phone/inbox item
- **And** every deferred item appears exactly once after policy permits delivery

### AT-011 - Explicit camera semantics

- **Covers**: AC-011
- **Level**: e2e
- **Environment**: cloud-linux
- **Given** a fake camera capability with fixture images and capture telemetry
- **When** a visual request is made followed by a contextual question
- **Then** exactly one capture occurs and the follow-up uses that image
- **And** control conversations without an explicit visual request record zero captures
- **When** the user explicitly says "remember this", **Then** the linked image/memory is persisted with provenance, can be inspected, and can be deleted without affecting unrelated memories

### AT-012 - Memory stewardship

- **Covers**: AC-012
- **Level**: integration
- **Environment**: cloud-linux
- **Given** explicit and derived fixture memories with provenance
- **When** the user lists, disables, exports, re-enables, and deletes them
- **Then** the output identifies source and derivation; disabled records remain inspectable/exportable but are excluded from retrieval and derivation; re-enabling restores eligibility; deletion survives a rebuild

### AT-013 - Request classification

- **Covers**: AC-013, FR-003
- **Level**: unit
- **Environment**: cloud-linux
- **Given** a deterministic corpus containing bounded reads/writes, consequence-governed actions, independent workstreams, and ambiguous requests
- **When** each request is classified
- **Then** it maps to bounded action, confirmation-required action, delegated task, or clarification as labeled
- **And** no case creates unsolicited work

### AT-014 - Provider-neutral contracts

- **Covers**: AC-014, FR-018
- **Level**: integration
- **Environment**: cloud-linux
- **Given** fake implementations for two differently shaped providers in each provider category
- **When** domain messages and stored records are serialized
- **Then** they validate against the same public schemas and contain no provider SDK types, event names, credentials, or raw stack traces

### AT-015 - Redacted diagnostics

- **Covers**: AC-015, FR-025
- **Level**: integration
- **Environment**: cloud-linux
- **Given** fixture sessions containing prompts, note content, messages, contacts, images, and credentials
- **When** connection, session, capability, task, inbox, routing, and latency diagnostics are exported
- **Then** operational state and correlation IDs remain useful while every seeded sensitive value is absent

### AT-016 - Text fallback matrix

- **Covers**: AC-016, FR-023, SC-009
- **Level**: e2e
- **Environment**: cloud-linux
- **Given** realtime audio is unavailable
- **When** the user executes each core interaction, bounded action, delegation, completion-follow-up, memory, and vision-result scenario through text
- **Then** every scenario completes or exposes only the genuinely unavailable input capability without losing assistant continuity

### AT-017 - Optional sensitive capabilities

- **Covers**: AC-017, FR-029, FR-030
- **Level**: scenario
- **Environment**: local-attested-android
- **Given** notification ingestion and direct communication are disabled, **When** use is attempted, **Then** no content is read and no side effect occurs
- **Given** a package/category allowlist and explicit direct-action grant, **When** a normal notification, OTP/work-profile fixture, unsupported reply, supported reply, direct send, and direct call are exercised, **Then** only allowlisted non-sensitive content and supported actions proceed with required confirmation and audit
- **When** either grant is revoked, **Then** advertisement and execution stop immediately

### AT-022 - Context class separation

- **Covers**: AC-022, FR-015
- **Level**: integration
- **Environment**: cloud-linux
- **Given** fixture hot turns, warm/cold retrieval records, explicit durable notes, derived memories, and worker history with distinct provenance
- **When** context is assembled for an active turn and each class is inspected
- **Then** hot context is bounded/transient, retrieval records remain cited and rebuildable, explicit knowledge remains canonical, derived memory remains labeled/deletable, and worker history is not silently promoted into memory or notes

### AT-018 - Foundation safety gate

- **Covers**: AC-018
- **Level**: smoke
- **Environment**: cloud-linux
- **Given** a clean foundation checkout without personal paths or credentials
- **When** build, schema validation, protocol/policy/path tests, and two synthetic smoke runs execute
- **Then** all pass, each smoke run owns a distinct generated root, each records zero instrumented out-of-root vault operations and one idempotent effect, and each removes only its own root

### AT-019 - Copilot worker adapter

- **Covers**: AC-019
- **Level**: integration
- **Environment**: cloud-self-hosted-copilot
- **Given** one existing specialist definition, a synthetic workspace, and a narrow permission envelope
- **When** the Copilot adapter submits the task asynchronously and normalizes its lifecycle
- **Then** the assistant remains available, all tool/vault activity stays within the envelope, and exactly one normalized terminal result identifies opaque artifacts

### AT-020 - Timed clean quickstart

- **Covers**: AC-020, SC-008
- **Level**: smoke
- **Environment**: cloud-linux
- **Given** a clean checkout with Node.js and documented prerequisites but no personal credentials
- **When** the documented quickstart commands run from a clean checkout under a monotonic timer
- **Then** the available synthetic quick-action and delegation scenarios complete in under ten minutes

### AT-A06 - Generated-vault Obsidian adapter

- **Covers**: AC-021
- **Level**: scenario
- **Environment**: local-attested-obsidian
- **Given** a supported Obsidian version, pinned adapter version, and physically separate generated vault
- **When** concurrent structural edits, stale revisions, read-only mode, exact previews, revocation, traversal, adapter restart, and failure injection are exercised
- **Then** atomic `Vault.process()` behavior preserves unrelated content, unsafe/stale/revoked operations produce no mutation, and no personal vault is discovered or selected

## Later device attestations

### AT-A01 - Android audio interruption

- **Covers**: FR-001, FR-023, FR-024
- **Level**: scenario
- **Environment**: local-attested-android
- **Given** a supported Android device running the Stage 1 client
- **When** the user interrupts assistant speech and then accepts a phone call
- **Then** assistant audio yields promptly, the call receives audio focus, and conversation context remains resumable afterward

### AT-A02 - Android background invocation

- **Covers**: FR-004, FR-024
- **Level**: scenario
- **Environment**: local-attested-android
- **Given** the app has only the documented permissions
- **When** the user invokes it from supported background and lock-screen states
- **Then** behavior matches the declared Android capability state and never implies unavailable wake or microphone access

### AT-A03 - Android lifecycle recovery

- **Covers**: FR-028
- **Level**: scenario
- **Environment**: local-attested-android
- **Given** a durable assistant session with an active task and queued inbox item
- **When** the application experiences process death, extended disconnect, device sleep, and reboot
- **Then** the next supported invocation resumes the logical session and reconciles task and inbox state without relying on the old media connection

### AT-A04 - Optional Android privileges

- **Covers**: FR-026, FR-027, FR-029, FR-030
- **Level**: scenario
- **Environment**: local-attested-android
- **Given** the application is not the default assistant and has no notification-listener or wake-word permission
- **When** the user uses text, push-to-talk, camera capture, compose-message, dial, and navigation actions
- **Then** core flows remain available and unavailable optional capabilities are represented accurately
- **And** wake word is disabled by default
- **When** wake word is explicitly enabled, **Then** recognition remains on-device, microphone use stays visibly indicated, an immediate stop control releases capture, and revocation updates advertisement and behavior without reinstalling the app

### AT-A05 - Visible camera lifecycle

- **Covers**: FR-017
- **Level**: scenario
- **Environment**: local-attested-android
- **Given** camera permission is granted and a one-shot capture is requested
- **When** capture begins, completes, is cancelled, or the app loses its supported visible lifecycle
- **Then** an unmistakable indicator remains visible for the full active interval and capture stops on completion, cancellation, or lifecycle loss

## Safety rule

AT-007 is intentionally excluded from unattended execution. Local-attested tests use generated content unless AT-007 explicitly promotes a user-selected target. Every other test must fail if it detects a non-generated vault identity, a path outside its temporary root, or a personal credential.
