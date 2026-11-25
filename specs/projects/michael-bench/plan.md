# Plan: Michael Bench

Status: contracts, bounded engine proof, ledger/report, and three calibrated replay packages are integrated. MB-005 offline CLI and full-trial sandbox controls are next; actual cloud-session identity/isolation and scored model trials remain gated.

## Prior decisions

- Target the broader working day, starting with coding replays.
- Compare controlled model capability separately from practical native-agent systems.
- Preserve original Local AI Setup evidence and additive corrections; do not restart or take over its running research.
- Use trusted Kerrigan test-ladder, test-environment, scenario-test, and smoke-test skills.
- The initial planning increment authorized no model execution, downloads, spending, or production changes. The November 23 overnight handoff authorizes off-laptop implementation with synthetic fixtures, not additional laptop benchmarks.
- Include recurring hardware-aware discovery of models, runtimes, quantizations, caching/speculation options, and agent compatibility; propose evaluations before changing the working setup.
- Evaluate Kerrigan's own instruction/skill/tool/orchestration overhead and configuration effectiveness; preserve comparison portability to a future custom harness without selecting migration now.
- November 24: proceed with offline implementation, then evaluate first bench versions in cloud Copilot sessions explicitly pinned to MAI Code 2 (`mai-code-2`) and Claude Sonnet 5.5 (`claude-sonnet-5.5`). Cloud-hosted agent execution is not proof of a directly controlled model API. Retain requested versus observed model identity and unsupported controls.
- Actual time to verified completion is a primary comparison output, not only completion before a deadline. Separate queue/provisioning/setup, agent work, verification, and end-to-end elapsed time.

## First cloud pilot

Native preflight found documented CLI model/tool filtering, including `strict-tools-list: true`, but no executed proof of app-native answer isolation or external session cancellation. The parent's app schema supports cloud/model selection; child host-local schemas do not disprove those parent capabilities. Effective host kind and observed model identity were not attested by worktree paths or self-identification.

The user approved proving a supervised Copilot CLI runner inside a cloud session as the initial route, with future local models in mind. Treat this as a distinct practical-system harness condition, not app-native evidence. The trusted supervisor owns provider transport, cancellation, incremental evidence, and sandbox tool routing; evaluated agents get only checked answer-free exports through a broker. Keep task/result/verification contracts transport-neutral. Do not change existing local services or presume Copilot credentials/entitlements are portable to another model provider.

The user delegated the initial screening size and limits. Start with the three calibrated coding replays, one fresh session/attempt per task per model: six trials, sequential execution, a 60-minute active-trial safety cutoff, no automatic retries or cap continuations, and no human implementation assistance. Record intervention if a trial requires it. Stop the pilot on isolation, identity, or evidence-accounting failure; do not silently rerun. Use only existing authorized Copilot cloud-session access, with no new paid API, infrastructure, or model downloads.

Freeze exact task packages, harness/configuration receipts, timeout enforcement, model identities, verifier isolation, task order, and cost/credit observability before starting. Alternate model order across tasks to reduce systematic order bias. Record hidden or changing host/harness settings as limits on practical-system comparability, not matched controls. Provisioning and verifier failures remain in coverage.

This screen tests whether the bench captures meaningful task outcomes and timing differences. Three historical coding cases are not full working-day representation or evidence of statistical superiority. Inspect per-task traces and failure attribution, then add fresh multi-file implementation, planning, research, review, and disposable operations cases before a broader recommendation. Do not increase repetitions or expand the live matrix automatically.

Prerequisites: remaining MB-001 contracts, MB-002 isolation/engine proof, MB-003 calibrated packages, MB-004 ledger/report, and MB-005 offline smoke. Dispatch these as small dependency-ordered increments; do not launch scored model sessions with answers or verifier material available in their repository/history.

## Parallel foundation: Harness audit and configuration experiments

The initial read-only audit measured repository instruction sizes and inspected current profile/skill validators. It did not measure the actual runtime's composed context or performance. See [harness-evaluation.md](harness-evaluation.md) for evidence and limits.

Inventory advertised, preloaded, activated, and resource-loaded context separately. Add native phase/token measurements where supported, then compare baseline with bounded variants for task-specific skill loading, compact linked references, tool-catalog disclosure, and history/compaction. Keep mandatory policy, permissions, safety, and independent verification fixed.

