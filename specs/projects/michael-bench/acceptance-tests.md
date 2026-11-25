# Acceptance tests: Michael Bench

MB-001a historical-import tests are implemented; other tests below are planned. Planned test IDs specify required behavior, not an existing test suite.

| AC | Planned test ID | Given / when / then |
|---|---|---|
| AC-MB-001 | `historical_import_preserves_evidence` | Given a checksummed synthetic pilot with a correction and aborted retry, importing it preserves source bytes, all attempts, original policy, and additive correction provenance; a mismatched digest is rejected explicitly. |
| AC-MB-002 | `replay_calibration_and_hidden_verifier` | Given each frozen coding base and independent reference, regression/base and held-out fail-to-pass calibration succeeds; the agent cannot read gold, held-out assertions, solution commits/history, or verifier state. |
| AC-MB-003 | `condition_identity_and_capabilities` | Given supported and unsupported provider semantics and split inference/agent/verifier hosts, the condition identifies each role; unsupported tools/reasoning/cache controls block or explicitly define a different condition, never silently change the run. |
| AC-MB-004 | `trial_terminal_accounting` | Given length-stop, voluntary stop, HTTP-200 stream error, duplicate/partial tool calls, cap continuation, evaluator OOM, timeout, safety cancellation, and controller interruption fixtures, each yields an attributed durable state with intact history, bounded continuation, and no false success. |
| AC-MB-005 | `report_cohorts_and_unknowns` | Given successful, failed, retried, ungraded, unknown-power/unknown-price, and incompatible-policy trials, the report retains every attempt, exposes partial assertions, prevents cohort pooling, includes failed-attempt cost/time, and makes no unsupported superiority claim. |
| AC-MB-006 | `laptop_native_agent_and_restoration` | Given an approved laptop manifest and finite trial, the actual selected agent issues attributed calls and real tools, independent grading records the outcome, resource evidence declares its scope, and exact owned-service restoration is attested after success and cancellation. |
| AC-MB-007 | `remote_target_portability` | Given approved disposable self-hosted and cloud targets, one frozen supported task produces the common contract from each; a hardware-only task is explicitly blocked where unavailable, and remote energy is unknown unless measured within a declared boundary. |
| AC-MB-008 | `offline_cli_smoke` | Given clean isolated state and no credentials, the public CLI runs a fake-model fixture, invokes the verifier, and emits a report in under two minutes; a second fresh run also passes. |
| AC-MB-009 | `discovery_provenance_and_deduplication` | Given official claims, independent reports, own measurements, unchanged revisions, a materially changed release, and inaccessible sources, discovery preserves provenance, emits only meaningful changes, and discloses incomplete coverage without calling a partial scan complete. |
| AC-MB-010 | `hardware_fit_and_unknowns` | Given known/unknown target profiles and dense/MoE candidates, screening accounts for weights, context/KV, drafter/residency/evaluator overhead, API/OS support, and headroom; incomplete inputs produce verification-needed rather than an invented fit guarantee. |
| AC-MB-011 | `bounded_evaluation_proposal` | Given a shortlisted candidate and baseline evidence, the proposal names a testable workflow hypothesis, matched controls, finite proposed budget, and safety/restoration policy; absent runner or hardware prerequisites remain explicit and no execution occurs. |
| AC-MB-012 | `recurring_research_only_report` | Given duplicate scans, new evidence, stale inventory, network failure, missing prior state, and a source requesting installation, the job preserves a dated report/cursor, reports gaps, rejects source instructions, and performs no installs, model runs, service changes, or paid inference. |
| AC-MB-013 | `harness_overhead_provenance` | Given native usage/timing, offline tokenizer estimates, static file counts, and unavailable host controls, the report keeps their provenance and coverage distinct and attributes observable startup/prefill/discovery/tool phases without inventing actual prompt content or timings. |
| AC-MB-014 | `skill_activation_canaries` | Given relevant, unrelated, overlapping, ambiguous, repeated, and missing-resource tasks, activation/resource events and duplicate loads are recorded alongside held-out outcomes and intervention; required permission/verification constraints remain enforced. |
| AC-MB-015 | `paired_harness_ablation` | Given frozen B0 and a single-dimension candidate plus an intentionally confounded variant, comparisons retain all attempts, paired conditions, predeclared promotion criteria, and held-out confirmation; confounded evidence cannot support an isolated harness improvement claim. |
| AC-MB-016 | `portable_harness_event_contract` | Given fake-model/tool traces for supported semantics, cancellation, duplicate action identity, checkpoint/resume, compaction loss, and unavailable GHCP controls, both adapters produce the common contract or an explicit incompatibility, with independent verifier state intact. |

## Completion timing

AC-MB-003/004/005 timing fixtures must include two successful tasks with different durations, a timeout, a retry, an evaluator failure, and missing cross-host timing. Verify that queue/setup, agent elapsed, verification, and end-to-end timing remain distinct with clock/source provenance; unfinished trials never receive a time-to-success. A quick failed task must not appear faster-to-completion than a slower successful task. Reports show paired task outcomes/times, all-attempt cost/time, graded coverage, and explicit denominators for success-only timing summaries.

## Scenario evidence

For AC-MB-006, use `local-attested-michael-laptop`: capture environment/condition hashes, native endpoint attribution, agent trajectory, independent grading receipt, before/after owned-setting hashes, cancellation outcome, and measurement coverage. A nominal failed task may be valid evidence of integration, but must not be reported as a successful model task.

For AC-MB-007, use `local-attested-michael-remote`: capture both target manifests, approved data policy and budget, task/condition hashes, telemetry availability, verifier outputs, blocked-capability case, and cleanup receipts. Self-hosted/cloud measurements require evidence from the actual targets, not mocked hardware claims.

## Existing pilot status

The source pilot reports calibrated coding replays and 23 focused offline correction checks. This does not satisfy these new tests until its actual source/fixtures are inventoried and the new contracts verified. Native desktop-agent and cross-target validation remain outstanding.
