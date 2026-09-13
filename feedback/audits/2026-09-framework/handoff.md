# Cross-device audit handoff

This packet is the durable coordination point. Read [findings](README.md),
[plan](plan.md) and [tasks](tasks.md) before investigating. It proposes a
migration; it does not replace the current agent instructions or verification.

**Introducing PR and coordination history:**
[Kerrigan #428](https://github.com/Kixantrix/kerrigan/pull/428).
Use its current head while open; after merge, read the default-branch packet
and any follow-up PRs linked from its discussion or [tasks](tasks.md).

## Continuation prompt

> Act as Kerrigan. Continue the framework-effectiveness audit from this packet
> and its GitHub PR. First identify the PR's current head and any newer findings.
> Contribute evidence from this device, not a second redesign. Read existing
> session/project inventories and time-bounded history; do not interrupt active
> workers, run builds/GPU jobs, alter settings or create automations for research.
> Start with seven days, widen only when needed, and state coverage limitations.
> Inspect at most two representative repositories initially: an app/monorepo
> and hardware-heavy work. Use one bounded read-only session per repository;
> reuse suitable existing audit sessions rather than recursive fanout.
> Keep private raw evidence local. Publish only sanitized findings and precise
> public sources. Report contradictions, counterexamples and missing data.
> Coordinate with the current audit owner before implementation or taking over
> dispatch. Do not assume saying "Kerrigan" changed the app agent picker.
> Prioritize clear work yourself; do not ask the owner "what next." Prefer
> cohesive reviewable PRs over a proliferation of small ones. Triage routes
> actionable exceptions to accountable owners instead of taking their work over.
> Also read remote-coordination.md. Investigate domain-related communication
> across devices using a harmless correlated receipt/acknowledgement test through
> supported surfaces. A queued message or synced history is not delivery to an
> agent. Do not expose devices, credentials or operational records publicly.

## What this device should add

| Question | Useful evidence |
|---|---|
| Agent discovery/defaults | Installed app/CLI version, profile revision, local/cloud creation path, visible picker before/after selection, explicit worker role; no tokens or private screenshots |
| Real dispatch | Count direct sessions vs issue-based starts in an explicitly selected sample; separate local execution, cloud sandbox, issue cloud-agent and code review |
| PR size/scope | Selection rule, dates/count, one-outcome assessment, hand-written vs generated diff, actual base/dependency and restack/review churn |
| Verification economics | Workflow/job timings and runner classes, critical path and queue delay, model build frequency, omitted-risk evidence; no guessed billed costs |
| Long-running coordination | Lead transfers, duplicate work, messages needed per outcome, resources requested/owned/released, observed contention |
| Availability | Exact sanitized error category, timing, active work, retry results and counterexamples; do not infer an undocumented concurrency cap |
| Automation | Which mechanism, new vs existing session, owner/scope/stop condition, useful/no-op runs, restart/overlap behavior, triage resolution vs duplicate nudges |
| Learning adoption | Local improvements absent upstream, upstream revision, conflicting overrides, smallest reusable rule and evidence |

## Contribution format

Use one small PR adding a device evidence note here, or a clearly labeled update
to the existing audit PR if its owner coordinates that edit. Do not force-push,
copy raw transcripts, edit another device's checkout, or duplicate these findings.
Use a neutral device alias; a Git commit/PR is the portable pointer, not a local
session ID or filesystem path.

Each note should state:

- Evidence date, app/runtime and harness revision, collection method/window/count,
  visible/missing sources, and exclusions (including review sessions).
- Findings keyed to F1-F29, or a new stable finding ID: observed vs reported vs
  proposed; source type; sanitized example; counterexample; confidence.
- A bounded recommendation, alternative considered, measurement, and whether it
  changes the current plan. Unknown should remain unknown.
- Disclosure review: no private repo names/links, credentials, patient/user
  content, device endpoints, environment dumps, raw prompts or debug archives.

For ownership transfer, record the incoming/outgoing conductor, acknowledged
handoff point, active slice/branch/PR/head, pending direction decisions,
worker/resource ownership and automation responsibilities in an appropriate
private operational record. Suspend the former owner's dispatch before the new
owner starts. Do not publish private session identifiers here.

## Current boundaries and decisions

Initial publication is an evidence/handoff deliverable, not a claim of completed
rollout. The owner authorized prioritization and bounded improvements without
routine "what next" approvals. P0/P1 profile loading, role defaults and
follow-through are one cohesive package; P4a verification guidance is independent.
No new scheduling, GPU allocation, agent installation, branch-protection
changes or satellite edits are authorized merely by reading this packet.
The owner already requested session-first work and local conductor/cloud executor
defaults. The unresolved product question is **how the installed app exposes and
persists selection**, not whether to preserve that preference.

The current conductor owns priority and next-ready-slice selection. Coordinate
ownership rather than asking the human to replan. Bring the human only a genuine
direction, authority, material risk/cost or reserved-judgment decision. Broader
CI and resource changes wait for measured evidence; do not quietly weaken
technical verification to reduce cost.

Cloud continuation has an additional open platform boundary: session metadata
creation worked, but reconnect required SDK streaming-session support unavailable
in this installation. Do not assume the telemetry worker completed, failed
remotely, or never started. Reconcile its actual ownership/execution through a
capable client before resuming elsewhere. The local operations PR also exposed
and corrected a main-target-only verification trigger; validate stack checks
on the real head, not just local tests or the lower PR's green status.

One audit-owned, once-only follow-up was configured for review reconciliation.
The owner observed its queued message, but no autonomous agent-turn receipt was
established. The reconciliation was handled in a normal user turn; any late
delivery is a duplicate, not authority for another review loop. Do not add a
replacement timer to hide the delivery gap. See
[remote coordination](remote-coordination.md) for the receiving-adapter questions.
The documented extension intake path has since passed one active-session probe
on this device, with actual agent receipt. Its executable was removed afterward.
The next useful evidence is idle and distinct-device receipt, not another
demonstration that a send call returns successfully.

Two device contributions are now incorporated in the audit's evidence table.
Use separate app, embedded-runtime and standalone-CLI versions; their loader
diagnostics differed while the same profile correction worked. Do not age work
from session `updated_at` alone, or treat host-local briefing prerequisites as
available on another device. The next canary should verify both receipt and
synthetic artifact availability/hash/prerequisite acceptance.
