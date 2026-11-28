# GPT 5.6 Sol scorecard

Generated from verified ledgers by `python -m benchmarks.michael.scorecards.generate`; do not hand-edit.

Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

- **Model ID:** `gpt-5.6-sol`
- **Deployment:** cloud
- **Conditions/epochs:** MB-R3/anchors-v13, MB-R3/models-screen-v11, MB-R3/models-screen-v12b
- **Overall:** 21/21 (85%–100%) across 21 tasks; pass@1 100%
- **pass^3:** not yet (fewer than 3 runs per task)
- **Pass-any:** 21/21 tasks
- **Verified time:** median [IQR] 86s [65–127]
- **Tokens per run (in / out):** 420,324 / 7,682
- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)
- **Use it for:** Implement × medium, Implement × small, Review and repair × medium
- **Avoid it for:** no work type with ≥2 runs below 67%

## By work type

| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |
|---|---:|---|---:|---:|
| Design × medium | 2 | 2/2 (34%–100%) | 129s | 265,829 / 10,042 |
| Experiment × large | 1 | 1/1 (21%–100%) | 126s | 1,344,777 / 8,697 |
| Experiment × medium | 1 | 1/1 (21%–100%) | 127s | 516,636 / 9,691 |
| Experiment × small | 1 | 1/1 (21%–100%) | 65s | 158,113 / 4,791 |
| Implement × medium | 3 | 3/3 (44%–100%) | 89s | 467,977 / 7,877 |
| Implement × small | 3 | 3/3 (44%–100%) | 72s | 137,325 / 5,043 |
| Operate × large | 1 | 1/1 (21%–100%) | 187s | 604,916 / 17,591 |
| Operate × small | 1 | 1/1 (21%–100%) | 36s | 116,623 / 1,592 |
| Orchestrate × large | 1 | 1/1 (21%–100%) | 211s | 904,666 / 17,548 |
| Orchestrate × medium | 1 | 1/1 (21%–100%) | 116s | 317,012 / 8,661 |
| Research × medium | 1 | 1/1 (21%–100%) | 44s | 156,654 / 2,979 |
| Research × small | 1 | 1/1 (21%–100%) | 42s | 115,398 / 2,562 |
| Review and repair × medium | 3 | 3/3 (44%–100%) | 118s | 684,214 / 8,631 |
| Understand and plan × small | 1 | 1/1 (21%–100%) | 50s | 191,810 / 2,482 |

## Public anchors

- **Raw (upstream-comparable):** 8/9 (57%–98%)
- **Adjusted:** 8/9 (57%–98%)

| Anchor | Runs | Raw pass |
|---|---:|---:|
| anchor-swepro-openlibrary | 3 | 3/3 |
| anchor-tb-fix-git | 3 | 2/3 |
| anchor-tb-nginx-request-logging | 3 | 3/3 |

Public anchors are scored only here, never in work-type routing. Raw is upstream-comparable; adjusted excludes failures confined to disclosed flagged behaviours (`anchor-overspecified`). Graded on the shared Colima VM (effective 2 GiB / 2 CPU cap). nginx base calibrates 2/8 natively vs 1/8 retained (admission holds). ansible and qutebrowser are admitted as `public-anchor-as-is`. element-web and tutanota: host-resource-unavailable (blocked pending user decision).

## Failure patterns

None observed in scored runs.

## Quality panel

0 scored failure(s); each was attributed by two independent auditors from other model families, deterministic evidence first. Only model-attributed failures are scored; harness/environment faults are listed under caveats and rerun as disclosed attempts.

## Routing picks

- Not currently a pick in any work type.

## Caveats

- Selection role in admission: co-audited which tasks were admitted, fixed or retired.
- Every run is a fresh session; repeats share tasks, so intervals are descriptive.
