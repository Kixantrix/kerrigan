# Inkling-2-mini (local) scorecard

Generated from verified ledgers by `python -m benchmarks.michael.scorecards.generate`; do not hand-edit.

Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

- **Model ID:** `mtplx-inkling-2-mini-optimized-quality`
- **Deployment:** local laptop
- **Conditions/epochs:** MB-R3/local-laptop/v9b, MB-R3/local-laptop/v9c, MB-R3/local-laptop/v9d
- **Overall:** 6/9 (35%–88%) across 9 tasks; pass@1 67%
- **pass^3:** not yet (fewer than 3 runs per task)
- **Pass-any:** 6/9 tasks
- **Verified time:** median [IQR] 100s [92–120]; 1 host-sleep timing(s) excluded
- **Tokens per run (in / out):** 111,841 / 7,091
- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)
- **Use it for:** no work type with ≥3 runs at ≥90% yet
- **Avoid it for:** Implement × small

## By work type

| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |
|---|---:|---|---:|---:|
| Design × medium | 1 | 1/1 (21%–100%) | — | 348,494 / 15,256 |
| Experiment × small | 1 | 1/1 (21%–100%) | 92s | 104,895 / 7,370 |
| Implement × small | 2 | 1/2 (9%–91%) | 154s | 70,110 / 5,787 |
| Operate × small | 1 | 1/1 (21%–100%) | 31s | 42,553 / 1,668 |
| Research × small | 2 | 2/2 (34%–100%) | 110s | 130,847 / 6,216 |
| Review and repair × medium | 1 | 0/1 (0%–79%) | — | 3,052 / 111 |
| Understand and plan × small | 1 | 0/1 (0%–79%) | — | 105,661 / 15,410 |

## Failure patterns

| Pattern | Count | Example |
|---|---:|---|
| `premature-stop-without-edit` | 2 | cs-mismatch-stage-authority-v2 repeat 1 (MB-R3/local-laptop/v9d) |
| `ignored-existing-state` | 1 | plan-dashboard-waves-v2 repeat 1 (MB-R3/local-laptop/v9d) |

## Quality panel

3 scored failure(s); each was attributed by two independent auditors from other model families, deterministic evidence first. Only model-attributed failures are scored; harness/environment faults are listed under caveats and rerun as disclosed attempts.

## Routing picks

- Not currently a pick in any work type.

## Caveats

- Local co-tenancy: resident idle Colima/pa-dev-postgres; sleep-affected timings excluded; never pooled with cloud.
- 6 unscored physical attempt(s) (harness/environment), excluded from rates: status (runtime:local_parallel_tools_denied); status (scratch:scratch_scan:spawnSync /Library/Developer/CommandLin); emv-thumbnails-gallery-v3 (runtime:local_native_tool_failed); foal-meadow-regression-review-v2 (harness-cap: local 64 KiB input-JSON heuristic, not a model ); review-conflict-predictor-v4 (environment: host sleep during inference (runtime:The operat); validator (harness-cap: local 64 KiB input-JSON heuristic, not a model )
- Every run is a fresh session; repeats share tasks, so intervals are descriptive.
