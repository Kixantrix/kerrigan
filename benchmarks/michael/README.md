# Michael Bench: offline contracts and engine proof

MB-001a preserves historical imports; MB-001b adds engine-neutral manifests.
MB-002 adds a bounded [Inspect offline compatibility proof](engine_proof/README.md).
MB-004 adds the offline [ledger/report API](ledger_report/api.py).
The contracts alone provide no runtime attestation. Neither the proof nor this
API is a general runner, public CLI, historical calibration, live telemetry,
or scored model trial.
See the [plan](../../specs/projects/michael-bench/plan.md).
## Historical import v1

`contracts/historical_import.py` exposes
`import_historical(source_bytes, *, expected_sha256, corrections=None)`.
It uses only Python's standard library, performs no I/O, and raises
`HistoricalImportError` with actionable field/source details on invalid input.

Source input is immutable UTF-8 JSON bytes. The small synthetic/sanitized pilot
shape requires integer `schema_version: 1`, `task`, `target`, and `condition`
objects with nonempty `id`, a `provenance` object with nonempty `source_id`,
a `denominators` object, and an `attempts` array of objects with unique nonempty
`id`. Optional `retry_of` references an earlier attempt. This is an interchange
shape, not a claim about the uninspected real pilot's schema. A future adapter
must preserve its raw evidence rather than rewriting it to fit this shape.

The historical envelope retains exact bytes in `source.bytes_base64`, their
SHA-256, the full parsed `source.payload`, and separate copies of the identifying
descriptors. Unknown source fields and denominator meanings are opaque and
retained, not recalculated. Verdicts, cancellations, evaluator failures, native/
derived/unknown usage, and absent/null telemetry are not normalized or repaired.
Power-only usage/cache may remain `not_applicable`; rail watts stay rail watts,
never inferred whole-device power.

Corrections are a separate array, each containing a unique nonempty `id`,
`source_sha256`, `attempt_id`, `field: "stop_reason"`, nonempty `original_value`
matching the source attempt, nonempty `corrected_value`, and a `provenance`
object with `source_id`. Extra correction fields survive. Multiple corrections
may annotate one original value; they are retained in order, not resolved by
last-write-wins. Corrections never patch or relabel original evidence.

`expected_sha256` must be the independently obtained lowercase 64-character
digest of the exact input bytes. Duplicate JSON keys, nonfinite numbers,
unsupported versions/types, and inconsistent references are errors.
`record_id` hashes the canonical envelope (excluding the ID itself).
Reimporting the same bytes and ordered corrections yields the same record.
Adding corrections yields a distinct record; persistence is caller-owned and
must be append-only, retaining earlier envelopes. No evidence writer exists here.

## Manifests v1

`contracts/manifests.py` exposes `validate_manifest(value)`,
`manifest_reference(value)`, and keyword-only
`validate_bundle(task=..., target=..., agent=..., condition=..., result=None)`.
These I/O-free standard-library APIs consume parsed JSON objects, raise
`ManifestError` with field paths, and return independent copies. Each descriptor
requires `schema_version: 1`, `kind`, `id`, `revision`, and `provenance.source_id`.
References contain `id`, `revision`, and SHA-256 of validated canonical JSON
(sorted keys, compact separators, UTF-8). Bundle validation checks exact matches.
Unknown structural fields/versions are rejected; provenance metadata is open.

Task descriptors declare `base` (`uri`, `sha256`) and nonempty `agent_material`
and `verifier_material` arrays (`uri`, `sha256`, `audience`), respectively
`requirement_only` and `verifier_only`, without shared URI/content digests.
Targets separate `requested_identity`
from evidenced `observed_identity` and `runtime`. Agents declare a frozen
`harness` reference and evidenced `configuration`.

Conditions reference task/target/agent and declare three `hosts` roles
(`inference`, `agent`, `verifier`), `track` (`practical_system`,
`controlled_capability`, `harness_configuration`), `cache_policy`, `budgets`
(`active_safety_seconds`, `response_tokens`, `reasoning_tokens`, `attempt_limit`),
`retry_policy` (`no_automatic_retries`, `declared_retries`), `capabilities`,
`observability`, and `required_semantics`. Required capabilities must be known
true; token/reasoning budgets need not be matched across practical systems.
Evidence uses `{status, source, value}` when `known`, otherwise
`{status, source, reason}` with `unknown`, `unsupported`, or `not_applicable`.
No unavailable value is converted to zero. Declarations are not proof of
provider identity, capability enforcement, or actual verifier isolation.

Results reference a condition and retain every attempt, with unique `id`,
optional earlier `retry_of`, independent `verdict`, `state`, `stop_reason`,
`verifier`, `events`, `timing`, and evidenced numeric `usage`. The synthetic
tests demonstrate exact shapes and failure cases. Runtime/infrastructure/safety
event codes remain source-attributed strings (including native stream errors).
Validation does not enforce budgets, persist a ledger, or score performance.

Timing phases are `queue`, `provisioning`, `setup`, `agent_work`, `verification`,
and `end_to_end`. Known measurements contain `seconds`, `scope`, `clock`,
`host_ids`, and `coverage` (`complete` or `partial`), inside source evidence.
`monotonic` is single-host only; `correlated_wall` requires `correlation_id`.
Durations are supplied, never computed by subtracting cross-host clocks or
summing possibly overlapping phases. Same-clock phases cannot exceed a complete
end-to-end duration. Missing timing/completion fields remain
unknown. `time_to_verified_completion`, when known, must equal the complete
end-to-end measurement of a completed, independently verified success.
Failed, capped, interrupted, cancelled, or ungraded attempts retain observed
elapsed time without invented completion time. Safety cutoffs are separate.

