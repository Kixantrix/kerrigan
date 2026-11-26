# Research: why does the "free" watcher cost money, and what should we do?

A serverless ticket-drop watcher was projected to cost USD 0.00 per month. The
first bill was not zero. Answer the decision questions below using only the
sources in `sources/` (S1–S6); no other knowledge or network is available.
Record your answers in `FINDINGS.json` (the only writable file), keeping its keys.

Monthly figures, in USD, rounded to the cent or better:
- `blob_cost_before_usd`: blob storage cost as measured (S4, before the fix).
- `blob_cost_after_fix_usd`: blob storage cost once the S5 fix is deployed.
- `functions_cost_usd`: execution plus compute cost. `logs_cost_usd`: log ingestion cost.
- `two_minute_timer_savings_usd`: monthly savings of option B relative to option A.
- `option_c_monthly_usd`, `email_service_monthly_usd` (email for ~500 messages a day):
  a number, or `null` when the sources cannot determine it.

Closed-vocabulary answers:
- `dominant_cost`: one of `blob_transactions`, `function_executions`,
  `function_compute`, `log_ingestion`.
- `excess_cause`: the application behavior that inflates the bill, one of
  `container-created-per-tick`, `index-fetched-per-race`, `oversized-log-retention`,
  `timer-too-frequent`, `state-blob-too-large`.
- `projection_error`: why the projection was wrong, one of
  `storage-transactions-omitted`, `free-grant-exceeded`, `price-sheet-outdated`,
  `log-volume-underestimated`.
- `recommendation`: `A`, `B` or `C` — the option that satisfies every requirement
  in S1 with costs the sources can establish.

Honesty and evidence:
- `unknowns`: the exact names of the keys above you set to `null` because the
  sources cannot determine them. Do not list keys you can determine.
- `citations`: for each non-null answer key, the list of source IDs (`S1`…`S6`)
  that support it, e.g. `{"blob_cost_before_usd": ["S2", "S4"]}`.

Read/write and tool/network boundaries are in policy.json. Offline Python 3
stdlib self-tests may help with the arithmetic.
