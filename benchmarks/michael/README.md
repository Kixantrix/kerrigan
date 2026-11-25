# Michael Bench: offline contracts, engine proof and replay packages

MB-001a preserves historical imports; MB-001b adds engine-neutral manifests.
MB-002 adds a bounded [Inspect offline compatibility proof](engine_proof/README.md).
MB-004 adds the offline [ledger/report API](ledger_report/api.py).
MB-003 adds three [historical replay packages](tasks/packages.py), with
requirement-only exports and separately retained verification/calibration.
The contracts alone provide no runtime attestation. Neither the proof nor this
API is a general runner, live telemetry,
or scored model trial.
See the [plan](../../specs/projects/michael-bench/plan.md).

## Public offline CLI (MB-005)

The synthetic integer fixture reuses Inspect, MB-002 materials and ledger/report APIs; **not** native identity/isolation proof, a replay trial or model performance. Cloud Linux prerequisites: owned venv with `engine_proof/requirements.txt`, Docker, Compose, pinned `cli/compose.yaml` image and credential-free `DOCKER_CONFIG` (no `config.json`) containing the plugin. Provisioning is timed separately; no local fallback.
```bash
python -m benchmarks.michael.cli compare /owned/new/comparison
bash benchmarks/michael/scripts/smoke.sh /owned/new/smoke-1
python -m benchmarks.michael.cli recover /owned/interrupted/trial
```

Modes: success/negative/runtime_error/timeout/background/symlink/special/extra_output/outside/evaluator_error/sentinel_spoof/verifier_tamper/oversized_stdout/oversized_stderr. `--seconds`: default 45, finite 0.1–90. The monotonic cap starts before worker launch, covering imports/setup, agent and verification, independently of the 30-second tool timeout. A **15-second alarm** bounds cleanup/evidence; exhaustion leaves an explicitly recoverable start.
End-to-end ends after cleanup/evidence collection, before terminal persistence. Queue/provisioning are unknown; setup includes imports. Phases are not summed; deadlines are not completion times. Agent root is read-only, network denied, capabilities dropped; only an owned `/work` volume is mounted, never host checkout/home/socket. Background workers are rejected and the whole agent killed before reading output/staging assertions.
Only regular `answer.py` (64 KiB; archive 1 MiB) enters a fresh candidate-execution container, without hidden assertions. After it stops, trusted validation consumes only a JSON array of three integers. A separate fresh grader runs the unchanged hidden assertions against a trusted response proxy, never candidate code. Candidate exit/stdout cannot establish a verdict; malformed responses are failed, assertion failure is failed, and evaluator errors are ungraded/error. No success sentinel or secret marker is used. No host archive extraction. Recovery kills owned resources and records interruption without replay. Exit: 0 verified, 2 failed/ungraded, 3 cutoff/interruption/recovery, 4 invalid input/preflight/reserve. Stdout: `{"synthetic":true,"directory":"/owned/new/comparison","exit_status":0}`.
Candidate and grader stdout **and** stderr are captured incrementally, with separate 65,536-byte limits. Overflow stops the owned attach process/container before grading and records `safety_stop`, an explicit channel-specific output-limit event, CLI exit 3 (comparison exit 2), and unknown completion time. `candidate-capture.json`/`verifier-capture.json` retain capped exact-byte Base64 prefixes, observed lower bounds (not invented stream totals), termination state and capture timing. Docker logging is disabled for these containers; no uncapped daemon log is retained. Existing whole-trial and cleanup reserves still apply.
The [stream-limit receipt](cli/evidence/stream-proof.json) and [raw proof archive](cli/evidence/stream-proof.tar.gz) retain both overflow cases, cutoff/recovery, two fresh smokes and byte-verified source bindings.
Retain raw Inspect JSON, immutable checkpoints, process receipts, terminals, SHA-256 bindings, ledgers and reports. Stable descriptors bind fixture/adapter bytes; both arms are synthetic. Reports keep paired times/coverage, failures and unknown/nonadditive usage. Native identity/tools, replay delivery and credits remain gated.

The [grading proof receipt](cli/evidence/grading-proof.json) records exact commands, durations and file hashes for the [raw synthetic archive](cli/evidence/grading-proof.tar.gz). It includes unchanged vulnerable-before receipts (explicitly **invalid completion evidence**), corrected spoof/tamper outcomes, evaluator error, cutoff/recovery, two fresh smokes and the exact tested adapter source snapshot.

## Historical replay packaging (MB-003)

Only `tasks/<name>/TASK.md`, allowlisted exact-base Git source/direct type-only
imports, pinned dependency files, and generated `policy.json` enter an agent
export. `tasks/<name>/manifest.json`, `calibration.json`, `tasks/hidden/`, this
README, the packaging code, and repository/history access are **verifier-only**.
Never launch an evaluated agent in this checkout: it contains the answers.
Deliver only the checked export to a separately proven isolated host/session.
Packaging labels do not enforce native Copilot tools, mounts, network, history
access, or process isolation. That proof is still outstanding.

