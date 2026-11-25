# MB-006b native transport verification

The original access-only record below is retained historically. The resumed
offline implementation and current native gates are recorded in the final section.

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

## Resumed independent implementation

Foundation `0dbd56d` integrates MB-005 through `a41376d` and the revised briefing.
Offline stoppage is resolved; the original native access failure remains open.
Existing benchmark modules are read-only and unchanged by this implementation.

`broker.py` implements one stdio MCP tool, `action`, with durable unique action
IDs, no replay, exact read/write allowlists, input/action/output budgets, and
actual Docker execution as UID 65534. The pinned image has no host mounts,
network `none`, read-only root, dropped capabilities, no-new-privileges,
256 MiB memory/swap, one CPU, 64 PIDs, bounded tmpfs, and no Docker log driver.
Model source can edit only the existing `solution.py` in the root-owned work
directory; requirements cannot be rewritten. Host paths and network operations
are not broker operations.

`supervisor.py` persists/fsyncs start before subprocess execution. An independent
Linux child-subreaper owns cancellation, controller-pipe loss, bounded stream
capture, monotonic deadline checks, PID-fd-bound descendant termination
(including detached children), sandbox removal, and durable ungraded terminal.
Recovery never launches a tool or model. `native.py` creates fixture-only
required-model profiles and requested filters/config hashes outside history.
It does not attest effective native inventory. Native launches remain gated;
no caller-supplied fake inventory can authorize them.

Public diagnosis (unauthenticated; no shared setting changes):

```bash
getent ahosts api.enterprise.githubcopilot.com
getent ahosts api.githubcopilot.com
curl -q --max-time 15 --silent --show-error --output /dev/null --write-out 'enterprise_meta http=%{http_code} remote=%{remote_ip}\n' https://api.enterprise.githubcopilot.com/meta
curl -q --max-time 15 --silent --show-error --output /dev/null --write-out 'copilot_ping http=%{http_code} remote=%{remote_ip}\n' https://api.githubcopilot.com/_ping
curl -q --max-time 15 --silent --show-error --output /dev/null --write-out 'proxy_ping http=%{http_code} remote=%{remote_ip}\n' https://copilot-proxy.githubusercontent.com/_ping
curl -q --max-time 15 --silent --show-error 'https://dns.google/resolve?name=api.enterprise.githubcopilot.com&type=A'
```

Enterprise resolution still fails; regular API resolution succeeds, and both
pings return HTTP 200 (curl reports peer `127.0.0.1`). Public DNS lookup service
resolution also fails, so no independent authoritative DNS result is claimed.
The official allowlist includes `*.enterprise.githubcopilot.com`: the observed
endpoint is covered, not demonstrated wrong. Reachable pings do not establish
reachability of the selected authorized account route. No supported correction
or changed enterprise reachability was found; no ACP recheck or inference ran.
References: [network diagnosis](https://docs.github.com/en/copilot/how-tos/troubleshoot-copilot/troubleshoot-network-errors)
and [allowlist](https://docs.github.com/en/copilot/reference/copilot-allowlist-reference).

Exact final command uses the session-owned validation environment above:

```bash
python -m pytest tests/projects/michael_bench/test_historical_import.py tests/projects/michael_bench/test_manifests.py tests/projects/michael_bench/test_native_transport.py -q --basetemp=/root/.copilot/session-state/7cde2236da934302bbaa594be2b596e6/files/native-tests-verified
python -m tools.validators.check_artifacts
python -m tools.validators.check_python_deps
git diff --check
docker ps -a --filter label=mb-native --format '{{.ID}} {{.Names}}'
```

Final checks passed: **128 tests**, no skips; both validators and whitespace
checks passed; no owned sandbox remains. This includes supervised fake MCP
read/edit/execute, actual write/network denial, both output channels' overflow,
external cancellation, killed controller plus detached-child cleanup, no
replay, and requested-model fixture/gating checks. The initial run found a
test probe incorrectly treating denied container `/root` access as failure;
the corrected probe requires denial and the complete suite passes.
Receipts under `native-tests-verified/` remain session-owned, synthetic-only.
Both native models still have **zero attempts**, unknown observed identity,
unknown effective native inventory, and unknown native usage. These checks
establish offline transport capability, not model capability or rankings.

## Supervisor-loss recovery correction

Follow-up on `7b35c5f`, November 25 at 05:18 UTC. The new real-process fixture
reproduced a gap: killing the supervisor itself left a detached client alive,
but recovery previously published a stopped terminal after Docker cleanup.
The pre-fix regression failed as expected and its receipt remains under
`supervisor-loss-before/`; the original native DNS evidence is unchanged.

Recovery now removes only known owned Docker resources, persists
`recovery.json` with `state: quiescence_unproven`, and raises explicitly.
It retains the original start and does **not** synthesize `terminal.json`,
signal a recorded PID, or replay any tool/model. Repeated recovery preserves
the first partial receipt. A present recorded PID also establishes neither
ownership nor quiescence, so recovery refuses rather than guessing.
Previously synthesized terminals lacking durable process/sandbox cleanup
proof are rejected too; the original evidence is not deleted or rewritten.

The regression uses a separate fixture-only subreaper controller. It verifies
the watcher/driver/child parent chain and process birth identities before
opening PID-fds, kills only the bound owned watcher, observes the detached
child still alive, and requires both recovery calls to refuse completion.
The fixture harness subsequently terminates/reaps its owned processes; this
is test cleanup, not a claim that production recovery proved quiescence.

Exact final invocation uses the same session-owned validation Python:

```bash
python -m pytest tests/projects/michael_bench/test_historical_import.py tests/projects/michael_bench/test_manifests.py tests/projects/michael_bench/test_native_transport.py -q --basetemp=/root/.copilot/session-state/7cde2236da934302bbaa594be2b596e6/files/supervisor-loss-verified
python -m tools.validators.check_artifacts
python -m tools.validators.check_python_deps
git diff --check
docker ps -a --filter label=mb-native --format '{{.ID}} {{.Names}}'
```

**129 tests passed**, no skips; validators and whitespace checks passed;
the owned-container query was empty. Final evidence directory:
`supervisor-loss-final/test_supervisor_loss_retains_s0/evidence/` is the earlier
passed follow-up receipt (hashes below); the final strengthened run is retained
separately under `supervisor-loss-verified/`.
SHA-256 of `start.json`:
`c73843799848ba99c7edd246b0aca42a7667a24435f1ac91e413f32ceeabe75d`;
SHA-256 of `recovery.json`:
`b4c16df620cec2b1a3908c87737f561b88e0f84656cebbb700ca2d3d96ffb0f1`.
No network diagnosis, native access recheck, or canary was repeated.