Start with the coding slice and a small activation fixture set. Do not shorten profiles on faith or introduce a new custom runtime solely to reduce file sizes. Screen a few variants, freeze a promising configuration, and confirm it on held-out tasks before changing defaults.

Deliverable: attributable overhead/quality results and a versioned preferred configuration per tested cohort. Later, a custom harness adapter must consume the same tasks and preserve event/verifier contracts. GHCP controls that cannot be matched limit the comparison to practical-system evidence.

## Parallel foundation: Discovery and experiment planning

Define approved hardware capability profiles and a bounded source watchlist. Implement source provenance, candidate deduplication, fit triage, and evaluation-proposal generation alongside the offline bench foundation.

The inspected pilot receipt records an Apple M5 Max with 18 CPU cores, 40 GPU cores, 64 GiB unified memory, and macOS 27.2.1. Treat these as dated observations, not current free-memory or service-readiness proof. Self-hosted GPU leads remain unverified; see [discovery.md](discovery.md). Inventory verification is a prerequisite to target-specific fit claims.

Use Hugging Face metadata/cards and upstream GitHub releases/docs as primary discovery inputs; community measurements are leads with explicit provenance, not replacements for own measurements. Monitor runtime and agent compatibility as well as model releases. Prefer experiments with a plausible workflow benefit and low setup/evaluation burden over exhaustive sweeps.

Start with one research-only recurring job, not an automation group. Execution location and cadence require a separate decision: local scheduling needs the machine/app available; always-on cloud research needs an approved sanitized hardware profile and source-only access. Activation and model execution are separate permissions.

Deliverable: hardware-aware candidate changes and finite evaluation proposals. The source scout may operate before the full bench is ready, but must label its proposals as not yet executable when runner prerequisites are missing.

## Milestone 1: Evidence contract and offline engine fit

Completed first slice: MB-001a, commit `857004c`, provides a pure-standard-library import boundary that retains exact source bytes, SHA-256, opaque source payloads/conditions/attempts/denominators, unknown telemetry, and separate additive corrections. It was implemented and verified in the isolated cloud session; the reviewed four-file change is integrated on the Michael Bench branch. No real pilot data or local model services were accessed. This is not completion of the remaining task/target/condition contracts or engine proof.

MB-001b, commit `c2c73df`, adds validated versioned task/target/agent/condition/result descriptors and frozen cross-references, separate unknown/unsupported/not-applicable evidence, capability requirements, attempt/verifier/stop states, and source/clock-attributed completion timing. The historical importer remains unchanged; 109 focused contract tests pass. Descriptors are not runtime identity, budget enforcement, isolation, or persistence attestations. Actual private pilot ingestion remains outside these synthetic slices.

Inventory the actual pilot source and sanitized evidence schema. Preserve historic outcome labels and additive corrections; establish an importable contract using synthetic/redacted fixtures. Exercise one tiny fake-model task in the smallest candidate engine and prove hidden-verifier separation, native-event preservation, offline reproducibility, and report export.

Prefer Inspect for broader evaluation composition or Harbor for task/environment packaging only after the compatibility evidence. If neither preserves requirements with a small adapter, document the specific gap before proposing a custom runner. No speculative framework rewrite.

MB-002, commit `fe63f63`, demonstrated one Inspect AI 0.3.292 scripted mock task in a digest-pinned Docker sandbox, positive/negative independent verification after solver stop, event/timing export, failure fixtures, and killed-controller recovery. The full run retained 109 contract and six sandbox passes; the strengthened interruption test passed separately after its probe was corrected. No cases were skipped. This selects Inspect only for the bounded fixture: whole-trial deadlines, adversarial process quiescence, and native Copilot-session identity/isolation are not proven. Raw synthetic receipts remain on the execution host; committed verification.md records exact commands, digests, cleanup, and limitations. No model performance result exists yet.

Deliverable: reproducible offline runner slice and a documented engine decision. No inference required.

## Milestone 2: Three coding replays and honest reporting