The three frozen v1 task descriptors use the existing task manifest contract.
Their provenance holds exact base/reference commits, source/material digests,
selected pre-existing checks and exposure limits. Calibration copies the actual
reference implementation for the single writable file, not reference docs,
toolchain changes, a toy implementation, or gold tests. Independent hidden
behavior assertions are authored here; preservation tests are unchanged bytes
from the base. The validator's existing AGENTS.md sanity test uses a minimal
`.github/agents/` fixture outside the agent export, not this harness's full docs.
Legacy parser compatibility assertions remain in both the pre-existing and
hidden suites.

| Task | Coverage | Limit |
| --- | --- | --- |
| grouping | Current-major filtering, mixed references, ordering, legacy API | Pure logic from public historical PR #405; no UI/browser evidence |
| status | Docs/plan/briefing filtering, closing references, implementation/status preservation | Offline adaptation of public historical PR #409; no live GitHub E2E |
| validator | Malformed YAML, block/inline lists, empty/mapping MCP values, skill checks, legacy helper | Public historical PR #434; no whole-toolchain change |

All three have known public historical exposure/recognition risk. They are not
a contamination-free leaderboard or representative working-day suite. Exact
direct type-only imports are supplied for context, but their transitive runtime
dependencies are not loaded by Vitest; this is not a full dashboard build/type
check. No model, MAI Code 2/Sonnet trial, private pilot evidence, or hardware is
used. Calibration durations are trusted host subprocess timings, **not** time
to agent-verified completion.

From this repository root, first fetch the six full Git object IDs in the
verifier-only manifests (a shallow clone may not have them). Do not expose those
IDs, closing PR references, or a Git clone/history to the evaluated agent.
Create an isolated Python environment and install
`benchmarks/michael/tasks/dependencies/requirements.txt` (pytest 8.3.5,
PyYAML 6.0.2). Node dependencies are Vitest 3.2.4 and its exact integrity-pinned
lockfile closure; Python also pins iniconfig 2.3.1, packaging 26.4 and pluggy
1.7.0. Calibration runs `npm ci --ignore-scripts --no-audit --no-fund`.
Dependency provisioning may use network **before** agent work; agent network
policy is denied. No shared/global settings are changed.

With that Python interpreter on PATH, for each name (`grouping`, `status`,
`validator`), run:

```bash
python -m benchmarks.michael.tasks.packages stage grouping /owned/new/agent-export
python -m benchmarks.michael.tasks.packages check grouping /owned/new/agent-export
python -m benchmarks.michael.tasks.packages calibrate grouping /owned/new/receipt.json
```

Use a nonexistent owned export directory, outside this repository. `stage`
copies exact Git bytes, then checks the full path/content allowlist, unexpected
directories, symlinks, pinned digests, historical solution references and full
hidden material leakage. `check` repeats those checks on the delivered view.
Both print SHA-256 of canonical sorted path-to-content-SHA-256 JSON (compact
UTF-8 with trailing LF). This is an export-content digest, not a tar digest.
The manifests remain outside the export; their `agent/` and `hidden/` URIs are
logical references resolved by the trusted packager, not public download URLs.

`calibrate` creates an owned temporary workspace, checks the export, installs
declared dependencies, and executes baseline preservation, baseline regression,
then reference preservation plus regression. Expected regression failure is
mandatory; any preservation failure, skip, error, missing dependency or missing
report blocks calibration. Receipts retain exact commands, versions, stdout/
stderr, exit codes, test-case counts, failure names/messages, report digests and
monotonic durations. Counts are test cases, not individual expect/assert calls.
Temporary workspaces are cleaned after the trusted runs. `freeze` is a
maintainer-only operation for deliberate new package revisions; never silently
refreeze to resolve a validation mismatch.

Fresh cloud-host calibration receipts are in `tasks/<name>/calibration.json`.
The first status fixture omitted the required stage label and failed with
verifier TypeErrors; it was corrected to the exact stage interface before the
retained successful calibration. No historical implementation or compatibility
assertion was changed to obtain a pass. The first system-Python check lacked
pytest; dependencies were installed only in an owned session venv.

Run package integration/legacy compatibility checks with:

```bash
python -m pytest tests/projects/michael_bench/test_historical_import.py tests/projects/michael_bench/test_manifests.py tests/projects/michael_bench/test_task_packages.py -q
```

The package tests rerun trusted calibration and compare retained denominators,
as well as reject contaminated exports. These are `integration` / `cloud-linux`
checks. MB-005 owns the public CLI smoke; no general runner/controller/report
API is added here.

Retained calibration counts (passed/total test cases):

| Task | Baseline preservation | Baseline regression | Reference full |
| --- | --- | --- | --- |
| grouping | 4/4 | 0/2 | 6/6 |
| status | 32/32 | 0/8 | 40/40 |
| validator | 15/15 | 7/10 | 25/25 |

No phase has skipped tests or evaluator errors. The 124 selected package/import/
contract checks and artifact/dependency validators passed. The dependency
validator initially lacked installed distribution metadata and flagged the new
namespace import; the test now follows the existing direct-import-root pattern,
and root-manifest dependencies were restored only in the owned session venv.
No shared dependency configuration or live code was changed.

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
These integration checks run on `cloud-linux`; MB-005 CLI smoke is documented above.

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
