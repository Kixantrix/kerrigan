# MB-006b blocked native-access preflight

Cloud Linux, November 25, 2026; foundation `49684ff`.
**No transport proof or model benchmark is complete.**

## Observed blocker

The installed GitHub Copilot CLI reports `1.0.112`, also observed in the
native ACP `initialize` response's `agentInfo.version`.
A single non-inference ACP access probe successfully initialized the protocol,
then `session/new` returned error `-32603`, category `connection`:

```text
error sending request for url (https://api.enterprise.githubcopilot.com/meta): client error (Connect): dns error: error resolving DNS: failed to lookup address information: No address associated with hostname [ENOTFOUND]
```

This is an endpoint-resolution failure, not demonstrated authentication failure
or model unavailability. The process exited zero after termination; that does
not negate the native protocol error. No fallback endpoint, authentication
change, network change, or retry was attempted.

The probe sent only `initialize` and `session/new`, never `session/prompt`.
It used an empty session-owned workspace outside the checkout and a new,
session-owned `COPILOT_HOME` and cache. Existing native access was inherited
without inspecting or copying credential material. Automatic plugin discovery
and MCP tool caching were disabled for that process only. No personal/shared
configuration was changed. No fixture profile or broker was loaded.

Both authorized canaries remain blocked, with zero attempts:

| Requested canary | Observed model | Effective tool inventory | Usage/credits |
| --- | --- | --- | --- |
| `mai-code-2` | unknown; no model invocation | unknown; session creation failed | unknown; no inference |
| `claude-sonnet-5.5` | unknown; no model invocation | unknown; session creation failed | unknown; no inference |

Neither requested model was selected in the access-only probe.
CLI help advertises `--available-tools`, `--excluded-tools`,
`--disable-builtin-mcps`, and `--model`; official custom-agent documentation
describes `strict-tools-list: true` and `model-policy: required`.
These are documented requested controls, not effective inventory or
enforcement evidence. No broker-only boundary, native action identity,
native timeout/recovery, or no-replay proof is claimed.

## Persistent session-owned evidence

Root: `/root/.copilot/session-state/7cde2236da934302bbaa594be2b596e6/files`.
The reviewed receipt contains protocol metadata and the connection error,
not credentials, model responses, private tasks, or solution material.

| File relative to evidence root | SHA-256 |
| --- | --- |
| `native-preflight.py` | `0b1e635cedb5d254358a198f638343bf21ebb9cf24b5d2f7cf4dc8d6011000ad` |
| `native-preflight/receipt.json` | `f107bfce3681f4bc69eb50e81edb31c8ed698b705ee56747f202f2854d439f27` |

Exact probe invocation:

```bash
python /root/.copilot/session-state/7cde2236da934302bbaa594be2b596e6/files/native-preflight.py
```

Owned CLI argv recorded by the probe:

```text
copilot --acp --no-auto-update --disable-builtin-mcps --available-tools=mb-broker-action --no-ask-user --sync-session=off --log-level=none --log-dir /root/.copilot/session-state/7cde2236da934302bbaa594be2b596e6/files/native-preflight/logs
```

The nonexistent broker name was only a requested filter for access discovery;
its acceptance is not evidence that tool filtering worked.
The probe bounded captured stdout/stderr to 65,536 bytes and waited at most
30 seconds, followed by at most five seconds each for owned process-group
TERM/KILL cleanup. It captured 6,835 bytes and completed in approximately
4.48 wall-clock seconds. These are preflight limits and wall time, not
monotonic trial phases or the required 180+15-second canary proof.
The owned CLI process group was terminated and reaped. No sandbox was created.

Docker `29.1.3` was already available. Its image cache was initially empty.
The existing MB-002 synthetic image was restored by immutable digest:

```bash
docker --config /root/.copilot/session-state/7cde2236da934302bbaa594be2b596e6/files/docker-config pull python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b
docker ps -a --filter label=michael-proof --format '{{.ID}} {{.Names}}'
```

The pull succeeded; the container query was empty. No container, network, or
service was created or started. The image cache and existing daemon were left
intact. This is prerequisite availability, not actual sandbox execution proof.

## Exact checks and remaining work

Bare host Python initially lacked `pytest` and `PyYAML`; dependency validation
also failed because declared distributions were not installed. Restoring the
existing root manifest into a session-owned virtual environment required no
manifest or shared environment changes:

```bash
python -m venv /root/.copilot/session-state/7cde2236da934302bbaa594be2b596e6/files/validation-venv
/root/.copilot/session-state/7cde2236da934302bbaa594be2b596e6/files/validation-venv/bin/python -m pip install --quiet -r requirements.txt
```

For the following commands, `python` denotes that virtual environment's
`bin/python`:

```bash
python -m pytest tests/projects/michael_bench/test_historical_import.py tests/projects/michael_bench/test_manifests.py -q
python -m tools.validators.check_artifacts
python -m tools.validators.check_python_deps
git diff --check
```

The unchanged foundation contracts passed **109 tests**. Artifact validation
passed; dependency validation passed with 55 test files scanned. Whitespace
validation passed. No tests were skipped.

`test_native_transport.py` was not created or executed. Fake transport,
actual sandbox boundary tests, native canaries, cancellation/controller-loss
recovery, bounded native tool logs, and effective inventory/model identity
remain **blocked and unproven**, not passed or silently skipped.
Existing benchmark modules and MB-005 work remain unchanged.

Before implementation resumes, authorized native session creation must work
from an isolated session-owned workspace, without credential, shared-config,
or network workarounds. A resumed slice must still prove fake/sandbox
boundaries before any model prompt; this preflight authorizes no canary.
