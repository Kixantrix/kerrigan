# Cost plan: Michael Bench

## Cost drivers

Model inference including reasoning and failed/retried attempts; cache/storage; self-hosted hardware availability and electricity; evaluator compute; queueing; human intervention and rework. Separate one-time model download/setup from steady-state use.

Report paid API token/request charges with provider price/version/time provenance. For subscriptions, distinguish incremental billed cost, credit consumption, and any explicit allocation method; do not fabricate a per-token price.

## Baseline estimate

No new inference or cloud spending is authorized by this planning increment. Dollar and energy estimates require selected targets and measured usage.

Recurring discovery itself consumes agent credits and research time even without benchmark inference. Bound each pass, prioritize source deltas, and publish only a small actionable shortlist. A single research job is the initial design; additional automations need a demonstrated benefit and separate approval.

Harness experiments must count skill/tool discovery requests, repeated reads, compaction, delegation, and recovery work as well as inference. Compare billed/native cache behavior: a shorter uncached payload can be slower or more expensive than a larger reusable prefix. Static prompt bytes cannot establish savings.

Include maintenance and migration burden when comparing GHCP, a thin custom loop, and an existing SDK. A custom harness does not inherit model-subscription entitlements or eliminate provider, hosting, permission, and verification costs.

The source pilot's CPU/GPU/ANE power samples cover shared compute engines, not inference-process or whole-laptop power. Do not relabel them as battery drain or whole-machine joules. Cloud energy is unavailable unless trustworthy measured data and boundary are supplied.

For a comparable batch, spend per success is total batch spend divided by verified successes; energy per success uses total measured energy over the same declared boundary and coverage. Zero successes makes either ratio undefined, not zero. Human time remains a separate measured dimension unless an explicit valuation is approved.

## Guardrails (budgets/alerts/tags)

Require an explicit per-batch spend/time ceiling before paid execution and reserve enough budget to terminate and collect evidence. Tag by task, condition, target, and trial. Log refusals and exhausted budgets.

Start with three coding cases and a small screen; only expand repetitions or context after demonstrated compatibility and useful signal. No unbounded matrix across every model/quantization/runtime/hardware permutation.

## Scale assumptions

Compare sequential interactive work separately from parallel unattended work. Record concurrency, evaluator placement, download contention, idle baseline, and thermal state. More throughput that destabilizes the user's laptop is not an unconditional improvement.

Prefer a workload-specific Pareto frontier over a universal score: quality and reliability first, then explain the tradeoffs among speed, attention, cost, energy, and memory/storage demand.
