# GPT 6.2 Astra scorecard

Generated from verified ledgers by `python -m benchmarks.michael.scorecards.generate`; do not hand-edit.

Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

- **Model ID:** `gpt-6.2-astra`
- **Deployment:** cloud
- **Conditions/epochs:** MB-R3/models-screen-v11, MB-R3/models-screen-v12b
- **Overall:** 22/22 (85%–100%) across 22 tasks; pass@1 100%
- **pass^3:** not yet (fewer than 3 runs per task)
- **Pass-any:** 22/22 tasks
- **Verified time:** median [IQR] 75s [55–122]
- **Tokens per run (in / out):** 259,635 / 4,091
- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)
- **Use it for:** Implement × medium, Implement × small, Review and repair × medium
- **Avoid it for:** no work type with ≥2 runs below 67%

## By work type

| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |
|---|---:|---|---:|---:|
| Design × medium | 2 | 2/2 (34%–100%) | 93s | 182,276 / 5,360 |
| Experiment × large | 1 | 1/1 (21%–100%) | 76s | 251,474 / 3,914 |
| Experiment × medium | 1 | 1/1 (21%–100%) | 68s | 201,819 / 2,740 |
| Experiment × small | 1 | 1/1 (21%–100%) | 49s | 130,221 / 1,827 |
| Implement × medium | 3 | 3/3 (44%–100%) | 95s | 410,529 / 6,249 |
| Implement × small | 3 | 3/3 (44%–100%) | 81s | 117,037 / 3,115 |
| Operate × large | 1 | 1/1 (21%–100%) | 175s | 603,359 / 9,641 |
| Operate × small | 1 | 1/1 (21%–100%) | 210s | 82,053 / 807 |
| Orchestrate × large | 1 | 1/1 (21%–100%) | 211s | 1,002,269 / 13,288 |
| Orchestrate × medium | 1 | 1/1 (21%–100%) | 120s | 362,266 / 5,132 |
| Research × medium | 1 | 1/1 (21%–100%) | 46s | 137,537 / 1,598 |
| Research × small | 2 | 2/2 (34%–100%) | 49s | 121,408 / 1,464 |
| Review and repair × medium | 3 | 3/3 (44%–100%) | 56s | 222,819 / 2,828 |
| Understand and plan × small | 1 | 1/1 (21%–100%) | 210s | 82,445 / 839 |

## Failure patterns

None observed in scored runs.

## Quality panel

0 scored failure(s); each was attributed by two independent auditors from other model families, deterministic evidence first. Only model-attributed failures are scored; harness/environment faults are listed under caveats and rerun as disclosed attempts.

## Routing picks

- Not currently a pick in any work type.

## Caveats

- Every run is a fresh session; repeats share tasks, so intervals are descriptive.
