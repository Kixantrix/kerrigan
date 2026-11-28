# MAI Code 2 scorecard

Generated from verified ledgers by `python -m benchmarks.michael.scorecards.generate`; do not hand-edit.

Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

- **Model ID:** `mai-code-2`
- **Deployment:** cloud
- **Conditions/epochs:** MB-009r, MB-010r, MB-R3/discovery-parity-v4, MB-R3/expanded-v5, MB-R3/foal-v6, MB-R3/gapfill-v8, MB-R3/original-tooltip-v1, MB-R3/policy-tooltip-v2, MB-R3/successors-v7c
- **Overall:** 44/52 (72%–92%) across 22 tasks; pass@1 85%
- **pass^3:** 11/15 tasks with ≥3 runs
- **Pass-any:** 21/22 tasks
- **Verified time:** median [IQR] 126s [86–217]
- **Tokens per run (in / out):** 403,311 / 7,659
- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)
- **Use it for:** Experiment × large, Implement × medium, Implement × small, Operate × large, Orchestrate × large, Research × medium, Research × small
- **Avoid it for:** Design × medium, Experiment × medium, Orchestrate × medium

## By work type

| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |
|---|---:|---|---:|---:|
| Design × medium | 6 | 3/6 (19%–81%) | 103s | 313,128 / 10,947 |
| Experiment × large | 3 | 3/3 (44%–100%) | 213s | 813,962 / 7,815 |
| Experiment × medium | 3 | 1/3 (6%–79%) | 119s | 268,201 / 6,711 |
| Experiment × small | 1 | 1/1 (21%–100%) | 52s | 75,399 / 2,101 |
| Implement × medium | 9 | 9/9 (70%–100%) | 154s | 333,223 / 8,481 |
| Implement × small | 3 | 3/3 (44%–100%) | 91s | 193,699 / 5,511 |
| Operate × large | 3 | 3/3 (44%–100%) | 278s | 762,581 / 13,618 |
| Operate × small | 1 | 1/1 (21%–100%) | 46s | 122,376 / 1,103 |
| Orchestrate × large | 3 | 3/3 (44%–100%) | 258s | 1,299,714 / 11,570 |
| Orchestrate × medium | 3 | 2/3 (21%–94%) | 202s | 261,729 / 8,536 |
| Research × medium | 3 | 3/3 (44%–100%) | 62s | 152,149 / 2,560 |
| Research × small | 4 | 4/4 (51%–100%) | 64s | 142,381 / 2,054 |
| Review and repair × medium | 9 | 7/9 (45%–94%) | 149s | 442,671 / 8,249 |
| Understand and plan × small | 1 | 1/1 (21%–100%) | 50s | 86,926 / 1,641 |

## Failure patterns

| Pattern | Count | Example |
|---|---:|---|
| `unsupported-defect-claim` | 3 | review-conflict-predictor-v4 repeat 2 (MB-R3/policy-tooltip-v2) |
| `wrong-domain-rule` | 3 | design-alethiometer-gear-mesh repeat 1 (MB-R3/expanded-v5) |
| `spec-misread` | 2 | yv-relevance-instrument-v4 repeat 1 (MB-R3/expanded-v5) |

## Quality panel

8 scored failure(s); each was attributed by two independent auditors from other model families, deterministic evidence first. Only model-attributed failures are scored; harness/environment faults are listed under caveats and rerun as disclosed attempts.

## Routing picks

- Not currently a pick in any work type.

## Caveats

- Every run is a fresh session; repeats share tasks, so intervals are descriptive.
