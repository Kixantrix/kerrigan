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

MB-006b is blocked before inference: CLI 1.0.112 initialized ACP, but native session creation failed with `ENOTFOUND` resolving `api.enterprise.githubcopilot.com/meta`. This is observed endpoint-resolution failure, not established authentication failure or model unavailability. The [preflight receipt](../../../benchmarks/michael/native_transport/verification.md), integrated at `8ef44bf`, records zero model prompts/canaries and no implemented transport, tool-inventory, isolation, or cancellation proof. Resume only after authorized endpoint reachability is restored outside this slice; all proof gates remain required. No scored model results exist.

Offline contracts, fixtures, reporting, and fake-model smoke work: `R-cloud-default`, using sanitized repository-contained materials.

Laptop-native integration and telemetry: `R-local.os-specific` / `R-local.device-io`. Personal credentials, if required, additionally match `R-local.paid-secret`. Local attestation applies to hardware evidence.

Self-hosted/cloud adapters are cloud-safe when configured capabilities and approved credentials are available. Actual target access and spending must be authorized separately; never move private pilot material merely to make a task cloud-runnable.

Public-source discovery with approved sanitized profiles: `R-cloud-default`. Reading current local inventory or locally running services: `R-local.device-io`; OS telemetry also matches `R-local.os-specific`. Scheduling location is an availability decision, not a reason to bypass data eligibility.
