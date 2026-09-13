# Session operations

**Start here for dispatch and triage in the GitHub Copilot app.** Direct app session dispatch is primary; GitHub issues are an optional contextual adapter, not a prerequisite for starting a worker. This is an operating contract, not an enforced scheduler, resource lock, new tool, or permission grant. Existing issue scripts, generated briefings, CI jobs, and repository gates remain valid; the verify PR-target trigger includes dependent branches as described below.

Use the existing [startup role policy](../AGENTS.md#startup-role-policy), [briefing packet](../.github/skills/briefing-packet/SKILL.md), [routing rubric](../.github/skills/delegation-rubric/SKILL.md), and [test strategy](../docs/test-strategy.md). Keep state in the existing plan, tasks, briefing, and [block](../.github/skills/block-report/SKILL.md) primitives; no mandatory tracking database or separate per-run artifact set.

## Dispatch one coherent outcome

The human defines the outcome; the coordinator prioritizes, sequences, advances, and verifies it through the authorized delivery boundary. Split only for independent outcomes, risk, or real review boundaries, not universal changed-line/file/depth caps. Routine worker plans go to the coordinator, not back to the human as a task queue. Escalate meaningful product/direction, risk, privacy, authority, or material unapproved-cost decisions.

1. Reuse the living plan/tasks and generate or refine the briefing. Name scope (`Touch`, `Read-only`, `Out of scope`), AC IDs, test commands and evidence, owner, base/dependency, resources, and stop condition before dispatch.
2. Select the `cloud` executor explicitly for implementation. Role is independent of host: a local worktree worker is still an executor. Use capability-appropriate local/cloud execution under the rubric; app transport alone does not authorize local-only resources or change routing defaults.
3. Use the app's available session-creation surface with the briefing and explicit role. Do not invent unavailable tools, assume a profile loaded, or infer a concurrency limit from a failed kickoff. Default to the project default branch for independent work; set a dependent base explicitly only when the slice genuinely depends on it. Verify the actual base branch and SHA before edits and the PR target before delivery.
4. Record the returned session identity and implementation owner in the existing task/briefing. The worker acknowledges its role, scope, base, delivery boundary, and resources before starting. A submitted request is not an acknowledged dispatch.

The [issue adapter](../.github/prompts/kerrigan.dispatch.prompt.md) (`/kerrigan.dispatch` / `/speckit.taskstoissues`, existing issue scripts and `@copilot` assignment) remains available when useful or when direct sessions are unavailable. Labels annotate that path; they do not start, stop, or select profiles in app sessions. An issue body can carry the same briefing. An issue-only merge gate, where configured, still applies: satisfy it through an authorized adapter or report the blocker, never bypass it because dispatch was session-first.

**Dependent-PR verification:** native stack registration does not override workflow target filters or prove CI ran. The former `pull_request.branches: [main]` filter in [verify](../.github/workflows/verify.yml) blocked actual verification on a PR targeting its parent branch. The PR trigger now accepts all target branches, retaining the same validators, smoke, tests, permissions, and `merge_group` support. Inspect runs for the current head after pushing; do not retarget a dependent PR to `main` merely to get checks.

### Briefing operations addendum

Append this section to the existing briefing, or link the same fields in the task. It is an operational addendum, not a change to generated Spec Kit templates or the briefing generator's schema. Older generated examples remain valid inputs; the coordinator fills operational gaps before live dispatch.

```markdown
## Operations
- Coordinator: <session identity/contact; one accountable lead>
- Implementation owner: <one worker session; pending until acknowledged>
- Role / host: cloud executor / <local worktree or cloud; rubric justification>
- Base / dependency: <repository, target branch, full base SHA, prerequisite PR/artifact or none>
- Resources: <file conflicts; GPU/device, CPU/RAM, ports, services; none if not needed>
- Stop condition: <verified delivery boundary; block on unresolved scope/authority/resource conflict>
- Next check: <event or time; who acts if blocked>
```

## Ownership and handoff

Maintain one coordinator and one implementation owner per slice. One session can own a bounded shaper-only package; parallel workers each own distinct slices. A triage session is not a second implementation owner.

Routine child questions go to the coordinator with evidence/options. Read the actual pending plan or input before using supported approval/answer tools; a chat message is not proof a blocked input was answered. Follow accepted decisions without expanding authority. If unavailable, record delivery failure and the needed handoff instead of claiming the child was unblocked.

Send completions, blockers, and direction changes, not chatter loops, repeated acknowledgments, or status-only pings. Summarize at a meaningful checkpoint. A worker stops at its briefing's delivery boundary; the coordinator remains accountable for any remaining accepted outcome.

**Lead transfer requires explicit acknowledgment.** Record old owner, proposed new owner, scope, current head/PR, last meaningful progress, unresolved decisions/blocks, resource/process state, next action, and next check in the existing task or briefing. The new owner must acknowledge before the old owner relinquishes responsibility. If the old owner is unavailable, the coordinator arranges an acknowledged replacement and confirms the old worker/process is quiescent before replacement writes. If that cannot be established, block; do not launch competing implementation. If the coordinator is unavailable, seek an authorized replacement rather than silently self-promoting.

## Bound active work and shared resources

Start with a small pilot of one or two active workers; choose an explicit bound in the plan based on budget and observed host/service capacity. Increase only after successful dispatch, useful throughput, and timely verification; reduce on contention or stalled review. This is adaptive operating guidance, not a service cap or an automatic increase in spending authority. Existing hard budgets still apply.

Run the existing file-conflict predictor for parallel candidates and respect dependencies/waves. Also inspect non-file conflicts: GPU/device use, CPU/RAM pressure, ports, build caches, local databases, services, credentials, and other shared state. Record needs and compatible reservations with the owner and next check in the briefing/task. Serialize exclusive use or choose a suitable authorized host.

**Worktrees isolate files, not devices or processes.** An advisory reservation is not enforced locking. Check actual usage before starting, and stop if a resource conflict is unresolved. A lease expiry, idle UI, lost connection, or completed agent turn does not prove release. Require actual process exit and resource release evidence (specific process/service, port, or device state) before reuse. Do not terminate another owner's process, perform name-wide kills, or steal a reservation to make progress. Route uncertainty to the owner/coordinator; no resource scheduler is implemented here.

## Accountable triage

Perform a manual read-only pass first, before proposing recurring automation. Read current app session status, PR/issue state, checks, review threads/evidence, and pending decisions within the authorized repositories. Reconcile them with existing task/briefing owners; do not use conversation memory as live status.

Look for ownerless or stale actionable PRs, issues, failing/pending checks, unresolved reviews, and decisions. Stale means an expected action/check is overdue without meaningful progress, not merely an old timestamp or an idle session. Capture the exception in the existing task/briefing or retained triage handoff, not a new mandatory database. Minimum example shape:

```yaml
item: "repository + PR/issue/session identity"
owner: "existing accountable session, or unassigned"
expected_next_action: "inspect failed check and route to implementation owner"
last_meaningful_progress: "UTC timestamp + evidence, or unknown"
blocker: "observed blocker, or none"
next_check: "event or UTC time + responsible coordinator"
dedupe_key: "repository + item + stable finding identity"
observed_head: "full current SHA, or not applicable"
observed_event: "latest inspected event identity/time"
finding_state: "open, resolved, or reopened"
occurrence: "first observation or confirmed reopening identity/time"
last_notification:
  at: "UTC timestamp, or never"
  owner: "recipient identity, or none"
  finding_state: "state notified, or none"
  occurrence: "occurrence notified, or none"
  evidence: "substantive evidence fingerprint notified, or none"
```

Route a new actionable finding to its existing owner with the evidence and next action; do not duplicate implementation. If ownerless, the coordinator assigns an owner and obtains acknowledgment. If an owner is unavailable, use the explicit transfer protocol.

Persist the stable dedupe key, observed head/event, finding state/occurrence, and `last_notification` in the existing task/briefing or retained triage handoff that each new-session run reads. Compare against the notified state, owner, occurrence, and substantive evidence fingerprint, not just the latest head. Update notification state only after confirmed delivery; reconcile unknown delivery before retrying.

The stable finding identity excludes head/event. The same finding in the same occurrence/state must not repeatedly notify or relaunch work. A new head alone is not a new problem; update freshness evidence and re-check whether the finding still applies. Notify again only on materially changed evidence, an agreed overdue escalation, an acknowledged owner transfer needing handoff, or a meaningful state transition. Record resolution even when no outward notification is needed. A confirmed reopened/resurfaced finding starts a new occurrence and can notify again; dedupe is not permanent suppression. Do not create a new occurrence just because a push arrived.

Notification dedupe is distinct from side-effect idempotency. Before any mutation or retry, re-read the current head/event and reconcile the specific operation's existing effects; never act on stale evidence just because the notification key is stable. These are documentation contracts, not enforced runtime deduplication.

**Idle alone never permits archive or close.** Preserve persistent work (including unpushed commits/unsaved drafts), automations, open PRs, unresolved issues, and active lifecycle ownership. Closing/archiving requires explicit authority plus inspection of that state and a completed/acknowledged handoff; unresolved actionable items stay owned. Triage reports exceptions, not a cleanup quota.

## Choose one automation lifecycle owner

After the manual pass, choose a mechanism based on scope and continuity, using only capabilities the current runtime actually exposes:

| Mechanism | Appropriate use | Ownership boundary |
|---|---|---|
| New-session automation | Bounded recurring repository triage from durable inputs | Each run starts fresh; read the existing ownership and dedupe record before routing. Do not assume old conversation context. |
| Same-session wake | Resume one ongoing outcome with retained context | Reconcile live state on every wake; stop when the owned outcome ends. |
| Agent merge | PR-specific review/check/conflict lifecycle, when enabled | Do not run a second PR driver or recurring fixer over the same PR lifecycle. |

One lifecycle owner per PR/outcome, even if read-only triage observes it. Before enabling anything, record the following in the existing plan/task (example limits are a proposed pilot, not permission to schedule):

```yaml
scope: "named repository and owned item set; read-only triage and owner notification"
lifecycle_owner: "one coordinator session"
mechanism: "new-session automation"
max_work_per_run: "inspect at most 10 items for at most 5 minutes; no implementation"
overlap: "check active owner/run; defer if already active or uncertain"
idempotency: "reconcile current head/event and operation effects; consult stable finding/notification state"
no_op: "no new actionable finding means silence"
expiry: "explicit UTC end time or bounded run count required before enabling"
stop: "outcome complete, ownership transferred, authorization expired, or unresolved access/budget block"
```

Define who disables/clears the automation at expiry/stop and verify that it stopped. No-op silence means no outward nag or fresh work; retain enough run evidence for accountability. If overlap cannot be ruled out, defer rather than treating an expired advisory lease as a lock release. Never layer a watcher, same-session wake, and Agent merge as competing mutation owners. This guide creates no live schedules and grants no new permissions, models, budgets, or cross-repository access.

## Diagnose failure before retry

Record the failing operation, error category, sanitized evidence, known side effects, and next action. Do not expose credentials, private transcripts, or unrelated repository data.

| Category | Evidence and response |
|---|---|
| API validation / unsupported operation | Read the response/schema; correct the request in scope. Do not retry an unchanged invalid request. |
| Quota / rate limit | Honor provider retry guidance and known budgets; wait or checkpoint. Do not claim hidden caps, rotate identities, or bypass limits. |
| Transport / timeout | Outcome may be unknown. Query for the created session, branch, PR, comment, or assignment before retrying. |
| Authentication / authorization | Distinguish missing/expired identity from forbidden scope. Stop affected writes; request authorized recovery, never broaden permissions silently. |
| Hook / profile loader | Inspect the named hook or configuration error. A failed startup is not evidence of concurrency exhaustion. |
| Context / handoff | Recover the bounded briefing and current owner/head; summarize or transfer with acknowledgment. Do not create a duplicate worker merely to obtain fresh context. |

Reconcile side effects before every retry of a mutating operation. If a session/PR/comment already exists, attach to the existing result rather than creating another. Use bounded retries within the existing budget only for supported transient cases. If effects cannot be determined safely, stop the affected path and route a structured block with attempts/options to the coordinator. No hidden-cap claims or limit bypasses.

## Review convergence and completion

The coordinator routes technical fixes to the existing implementation owner on the same branch; use an app session message or the issue-agent `@copilot` adapter appropriate to that owner. Do not start another fixer. Replies belong in the original review thread and resolution follows a successful reply.

At a repeated review cycle or before budget exhaustion, checkpoint the tested head, each unresolved finding, correctness/AC impact, evidence, owner, and next action. Keep genuine correctness, security, and AC blockers open until addressed or disproved with evidence; later rounds do not automatically become advisory. Resolve genuine nits with rationale, consolidate duplicate findings, and separate new scope for coordinator decision. A checkpoint pauses churn, not verification gates.

A configured/requested reviewer is not actual review evidence. Inspect completed review records, reviewed SHA, conclusions and unresolved threads; distinguish missing, pending, stale, and current review. Green checks alone do not prove review completion, and branch protection alone does not prove a review happened. Retain self-verification, required CI, attestation where declared, and actual required review evidence before claiming readiness. Missing required evidence is a blocker, not an implied pass.

On completion, reconcile living decisions in plan/tasks/briefing with what shipped: AC evidence, exact base/head and PR state, superseded decisions, unresolved deferrals with owner/next action, and the authorized delivery boundary. Confirm process/resource release and automation stop or acknowledged continuation. Report completion to the coordinator once with delivery evidence; do not call an accepted outcome complete merely because a worker stopped or a PR opened.
