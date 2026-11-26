# Tasks: Michael Bench

Implementation roadmap: contracts, bounded engine proof, ledger/report, MB-003 packages, MB-005 offline CLI, and MB-006b fake-client broker/supervision proof are integrated. Cloud native trials remain gated by endpoint DNS resolution. The selected next route is direct local CLI/MXC, scoped in MB-006c; no native model scores exist.

## Milestone 1

- [ ] MB-001: Define versioned task, target, condition, result, and historical-import contracts using synthetic/redacted pilot fixtures.
  - Done when: AC-MB-001 and the manifest portion of AC-MB-003 pass; imports preserve originals and corrections.
  - Scope: future `benchmarks/michael/contracts/` and focused contract tests. Raw pilot evidence remains read-only/local.
  - Dependencies: none.
  - Completed bounded slice: MB-001a historical-evidence import contract, commit `857004c` ([briefing](../../../.specify/briefings/MB-001a.md)); other manifest contracts remain pending.
  - Completed bounded slice: MB-001b task/target/agent/condition/result contracts, including timing provenance and interrupted-trial semantics, commit `c2c73df` ([briefing](../../../.specify/briefings/MB-001b.md)). Pure offline contracts; no runner or scored model trials. Private pilot ingestion is not completed by synthetic contract tests.
- [ ] MB-002: Prove one offline task in an existing engine and select the smallest compatible foundation.
  - Done when: hidden verification, complete native-event transport, interrupted-ledger recovery, and offline execution are demonstrated; engine choice cites evidence.
  - Scope: future `benchmarks/michael/` adapter spike and fixture tests; no model downloads or live endpoints.
  - Dependencies: MB-001.
  - Closed execution scope: [MB-002 briefing](../../../.specify/briefings/MB-002.md). Synthetic evidence only; prove real sandbox/verifier separation rather than relying on descriptor labels.
  - Implemented bounded fixture: `fe63f63`, Inspect AI 0.3.292/Docker, executed success/failure/cancellation/timeout/interruption evidence. Whole-trial caps, adversarial quiescence, and actual Copilot-session isolation/identity remain unproven; see `benchmarks/michael/engine_proof/verification.md`.

## Milestone 2

- [x] MB-003: Package and calibrate the three existing coding replays.
  - Done when: AC-MB-002 passes for every task, including preservation tests and solution-leakage checks.
  - Scope: future `benchmarks/michael/tasks/` with approved exact-base archives and verifier-only references.
  - Dependencies: MB-001, MB-002.
  - Closed next slice: [MB-003 briefing](../../../.specify/briefings/MB-003.md), requiring fresh baseline/regression/reference calibration and answer-free agent exports.
  - Implemented `cac8e3d`; all three reference packages pass preservation plus held-out checks. Packaging is not actual native cloud-session isolation. Calibration times are not model completion times.
- [ ] MB-004: Implement the bounded trial ledger and cohort-aware report.
  - Done when: AC-MB-003, AC-MB-004, and AC-MB-005 pass with success, incomplete, infrastructure-failure, and missing-data fixtures.
  - Scope: future runner/report modules and focused tests; preserve all attempts and separate diagnostic/practical/historical cohorts.
  - Dependencies: MB-001, MB-002.
  - Timing requirement: actual time to independently verified completion, with queue/setup/agent/verification phases, paired per-task times, all-attempt elapsed accounting, and unfinished trials reported without completion times. Success-only statistics must disclose denominators.
  - Closed implemented slice: [MB-004 briefing](../../../.specify/briefings/MB-004.md); offline ledger/report fixtures only, not permission to execute the cloud comparison.
  - Implemented API through `0e81c63`, 142 focused checks passed; actual controller/event transport and full runtime AC-MB-004 remain gated on executable integration. Typed additivity and configuration-payload compatibility were corrected before integration.
