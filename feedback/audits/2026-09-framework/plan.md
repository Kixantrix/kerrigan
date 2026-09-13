# Improvement plan

**State:** proposed, evidence-led rollout. See [findings](README.md) and
[PR-sized tasks](tasks.md). This is not permission to weaken gates or deploy
configuration across every repository.

## Operating model

Keep two roles: **Kerrigan coordinates; cloud executes a bounded slice**.
Treat the executor's existing name as a compatibility name, not a requirement
to execute remotely. Record role, host, capability needs and approval policy
separately. Local human-facing conversations should default behaviorally to
Kerrigan; explicitly delegated workers remain executors on either host.
Unknown host/role must not silently grant wider permissions.

An accepted outcome delegates prioritization. Kerrigan chooses and advances
the next ready slice, resolves in-scope child plans/questions, and continues
through verification and review. Do not ask the human to choose routine order
or reapprove work already within the outcome. Escalate a material scope/product
tradeoff, conflicting evidence that changes direction, authority/privacy
boundary, significant unapproved cost, or irreversible/shared-state action.
When independent authorized work remains, continue it while a real decision
is pending. Notifications and ordinary idle states are not approval gates.

Use direct app sessions as the normal dispatch path. An issue is optional
tracking/context, not an execution prerequisite. Keep AC/test mapping, closed
file scope, decisions, verification and blocks from the existing briefing.
Add one owner, expected base/head, dependency, stop condition and resource needs.
Do not select models or change account configuration as an incidental migration.

## Host selection

| Work | Preferred route, subject to verified capability and budget |
|---|---|
| Human direction, live app/device debugging, machine-only credentials | Local conductor or explicitly scoped local executor |
| Portable implementation, headless tests, independent repo-only work | Direct cloud worker when setup/access are ready and it saves local capacity |
| OS/hardware final verification with portable implementation | Split cloud implementation from local attestation; retain a real completion gate |
| GPU training, model conversion, large datasets | Dedicated approved compute/artifact pipeline, not automatically GitHub Actions or a generic Linux cloud session |
| Missing cloud capability or unclear data-export authority | Keep local or block with a reason; never copy personal secrets/data to make routing work |

Choose per slice, not per repository. Cloud offload is not a remedy for shared
account/model limits. Windows code can be implemented remotely while its actual
Windows behavior still requires a capable verifier.

## Small PRs without stack proliferation

Every slice names one outcome, its ACs, tests and a working post-merge state.
Prefer independently landable vertical slices. Use a dependent PR only for a
real prerequisite; its session/branch must start from the intended parent and
its review diff must be against that parent. Record order and owner for restacks.
Checkpoint scope at planning, first useful result and before opening the PR.
A second outcome means a new slice or an explicit direction decision.

Pilot a review warning at roughly 400 hand-written changed lines or 10 files,
not a hard CI limit or a definition of quality. Show generated/fixture changes
separately without hiding their review requirements. Review dependency depth
after three unmerged layers; land/unblock foundations before adding more.
These numbers are tunable hypotheses, not product limits or universal research
findings. Splitting must not manufacture broken intermediate states.

Deduplicate review findings by affected behavior and batch related fixes.
After two non-converging correction rounds, have the conductor reassess scope,
oracle and finding novelty; do not automatically dismiss later findings or
request reviews forever. Retain correctness blockers and evidence of actual
review, not merely a configured reviewer. Reconcile the final decisions into
the living plan and report implemented/CI-verified/target-verified separately.

## Deep verification with lower routine cost

Extend [the existing two-axis strategy](../../../docs/test-strategy.md).
For each AC, specify the risk, oracle/threshold, level, execution environment,
trigger and evidence. Keep cheap deterministic unit/contract/integration checks
on PRs; run affected application smoke/e2e paths and transitive consumers.
Shared code, dependency/lockfile, build, workflow and selection-policy changes
expand coverage conservatively. Unknown selection means broader tests, not pass.

Use tiny deterministic model fixtures for interfaces, shapes and failure paths;
use checksum-pinned prebuilt artifacts rather than rebuild unchanged models.
Real-checkpoint quality, performance and device tests remain required when the
changed risk demands them. Scheduled deep tests supplement, not replace,
change-critical tests. Normal application build/packaging checks remain when
they are the only evidence of buildability.

First run affected selection in shadow alongside current broad gates. Keep
individual results visible. A stable required aggregator, if adopted, must
reject failed planning, absent evidence and cancelled/incorrectly skipped
required jobs. Handle `merge_group` against the combined candidate. Don't solve
pending checks by returning unconditional success or silently dropping a gate.

Local evidence should bind exact tested commit and clean/patch state, relevant
model/data/artifact digests, environment/device class, test/policy version, ACs,
thresholds, result and retained logs. New code or inputs invalidate evidence by
default. Merge candidates require retest or a separately reviewed relevant-input
equivalence policy plus combined-source integration. Unsigned manifests are
records, not cryptographic assurance; specify evidence retention and trust.

## Bounded coordination, resources and recovery

Start the pilot with one conductor, at most two independent active workers,
and one owner of each scarce GPU/device. Queue other work; no recursive fanout
by default. Count active work, not old idle session tabs. Reduce to one worker
on service instability, preserve checkpoints and increase only after recovery.
Measure useful completion and contention rather than maximize concurrency.

Send results at completion, blockers or direction changes, not repeated status
requests or acknowledgments. Disagreements cite an AC/evidence and a proposed
resolution; no peer scoring or open-ended argument. Changing the lead session
requires explicit transfer and acknowledgment of dispatch ownership, worker
list, decisions, resources and automation responsibilities. The former lead
stops dispatching; it does not delete the user's sessions.

Start resource coordination with one supervisor/launcher that owns the workload
through process exit and cleanup. A repo file is only advisory, not a lock.
One host can use an OS mutex; shared multi-host resources need a real common
authority and fencing before parallel access. Expired leases or dead supervisors
do not prove their child processes stopped. Never kill unowned processes.

Classify inference throttling, quota exhaustion, GitHub API limits, authentication,
transport, hooks and context failures separately. Honor documented retry signals,
bound retries, and reconcile whether a side effect succeeded before replay.
Capture sanitized timestamps/request IDs. `/restart-session` and `/compact`
address different failures; clearing history is not a default recovery step.
Do not rotate accounts, bypass limits or upload diagnostic archives by default.

## Automations that have a job

Prefer completion/review events and existing Agent merge over another PR watcher.
Use a same-session wake for a finite owned task only when its runtime semantics
are verified; use a new-session automation for independent recurring work with
durable input. Each needs owner, scope, eligibility, dedupe key, maximum work
per run, overlap protection, stop/expiry and failure escalation. A wake checks
current ownership, head and blocked state before taking action.

One mechanism owns each lifecycle. Do not combine Agent merge, another watcher
and a recurring progress prompt on the same PR. No-op ticks must not send chatter,
spawn replacement workers or restart completed tasks. Test manually before any
schedule; check device-online/restart behavior and cloud eligibility first.

## Centralizing learning and adoption

Use existing `feedback/` intake and canonical skills/playbooks, not a new database
or dashboard. Each learning needs an evidence class, bounded applicability,
decision, target canonical rule, revision and pilot/adoption outcome. Promote
only validated general lessons; keep domain-specific details in their repo.
Close the intake with links once absorbed; use Git history, not contradictory
retention policies or a second permanent archive of duplicate guidance.

Pin the adopted harness revision per satellite; update selectively with a diff,
preserving local instructions. Validate on one device and one representative
repo before expanding. Record declined/deferred adoption as well as success.
Centralized learning must not mean automatically overwriting every satellite.
