# Michael Bench: offline historical import

MB-001a implements only the engine-neutral historical-evidence import boundary.
It does **not** complete MB-001's task/target/condition manifests, select an engine,
or provide a runner, CLI, reporting, discovery, or live telemetry collection.
See the [plan](../../specs/projects/michael-bench/plan.md).

## Contract v1

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

## Synthetic verification

`contracts/fixtures/pilot-v1.json` contains no real pilot data.
Run `python -m pytest tests/projects/michael_bench/test_historical_import.py -q`.
These integration checks run on `cloud-linux`; smoke is not applicable until
MB-005 provides the offline CLI.
