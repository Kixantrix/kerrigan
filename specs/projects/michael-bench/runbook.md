# Runbook: Michael Bench

Status: operating requirements for a planned runner. There is no new runnable bench command yet.

## Deploy

First implement MB-001 through MB-005 and record verified setup/CLI commands. Pin the selected engine, dependencies, task assets, runtime versions, and digests. Keep local service adapters separate from the generic evaluator.

Do not install or replace the user's working model setup as part of bench installation.

## Operate

Discovery passes read only approved capability profiles, public source metadata, and permitted prior reports. Publish a dated delta/shortlist with source coverage and explicit no-change or incomplete-scan status. Missing inventory or prior state is a disclosed gap, not an excuse to inspect arbitrary host files. See [discovery.md](discovery.md).

Local recurring jobs require the app/machine to be available; cloud jobs require approved sanitized inputs and verified tool access. Document the saved schedule, location, activation state, and report destination. A review draft is not a saved or enabled job. No scheduler is configured by the project documents alone.

Do not run an evaluation merely because discovery recommends it. Approval freezes the relevant trial conditions and expenditure boundaries before dispatch. Revalidate live fit and service ownership at execution time.

For harness experiments, freeze instruction/skill/tool/configuration digests and observable controls as B0. Use isolated candidate configurations and preserve mandatory safeguards. Separate cold startup from warm turns, and include loader/tool/compaction overhead as well as verified completion. Do not alter the user's selected GHCP profile while collecting the baseline.

Record a promoted configuration's tested cohort, threshold evidence, and rollback manifest. Restore the previous configuration after an unsuccessful experiment. A future custom adapter must preserve the same task/verifier/event contracts and use independently authorized model access.

Before a live batch, freeze task/target/agent/verifier manifests, privacy eligibility, maximum time/spend, response/turn/action budgets, retry/continuation policy, concurrency, and stop criteria.

Preflight actual host capabilities and resource demand. Check owned request quiescence before model transitions. Use isolated ports/caches/evaluators, default-denied task network access, and finite deadlines. Do not disable memory admission or change shared-system limits.

Run a short compatibility gate before a comparative batch. Persist starts before execution, checkpoint interruption states, grade independently, and produce evidence even on failure. Native counters establish cache reuse; labels such as "cold" are not proof.

For interactive suitability, record queue/first-visible-response/complete-task latency and human intervention. For unattended suitability, measure verified completions per elapsed batch hour under a declared concurrency and contention profile.

## Debug

Identify whether the event is task failure, budget exhaustion, provider incompatibility, service failure, evaluator failure, or safety cancellation before changing policy. Preserve raw records and corrections. A changed prompt/budget/tool policy creates a new condition and never retroactively fixes old results.

If a run crashes, reconcile owned request IDs and mark recovery state before restarting. Do not repeat a side-effecting action on ambiguous receipt. Unknown telemetry or clock coverage makes the affected measurement unavailable, not zero.

For harness regressions, distinguish excessive context, wrong skill activation, repeated resources, orchestration delay, tool failure, model behavior, and compaction loss. A shorter profile that loses task context or required verification is not an optimization.

## Rollback

Stop only verified owned requests/services/evaluators. Restore owned service launch and live settings to the snapshot, verify the original endpoint and cache preservation, and publish a restoration receipt. Preserve downloaded assets and immutable results unless targeted deletion is explicitly authorized.

Interrupted or failed restoration blocks subsequent local trials until resolved.

## Secrets & access

Use approved credential stores and references; never task prompts, committed files, or shared trajectories. Explicit task-level approval is required before hosted inference sees nonpublic material. External model judging is not enabled by default.

Privileged power instrumentation requires separate authentication/approval. Prior pilot permission is not blanket authorization for new privileged actions, overnight execution, or cloud spending.
