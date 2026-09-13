# Cross-device audit handoff

This packet is the durable coordination point. Read [findings](README.md),
[plan](plan.md) and [tasks](tasks.md) before investigating. It proposes a
migration; it does not replace the current agent instructions or verification.

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

## What this device should add

| Question | Useful evidence |
|---|---|
| Agent discovery/defaults | Installed app/CLI version, profile revision, local/cloud creation path, visible picker before/after selection, explicit worker role; no tokens or private screenshots |
| Real dispatch | Count direct sessions vs issue-based starts in an explicitly selected sample; separate local execution, cloud sandbox, issue cloud-agent and code review |
| PR size/scope | Selection rule, dates/count, one-outcome assessment, hand-written vs generated diff, actual base/dependency and restack/review churn |
| Verification economics | Workflow/job timings and runner classes, critical path and queue delay, model build frequency, omitted-risk evidence; no guessed billed costs |
| Long-running coordination | Lead transfers, duplicate work, messages needed per outcome, resources requested/owned/released, observed contention |
| Availability | Exact sanitized error category, timing, active work, retry results and counterexamples; do not infer an undocumented concurrency cap |
| Automation | Which mechanism, new vs existing session, owner/scope/stop condition, observed useful/no-op runs, restart and overlap behavior |
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
- Findings keyed to F1-F14, or a new stable finding ID: observed vs reported vs
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
rollout. No new scheduling, cloud spending, GPU allocation, agent installation,
branch-protection changes or satellite edits are authorized by this packet.
The owner already requested session-first work and local conductor/cloud executor
defaults. The unresolved product question is **how the installed app exposes and
persists selection**, not whether to preserve that preference.

The next direction checkpoint should choose the P1 pilot scope and a
representative device/repo, then execute a separate small PR. Broader CI and
resource changes wait for measured evidence; do not quietly weaken technical
verification to reduce cost.
