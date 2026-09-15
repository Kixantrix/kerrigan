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
| Installed extension API | A session-scoped `joinSession()` + immediate `session.send()` probe produced a correlated runtime user event and an actual agent receipt | Active-session steering is verified on this installation; idle wakeup, other devices and remote transport are not |
| Existing satellite primitives | A bounded six-file sample found durable task/event claims, worker interfaces and artifact handoff contracts | Shared-database coordination is not verified deployment, device authentication or GPU fencing |
| Automation delivery | Owner saw the once-only audit message queued; the agent had no matching turn receipt | Queuing is not agent intake or completed action |

Do not infer that an app-local UUID, a history session ID and a GitHub task ID
are interchangeable. Keep the mapping from stable logical recipient to its
current app-local session at the receiving device.

### Local intake probe result

On 2026-09-13 a temporary, no-network/no-credential extension sent exactly one
fixed harmless message to its joined session. The send-returned message ID
matched the runtime user event, marked as steering into an active turn. The
agent then acknowledged the injected nonce through the probe's receipt tool.
This is evidence beyond send acceptance or UI queuing, not an end-to-end
cross-device or idle-wakeup test.

The source and private receipt were retained as session artifacts. The executable
extension was removed from discovery and reloading confirmed zero extensions
running. No persistent user/project extension or recurring listener was installed.

### Idle-triggered probe: no send observed

A separate one-shot probe was armed on September 13 for the next qualifying
root `session.idle` event, with a five-minute eligibility deadline. When the
owner returned on September 14 (user-local date), its receipt still recorded
`send_attempted: false`: no qualifying idle event, send acceptance, or agent
receipt had been recorded. The deadline had elapsed. Its executable was then
removed and extension reload confirmed zero running extensions; source and
receipt were retained privately.

This does not prove that SDK delivery to an idle session is impossible: the
probe never reached its send step, and the event/filter/host-lifecycle cause was
not established. It does prove that this experiment did not provide background
continuation. An armed probe must not be presented as active coordination or
left as an unexplained in-progress task after its observation window.

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
2. **Extend the bounded intake check if native routing is insufficient.** The
   documented extension `joinSession()`/`send()` path passed the active-session
   probe here. Next verify idle receipt and the second device with harmless
   messages, not just a successful API return or queued UI item.
   Do not attach via private app ports,
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

Two external device notes independently constrain the next check: native
enumeration did not establish authenticated physical-host identity, and the
six-brief W1 sample contained host-absolute prerequisites in every brief
(session-state paths in four). Those paths were valid same-device references;
they do not demonstrate a failed transfer or prove no portable copy exists.
Moving a file to a persistent local directory still does not deliver it remotely.

## Next-device capability check

Record runtime/app and harness revision, physical-device alias, supported
addressing method, and privacy/authority boundary privately. Exchange a harmless
nonce with an already authorized peer only after its identity is established.
Record send acceptance, queue visibility, receiver-turn receipt, acknowledgement
and correlation, then try one offline/reconnect case without new work.

Use an artifact-dependent briefing as the canary, but substitute a harmless
synthetic artifact unless private transfer is separately authorized. Verify
four distinct outcomes: message receipt, authorized access to manifest and
required bytes, matching content hashes, and recipient acknowledgement that
all execution prerequisites are available. Do not admit execution from a
message acknowledgement or matching history text alone.

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
