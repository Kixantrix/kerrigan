# Executed MB-002 evidence

Cloud Linux, November 25, 2026; foundation `8bbbacf`.
Inspect AI `0.3.292`, Docker `29.1.3`, Compose `v2.40.3`.
Compose binary SHA-256:
`dba9d98e1ba5bfe11d88c99b9bd32fc4a0624a30fafe68eea34d61a3e42fd372`.
The image digest is frozen in `compose.yaml`.

Artifact root on this execution host:
`/root/.copilot/session-state/b873bebab21d4bd286788cca9537d60d/files`.
Full synthetic bundles, raw engine JSON, source-attributed event exports,
verifier errors, and cleanup receipts remain there, not private pilot data.

## Exact validation

Prefix proof/test commands with:
`DOCKER_CONFIG="$PWD/benchmarks/michael/engine_proof/.docker"`.
Python below is `benchmarks/michael/engine_proof/.venv/bin/python`.

```bash
python -m pytest tests/projects/michael_bench/test_historical_import.py tests/projects/michael_bench/test_manifests.py tests/projects/michael_bench/test_engine_proof.py -q --basetemp=/root/.copilot/session-state/b873bebab21d4bd286788cca9537d60d/files/mb002-final
python -m pytest tests/projects/michael_bench/test_engine_proof.py::test_killed_controller_recovers_ungraded_without_replaying -q --basetemp=/root/.copilot/session-state/b873bebab21d4bd286788cca9537d60d/files/mb002-recovery-final
python -m tools.validators.check_artifacts
python -m tools.validators.check_python_deps
python -m pip check
git diff --check
```

The full run retained **115 passing cases** (109 existing contract checks and
six sandbox fixtures). Its strengthened interruption probe failed because
Docker `top -eo args` requires a PID column. After changing only that test
probe to `-eo pid,args`, the exact interrupted-controller test passed in 7.79s,
including observing the running worker, killing its controller, recovery,
cleanup, and idempotent recovery. No sandbox cases were skipped.
An earlier full run passed all 116 before that probe was strengthened.
Artifact, dependency (53 test files), package consistency, and whitespace
checks passed after restoring existing root validation dependencies in the
isolated virtual environment. The bare host Python lacked PyYAML; it was not
used to substitute for sandbox execution.

## Measured final fixture phases

Seconds, one controller monotonic clock per attempt. End-to-end includes
Inspect teardown and cleanup, so these rows are not sums of the named phases.

| Fixture | Verdict | Setup | Agent work | Verification | End-to-end |
|---|---|---:|---:|---:|---:|
| success | passed | 3.2399 | 0.5705 | 0.4026 | 14.5197 |
| negative | failed | 3.4065 | 0.5635 | 0.4168 | 14.7018 |
| runtime error | ungraded | 3.2531 | 0.5470 | unknown | 14.1284 |
| timeout | ungraded | 3.4155 | 1.5898 | unknown | 15.3407 |
| cancellation | ungraded | 3.0362 | 0.5624 | unknown | 13.9020 |
| evaluator error | ungraded | 3.0701 | 0.5774 | 0.3792 | 14.3313 |
| interruption, corrected probe | ungraded | 3.7113 | unknown | unknown | unknown |

Only the successful row has time-to-verified-completion. Timeout's one-second
per-tool safety cutoff is not that metric. Queue and separate provisioning are
unknown in every row. These numbers assess transport, not model performance.

Raw JSON SHA-256s (six fixtures in `mb002-final`, corrected interruption in
`mb002-recovery-final`; filenames are in each fixture's `raw/` directory):

| Fixture | Raw SHA-256 |
|---|---|
| success | `c0a7bd1f7a623444bdecf5fb6a68780ce0cb0795036fefc494f91d0b6f5de3c8` |
| negative | `70c2c920655380b0ffc5a9ab0230db189ff8e3f005508a04a3dea151db73fa9d` |
| runtime error | `b08241d7cfbb71be595e9dc3e82b75aee54a347e58022e6d16c12585b3b86183` |
| timeout | `05208bc5fba0517562f440519dd0ef55a1fad8451e2e81fca90a907e2e70bad6` |
| cancellation | `dd74711521e86fda54d3da783845c7b8a1d6af546f628fd69d2dab5db410f9d2` |
| evaluator error | `426bf097bc1aaa705eec3883b5757db2c30df0712bba3ef949a526d8ac2ebe05` |
| interruption | `c8b96fbd4e138f6c77ee75e8c84f5fb6c05b316262a0ad277df4a80b6b2c20ee` |

Every normal fixture's cleanup receipt has no remaining owned containers.
Recovery removed its one owned container. Final Docker queries found no
`michael-proof` containers or Compose project networks. No shared images or
daemon were removed; the pinned image cache and ignored workspace dependencies
remain intentionally. No real inference, live API, scored session, historical
calibration, or public CLI smoke was executed.
