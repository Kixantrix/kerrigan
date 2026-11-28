# Model overview

Generated from verified ledgers; do not hand-edit. Cloud and local are never pooled in one cell. Cost is unknown for every model. Latest admitted task versions only; superseded versions excluded here (still in the matrix): design-alethiometer-case-v2, emv-thumbnails-gallery-v2, kerrigan-plan-conflict-queue-v2, orchestrate-voice-integration-v3, review-conflict-predictor-v3, yv-relevance-instrument-v2.

| Model | Deployment | Pass (95% Wilson) | Tasks | Median verified | Tokens in / out per run | Cost | Top failure pattern | Anchors raw / adjusted |
|---|---|---|---:|---:|---:|---|---|---|
| [Claude Sonnet 5.5](claude-sonnet-5.5.md) | cloud | 48/52 (82%–97%) | 22 | 40s | 254,896 / 7,132 | unknown | `stale-derived-document` ×2 | — |
| [MAI Code 2](mai-code-2.md) | cloud | 44/52 (72%–92%) | 22 | 126s | 403,311 / 7,659 | unknown | `unsupported-defect-claim` ×3 | — |
| [Claude Opus 5.5](claude-opus-5.5.md) | cloud | 20/22 (72%–97%) | 22 | 58s | 342,043 / 9,829 | unknown | `wrong-domain-rule` ×2 | — |
| [GPT 6.2 Sol](gpt-6.2-sol.md) | cloud | 20/21 (77%–99%) | 21 | 89s | 574,246 / 7,096 | unknown | `unsupported-defect-claim` ×1 | — |
| [GPT 6.2 Astra](gpt-6.2-astra.md) | cloud | 22/22 (85%–100%) | 22 | 75s | 259,635 / 4,091 | unknown | none | — |
| [Gemini 4 Neon](gemini-4-neon.md) | cloud | 21/21 (85%–100%) | 21 | 158s | 159,357 / 19,179 | unknown | none | — |
| [GPT 5.6 Sol](gpt-5.6-sol.md) | cloud | 21/21 (85%–100%) | 21 | 86s | 420,324 / 7,682 | unknown | none | — |
| [Inkling-2-mini (local)](mtplx-inkling-2-mini-optimized-quality.md) | local laptop | 8/15 (30%–75%) | 15 | 100s | 126,234 / 9,240 | unknown | `premature-stop-without-edit` ×3 | — |

## Pass rate by work type

| Work type | Claude Sonnet 5.5 | MAI Code 2 | Claude Opus 5.5 | GPT 6.2 Sol | GPT 6.2 Astra | Gemini 4 Neon | GPT 5.6 Sol | Inkling-2-mini (local) |
|---|---|---|---|---|---|---|---|---|
| Design × medium | 4/6 | 3/6 | 1/2 | 1/1 | 2/2 | 2/2 | 2/2 | 1/2 |
| Experiment × large | 3/3 | 3/3 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | — |
| Experiment × medium | 3/3 | 1/3 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 |
| Experiment × small | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| Implement × medium | 9/9 | 9/9 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 0/1 |
| Implement × small | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 |
| Operate × large | 3/3 | 3/3 | 1/1 | 1/1 | 1/1 | — | 1/1 | — |
| Operate × small | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| Orchestrate × large | 1/3 | 3/3 | 0/1 | 1/1 | 1/1 | 1/1 | 1/1 | — |
| Orchestrate × medium | 3/3 | 2/3 | 1/1 | 0/1 | 1/1 | 1/1 | 1/1 | 0/1 |
| Research × medium | 3/3 | 3/3 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| Research × small | 4/4 | 4/4 | 2/2 | 2/2 | 2/2 | 2/2 | 1/1 | 2/2 |
| Review and repair × medium | 9/9 | 7/9 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 0/1 |
| Understand and plan × small | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 |

## Routing picks (cloud, pooled across conditions)

| Work type | Established | Provisional | Most reliable |
|---|---|---|---|
| Design × medium | insufficient evidence | insufficient evidence | Claude Sonnet 5.5 |
| Experiment × large | insufficient evidence | insufficient evidence | insufficient evidence |
| Experiment × medium | insufficient evidence | insufficient evidence | insufficient evidence |
| Experiment × small | insufficient evidence | insufficient evidence | insufficient evidence |
| Implement × medium | insufficient evidence | Claude Sonnet 5.5 | Claude Sonnet 5.5 |
| Implement × small | insufficient evidence | insufficient evidence | insufficient evidence |
| Operate × large | insufficient evidence | insufficient evidence | insufficient evidence |
| Operate × small | insufficient evidence | insufficient evidence | insufficient evidence |
| Orchestrate × large | insufficient evidence | insufficient evidence | insufficient evidence |
| Orchestrate × medium | insufficient evidence | insufficient evidence | insufficient evidence |
| Research × medium | insufficient evidence | insufficient evidence | insufficient evidence |
| Research × small | insufficient evidence | insufficient evidence | insufficient evidence |
| Review and repair × medium | insufficient evidence | Claude Sonnet 5.5 | Claude Sonnet 5.5 |
| Understand and plan × small | insufficient evidence | insufficient evidence | insufficient evidence |

Established: n≥5, 95% lower bound ≥80%, fastest. Provisional (weaker): n≥6 across ≥2 tasks, point success ≥90%, lower bound ≥50%, fastest. Every run is a fresh session; selection roles in admission are disclosed per scorecard.

Public anchors are scored only here, never in work-type routing. Raw is upstream-comparable; adjusted excludes failures confined to disclosed flagged behaviours (`anchor-overspecified`). Graded on the shared Colima VM (effective 2 GiB / 2 CPU cap). nginx base calibrates 2/8 natively vs 1/8 retained (admission holds). ansible and qutebrowser are admitted as `public-anchor-as-is`. element-web and tutanota: host-resource-unavailable (blocked pending user decision).