- [x] MB-005: Add the offline CLI smoke path.
  - Done when: AC-MB-008 passes from clean isolated state twice without credentials; CLI invocation is documented with its verified command.
  - Scope: future CLI entry point, project smoke script, and operator documentation.
  - Dependencies: MB-003, MB-004.
  - Closed next slice: [MB-005 briefing](../../../.specify/briefings/MB-005.md); integrate the fake-model CLI/ledger/report path and whole-trial sandbox cutoff/quiescence proof, without native scored model calls.
  - Implemented through `a41376d`: two fresh owned-state synthetic smoke runs pass with dependencies/image preprovisioned; 161 cloud checks cover independent grading, false-success rejection, bounded stdout/stderr, cutoff and recovery. See committed CLI evidence receipts. No model scores or native transport proof.

## Milestones 3 and 4

- [ ] MB-006: Establish the laptop-native practical baseline.
  - Done when: AC-MB-006 has an attested receipt covering provider attribution, tool calls, grading, resource scope, and restoration.
  - Scope: an authorized local integration procedure and bounded adapter changes, not global provider replacement.
  - Dependencies: MB-005; external: approved local run conditions and budgets.
  - Selected next slice: [MB-006c briefing](../../../.specify/briefings/MB-006c.md), direct CLI/MXC on this laptop with cloud inference. Prove session-owned setup, authentication, actual Seatbelt/tool containment and bounded native canaries before scored tasks. Shared canary allowance remains two total; cloud canaries are paused at zero.
  - Explicit bounded continuation: [MB-006d briefing](../../../.specify/briefings/MB-006d.md), integrate the evaluated strict SDK session and no-fork MXC/lifetime mechanisms. Reuse the existing local executor and two-canary allowance; no additional inference budget or scored historical task.
  - TLS follow-up: [MB-006e briefing](../../../.specify/briefings/MB-006e.md), at most 20 implementation turns and zero model prompts. Both original canary slots failed before task actions and remain spent; native trust readiness must be established without weakening containment.
  - MB-006e integrated at `fd776dc`: source/config-bound native HTTPS passed with the three-service public-trust grant confined to the trusted transport. Task policy and original evidence are preserved. Platform attestation and separately frozen fresh-canary authorization remain pending.
  - [MB-006f](../../../.specify/briefings/MB-006f.md) authorizes local-agent attestation and two fresh corrected-condition canaries, one per selected model, 180+15 seconds each. Do not reuse original spent slots or claim scored-task completion.
  - MB-006f retained at `6fc4794`: both native streams hit the unchanged aggregate stdout cap before tool actions. Both new slots are spent. [MB-006g](../../../.specify/briefings/MB-006g.md) is a 20-turn offline-only stream-handling slice with zero new prompts.
  - MB-006g integrated at `5761e49`: finite separate protocol framing/aggregate/event/disk limits and offline owner/broker replay; no live tool-loop claim. Proposed [MB-006h](../../../.specify/briefings/MB-006h.md) requires direct human approval before two fresh fixed-condition checks.
  - MB-006h authorized and integrated at `9febde3`: Sonnet native tiny loop completed; MAI hit the distinct native HTTP-response cap. All six slots spent, no scores. [MB-006i](../../../.specify/briefings/MB-006i.md) is a 15-turn offline-only full-budget/source-binding correction.
  - MB-006i integrated at `460fa55`: offline-proposed cross-layer budget and environment-source binding; no live authorization. [MB-006j](../../../.specify/briefings/MB-006j.md) adds isolated independently authoritative Python-validator replay grading, zero inference, before native adapter integration.
  - MB-006j initial `1d94a73` was withheld pending correction: calibration reproduced, but controller-loss-independent candidate deadline/cleanup was missing; superseded by `9c35f62` below.
  - MB-006j corrected/integrated at `9c35f62`: independent lifecycle owner, actual controller-loss/deadline proof, base15/15+7/10/reference25/25, original authority-gap evidence superseded and retained. [MB-006k](../../../.specify/briefings/MB-006k.md) connects native staging/artifact collection to independent grading offline, zero inference.
  - MB-006k integrated at `789cc3f`: actual native offline task boundary, post-quiescence source handoff and independent calibration; deterministic fixtures only, no model scores. [MB-006l](../../../.specify/briefings/MB-006l.md) prepares the frozen real-model condition/self-test workflow/ledger integration offline; no prompts or new slots before later direct human authorization.
  - After reliable real-task grading, completion timing and lifecycle evidence, coordinate with **Local AI setup** on its frozen model/runtime inventory and separate local-model conditions. Preserve the historical pilot without relabeling or pooling.
