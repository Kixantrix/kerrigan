# GPT 6.2 Sol scorecard

Generated from verified ledgers by `python -m benchmarks.michael.scorecards.generate`; do not hand-edit.

Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

- **Model ID:** `gpt-6.2-sol`
- **Deployment:** cloud
- **Conditions/epochs:** MB-R3/anchors-v13, MB-R3/models-screen-v11, MB-R3/models-screen-v12b
- **Overall:** 20/21 (77%–99%) across 21 tasks; pass@1 95%
- **pass^3:** not yet (fewer than 3 runs per task)
- **Pass-any:** 20/21 tasks
- **Verified time:** median [IQR] 89s [60–122]
- **Tokens per run (in / out):** 574,246 / 7,096
- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)
- **Use it for:** Implement × medium, Implement × small, Review and repair × medium
- **Avoid it for:** no work type with ≥2 runs below 67%

## By work type

| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |
|---|---:|---|---:|---:|
| Design × medium | 1 | 1/1 (21%–100%) | 64s | 163,728 / 3,544 |
| Experiment × large | 1 | 1/1 (21%–100%) | 138s | 1,472,525 / 7,496 |
| Experiment × medium | 1 | 1/1 (21%–100%) | 120s | 428,705 / 7,799 |
| Experiment × small | 1 | 1/1 (21%–100%) | 48s | 145,383 / 2,484 |
| Implement × medium | 3 | 3/3 (44%–100%) | 116s | 808,403 / 8,516 |
| Implement × small | 3 | 3/3 (44%–100%) | 70s | 481,891 / 4,387 |
| Operate × large | 1 | 1/1 (21%–100%) | 357s | 990,979 / 27,673 |
| Operate × small | 1 | 1/1 (21%–100%) | 35s | 139,333 / 1,167 |
| Orchestrate × large | 1 | 1/1 (21%–100%) | 311s | 1,928,260 / 21,218 |
| Orchestrate × medium | 1 | 0/1 (0%–79%) | — | 552,468 / 8,678 |
| Research × medium | 1 | 1/1 (21%–100%) | 49s | 230,581 / 2,064 |
| Research × small | 2 | 2/2 (34%–100%) | 74s | 269,612 / 3,950 |
| Review and repair × medium | 3 | 3/3 (44%–100%) | 111s | 483,339 / 6,261 |
| Understand and plan × small | 1 | 1/1 (21%–100%) | 38s | 147,087 / 1,506 |

## Public anchors

- **Raw (upstream-comparable):** 9/9 (70%–100%)
- **Adjusted:** 9/9 (70%–100%)

| Anchor | Runs | Raw pass |
|---|---:|---:|
| anchor-swepro-openlibrary | 3 | 3/3 |
| anchor-tb-fix-git | 3 | 3/3 |
| anchor-tb-nginx-request-logging | 3 | 3/3 |

Public anchors are scored only here, never in work-type routing. Raw is upstream-comparable; adjusted excludes failures confined to disclosed flagged behaviours (`anchor-overspecified`). Graded on the shared Colima VM (effective 2 GiB / 2 CPU cap). nginx base calibrates 2/8 natively vs 1/8 retained (admission holds). ansible and qutebrowser are admitted as `public-anchor-as-is`. element-web and tutanota: host-resource-unavailable (blocked pending user decision).

## Failure patterns

| Pattern | Count | Example |
|---|---:|---|
| `unsupported-defect-claim` | 1 | orchestrate-voice-integration-v5 repeat 1 (MB-R3/models-screen-v12b) |

## Quality panel

1 scored failure(s); each was attributed by two independent auditors from other model families, deterministic evidence first. Only model-attributed failures are scored; harness/environment faults are listed under caveats and rerun as disclosed attempts.

## Routing picks

- Not currently a pick in any work type.

## Caveats

- Every run is a fresh session; repeats share tasks, so intervals are descriptive.
