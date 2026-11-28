# Gemini 4 Neon scorecard

Generated from verified ledgers by `python -m benchmarks.michael.scorecards.generate`; do not hand-edit.

Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

- **Model ID:** `gemini-4-neon`
- **Deployment:** cloud
- **Conditions/epochs:** MB-R3/models-screen-v11, MB-R3/models-screen-v12b
- **Overall:** 21/21 (85%–100%) across 21 tasks; pass@1 100%
- **pass^3:** not yet (fewer than 3 runs per task)
- **Pass-any:** 21/21 tasks
- **Verified time:** median [IQR] 158s [110–222]
- **Tokens per run (in / out):** 159,357 / 19,179
- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)
- **Use it for:** Implement × medium, Implement × small, Review and repair × medium
- **Avoid it for:** no work type with ≥2 runs below 67%

## By work type

| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |
|---|---:|---|---:|---:|
| Design × medium | 2 | 2/2 (34%–100%) | 286s | 198,330 / 26,504 |
| Experiment × large | 1 | 1/1 (21%–100%) | 225s | 213,316 / 21,432 |
| Experiment × medium | 1 | 1/1 (21%–100%) | 145s | 126,228 / 13,696 |
| Experiment × small | 1 | 1/1 (21%–100%) | 100s | 106,958 / 8,278 |
| Implement × medium | 3 | 3/3 (44%–100%) | 209s | 131,445 / 18,706 |
| Implement × small | 3 | 3/3 (44%–100%) | 170s | 121,072 / 14,525 |
| Operate × small | 1 | 1/1 (21%–100%) | 51s | 56,358 / 3,722 |
| Orchestrate × large | 1 | 1/1 (21%–100%) | 381s | 424,665 / 40,630 |
| Orchestrate × medium | 1 | 1/1 (21%–100%) | 158s | 107,088 / 16,078 |
| Research × medium | 1 | 1/1 (21%–100%) | 105s | 71,030 / 9,405 |
| Research × small | 2 | 2/2 (34%–100%) | 150s | 101,812 / 15,074 |
| Review and repair × medium | 3 | 3/3 (44%–100%) | 248s | 269,582 / 32,327 |
| Understand and plan × small | 1 | 1/1 (21%–100%) | 118s | 74,269 / 9,679 |

## Failure patterns

None observed in scored runs.

## Quality panel

0 scored failure(s); each was attributed by two independent auditors from other model families, deterministic evidence first. Only model-attributed failures are scored; harness/environment faults are listed under caveats and rerun as disclosed attempts.

## Routing picks

- Not currently a pick in any work type.

## Caveats

- Selection role in admission: every admitted round-3 task required a passing Gemini 4 Neon blind solve, so the task set is filtered toward tasks it can solve.
- Admission blind-solve record (round 3, native): 22 passed, 0 failed; one VHS-v2 blind slot was a disclosed harness fault.
- Every run is a fresh session; repeats share tasks, so intervals are descriptive.