## Synthetic verification

`contracts/fixtures/pilot-v1.json` contains no real pilot data.
Run `python -m pytest tests/projects/michael_bench/test_historical_import.py tests/projects/michael_bench/test_manifests.py -q`.
These integration checks run on `cloud-linux`; smoke is not applicable until
MB-005 provides the offline CLI.

## Offline ledger and explicit comparisons (MB-004)

Import `Ledger`, `LedgerError`, and `compare` from
`benchmarks.michael.ledger_report.api` with the repository on Python's path.
`Ledger(path)` owns a caller-selected JSONL file in an existing directory.
It uses Linux advisory locks, append/fsync, sequence numbers, and a SHA-256 chain.
Every read revalidates all records and frozen bundle references. Corrupt/torn
writes raise explicit errors; there is no silent repair. Identical operations
return `False` without appending. Conflicting starts/events/terminals fail.
Retain an external final digest/receipt if detection of whole-tail deletion is
required: a hash chain alone cannot detect removal of a valid suffix.

Call `start(trial_id, bundle, attempt_id=..., origin="synthetic"|"new_trial")`
before execution elsewhere. The bundle must omit `result`. `checkpoint` requires
the active attempt, a unique event ID, a contract event, timing evidence, and
`artifacts` containing URI/SHA-256 references. No referenced artifact is opened.
`finalize(trial_id, result, partial=None)` consumes a validated cumulative result,
retaining prior attempts unchanged and checkpoint events/elapsed observations.
Retries require another explicit start bound by `retry_of` and the frozen retry
policy/attempt limit. This records declarations; it cannot enforce runtime caps.
`recover(trial_id)` explicitly finalizes an unfinished start as interrupted/
ungraded, preserving events/artifact provenance and observed elapsed time, with
partial end-to-end coverage. It never creates another start or replays tools.

Optional auxiliary `partial` evidence has exactly `result` (manifest reference),
`attempt_id`, integer `passed`/positive `total`, `source`, and nonempty `artifacts`
(URI/SHA-256 references). It binds the exact cumulative result/current attempt.
Counts are not task passes; missing assertion measurements are not zero passes.

`compare(ledger, cohorts={"A": ["trial-a"], "B": ["trial-b"]}, suite=[task_ref])`
requires two named cohorts and an explicit frozen eligible suite; it never
auto-groups records. The default varying factor is `target`; alternatively
`factor="agent_configuration"` fixes the target and harness while allowing
configuration changes. Task digests, track, harness, budgets, retry/cache
policies, capabilities, and required semantics must match. Within-cohort
factor changes and synthetic/new-trial pooling fail. Historical envelopes remain
separate; they cannot be passed off as starts. Controlled tracks require known
matched controls/hosts and matched observability/runtime. Practical host and
observability differences remain visible in complete bundle disclosures.
Compatibility ignores `source`/`reason` only on evidence envelopes, never inside
their `value` payloads. Configuration/control payload keys and descriptor
provenance remain intact, including keys named `source` and `reason`.

Reports retain all starts, attempts, retries, terminal references, events,
artifacts, stop/verifier states, and auxiliary counts. Completion coverage uses
eligible tasks, including absent tasks. Per-task pairs retain failures and expose
both-success complete-time subset denominators. Phase totals exist only with
complete all-attempt evidence; observed sums are labeled, not estimates.
Usage names carry no unit/additivity semantics: even `price` is not assumed to
be spend. Without report-side declarations every usage sum/total stays unknown,
while raw measurements and coverage counts survive.

Optional `compare(..., usage_declarations=[...])` declarations require exactly
`trial_id`, `attempt_id`, `result` (exact terminal manifest reference for that
attempt), `metric`, `quantity`, `unit`, and nonempty `source`. Each binds one
existing metric; duplicates, absent metrics, incorrect result bindings, and
inconsistent quantity/unit pairs across the comparison fail explicitly.
All known values contributing to a sum require declarations. Supported additive
pairs are `count` with `tokens`, `credits`, `calls`, or `bytes` (integer values);
`total_spend` with `USD`, `EUR`, or `GBP`; and `energy` with `joules` or
`watt_hours`. Other units remain raw rather than being guessed or converted.
`gauge`, `rate`, and `unit_price` declarations preserve arbitrary nonempty unit
labels but never yield sums. Watts are not energy; prices per token are not spend.
Declarations are source-attributed claims, not measurement attestations.

For example, a declaration for a raw `expense` measurement can be:
`{"trial_id":"trial-a","attempt_id":"a1","result":result_ref,"metric":"expense",
"quantity":"total_spend","unit":"USD","source":"synthetic-receipt"}`.
Two declared USD expenses of 2.5 yield a total of 5; two undeclared `price`
values of 2.5, or two `rail_watts` gauge values, yield no sum or total.
Complete totals still require every attempt, including failures/retries, to
have known evidence. Missing quantities remain unknown, never zero.
No overlapping phases are summed into end-to-end time, no unknown becomes zero,
and zero-success time ratios are undefined. No universal ranking is produced.

Run the historical-import, manifests, and `test_ledger_report.py` tests together
with `python -m pytest ... -q` (exact paths in MB-004's briefing).
All are synthetic `cloud-linux` integration tests; CLI smoke belongs to MB-005.
