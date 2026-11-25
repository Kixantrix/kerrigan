# Tasks: Michael Bench

Implementation roadmap: MB-001a/b, bounded MB-002, and MB-004 are integrated; MB-003 is the next scoped dispatch. Subsequent slices are not issued or dispatched. Suggested implementation paths below are to be finalized in briefing packets.

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

- [ ] MB-003: Package and calibrate the three existing coding replays.
  - Done when: AC-MB-002 passes for every task, including preservation tests and solution-leakage checks.
  - Scope: future `benchmarks/michael/tasks/` with approved exact-base archives and verifier-only references.
  - Dependencies: MB-001, MB-002.
  - Closed next slice: [MB-003 briefing](../../../.specify/briefings/MB-003.md), requiring fresh baseline/regression/reference calibration and answer-free agent exports.
- [ ] MB-004: Implement the bounded trial ledger and cohort-aware report.
  - Done when: AC-MB-003, AC-MB-004, and AC-MB-005 pass with success, incomplete, infrastructure-failure, and missing-data fixtures.
  - Scope: future runner/report modules and focused tests; preserve all attempts and separate diagnostic/practical/historical cohorts.
  - Dependencies: MB-001, MB-002.
  - Timing requirement: actual time to independently verified completion, with queue/setup/agent/verification phases, paired per-task times, all-attempt elapsed accounting, and unfinished trials reported without completion times. Success-only statistics must disclose denominators.
  - Closed implemented slice: [MB-004 briefing](../../../.specify/briefings/MB-004.md); offline ledger/report fixtures only, not permission to execute the cloud comparison.
  - Implemented API through `0e81c63`, 142 focused checks passed; actual controller/event transport and full runtime AC-MB-004 remain gated on executable integration. Typed additivity and configuration-payload compatibility were corrected before integration.
- [ ] MB-005: Add the offline CLI smoke path.
  - Done when: AC-MB-008 passes from clean isolated state twice without credentials; CLI invocation is documented with its verified command.
  - Scope: future CLI entry point, project smoke script, and operator documentation.
  - Dependencies: MB-003, MB-004.

## Milestones 3 and 4

- [ ] MB-006: Establish the laptop-native practical baseline.
  - Done when: AC-MB-006 has an attested receipt covering provider attribution, tool calls, grading, resource scope, and restoration.
  - Scope: an authorized local integration procedure and bounded adapter changes, not global provider replacement.
  - Dependencies: MB-005; external: approved local run conditions and budgets.
- [ ] MB-007: Prove one self-hosted and one cloud target.
  - Done when: AC-MB-007 has target-specific attestation and identical contract versions, with unavailable cloud telemetry explicitly unknown.
  - Scope: approved disposable target adapters and capability scenarios; no production operations.
  - Dependencies: MB-005; external: approved target access, data eligibility, and spending ceiling.

## Milestone 5

- [ ] MB-008: Curate the next working-day task families.
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
