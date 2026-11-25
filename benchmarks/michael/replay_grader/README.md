# Offline validator replay grader (MB-006j)

`api.grade(source_bytes, new_receipt_directory, seconds=10)` grades only the
existing validator package. `policy.py` maps all original 15 preservation and
10 regression node IDs to their original assertion clauses. Package/reference/
original-test hashes are checked against the unchanged frozen manifest.
Tests additionally run the original **trusted** assertions against observation
proxies, never against a candidate import on the host.

The trusted controller sends source plus answer-free behavioral inputs/adapter
over bounded stdin to a fresh Docker container: no network, host mounts, history,
credentials, Docker socket, expectations, reference, or assertion code.
The image root is read-only, UID/GID 65534, capabilities dropped, no-new-privileges,
128 MiB memory/swap combined, one CPU, 32 PIDs, 16 MiB scratch tmpfs, 1 MiB file
limit and 64 FDs. Source is <=256 KiB; exactly 25 observations, <=8 KiB per frame
and <=128 KiB combined stdout/stderr. Docker logging is disabled. Execution
(including stdin staging) has a finite <=30s wall deadline; every Docker control
operation has a 15s deadline. Only owned CLI children are killed/reaped.

An independent host process owns the entire Docker lifecycle. Durable start and
owner registration precede `docker create`; an absolute monotonic deadline is
persisted before `start`. Only the controller holds the liveness pipe's writer.
The owner watches its reader while bounding execution, so controller SIGKILL
triggers cleanup and controller SIGSTOP cannot suspend the deadline. Creation
is allowed to finish registering before responding to controller loss; it
cannot execute code, and only the already-registered owner may subsequently
start it. Candidate code has no access to the owner, pipe, receipts or Docker.
The controller accepts results only after owner exit and a hash-bound durable
terminal receipt. Owner/proof loss is ungraded with cleanup unknown; recovery
can remove labeled sandboxes but cannot assert missing owner quiescence.
Docker/host/owner availability remains trusted infrastructure; this is not
crash resilience against simultaneous owner/daemon/host failure.

On Linux, registration retains the exact `/proc/self/stat` start-ticks identity.
On macOS, `process_start_ticks` is null and identity explicitly unknown; current
PID/platform are observational metadata, never a recovered process handle.
No saved-PID signaling or substitute `ps` identity is introduced. Prior Linux
receipts/source snapshots remain archived unchanged.

Only after container exit does the host validate observations and apply hidden
clauses. Malformed/duplicate/missing/truncated/overflow data, nonzero exit, OOM,
timeout and evaluator errors are ungraded, not ordinary assertion failures.
Each report includes clause diagnostics, every denominator, input/package/policy/
image/archive/observation bindings, separate same-host monotonic phase intervals,
and label-owned cleanup proof. Unreached phases are null, not invented durations.
`api.recover(receipt_directory)` only removes containers with that persisted
128-bit ownership label; it never restarts execution or guesses/signals a PID.
Protect trusted receipt directories from other host users; Docker/kernel and
the preprovisioned image are trusted infrastructure, not proven secure here.

## Reproduce

From the repository root, preprovision **before** offline grading:

```bash
python -m venv /tmp/mb006j-venv
/tmp/mb006j-venv/bin/pip install -r benchmarks/michael/tasks/dependencies/requirements.txt
docker pull python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b
docker build --pull=false -t michael-replay-grader:mb006j benchmarks/michael/replay_grader
PATH=/tmp/mb006j-venv/bin:$PATH bash benchmarks/michael/replay_grader/scripts/smoke.sh /tmp/mb006j-smoke-one
PATH=/tmp/mb006j-venv/bin:$PATH bash benchmarks/michael/replay_grader/scripts/smoke.sh /tmp/mb006j-smoke-two
```

In shallow checkouts, fetch the exact base/reference commits listed in the
unchanged validator manifest beforehand. Smoke never provisions dependencies
or pulls an image. Receipt directories must be new. Candidate image dependencies
are Python 3.12 from the pinned base and PyYAML 6.0.2; immutable image IDs bind
their exact installed bytes. Host tests use the package's complete pinned list.
`verification.json` and `evidence.tar.gz` retain the current commands and receipts.
`superseded-1d94a73.*` preserve the earlier evidence, which lacked independent
controller-loss containment and must not be used to claim that guarantee.

Passing these finite held-out observations is not proof of general correctness,
non-hardcoding, contamination-free evaluation, model performance, laptop speed/
power, or end-to-end task completion. Public historical solutions may be known.
No inference or live service is used; earlier canary allowances are untouched.
