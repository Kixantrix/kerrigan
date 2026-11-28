# Cost Plan: Personal Assistant Platform

## Principles

- Measure user-visible latency and value before scaling infrastructure.
- Keep the control plane portable and self-hostable; external model, speech, notification, and TURN dependencies remain explicit.
- Prefer one small database-backed service before adding distributed systems.
- Synthetic tests use deterministic providers and incur no model cost.

## Stage 0 foundation

| Component | Initial shape | Cost control |
|---|---|---|
| Protocol/domain packages | Build/test only | No runtime cost |
| Synthetic vault | Temporary local/CI files | Deleted after run |
| Deterministic providers | In-process fixtures | No API usage |
| CI | Existing GitHub Actions allowance | Target smoke under 2 minutes |

## Stage 1 runtime

| Component | Initial shape | Main cost driver | Control |
|---|---|---|---|
| Assistant service | One small container | CPU/memory/uptime | Scale vertically first; sleep noncritical dev environments |
| PostgreSQL + pgvector | Small managed or self-hosted instance | Provisioned tier/storage/backups | One database; retention and index monitoring |
| LiveKit server | One self-hosted deployment for active sessions | Bandwidth, TURN relay, uptime | No idle rooms; measure relay percentage |
| Realtime model/STT/TTS | Replaceable external or self-hosted providers | Audio minutes/tokens | Active-session only; explicit provider budgets |
| Copilot worker | Existing entitlement/runtime | Concurrency and task duration | Independent workstreams only; task timeouts |
| Attachment storage | Object/blob storage | Capacity/egress | Lifecycle rules; explicit visual capture |
| Mobile delivery | Platform push where used | Usually negligible direct fee | High priority only for user-visible urgency |

## Deferred operational costs

- NATS JetStream cluster: deferred until multi-service fan-out/replay justifies at least three replicated nodes.
- Mem0 service: deferred until measured retrieval improvement justifies model and storage calls.
- Dedicated vector database: deferred until PostgreSQL search scale is inadequate.
- Windows/web/iOS clients and VIVE adapter: separate later milestones.
- Fully local model inference: hardware, power, maintenance, and model-license evaluation required.

## Budget telemetry

Track by session/task/provider:

- active media minutes and TURN-relayed bytes;
- STT/TTS seconds, model tokens, and vision requests;
- worker duration, retries, and concurrency;
- database/storage growth and backup size;
- notification delivery count;
- cache/index hit and retrieval counts without logging content.

Define configurable daily and monthly provider budgets. When a budget is exhausted, preserve text fallback, task state, and user data; fail optional paid capabilities explicitly rather than silently switching providers.

## Cost review gates

- Before M4: compare self-hosted LiveKit on available Azure resources with managed transport using measured expected minutes.
- Before M5: estimate camera/vision and notification volume.
- Before M6: benchmark explicit pgvector memory against any Mem0 experiment.
- Before adding NATS or a new service: document the concrete availability, throughput, isolation, or replay requirement that PostgreSQL cannot meet.