Package the existing Kerrigan cases for foreign-reference milestone filtering (#405), implementation-status filtering (#409), and validator compatibility (#434). Each gets a requirement-only prompt, frozen base, hidden behavior/preservation checks, and fresh calibration receipts.

The #409 pilot is an offline adaptation of a historical live-GitHub requirement; label it accordingly. It is not live GitHub end-to-end evidence. Validator legacy compatibility is part of the task, not an evaluator defect to delete.

First report should explain correctness and incomplete attempts without model inference: synthetic success, regression, cap exhaustion, evaluator failure, cancellation, and missing telemetry cohorts. Import historic pilot results only as a separately labeled cohort.

MB-004 is integrated through `0e81c63`: a durable locked/hash-chained ledger and explicit compatible-cohort comparison API retain starts, retries, incomplete trials, partial assertions, and paired completion-time coverage. Review corrected nonadditive telemetry aggregation and nested configuration-payload compatibility; 142 focused checks pass. Usage sums require result-bound unit/quantity declarations; watts, rates, and unit prices are not summed. Synthetic reports are report-math evidence, not model results. The API does not execute trials, enforce deadlines, or establish native session identity/isolation.

MB-003, `cac8e3d`, adds exact-base allowlisted exports and separately hidden verification. Passed/total calibration counts are grouping: preservation 4/4, baseline regression 0/2, reference 6/6; status: 32/32, 0/8, 40/40; validator: 15/15, 7/10, 25/25. All had zero skips/errors. These calibrate behavioral grading, not model performance. Grouping covers pure logic, status is an offline adaptation, validator includes legacy-parser preservation; all three are publicly exposed historical cases. The trusted packager's repository contains answers and must never be the evaluated agent's accessible checkout.

Deliverable: a reproducible three-case coding suite and report contract.

## Milestone 3: Laptop-native practical baseline

The user selected direct local Copilot CLI with Microsoft eXecution Container
(MXC) for the first native pilot. This is local agent/tool execution with cloud
model inference, not the original cloud-hosted-tools condition. MB-006c proves
session-owned CLI setup/authentication, effective Seatbelt containment and tool
inventory, external termination and two bounded native canaries before scored
tasks. MXC is not a VM and does not OS-sandbox the CLI's in-process file tools;
those side channels must be mechanically excluded. Existing locked test skills
cover this route; no additional skill installation is needed.

MB-006c partial proof is integrated at `9790949`: official session-owned CLI
1.0.115 and MXC executor 1.1.0, actual synthetic Seatbelt denials, and successful
post-login access-only native session creation. Both selected models are
advertised enabled, but no invocation identity, model response or score exists.
Full effective native tool policy and escaped-descendant cutoff remain unproven;
the executor is continuing those gates. Direct-child reaping is explicitly
insufficient and does not permit canaries.

The MB-006c addendum at `b386fa8` records actual single external-tool inventory,
explicit SDK-session sandbox policy, fork/posix_spawn denials and live-handle
cancellation of a non-forking task. The handler is still a stub; those component
receipts do not prove integrated execution/recovery. Its implementation-turn
block is resolved by the explicit MB-006d continuation, using the same local
executor and unchanged two-canary allowance.

MB-006d's integrated native runner is retained through `5129a98`. Both original
canaries stopped on TLS trust-store initialization before candidate actions:
MAI active/cleanup 5.824s/0.105s, Sonnet 6.362s/0.088s. Native starts were at
least two/three due CLI-internal retries despite zero controller retries.
Requested model-call pins were observed, but backend invocation identity and
usage remain unknown. These are failed capability attempts, not model scores.
Their allowance is exhausted. MB-006e is a separate 20-turn **non-inference**
TLS diagnosis; it grants no replacement canary or scoring attempt.

MB-006e is integrated through `fd776dc`. The native HTTPS failure was isolated
to missing public-trust IPC in the custom trusted-CLI profile. With the pinned
public PEM and exactly three documented service grants, the installed native
transport returned a strictly validated HTTP 200. Parent review verified source,
archive and configuration bindings, the exact transport-only delta and unchanged
task profile. Live task credential/Keychain/trust-service/fork denials and owned
controller-loss/deadline cleanup are retained. No model prompt ran. Native
platform attestation and a separately authorized fresh canary condition remain
pending; neither original slot is restored, and model usage/identity remain
unknown. See `benchmarks/michael/local_transport/tls-diagnosis.json`.

The corrected-condition follow-up is [MB-006f](../../../.specify/briefings/MB-006f.md):
authorized local-agent attestation and two fresh, sequential 180+15-second
canaries, one per selected model. Preserve exhausted MB-006d slots separately;
this is readiness evidence, not a scored benchmark.

MB-006f is retained through `6fc4794`. Both sessions passed live HTTPS and
effective sandbox/tool checks and emitted matching native model-call starts,
but the 65,536-byte aggregate CLI stdout cap stopped them before tool execution.
MAI active/cleanup was 3.863s/0.055s; Sonnet 2.820s/0.048s. These are cutoff
durations, not completion times. Both new slots are spent, no retry event was
observed before cutoff, later events and full usage/backend identity remain
unknown. [MB-006g](../../../.specify/briefings/MB-006g.md) addresses protocol
versus candidate-output budgets with offline evidence only, zero new prompts.

MB-006g integrated at `5761e49` separates finite native protocol budgets from
unchanged candidate output/action budgets. Retained-stream replay and a labeled
synthetic owner/broker loop passed; fresh native HTTPS, task denials and owned
cutoff evidence are retained. No model prompt ran and old approvals stay stale.
[MB-006h](../../../.specify/briefings/MB-006h.md) proposes two fresh live tool-loop
checks under the new fixed limits, pending direct human authorization.

MB-006h was directly authorized and integrated at `9febde3`. Sonnet completed
the real native write/run/result/idle readiness loop with `5\n`, 4.357 active
seconds plus 0.041 cleanup, three natural calls and native token counters.
This is not independently graded historical work or comparative performance.
MAI stopped before actions on the separate native HTTP-response 65,536-byte
limit, 3.746 active plus 0.073 cleanup seconds. Six slots are now spent.
[MB-006i](../../../.specify/briefings/MB-006i.md) reviews the full budget chain
and source/environment binding offline, without new prompts.

MB-006i integrated at `460fa55` binds `proof.py` and explicit cross-layer budgets
and validates large synthetic observations/tool-result handoff. Its expanded
resource envelope is offline-proposed, not an authorized live condition;
native acceptance/counting of the changed HTTP limit remains unverified.
All six existing slots stay spent. Next,
[MB-006j](../../../.specify/briefings/MB-006j.md) implements independent grading
for the real validator replay offline, without waiting on another canary.

MB-006j integrated at `9c35f62` after correcting controller-loss containment.
The independent Docker observation grader preserves 15 preservation plus 10
regression assertions; base15/15+7/10 and reference25/25 reproduced twice.
Independent owner deadline/liveness covers running and create/start-gap
controller loss; owner/proof loss stays ungraded with cleanup unproven.
Parent verified all 141 evidence-member hashes and executed-policy bindings.
[MB-006k](../../../.specify/briefings/MB-006k.md) connects native task staging,
bounded candidate collection and this grader offline, zero inference, before
proposing an actual model-driven replay.

MB-006k integrated at `789cc3f`: real native task staging/write/run/collection
hands exact source to independent Docker grading only after owned quiescence.
Trusted base/reference fixtures retain 15/15+7/10 versus25/25, not model scores.
Parent verified all 94 archive-member hashes, 23 source bindings and 32 preserved
historical artifacts. The macOS task boundary and post-stop tamper rejection
have actual offline evidence; no new model prompt or slot was used.
[MB-006l](../../../.specify/briefings/MB-006l.md) prepares and freezes the real
model-driven condition, public self-test/repair workflow and result/ledger
handoff offline. Fresh direct human authorization remains necessary afterward.

After the bench reliably grades real tasks, measures independently verified
completion time and preserves lifecycle/cost evidence, coordinate with the
existing **Local AI setup** session to evaluate its models. Freeze the current
model/runtime/hardware inventory and run separate local-model conditions through
the same applicable task/verdict contracts. Canary success alone does not close
this gate. Keep the original ad hoc pilot read-only, historical and unpooled.

Run a bounded baseline with the actual agent/provider the user uses, after environment and execution-budget approval. Attribute calls from native counters/logs, verify tools and outcome independently, record actual context/cache/reasoning transport, and restore all owned temporary changes.

Then compare another explicitly chosen target under a frozen matched condition. Do not infer native-agent quality from the existing endpoint pilot. Use a small screening batch before funding repetitions; freeze repeats/order/deadline/intervention policy before execution.

Deliverable: a practical setup comparison with workload evidence, not just decode throughput.

## Milestone 4: Self-hosted and cloud portability

Separate inference host from agent and verifier hosts. Add one disposable self-hosted target and one approved cloud endpoint without assuming model weights or cloud energy are inspectable. Prove the same task/result contract and capability-based blocking.

Deliverable: comparable cohorts with explicit environment and telemetry differences.

## Milestone 5: Broader working-day curriculum

Add fresh cases for planning/briefings, evidence-backed research, review/repair, and disposable operations. Calibrate each rubric before a model comparison. Use held-out objective checks first; human judgment is limited to irreducible quality judgments with recorded rubric and time.

Begin family-specific recommendations for interactive, background, offline/private, and cost-constrained work. Select task weights from an approved representative work mix only if a weighted recommendation is later needed; retain unweighted per-family evidence.

## Dispatch and routing

Implementation tasks are listed in [tasks.md](tasks.md). Contracts, bounded engine proof, ledger/report, calibrated packages, and MB-005 offline CLI are integrated. Native cloud-session identity and tool-boundary isolation must still be demonstrated before scored execution. Create scoped briefings and run conflict prediction before parallel assignment.

MB-005 is integrated through `a41376d`: the synthetic CLI ties actual sandbox execution to independent trusted grading, ledger/report output, whole-trial deadlines, interrupted recovery, and bounded stdout/stderr capture. Review corrected false success from candidate sentinel/tampering and uncapped stream accumulation. The cloud execution receipt records 161 passing checks and two fresh-state smoke runs (14.75s and 14.50s), excluding preprovisioning; these are synthetic harness checks, not model performance. Both output-overflow cases stop before grading with ungraded outcomes and unknown completion times. The committed [grading](../../../benchmarks/michael/cli/evidence/grading-proof.json) and [stream](../../../benchmarks/michael/cli/evidence/stream-proof.json) receipts preserve raw proof and source snapshots; original vulnerable false-success evidence stays explicitly invalid.

MB-006b native canaries are blocked before inference: CLI 1.0.112 initialized ACP, but native session creation failed with `ENOTFOUND` resolving `api.enterprise.githubcopilot.com/meta`. This is observed endpoint-resolution failure, not established authentication failure or model unavailability. The [preflight receipt](../../../benchmarks/michael/native_transport/verification.md), integrated at `8ef44bf`, records zero model prompts/canaries and no implemented transport, tool-inventory, isolation, or cancellation proof. The resumed slice diagnoses public endpoint reachability without credentials or network/configuration workarounds and implements offline transport/broker/supervision checks independently. Only native canaries remain gated on restored authorized reachability and proven isolation; offline progress must not be reported as native proof. No scored model results exist.

The independent MB-006b broker/supervisor proof is integrated through `7c7e279`,
including fail-closed recovery after supervisor loss; its cloud receipt records
129 passing checks. This is real Docker/fake-client evidence, not native model
execution. Cloud canaries stay paused while MB-006c owns the shared two-canary
budget for the selected local route.

Offline contracts, fixtures, reporting, and fake-model smoke work: `R-cloud-default`, using sanitized repository-contained materials.

Laptop-native integration and telemetry: `R-local.os-specific` / `R-local.device-io`. Personal credentials, if required, additionally match `R-local.paid-secret`. Local attestation applies to hardware evidence.

Self-hosted/cloud adapters are cloud-safe when configured capabilities and approved credentials are available. Actual target access and spending must be authorized separately; never move private pilot material merely to make a task cloud-runnable.

Public-source discovery with approved sanitized profiles: `R-cloud-default`. Reading current local inventory or locally running services: `R-local.device-io`; OS telemetry also matches `R-local.os-specific`. Scheduling location is an availability decision, not a reason to bypass data eligibility.

## Standing autonomy (user direction, 2026-11-25)

User: "I don't want to be asked ANYTHING in the process. The bench should be
set it and you run through and learn what you need to about the models and tell
me afterwards how they stack up for my use case."

This is the standing authorization for frozen, reviewed Michael Bench
conditions. Executors do not ask the human. Before each live run the
coordinator reviews the exact frozen condition, and the executor records the
condition digest plus this direction as its authorization. Safety boundaries
still apply: credential state stays uninspected, there is no host execution of
generated code, and limits are finite and frozen per condition. Attempts,
retries and errors are preserved, and unknowns are never treated as zero. The
human receives a single comparative report afterwards.
