# Research: Personal Assistant Platform

**Reviewed**: 2026-09-10 to 2026-09-11  
**Scope**: Current Android/realtime, Obsidian, events, memory, and worker-runtime choices for Stage 1.

## Decision: LiveKit for active realtime interaction

Use native Kotlin/Compose with compatibility-tested pins captured during the 2026-09 research pass: LiveKit Android SDK 2.28.2, Android Compose components 2.4.2, Agents 1.8.1, and Server 1.13.6. T006 must re-check these pins against current supported releases and record a compatibility matrix before dependency lock changes. LiveKit has maintained Android SDKs, a native starter, automatic WebRTC reconnect, camera/data/RPC support, and mature server-side interruption behavior.

Durable assistant state stays outside a LiveKit room. The room exists only during active conversation; PostgreSQL state and mobile notifications recover from process death, sleep, reboot, and extended disconnect.

**Alternatives considered**:

- Pipecat has strong interruption semantics and an open RTVI protocol, but its native Android transport ecosystem and release discipline are less mature.
- Direct provider WebRTC reduces one layer but increases provider coupling and weakens the self-hostable transport boundary.

**Sources**:

- [LiveKit Android SDK](https://github.com/livekit/client-sdk-android)
- [LiveKit Agents turns and interruptions](https://docs.livekit.io/agents/logic/turns/)
- [LiveKit connection reliability](https://docs.livekit.io/intro/basics/connect/#connection-reliability)
- [LiveKit self-hosting](https://docs.livekit.io/transport/self-hosting/deployment/)
- [Pipecat interruptions](https://docs.pipecat.ai/pipecat/fundamentals/interruptions.md)

## Decision: Optional Android privileges

Core text, push-to-talk, camera, compose-message, dial, and navigation flows work without default-assistant or notification-listener status. A lightweight `VoiceInteractionService` improves invocation when the user selects it. Wake word remains on-device, disabled by default, and backed by a visible microphone foreground service and stop control.

Stage 1 uses user-mediated `ACTION_SENDTO`, `ACTION_DIAL`, and navigation intents. Direct send/call and notification replies remain separately granted consequential capabilities.

**Rationale**: Android 12+ restricts background foreground-service starts; Android 14+ checks microphone/camera while-in-use permission provenance; Android 15+ restricts audio focus; Android 17 further hardens background playback and focus. Hardware hotword APIs are not portable third-party APIs.

**Sources**:

- [VoiceInteractionService](https://developer.android.com/reference/android/service/voice/VoiceInteractionService)
- [Foreground-service background restrictions](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start)
- [Android 14 foreground-service types](https://developer.android.com/about/versions/14/changes/fgs-types-required)
- [Audio focus](https://developer.android.com/media/optimize/audio-focus)
- [Common intents](https://developer.android.com/guide/components/intents-common)
- [CameraX architecture](https://developer.android.com/media/camera/camerax/architecture)
- [Home Assistant Android](https://github.com/home-assistant/android)

## Decision: PostgreSQL transactional outbox before NATS

Use one PostgreSQL transaction for domain state and immutable outbox rows. Dispatchers use `FOR UPDATE SKIP LOCKED`; `LISTEN/NOTIFY` may reduce latency but is only a wake signal. SSE maps durable event IDs to `Last-Event-ID` for reconnect.

Use a purpose-built outbox initially. Adopt `pg-boss` if scheduling, retries, dead-letter management, and operational UI justify it. Add NATS JetStream only after independently deployed/multi-language consumers or substantial replay/fan-out needs appear.

**Alternatives considered**:

- NATS JetStream is capable and actively maintained but adds another failure domain, replication/storage cost, patching duty, and still requires idempotent effects.
- WebSocket remains appropriate for bidirectional active interaction but should not be the durable event store.

**Sources**:

- [PostgreSQL transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)
- [PostgreSQL `SKIP LOCKED`](https://www.postgresql.org/docs/current/sql-select.html)
- [PostgreSQL `NOTIFY`](https://www.postgresql.org/docs/current/sql-notify.html)
- [WHATWG Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html#server-sent-events)
- [pg-boss](https://github.com/timgit/pg-boss)
- [NATS JetStream](https://docs.nats.io/nats-concepts/jetstream)

## Decision: Atomic semantic Obsidian adapter

Use a narrow gateway built on the official Obsidian Plugin API. Reuse `coddingtonbear/markdown-patch` for heading/block/frontmatter-aware changes, executed inside `Vault.process()` so version verification and write are atomic.

`obsidian-local-rest-api` 5.1.0+ is useful local-only prior art and may support wrapped reads, but its generic command/MCP surface is not given directly to models. Its current read-then-modify patch path retains a race window despite `ifMatch`, so gateway path serialization and/or an atomic custom bridge remains required.

**Alternatives considered**:

- The official Obsidian CLI is useful for allowlisted local automation but controls a running desktop app and is not a semantic patch API.
- `swarogan/obsidian-api` is newer, smaller, and currently has weaker optimistic-concurrency behavior.
- Direct filesystem access bypasses Obsidian's serialization and plugin abstractions.

**Sources**:

- [Official Obsidian API](https://github.com/obsidianmd/obsidian-api)
- [Obsidian vault development guidance](https://docs.obsidian.md/Plugins/Vault)
- [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)
- [markdown-patch](https://github.com/coddingtonbear/markdown-patch)

## Decision: PostgreSQL/pgvector memory foundation

Store inspectable memory facts, provenance, extraction metadata, consent, supersession, deletion, and embeddings together. Explicit Obsidian knowledge remains canonical and derived indexes are rebuildable.

Evaluate Mem0 later behind `MemoryProvider`. If tested, disable telemetry and configure every outbound LLM/embedder explicitly. Do not rely on Mem0 as the only store of memory, history, provenance, or consent.

**Alternatives considered**:

- Mem0 OSS is active and has useful APIs/server/UI, but extraction is model-driven, some advertised capabilities are hosted-only, and history/vector persistence can be separate.
- Graphiti adds temporal graph capability but introduces graph and model infrastructure too early.
- A dedicated vector database is unnecessary at personal-vault scale while PostgreSQL is already foundational.

**Sources**:

- [pgvector](https://github.com/pgvector/pgvector)
- [Mem0 OSS](https://github.com/mem0ai/mem0)
- [Graphiti](https://github.com/getzep/graphiti)

## Decision: Synthetic-vault promotion model

Automated development uses a physically separate generated vault, distinct credentials, adversarial fixtures, exact diff previews, per-note serialization, optimistic versions, post-write verification, and an I/O manifest.

Personal-vault promotion is a recorded administrative action, not an environment toggle. It records validated adapter/version, synthetic-suite revision, target identity, scopes, expiry, approver, and rollback checkpoint, then issues a different read-only credential.

**Rationale**: This makes the user's requested safety boundary mechanically verifiable and prevents accidental discovery or mutation of a personal vault by CI, workers, or normal assistant tools.

## Existing code to reuse

- `services/obsidian-agent/functions/src/runner.ts`: injectable Copilot SDK runner.
- `services/obsidian-agent/functions/src/tools.ts`: tool registry, path constraints, mutation normalization, and SSRF-aware fetch behavior.
- `services/obsidian-agent/functions/src/vaultFs.ts`: snapshot materialization and mutation diffing.
- `services/obsidian-agent/functions/src/functions/processJob.ts`: asynchronous job lifecycle and streaming progress.
- `services/obsidian-agent/plugin/src/vaultContext.ts`: snapshot/context patterns.
- `services/obsidian-agent/plugin/src/types.ts`: agent definitions and normalized file operations.

These are migration inputs, not the new domain boundary. Existing stable behavior is left untouched while new adapters are proven behind feature flags and synthetic fixtures.

## Open empirical research

- Android API 31/34/35/36/37 behavior across Pixel and Samsung devices.
- Bluetooth routing, call interruption, Doze, process death, network handoff, and permission revocation.
- LiveKit deployment topology and provider pipeline latency on available Azure infrastructure.
- Copilot worker authentication, cancellation, resume, concurrency, and entitlement limits in the selected deployment.
- Personal vault sync/concurrency behavior after read-only promotion.
- Whether Mem0 improves retrieval quality enough to offset another model-driven subsystem.
