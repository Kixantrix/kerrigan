# Implementation Plan: Personal Assistant Platform

**Branch**: `kixantrix-local-obsidian-agent` | **Date**: 2026-09-11 | **Spec**: [spec.md](spec.md)

## Summary

Build the product in vertical slices around a small set of provider-neutral contracts. Start with a deterministic text client, durable task/event state, dynamic capabilities, and a synthetic vault. Then integrate the existing Copilot worker, Obsidian adapter, Android voice/camera, and personal productivity capabilities. Personal-vault access is never part of automated implementation; it is a final local-attested promotion after synthetic gates pass.

## Technical Context

**Languages/versions**: TypeScript on Node.js 22+ for server/protocol/worker; Kotlin on the current supported Android toolchain for the client  
**Primary dependencies**: PostgreSQL, pgvector, Zod/JSON Schema, LiveKit Server/Agents/Android SDK, Jetpack Compose, CameraX, official Obsidian API, `markdown-patch`, GitHub Copilot SDK adapter  
**Storage**: PostgreSQL for durable state/outbox/memory; Obsidian for explicit knowledge; object storage for attachments when needed  
**Testing**: Jest/Vitest-compatible TypeScript tests, Android unit/instrumentation tests, deterministic provider contract tests, synthetic-vault smoke/E2E, local attestations  
**Target platforms**: Portable containerized server; Android API matrix 31, 34, 35, 36, 37; future Windows/web/wearable adapters  
**Project type**: Mobile client + modular backend + isolated worker + local Obsidian adapter  
**Performance goals**: delegation acknowledgment within one second of durable creation; active turn latency instrumented end-to-end; synthetic smoke under two minutes  
**Constraints**: one owner initially; no personal vault in CI; no generic interactive-assistant shell/filesystem; active media sessions are ephemeral; provider-specific schemas do not cross domain contracts  
**Scale/scope**: personal use, several connected devices, tens of concurrent tasks at most, a vault-sized knowledge corpus

## Constitution Check

| Principle | Plan evidence | Status |
|---|---|---|
| Quality from day one | Contracts, deterministic providers, test plan, smoke, synthetic isolation | Pass |
| Small reviewable increments | Ten dependency-ordered tasks; first PR is protocol + synthetic workspace only | Pass |
| Artifact-driven | Full project artifact set and ADRs precede code dispatch | Pass |
| Tests are part of feature | Each AC has one level, environment, and named acceptance test | Pass |
| Stack-agnostic and contract-driven | Product-domain contracts isolate LiveKit, Copilot, Obsidian, and memory providers | Pass |
| Operational responsibility | Runbook, cost plan, redacted observability, explicit promotion | Pass |
| Human-in-loop | Consequential confirmations and personal-vault promotion require explicit approval | Pass |
| Agent clarity | Scope, reuse points, task waves, and safety stop conditions are explicit | Pass |

## Project Structure

```text
apps/
└── personal-assistant-android/
    ├── app/
    └── feature/

services/
├── personal-assistant/
│   ├── src/
│   │   ├── protocol/
│   │   ├── domain/
│   │   ├── session/
│   │   ├── capability/
│   │   ├── task/
│   │   ├── inbox/
│   │   ├── vault/
│   │   ├── memory/
│   │   └── providers/
│   ├── migrations/
│   └── tests/
├── personal-assistant-worker/
└── obsidian-agent/                 # existing stable system; migration input

adapters/
├── obsidian/
├── copilot/
└── livekit/

deployment/
├── local/
└── azure/

tests/
├── fixtures/synthetic-vault/
├── interaction/
└── scenario/
```

**Structure decision**: The Stage 1 backend is one deployable service with internal protocol and domain modules. Schemas are exported as portable JSON artifacts for Android and future clients; a separate package is extracted only when a second server consumer makes it valuable. The Copilot worker is isolated because it runs longer and has a distinct permission envelope. Android and local Obsidian integration are adapters around stable contracts. Directories are introduced only in the slice that needs them.

## Milestones

### M0 - Protocol and synthetic safety foundation