- [ ] MB-007: Prove one self-hosted and one cloud target.
  - Done when: AC-MB-007 has target-specific attestation and identical contract versions, with unavailable cloud telemetry explicitly unknown.
  - Scope: approved disposable target adapters and capability scenarios; no production operations.
  - Dependencies: MB-005; external: approved target access, data eligibility, and spending ceiling.

## Milestone 5

- [ ] MB-008: Curate the next working-day task families. In progress: [brief](../../../.specify/briefings/MB-008.md) covers 8 families mined from the user's real repo work mix.
  - Done when: proposed planning, research, review, and operations cases have approved requirements, outcome rubrics, privacy classifications, and calibration plans before execution.
  - Scope: task specifications and fixture design, not unbounded expansion of the initial runner.
  - Dependencies: MB-003, MB-004; external: representative-work selection.

Dependencies do not imply parallel safety. Compute actual file-overlap waves after scoped briefing paths are final.

## Hardware-aware discovery

- [ ] MB-009: Define sanitized hardware profiles, source watchlist, and candidate/disposition contracts.
  - Done when: dated measured/reported/unknown hardware facts and candidate provenance are distinguishable; AC-MB-010 has fit and missing-data fixtures.
  - Scope: future discovery contracts and approved capability profiles; no live remote-host probing or secret extraction.
  - Dependencies: MB-001; external: approved hardware inventory.
- [ ] MB-010: Implement bounded model/runtime discovery and compatibility triage.
  - Done when: AC-MB-009 and AC-MB-010 pass for changed/unchanged releases, unsupported APIs, uncertain memory demand, and unavailable sources.
  - Scope: future discovery source adapters, ledger, and fake-source tests; metadata only, no model downloads.
  - Dependencies: MB-009.
- [ ] MB-011: Generate baseline-linked evaluation proposals from shortlisted candidates.
  - Done when: AC-MB-011 passes, with workload-specific hypotheses, finite budgets, missing-prerequisite labels, and no synthetic claims of measured improvement.
  - Scope: future proposal generator and fixtures using existing task/result contracts.
  - Dependencies: MB-003, MB-004, MB-010.
- [ ] MB-012: Configure one recurring research-only discovery job.
  - Done when: AC-MB-012 passes, exact location/cadence/state are verified, and dated reports remain accessible across runs without repeating unchanged recommendations.
  - Scope: approved scheduling configuration, standalone prompt, report publication, and failure reporting.
  - Dependencies: MB-010; external: approved scheduling location, cadence, and activation.

An interim agent-authored discovery report may precede MB-010, but is not completion of the automated collector or these tests.

## Harness efficiency and portability

- [ ] MB-013: Instrument instruction/skill/tool inventories and observable runtime phases.
  - Done when: AC-MB-013 passes with native/estimated/unknown telemetry fixtures and phase attribution; supported live baseline collection is documented separately.
  - Scope: future bench instrumentation and focused fixture tests; no profile shortening or credential interception.
  - Dependencies: MB-001, MB-004.
- [ ] MB-014: Add skill activation and repeated-load canaries.
  - Done when: AC-MB-014 passes for relevant/irrelevant/ambiguous/repeated tasks and missing resources, with correctness and intervention evidence.
  - Scope: future activation fixtures and loader adapters; preserve runtime-required controls.
  - Dependencies: MB-002, MB-013.
