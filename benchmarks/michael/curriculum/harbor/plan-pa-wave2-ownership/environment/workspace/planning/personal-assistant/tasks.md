# Tasks: Personal Assistant Platform

Tasks are ordered by dependency. Each implementation task owns one reviewable increment and leaves the repository green.

## Wave 1 - Safe foundation

- [ ] Task: T001 - Build protocol and synthetic-vault foundation
  - Define versioned TypeScript schemas and pure domain policies for workspace trust, device capabilities, confirmation state, task events, worker results, and errors.
  - Generate an adversarial synthetic vault in a unique temporary root.
  - Record and verify an I/O manifest; reject non-synthetic workspace kinds and out-of-root access.
  - Add deterministic contract, path-boundary, idempotency, and smoke tests.
  - Done when: AC-005, AC-008, AC-009, foundation gate AC-018, and timed clean quickstart AC-020 pass without secrets, Obsidian installation, or personal paths. AC-006 remains cumulative.
  - Touch: `services/personal-assistant/**`, `scripts/smoke.sh`, `.github/workflows/personal-assistant-ci.yml`, directly related service documentation.
  - Out of scope: network service, database, Android, Copilot SDK, Obsidian plugin changes, personal promotion execution.

## Wave 2 - Durable state and vault semantics

- [ ] Task: T002 - Add durable task, outbox, and inbox state
  - Add assistant-session, task, event, outbox, and inbox persistence.
  - Commit state transition and outbox record atomically.
  - Add idempotent/out-of-order event ingestion and resumable SSE delivery.
  - Done when: AC-001, AC-003, AC-004, and AC-010 pass with deterministic providers.
  - Dependencies:
    - task:T001

- [ ] Task: T003 - Add synthetic semantic vault gateway
  - Implement search/read and structural change proposals for quick capture, append, todo, and property update.
  - Build the independently rebuildable derived search projection with opaque note/section identities, content hashes, provenance, and embeddings.
  - Enforce per-note serialization, atomic revision check, exact diff, confirmation, post-write verification, and audit.
  - Use generated vaults only.
  - Done when: AC-002 and AC-005 pass across all adversarial fixtures.
  - Dependencies:
    - task:T001

## Wave 3 - Assistant and worker

- [ ] Task: T004 - Add persistent text assistant shell
  - Provide authenticated text interaction, logical session resume, context selection, bounded-action routing, delegation classification, and redacted diagnostics.
  - Use deterministic conversation and worker providers.
  - Done when: contextual turns and independent worker execution pass the scripted scenarios.
  - Dependencies:
    - task:T002

- [ ] Task: T005 - Adapt Copilot specialist workers
  - Wrap the existing Obsidian-agent Copilot SDK runner behind `WorkerProvider`.
  - Normalize lifecycle, failures, cancellation intent, results, and vault change proposals.
  - Preserve existing stable Obsidian plugin/backend behavior.
  - Done when: AT-019 routes one existing specialist through the Copilot adapter, proves its permission envelope, and emits one normalized completion.
  - Dependencies:
    - task:T002
    - task:T003

## Wave 4 - Android interaction

- [ ] Task: T006 - Build Android text and voice shell
  - Add Kotlin/Compose client, bootstrap, text UI, push-to-talk, ephemeral LiveKit room, barge-in, text fallback, task/inbox view, and diagnostics.
  - Persist no provider credential in the client.
  - Done when: cloud contract tests and the shell-only subset of AT-016 pass; AT-A01/AT-A03 remain a required local Android attestation handoff. Full AT-016 remains cumulative through T008.
  - Routing: cloud implementation via `R-cloud-default`; completion remains pending until `R-local-attested.platform-specific` evidence exists.
  - Dependencies:
    - task:T004

## Wave 5 - Capabilities and memory

- [ ] Task: T007 - Add bounded Android capabilities
  - Implement capability leases, permission state, one-shot CameraX capture, compose-message, dial, navigation, and app completion notifications.
  - Keep default-assistant, wake-word, and system notification access separately gated and revocable.
  - Done when: cloud-reproducible AC-008/AC-009/AC-011 tests pass; AT-A02/AT-A04/AT-A05 and AT-017 remain a required local Android attestation handoff.
  - Routing: cloud implementation via `R-cloud-default`; completion remains pending until `R-local-attested.platform-specific` evidence exists.
  - Dependencies:
    - task:T006

- [ ] Task: T008 - Add memory stewardship and completion UX
  - Implement explicit/derived memory records with provenance, inspection, reversible disable/re-enable, export, deletion, and rebuild-safe tombstones.
  - Implement quiet mode, deferred delivery, assistant inbox, and concise completion follow-up.
  - Done when: AC-010, AC-012, and context-separation AC-022 pass and the full cumulative AT-016 text-fallback matrix is green.
  - Dependencies:
    - task:T004

## Wave 6 - Isolated Obsidian adapter

- [ ] Task: T009 - Build and attest the isolated Obsidian adapter
  - Implement an official Obsidian API bridge using atomic `Vault.process()` structural edits and version checks against a physically separate generated vault.
  - Validate adapter identity/version, read-only mode enforcement, concurrency, stale revisions, preview/approval, revocation, traversal, and failure behavior without selecting a personal vault.
  - Done when: AC-021/AT-A06 and the complete synthetic suite pass using generated content only.
  - Routing: implementation may run in cloud; application behavior requires `R-local.device-io` and `R-local-attested.platform-specific`.
  - Out of scope: discovering, selecting, reading, or writing a personal vault.
  - Dependencies:
    - task:T003

## Wave 7 - Explicit local promotion

- [ ] Task: T010 - Attest read-only personal-vault promotion
  - Verify all prior synthetic gates are green.
  - Run the local administrative promotion procedure with a user-selected target, rollback checkpoint, narrow scopes, expiry, and distinct read-only credential.
  - Produce redacted evidence only.
  - Done when: AC-007/AT-007 has a local-attested receipt and revocation has been exercised.
  - Routing: `R-local.device-io` and `R-local-attested.platform-specific`.
  - Out of scope: structural writes, permanent delete, arbitrary commands, committing personal data.
  - Dependencies:
    - task:T001
    - task:T002
    - task:T003
    - task:T004
    - task:T005
    - task:T006
    - task:T007
    - task:T008
    - task:T009
