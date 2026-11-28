# Inkling-2-mini (local) scorecard

Generated from verified ledgers by `python -m benchmarks.michael.scorecards.generate`; do not hand-edit.

Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

- **Model ID:** `mtplx-inkling-2-mini-optimized-quality`
- **Deployment:** local laptop
- **Conditions/epochs:** MB-R3/local-laptop/v12b, MB-R3/local-laptop/v9b, MB-R3/local-laptop/v9c, MB-R3/local-laptop/v9d
- **Overall:** 8/15 (30%–75%) across 15 tasks; pass@1 53%
- **pass^3:** not yet (fewer than 3 runs per task)
- **Pass-any:** 8/15 tasks
- **Verified time:** median [IQR] 100s [86–137]; 1 host-sleep timing(s) excluded
- **Tokens per run (in / out):** 126,234 / 9,240
- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)
- **Use it for:** no work type with ≥3 runs at ≥90% yet
- **Avoid it for:** Design × medium, Implement × small

## By work type

| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |
|---|---:|---|---:|---:|
| Design × medium | 2 | 1/2 (9%–91%) | — | 198,994 / 16,114 |
| Experiment × medium | 1 | 0/1 (0%–79%) | — | 192,344 / 12,792 |
| Experiment × small | 1 | 1/1 (21%–100%) | 92s | 104,895 / 7,370 |
| Implement × medium | 1 | 0/1 (0%–79%) | — | 14,406 / 4,899 |
| Implement × small | 3 | 2/3 (21%–94%) | 179s | 145,388 / 9,740 |
| Operate × small | 1 | 1/1 (21%–100%) | 31s | 42,553 / 1,668 |
| Orchestrate × medium | 1 | 0/1 (0%–79%) | — | 232,581 / 16,903 |
| Research × medium | 1 | 1/1 (21%–100%) | 81s | 102,176 / 5,573 |
| Research × small | 2 | 2/2 (34%–100%) | 110s | 130,847 / 6,216 |
| Review and repair × medium | 1 | 0/1 (0%–79%) | — | 3,052 / 111 |
| Understand and plan × small | 1 | 0/1 (0%–79%) | — | 105,661 / 15,410 |

## Failure patterns

| Pattern | Count | Example |
|---|---:|---|
| `premature-stop-without-edit` | 3 | cs-mismatch-stage-authority-v2 repeat 1 (MB-R3/local-laptop/v9d) |
| `ignored-existing-state` | 1 | plan-dashboard-waves-v2 repeat 1 (MB-R3/local-laptop/v9d) |
| `budget-noncompletion` | 1 | design-alethiometer-gear-mesh repeat 1 (MB-R3/local-laptop/v12b) |
| `unsupported-defect-claim` | 1 | orchestrate-voice-integration-v5 repeat 1 (MB-R3/local-laptop/v12b) |
| `spec-misread` | 1 | yv-relevance-instrument-v4 repeat 1 (MB-R3/local-laptop/v12b) |

## Quality panel

7 scored failure(s); each was attributed by two independent auditors from other model families, deterministic evidence first. Only model-attributed failures are scored; harness/environment faults are listed under caveats and rerun as disclosed attempts.

## Routing picks

- Not currently a pick in any work type.

## Caveats

- Local co-tenancy: resident idle Colima/pa-dev-postgres; sleep-affected timings excluded; never pooled with cloud.
- Overall combines local adapter epochs (v9b, v9d, v12b) that share the 64 KiB input cap; v12b also passes multiple tool calls and raised the protocol event-count cap. Per-epoch cells are in the matrix; later epochs run concurrently with cloud cohorts.
- 13 unscored physical attempt(s) (harness/environment), excluded from rates: status (runtime:local_parallel_tools_denied); status (scratch:scratch_scan:spawnSync /Library/Developer/CommandLin); emv-thumbnails-gallery-v3 (runtime:local_native_tool_failed); foal-meadow-regression-review-v2 (harness-cap: input-admission unavailable (64 KiB input-JSON ); review-conflict-predictor-v4 (environment: host sleep during inference (runtime:The operat); validator (harness-cap: input-admission unavailable (64 KiB input-JSON ); foal-meadow-regression-review-v2 (harness-cap: input-admission unavailable (64 KiB input-JSON ); kerrigan-plan-conflict-queue-v4 (harness-cap: input-admission unavailable (64 KiB input-JSON ); kirkland-compose-adoption (harness-cap: input-admission unavailable (64 KiB input-JSON ); orchestrate-sl-sim-phase-one (harness-cap: input-admission unavailable (64 KiB input-JSON ); review-conflict-predictor-v4 (runtime:local_native_tool_failed); te-baseline-eval (harness-cap: input-admission unavailable (64 KiB input-JSON ); vhs-room-registry-sync-v2 (harness-cap: input-admission unavailable (64 KiB input-JSON )
- Every run is a fresh session; repeats share tasks, so intervals are descriptive.