- [ ] MB-015: Compare a bounded set of harness configuration variants.
  - Done when: AC-MB-015 passes with an immutable B0 condition, named isolated changes, predeclared thresholds, held-out confirmation, and cohort-specific recommendations.
  - Scope: isolated candidate configuration manifests, experiments, and reports; changes to shared harness defaults require a separate scoped harness task.
  - Dependencies: MB-003, MB-004, MB-013, MB-014; external: approved native baseline/evaluation budgets.
- [ ] MB-016: Prove the runtime-neutral adapter contract for a future custom harness.
  - Done when: AC-MB-016 passes using fake-model/tool/event fixtures; unmatched GHCP controls remain explicit and one live coding comparison is proposed, not assumed completed.
  - Scope: future bench adapter proof, not a new production agent platform or migration of the user's provider.
  - Dependencies: MB-002, MB-004, MB-013.

The initial static audit in `harness-evaluation.md` is completed research, not completion of MB-013 runtime instrumentation.
  - MB-006l live v2 integrated at `af79d08`: harness-injected response cap removed (stock CLI). Validator repair: MAI 25/25 in 86.7 s, Sonnet 25/25 in 36.1 s, independently graded; v1 harness-cap failures retained ungraded. One public task only, not a ranking. Next: grouping/status graders and broader work families.
  - MB-008 integrated at `848f265`: 44-candidate catalog across 8 families (HOBL/WindowsDeveloperConfig excluded), 7 Docker-calibrated packages (validator, grouping, status, sr-temporal-assay, selfhost-redeploy-state, review-conflict-predictor, plan-dashboard-waves), Harbor export, PR mining, admission/attribution/quality rules, 10 public anchors. Parent macOS reproduction found an irreproducible sr-temporal-assay freeze (untracked bytecode pinned) and host-specific Harbor/mining paths; correction dispatched. LLM audits/quality panel and anchors not yet run.
  - MB-008 portability correction integrated at `c2e8d06` and verified on macOS (115 passed/1 Linux-only skip + 202 passed). [MB-009r](../../../.specify/briefings/MB-009r.md): generalize native runner, run admission and live MAI/Sonnet trials across all 7 packages, quality panel, per-family report.
  - MB-009r integrated at `bd3d41e`: [results-v1](../../../benchmarks/michael/curriculum/results-v1.md). Both models 5/5 admitted tasks, 90/90 checks; Sonnet 140 s total vs MAI 401 s (2.86x), fewer tokens. Plan/review packages retired for instruction/check contradictions. Ceiling effect: all tasks short and saturated — next round needs harder/long-horizon tasks to discriminate. [MB-010c](../../../.specify/briefings/MB-010c.md).
  - MB-010c integrated at `1f6101a`: 8 new calibrated packages (plan/review v2, research, design, orchestrate, 3 more long-horizon multi-file TS/JS), Harbor 0 lint findings, macOS fresh verification green. [MB-010r](../../../.specify/briefings/MB-010r.md): multi-file native collection, admission, live trials, results-v2.
  - MB-010r final at `6adb968`: [results-v2](../../../benchmarks/michael/curriculum/results-v2.md). Round 2: Sonnet 8/8 tasks (120/120 checks), MAI 6/8 (117/120); on six common passes MAI 691 s vs Sonnet 180 s (3.83x). Pooled v1+v2: Sonnet 13/13, MAI 11/13. MAI's two misses were model-caused review/defect-ledger claims (false glob-overlap; claimed-but-unfixed race). Round 3 queued: review-v4, design-v3, queue-v3, yv-v3, emv-v3, orchestrate-v5 (literal/overspecification fixes). Known macOS-host gaps: test_engine_proof (needs Inspect AI) and test_native_transport (Linux subreaper) fail on this Mac; unchanged since 7c7e279.
