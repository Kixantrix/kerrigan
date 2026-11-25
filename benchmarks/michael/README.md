# Michael Bench: offline contracts and engine proof

MB-001a preserves historical imports; MB-001b adds engine-neutral manifests.
MB-002 adds a bounded [Inspect offline compatibility proof](engine_proof/README.md).
The contracts alone provide no runtime attestation. The proof is not a general
runner, ledger, public CLI, report, historical calibration, live telemetry,
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
