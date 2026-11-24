# Test plan: Michael Bench

## Levels

Use integration tests for task calibration, hidden-verifier separation, manifest capability handling, native-event transport, controller failure accounting, import integrity, and report math. Use unit tests only for nontrivial isolated policy and aggregation logic introduced by implementation.

Use an offline fake-model smoke test for the public CLI path. Do not require live inference or credentials in CI. Native laptop and remote hardware/provider evidence are scenario tests with attestation; simulated telemetry cannot close them.

## Tooling

Engine and language-specific test runner are pending MB-002. Reuse the selected engine's task/verifier facilities and the repository's existing validation chain rather than adding duplicate orchestration tooling.

Planning-artifact validation: `python3 -m tools.validators.check_artifacts`.

Implementation verification commands are to be recorded exactly in each briefing after engine selection. No nonexistent CLI/test command is presented as runnable. The implementation must document unit, integration, lint/type-check where applicable, and project smoke commands before dispatch completion.

## Risk areas / focus

- Reference/history leakage and task contamination.
- Lost terminal records, duplicate tool execution, invalid continuation history, and misattributed native request IDs.
- Response-cap exhaustion mistaken for voluntary completion or total-context exhaustion.
- Evaluator failure erased from coverage or graded as model incorrectness.
- Imported historical scores rewritten under a changed policy.
- Unmatched cache, quantization, reasoning, thermal, and concurrency conditions.
- Cloud energy or unavailable usage inferred as zero.
- Host generated-code execution or dangerous cleanup of unowned processes.
- Full pipeline overhead hidden behind fast decode numbers.
- Popularity or vendor throughput treated as proof of workflow value.
- Discovery state loss, repeat recommendations, source outages, and changed runtime compatibility.
- Stale hardware inventory mistaken for live available headroom.
- Web/model-card instructions crossing from research into unauthorized installation or execution.

Discovery collector/proposal tests use recorded synthetic source responses and hardware manifests. CI needs no third-party token, external inference, hardware probe, or live network. A separately approved source-connectivity check can verify real metadata access without downloading weights.

## Harness configuration assurance

Start with static inventory and fake-event/activation tests, then collect supported native baseline evidence under approved conditions. Compare task outcome and phase timings together; bytes/token estimates are diagnostic inputs, not an effectiveness gate.

Material skill/instruction/tool changes require negative activation and preservation canaries. Compaction/checkpoint changes require long-horizon retention and interruption tests. Use held-out tasks for confirmation after configuration screening and label unsupported cross-runtime controls explicitly.

Do not impose a global instruction-token threshold before measuring the actual composed baseline. Predeclare configuration-specific quality and meaningful-efficiency thresholds before experiments, with all-attempt accounting and protected scope/permission/verification outcomes.

## Statistical policy

Screening pilots describe observed cases, not statistical superiority. Freeze task selection, paired repetitions/order, deadlines, retry policy, and stopping rules before comparisons. Show trial counts and paired outcome differences; use uncertainty intervals appropriate to the sample rather than asserting equivalence from a small difference.

Report first-attempt completion and eventual completion separately. Include all starts in service coverage; independently show valid-graded coverage when the evaluator fails. Break down workload families before any overall aggregate.