- Versioned schemas and exported JSON artifacts for devices, capabilities, tasks, worker results, notifications, vault workspace trust, and errors.
- Pure state machines and policy functions.
- Generated adversarial synthetic vault and I/O manifest.
- Administrative promotion contract that is disabled by default.
- Deterministic contract and smoke tests.

**Exit**: AC-005, AC-008, AC-009, foundation-only AC-018, and timed quickstart AC-020 pass without personal paths or secrets. AC-006 remains a cumulative project gate expanded by later milestones.

### M1 - Text assistant and durable state

- Text/debug client, assistant session persistence, task/outbox/inbox schema.
- SSE reconnect and event idempotency.
- Deterministic conversation and worker providers.

**Exit**: AC-001, AC-003, AC-004, and AC-010 pass.

### M2 - Synthetic vault retrieval and capture

- Semantic vault gateway, structural patches, optimistic concurrency, exact diff preview.
- Independent index with provenance and synthetic-only credentials.
- Quick capture remains an assistant-owned bounded action.

**Exit**: AC-002 and AC-005 pass across adversarial fixtures.

### M3 - Copilot worker integration

- Adapt existing agents and runner behind `WorkerProvider`.
- Normalize lifecycle, cancellation, failure, and result artifacts.
- Enforce per-worker tool and vault scopes.

**Exit**: one specialist completes a synthetic multi-note task asynchronously and reports a normalized result once.

### M4 - Android conversational shell

- Kotlin/Compose client, authenticated bootstrap, push-to-talk, LiveKit active sessions, barge-in, text fallback, diagnostics.
- Durable recovery independent of room lifetime.

**Exit**: AT-A01 and AT-A03 have local Android evidence; core text flows remain cloud-tested.

### M5 - Android capabilities and productivity

- Dynamic capability leases; compose-message, dial, navigation, camera, notifications.
- Calendar/todo/reminder adapters added one bounded capability at a time.
- Optional default-assistant, wake-word, and notification-listener experiments remain independently gated.

**Exit**: AC-008, AC-009, AC-011, AC-017 and AT-A02/AT-A04/AT-A05 pass at their declared environments.

### M6 - Memory and completion experience

- Explicit/derived memory inspection, disable/re-enable, export, deletion, and provenance.
- Assistant inbox, quiet mode, completion headline and follow-up.

**Exit**: AC-010 and AC-012 pass.

### M7 - Isolated Obsidian adapter

- Implement the official Obsidian API bridge and atomic structural patching against a physically separate generated vault.
- Validate adapter identity/version, `Vault.process()` concurrency, mode enforcement, preview, revocation, and failure behavior.
- Keep personal-vault selection unavailable.

**Exit**: the adapter passes the synthetic suite and local attestation without personal content.

### M8 - Read-only personal-vault promotion

- Execute the separately attested promotion procedure only after M0-M7 synthetic and adapter gates are green.
- Start read-only, observe retrieval quality and concurrency, retain immediate revocation.
- Structural writes require a later explicit approval and are not implied by this milestone.

**Exit**: AC-007 has a redacted local attestation; no personal content enters repository artifacts.

## Delivery waves

| Wave | Tasks | Parallelism |
|---|---|---|
| 1 | T001 protocol/domain schemas and synthetic harness | One cohesive foundation package |
| 2 | T002 durable task/outbox; T003 vault gateway | Parallel after Wave 1 contracts |
| 3 | T004 text assistant; T005 Copilot worker adapter | Parallel after task and vault contracts |
| 4 | T006 Android shell | Single integrated mobile slice |
| 5 | T007 Android bounded capabilities; T008 memory/inbox | Parallel after shell contracts |
| 6 | T009 isolated Obsidian adapter | Local-attested against generated vault only |
| 7 | T010 personal-vault promotion | Local-attested only after all synthetic gates |

## Complexity Tracking

No constitutional violation is required. The separate worker is justified by long-running execution and independent permissions, not by organizational preference. NATS, Mem0, additional model providers, and microservices are explicitly deferred.
