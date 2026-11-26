# MB-006l: first real validator comparison

Both models independently passed all 25 checks on the same historical Python
validator repair task using stock CLI response behavior and the same confined
native tools. Sonnet completed this single task about 2.4 times faster.

| Requested model | Preservation | Regression | Verified end-to-end | Active native session | Native calls | Agent actions |
|---|---:|---:|---:|---:|---:|---:|
| MAI Code 2 | 15/15 | 10/10 | 86.67 s | 85.33 s | 8 | 7 |
| Sonnet 5.5 | 15/15 | 10/10 | 36.07 s | 34.73 s | 7 | 6 |

One additional controller-owned final source read is excluded from agent action
counts. Each model received one controller prompt in this corrected condition;
natural tool-loop inference calls are not retries. Both sessions ended idle,
all native handles were reaped, and independent Docker grading followed exact
final-source collection. Cleanup took 0.158 s and 0.221 s respectively.

Native usage events reported 95,599 input / 4,339 output tokens for MAI and
118,479 input / 4,747 output tokens for Sonnet. These are summed per-call
provider reports, including repeated context, not independent token measures.
Cache-read totals were 61,952 and 94,762; cache-write totals were 0 and 23,701.
Reported reasoning totals were 2,178 and 927. Monetary cost and independently
attested backend identity remain unknown; the native cost field's unit is not
established, so it is not used for a price comparison.

The first live condition failed both models at the harness-injected 131072-byte
HTTP response ceiling: MAI before task actions, Sonnet after three. Those
attempts remain ungraded and retained in `mb006l-live-v1-*`, not counted as model
task failures. The corrected condition removes that environment variable
entirely. It retains finite 8 MiB frame / 96 MiB aggregate / 16,384 event / 1 GiB
disk caps, unchanged task/action/output limits, explicit sandbox, no-fork,
credential/network denial, and fresh verified public HTTPS before each prompt.
Actual protocol traffic was 1,704,171 bytes / 1,637 events for MAI and 1,490,621
bytes / 2,799 events for Sonnet, comfortably inside that envelope.

For this use case, the observation favors Sonnet for turnaround on this small
validator repair, while MAI achieved the same correctness. This is one public
historical task per model, run sequentially; cache conditions, order effects
and possible prior exposure are not controlled. It is not evidence of general
model superiority, broader reliability, private-task performance or price.

Corrected condition SHA256:
`b50d47b8db6e09b03f7f1ceadf9a14f551c003088c4c1eb760d26e8519bf22d7`.
`mb006l-live-v2-verification.json` binds the safe attempt archive, native usage
projections, independent grader reports, exact candidate bytes, and the
existing ledger's target-comparison report. `mb006l-stock-safety-*` preserves
the final-source offline/native safety verification. All six earlier canary
slots and both first-condition validator attempts are unchanged.
