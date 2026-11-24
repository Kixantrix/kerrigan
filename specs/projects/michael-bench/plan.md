# Plan: Michael Bench

Status: direction confirmed; MB-001a historical import boundary completed. Remaining contracts, engine selection, and broader dispatch are pending.

## Prior decisions

- Target the broader working day, starting with coding replays.
- Compare controlled model capability separately from practical native-agent systems.
- Preserve original Local AI Setup evidence and additive corrections; do not restart or take over its running research.
- Use trusted Kerrigan test-ladder, test-environment, scenario-test, and smoke-test skills.
- The initial planning increment authorized no model execution, downloads, spending, or production changes. The November 23 overnight handoff authorizes off-laptop implementation with synthetic fixtures, not additional laptop benchmarks.
- Include recurring hardware-aware discovery of models, runtimes, quantizations, caching/speculation options, and agent compatibility; propose evaluations before changing the working setup.
- Evaluate Kerrigan's own instruction/skill/tool/orchestration overhead and configuration effectiveness; preserve comparison portability to a future custom harness without selecting migration now.

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

Inventory the actual pilot source and sanitized evidence schema. Preserve historic outcome labels and additive corrections; establish an importable contract using synthetic/redacted fixtures. Exercise one tiny fake-model task in the smallest candidate engine and prove hidden-verifier separation, native-event preservation, offline reproducibility, and report export.

Prefer Inspect for broader evaluation composition or Harbor for task/environment packaging only after the compatibility evidence. If neither preserves requirements with a small adapter, document the specific gap before proposing a custom runner. No speculative framework rewrite.

Deliverable: reproducible offline runner slice and a documented engine decision. No inference required.

## Milestone 2: Three coding replays and honest reporting

Package the existing Kerrigan cases for foreign-reference milestone filtering (#405), implementation-status filtering (#409), and validator compatibility (#434). Each gets a requirement-only prompt, frozen base, hidden behavior/preservation checks, and fresh calibration receipts.

The #409 pilot is an offline adaptation of a historical live-GitHub requirement; label it accordingly. It is not live GitHub end-to-end evidence. Validator legacy compatibility is part of the task, not an evaluator defect to delete.

First report should explain correctness and incomplete attempts without model inference: synthetic success, regression, cap exhaustion, evaluator failure, cancellation, and missing telemetry cohorts. Import historic pilot results only as a separately labeled cohort.

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

Implementation tasks are listed in [tasks.md](tasks.md). MB-001a was dispatched and completed under its [closed briefing](../../../.specify/briefings/MB-001a.md); remaining slices are not dispatched. Create scoped briefings and run conflict prediction before parallel assignment. Completing the import boundary does not imply an implemented CLI.

Offline contracts, fixtures, reporting, and fake-model smoke work: `R-cloud-default`, using sanitized repository-contained materials.

Laptop-native integration and telemetry: `R-local.os-specific` / `R-local.device-io`. Personal credentials, if required, additionally match `R-local.paid-secret`. Local attestation applies to hardware evidence.

Self-hosted/cloud adapters are cloud-safe when configured capabilities and approved credentials are available. Actual target access and spending must be authorized separately; never move private pilot material merely to make a task cloud-runnable.

Public-source discovery with approved sanitized profiles: `R-cloud-default`. Reading current local inventory or locally running services: `R-local.device-io`; OS telemetry also matches `R-local.os-specific`. Scheduling location is an availability decision, not a reason to bypass data eligibility.
