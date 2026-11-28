# Test Plan: Personal Assistant Platform

## Objectives

- Prove the assistant/worker boundary through user-visible scenarios.
- Prove capability routing, confirmations, event idempotency, and notification policy before provider integrations.
- Make synthetic-vault isolation an executable invariant rather than a convention.
- Separate cloud-reproducible correctness from Android and personal-vault attestations.

## Test layers

| Layer | Purpose | Typical scope |
|---|---|---|
| Unit | Pure policy, schema, state-transition, and path-validation logic | Capability policy, task reducer, interruption policy, vault path guards |
| Integration | Durable boundaries and provider-neutral contracts | Task/outbox transactions, adapter contracts, session resume, memory lifecycle |
| Smoke | Fast synthetic happy path from service start through quick action and delegation | Root `scripts/smoke.sh`, which invokes `npm run smoke` in `services/personal-assistant` |
| E2E | Client-facing flows with deterministic media/device providers | Text client, fake camera, event stream reconnect |
| Scenario | Hardware, OS, or explicit operator behavior unavailable in cloud | Android audio/background; personal-vault promotion |

## Environments

| Environment | Use | Data policy |
|---|---|---|
| `cloud-linux` | Unit, integration, smoke, deterministic E2E | Generated identities and temporary synthetic vaults only |
| `cloud-self-hosted-copilot` | Copilot worker adapter contract/integration with repository-managed non-personal entitlement | Synthetic workspace/context only; least-privilege secret-store credential, restricted egress, redacted logs, and immediate revocation |
| `local-attested-android` | Android microphone, audio focus, notifications, camera, background lifecycle | Fixture accounts and media; no personal vault required |
| `local-attested-obsidian` | Official Obsidian API/adapter behavior against a running desktop application | Physically separate generated vault and ephemeral adapter credential; redacted attestation, no personal vault discovery |
| `local-attested-personal-vault` | One-time promotion validation after all synthetic gates pass | Redacted evidence only; no note content in logs or repository |

## Synthetic vault fixture

The generator must create a unique temporary root and manifest for every run. It must include:

- ordinary notes, nested folders, links, frontmatter, tasks, and attachments;
- duplicate headings and block identifiers;
- malformed frontmatter and heading-like text inside code fences;
- Unicode names, spaces, reserved characters, and encoded separator attempts;
- large notes and binary files;
- conflicting revisions for optimistic concurrency tests;
- a sibling directory and symlink escape target that must remain inaccessible.

The fixture manifest records generated paths and hashes. The teardown check fails if any I/O occurred outside the generated root.

## Provider test doubles

- **Conversation provider**: deterministic streamed tokens, interruption, and reconnect behavior.
- **Worker provider**: controllable startup, progress, completion, duplicate events, crash, timeout, and cancellation.
- **Device provider**: dynamic capability advertisement and disconnects.
- **Camera provider**: fixture images plus capture-count telemetry.
- **Vault provider**: semantic operations, structural diffs, optimistic versions, and explicit promotion state.
- **Memory provider**: inspectable records with deterministic retrieval and deletion.

Test doubles implement the same domain contracts as production adapters. Tests must not branch on provider names.

## Required safety assertions

1. Development defaults contain no personal vault path.
2. Test processes receive no personal vault environment variable or credential.
3. Vault identities are typed as `synthetic` or `promoted`; arbitrary roots are invalid.
4. Every I/O operation is checked against the active workspace root before execution.
5. Promotion is a separate administrative operation and cannot occur through normal assistant or worker tools.
6. Promotion receipts contain identity and evidence, never note content.
7. Destructive vault operations remain disabled during initial read-only promotion.
8. Logs redact prompts, note bodies, message contents, tokens, and contact details by default.

## CI gates

1. Schema and unit tests.
2. Integration tests with temporary durable storage.
3. Synthetic-vault adversarial suite.
4. Deterministic assistant/worker E2E.
5. Smoke test under a clean environment with no secrets.
6. Artifact validators and lint/type checks.

T001 delivers `.github/workflows/personal-assistant-ci.yml`, which invokes the service smoke command on every relevant pull request on Linux and Windows, and a root `scripts/smoke.sh` wrapper for the repository smoke contract. Until T001 lands, these are planned gates rather than capabilities of the architecture-only commit.

No CI job may reference a user home directory, discovered Obsidian configuration, or machine-specific vault path.

## Device and promotion handoff

Scenario tests produce a YAML or JSON attestation containing:

- acceptance-test ID;
- environment class and non-sensitive device/adapter version;
- fixture or target vault identity;
- commit SHA;
- timestamp and attesting principal;
- pass/fail observations;
- redacted evidence pointers.

An attestation never marks unrelated cloud tests complete.

## Exit criteria for each increment

- Every included acceptance criterion has a passing primary test at its declared level and environment.
- The smoke test completes in under two minutes and is idempotent.
- No test requires a paid secret unless the increment explicitly introduces that provider and documents the requirement.
- Synthetic I/O manifests show zero out-of-root access.
- Any local-attested criterion remains visibly pending until evidence is recorded.
