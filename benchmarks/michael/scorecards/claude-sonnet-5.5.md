# Claude Sonnet 5.5 scorecard

Generated from verified ledgers by `python -m benchmarks.michael.scorecards.generate`; do not hand-edit.

Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

- **Model ID:** `claude-sonnet-5.5`
- **Deployment:** cloud
- **Conditions/epochs:** MB-009r, MB-010r, MB-R3/anchors-v13, MB-R3/discovery-parity-v4, MB-R3/expanded-v5, MB-R3/foal-v6, MB-R3/gapfill-v8, MB-R3/original-tooltip-v1, MB-R3/policy-tooltip-v2, MB-R3/successors-v7c
- **Overall:** 48/52 (82%–97%) across 22 tasks; pass@1 92%
- **pass^3:** 13/15 tasks with ≥3 runs
- **Pass-any:** 22/22 tasks
- **Verified time:** median [IQR] 40s [26–49]
- **Tokens per run (in / out):** 254,896 / 7,132
- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)
- **Use it for:** Experiment × large, Experiment × medium, Implement × medium, Implement × small, Operate × large, Orchestrate × medium, Research × medium, Research × small, Review and repair × medium
- **Avoid it for:** Design × medium, Orchestrate × large

## By work type

| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |
|---|---:|---|---:|---:|
| Design × medium | 6 | 4/6 (30%–90%) | 121s | 282,060 / 10,942 |
| Experiment × large | 3 | 3/3 (44%–100%) | 44s | 202,935 / 5,573 |
| Experiment × medium | 3 | 3/3 (44%–100%) | 26s | 61,566 / 3,367 |
| Experiment × small | 1 | 1/1 (21%–100%) | 29s | 71,474 / 2,734 |
| Implement × medium | 9 | 9/9 (70%–100%) | 42s | 258,499 / 8,165 |
| Implement × small | 3 | 3/3 (44%–100%) | 35s | 74,590 / 4,231 |
| Operate × large | 3 | 3/3 (44%–100%) | 140s | 633,065 / 21,206 |
| Operate × small | 1 | 1/1 (21%–100%) | 20s | 72,213 / 1,143 |
| Orchestrate × large | 3 | 1/3 (6%–79%) | 152s | 1,008,443 / 18,025 |
| Orchestrate × medium | 3 | 3/3 (44%–100%) | 44s | 146,717 / 5,611 |
| Research × medium | 3 | 3/3 (44%–100%) | 26s | 131,980 / 2,557 |
| Research × small | 4 | 4/4 (51%–100%) | 29s | 129,092 / 2,584 |
| Review and repair × medium | 9 | 9/9 (70%–100%) | 41s | 190,470 / 3,732 |
| Understand and plan × small | 1 | 1/1 (21%–100%) | 22s | 83,588 / 2,218 |

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
| `stale-derived-document` | 2 | design-alethiometer-case-v4 repeat 2 (MB-R3/expanded-v5) |
| `wrong-domain-rule` | 2 | orchestrate-sl-sim-phase-one repeat 1 (MB-R3/gapfill-v8) |

## Quality panel

4 scored failure(s); each was attributed by two independent auditors from other model families, deterministic evidence first. Only model-attributed failures are scored; harness/environment faults are listed under caveats and rerun as disclosed attempts.

## Routing picks

- Design × medium: most reliable (cloud, pooled across conditions)
- Implement × medium: provisional (cloud, pooled across conditions)
- Implement × medium: most reliable (cloud, pooled across conditions)
- Review and repair × medium: provisional (cloud, pooled across conditions)
- Review and repair × medium: most reliable (cloud, pooled across conditions)

## Caveats

- Selection role in admission: co-audited which tasks were admitted, fixed or retired.
- Every run is a fresh session; repeats share tasks, so intervals are descriptive.
