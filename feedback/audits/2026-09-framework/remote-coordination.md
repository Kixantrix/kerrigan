# Domain-scoped cross-device coordination

**Status:** researched direction and capability checks, not an implemented mesh.
The owner wants related agents on a training device, workstation and laptop to
communicate without the human relaying messages. Domain membership should be
explicit; machine location should not define the collaboration boundary.

## What is established

| Surface | Evidence | Boundary |
|---|---|---|
| Native app session orchestration | Same-installation parent/child messaging works in this audit | Independent-device discovery, addressing, intake and acknowledgments remain unverified |
| Remote control | Official docs describe browser/mobile control of an existing local session | Execution stays on its online host; not a general agent-to-agent bus or execution migration |
| Synced history | Supports retrospective discovery | Not live presence, a mailbox, or proof a destination is reachable |
| Cloud continuation | Documented separately from local sessions | This installation's cloud reconnect failed; do not use it as proof of a working bridge |
| Installed extension API | CLI 1.0.84-4 extension documentation/types describe `joinSession()` and `session.send()` for the current foreground session | A promising supported local intake adapter; not yet exercised here or proven across devices |
| Existing satellite primitives | A bounded six-file sample found durable task/event claims, worker interfaces and artifact handoff contracts | Shared-database coordination is not verified deployment, device authentication or GPU fencing |
| Automation delivery | Owner saw the once-only audit message queued; the agent had no matching turn receipt | Queuing is not agent intake or completed action |

Do not infer that an app-local UUID, a history session ID and a GitHub task ID
are interchangeable. Keep the mapping from stable logical recipient to its
current app-local session at the receiving device.

## Minimum contract

Use a compact envelope: schema version, message ID, correlation/reply-to ID,
domain, sender, intended recipient, task/attempt/revision, kind, creation/expiry,
and concise payload or artifact reference. Kinds initially cover status,
question, artifact-ready, handoff, acknowledgement and blocked.

One owner receives a request; only registered interested peers receive factual
updates. No global broadcast, recursive forwarding, acknowledgements of
acknowledgements, or model turns just to emit heartbeats. Use a stable finding
identity for notifications and separate source revisions for action freshness.

Delivery states must distinguish **created, durably accepted, queued, received,
ownership accepted, acted and completed**. Persist an outbox, recipient cursor
and deduplication receipts in the chosen transport/receiver. Expect duplicates,
out-of-order events and offline devices; never claim exactly-once execution.
Reconcile ambiguous sends before reposting. A late message cannot repeat a
manually completed action.

Artifact-ready means a manifest/reference is published, not that another machine
has the bytes. Track receiver download/hash verification and acceptance
separately. Include source commit, producer attempt, content hashes/sizes and
target/runtime compatibility. A sender's local path is not an artifact transfer.
Keep large or sensitive bytes in an explicitly authorized private transport.

Messages do not grant authority. Authenticate publishers and receivers, authorize
domain access, and treat received text/artifacts as data subject to local policy.
A claimed device ID or environment label is not authenticated identity. This
first channel does not authorize shell RPC, deployments, starting/stopping
training, automatic human-approval responses, or secret transfer.

Task/event leases are not hardware leases. The device owner must enforce any
resource claim; expiry or an offline heartbeat does not prove a training process
stopped. Unknown ownership remains unknown until reconciled, not permission to
launch another expensive job.

## Transport choices, in order

1. **Verify supported native delivery first.** Use two existing authorized
   sessions on distinct physical hosts and supported enumeration/send surfaces.
   Require verified recipient identity and host, then exchange one harmless
   correlated message and acknowledgement. No guessed IDs or new workload.
2. **Prove local intake if native routing is insufficient.** The documented
   extension `joinSession()`/`send()` path is worth a session-scoped, no-network,
   no-credential probe. Verify actual agent receipt while idle/busy, not just a
   successful API return or queued UI item. Do not attach via private app ports,
   inject its database, or assume generic SDK sessions attach to arbitrary app
   sessions. No user-wide extension rollout is authorized by this plan.
3. **Use a private GitHub coordination record for sparse handoffs if appropriate.**
   One domain/task thread can carry small status and manifest-reference events.
   It is coordination storage, not issue-assigned execution: no automatic
   Copilot assignment or issue-per-session requirement. Comments are editable,
   not an immutable log or atomic job queue. Repository access, not labels,
   defines the privacy boundary. A comment does not itself wake an app agent;
   the receiving adapter still has to be demonstrated.
4. **Reuse an authenticated durable broker only when justified.** Low latency,
   offline subscriptions and a known receiver may justify an already operated
   service. Prefer outbound device connections, scoped domains, explicit
   acknowledgements and bounded retention. Do not deploy a new broker before
   resolving receiving-session intake, ownership, operation and privacy costs.

The satellite sample contains useful shared-database outbox/claim design and
hash-bound artifact contracts. Reuse those lessons; do not expose a private
product database or make the generic harness depend on that product.

## Next-device capability check

Record runtime/app and harness revision, physical-device alias, supported
addressing method, and privacy/authority boundary privately. Exchange a harmless
nonce with an already authorized peer only after its identity is established.
Record send acceptance, queue visibility, receiver-turn receipt, acknowledgement
and correlation, then try one offline/reconnect case without new work.

Success requires receipt and deduplication, not just transport acceptance.
The automation pilot demonstrated why: its schedule disappeared and the owner
observed a queued message, but no autonomous agent receipt was established.
Its bounded review reconciliation was handled in a normal user turn instead;
late delivery must not repeat that action.

Publish only sanitized conclusions in this audit. Do not put private domain
registrations, session/device IDs, repository identities, tokens or manifests
containing user data in this public harness.

## Sources and applicability

Official web sources retrieved 2026-09-13; installed extension documentation was
read on this device, not treated as a cross-device runtime test.

- [App sessions](https://docs.github.com/en/copilot/how-tos/github-copilot-app/agent-sessions), [remote control](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-remote-control), [ID/deep-link distinctions](https://docs.github.com/en/copilot/how-tos/github-copilot-app/open-with-deep-links).
- [Chronicle](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/chronicle), [cloud/local sandboxes](https://docs.github.com/en/copilot/concepts/about-cloud-and-local-sandboxes), [SDK steering/queueing](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/steering-and-queueing).
- [Issue comments](https://docs.github.com/en/rest/issues/comments), [REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api), [webhook delivery](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-webhooks).
- [Publish/subscribe](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber), [competing consumers](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers), [durable pull consumers](https://docs.nats.io/learn/jetstream/pull-consumers). These describe options, not dependencies selected or installed by this audit.
