# Claude Opus 5.5 scorecard

Generated from verified ledgers by `python -m benchmarks.michael.scorecards.generate`; do not hand-edit.

Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

- **Model ID:** `claude-opus-5.5`
- **Deployment:** cloud
- **Conditions/epochs:** MB-R3/models-screen-v11, MB-R3/models-screen-v12b
- **Overall:** 20/22 (72%–97%) across 22 tasks; pass@1 91%
- **pass^3:** not yet (fewer than 3 runs per task)
- **Pass-any:** 20/22 tasks
- **Verified time:** median [IQR] 58s [38–73]
- **Tokens per run (in / out):** 342,043 / 9,829
- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)
- **Use it for:** Implement × medium, Implement × small, Review and repair × medium
- **Avoid it for:** Design × medium

## By work type

| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |
|---|---:|---|---:|---:|
| Design × medium | 2 | 1/2 (9%–91%) | 56s | 530,272 / 18,658 |
| Experiment × large | 1 | 1/1 (21%–100%) | 67s | 199,089 / 7,104 |
| Experiment × medium | 1 | 1/1 (21%–100%) | 66s | 149,741 / 7,119 |
| Experiment × small | 1 | 1/1 (21%–100%) | 38s | 74,042 / 3,801 |
| Implement × medium | 3 | 3/3 (44%–100%) | 88s | 425,601 / 12,847 |
| Implement × small | 3 | 3/3 (44%–100%) | 61s | 102,680 / 6,126 |
| Operate × large | 1 | 1/1 (21%–100%) | 252s | 1,110,315 / 28,910 |
| Operate × small | 1 | 1/1 (21%–100%) | 25s | 97,035 / 1,739 |
| Orchestrate × large | 1 | 0/1 (0%–79%) | — | 1,442,143 / 29,714 |
| Orchestrate × medium | 1 | 1/1 (21%–100%) | 73s | 234,441 / 7,161 |
| Research × medium | 1 | 1/1 (21%–100%) | 38s | 173,772 / 3,320 |
| Research × small | 2 | 2/2 (34%–100%) | 37s | 147,763 / 3,110 |
| Review and repair × medium | 3 | 3/3 (44%–100%) | 74s | 340,497 / 8,283 |
| Understand and plan × small | 1 | 1/1 (21%–100%) | 26s | 81,974 / 2,066 |

## Failure patterns

| Pattern | Count | Example |
|---|---:|---|
| `wrong-domain-rule` | 2 | design-alethiometer-gear-mesh repeat 1 (MB-R3/models-screen-v11) |
| `unsupported-defect-claim` | 1 | orchestrate-sl-sim-phase-one repeat 1 (MB-R3/models-screen-v12b) |

## Quality panel

2 scored failure(s); each was attributed by two independent auditors from other model families, deterministic evidence first. Only model-attributed failures are scored; harness/environment faults are listed under caveats and rerun as disclosed attempts.

## Routing picks

- Not currently a pick in any work type.

## Caveats

- Every run is a fresh session; repeats share tasks, so intervals are descriptive.
