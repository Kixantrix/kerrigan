# MB-006c: local MXC proof, native canaries still gated

Foundation: `2df6f85`. Environment: `local-attested-macos`; results are dated
operator observations, not human-attested completion. This condition is **local
agent/tools with cloud inference**, not cloud-hosted tools or local inference.
No scored tasks or model prompts ran. Both shared canaries remain unused;
requested `mai-code-2` and `claude-sonnet-5.5` identity, usage and cost are unknown.

## Observed results

The session-owned official Copilot CLI reports **1.0.115**, including native ACP
`agentInfo.version`. [runtime.json](runtime.json) pins its official archive URL,
release SHA-256 and executable SHA-256. No executable was found on PATH or at
the three checked standard locations. No global installation/settings changed.

Native non-inference ACP `initialize` succeeded; `session/new` returned
**-32000, Authentication required**. No `session/prompt` was sent.
The parent completed the visible isolated-home OAuth web-flow. One bounded
post-login `initialize`/`session/new` recheck then succeeded in 2.312 active
seconds, advertising both requested models as enabled. This is native catalog
availability, not observed invocation identity or usage. The returned metadata
has no effective tool inventory. No further login or model prompt ran.
The entire authentication state is credential-bearing and excluded from
inspection and publication; no authorization URL, configuration or token was
collected.
Unauthenticated local HTTPS requests to both regular and enterprise `/meta`
reached HTTP 400. This proves endpoint reachability for those requests, not
Copilot authorization or successful authenticated API calls. It differs from
the earlier cloud host's DNS failure.

The official MXC **1.1.0** package supplied the standalone ARM64
`mxc-exec-mac`; the initial proof uses no Node SDK imports. The archive integrity and exact
native executable bytes are pinned in runtime.json. Initial acquisition used
an owned npm installation with scripts disabled; a subsequent `npm pack`
retained the identical integrity-pinned package. Only the standalone executor
is needed to reproduce the probes, not its Node dependency closure.

Actual `containment: seatbelt`, contract `1.0.0` synthetic execution:

| Probe | Actual observation |
| --- | --- |
| Task directory read/write | Allowed; synthetic round-trip succeeded |
| Synthetic credential-file read and denied directory write | EPERM (1), not missing-file failure |
| Outbound test address and known reachable owned loopback listener | EPERM (1), not timeout/refusal |
| `com.apple.securityd` Mach lookup | Bootstrap denial 1100; zero credential items queried |
| Unsupported per-CIDR egress policy | `policy_validation`, exit 1; harmless command never executed |

The `--debug` receipt includes the generated `(deny default)` profile,
filesystem grants/denials, absent general IP egress, `sandbox_init` application,
and separately appended per-run Mach cleanup rules. Requested config and raw
effective profile bytes are retained/hash-bound in the evidence bundle.
The xcrun Python shim emitted denied `/tmp` cache warnings; the probe still
completed and all required denial assertions passed. These warnings were not
silenced by broadening temporary-directory access.

**This is standalone MXC proof, not the CLI's effective policy/tool proof.**
Copilot's installed help confirms its in-process file tools are not OS-confined.
The access-only run requested `--sandbox`, no bypass, disabled built-in MCPs,
an intentionally nonexistent available-tool name, no user-question tool and
isolated policy. Acceptance of these flags is not an observed effective tool
inventory. No real agent, generated code or candidate grader was launched.
Managed safety policy is not disabled, replaced or shortened.

## Diagnostic cutoff and remaining gates

`proof.py` supports trusted synthetic/setup diagnostics only. Each invocation
creates/fsyncs an exclusive durable start before launch, rejects reuse, caps
input at 8,192 bytes and each output channel at 65,536 bytes, and records exact
Base64 prefixes plus observed byte lower bounds. No completion time or model
usage is fabricated. The external watcher observes controller-pipe loss and
host-wide monotonic deadlines (at most 180 seconds), with 15 seconds for direct
child cleanup. It signals only a live owned Popen child, never a saved/guessed
PID or process name. No action or model is replayed.

**Whole-process cleanup remains unproven.** Direct-child reaping cannot establish
that escaped descendants stopped. The detached-child negative test demonstrates
this gap rather than disguising it: a short-lived synthetic descendant can
finish after the direct-parent cutoff. Every receipt remains ungraded and
recoverable; recovery sends no PID signals and refuses a quiescence claim.
`capture(native=True)` is unconditionally rejected; diagnostic helpers must
not be exposed as evaluated tools or used to run generated code.

Before either single 180+15-second canary, complete:

1. Actual full effective native inventory showing no in-process file tools,
   other built-ins, remote MCPs, hooks, extensions, delegated agents or other
   unsandboxed execution channels; broker-only requested filters are insufficient.
2. An owned macOS mechanism that proves external cancellation/deadline cutoff
   and recovery for the CLI **and** escaped task descendants. Neither Linux
   PID-fd/subreaper code nor direct-parent reaping supplies this proof.
3. CLI-effective policy/profile hashes and denial receipts for the actual
   evaluated surface, retaining managed policy and denying bypass/credentials.

Authentication alone cannot open these gates. Existing benchmark APIs,
independent grading, historical packages and previous raw evidence are unchanged.
No general native runner or scored replay support is claimed.

## Reproduction and evidence

Owned root on this execution host:
`/Users/mvh/.copilot/session-state/a45ee9a4-394e-4af7-afba-d8f78ae19672/files/local-mxc`.
The safe [evidence bundle](evidence.tar.gz) contains only selected synthetic
receipts, requested settings/policies, setup/probe driver source and tested
source snapshots, never the CLI authentication state, credential files, logs
or browser authorization material. [receipt.json](receipt.json) binds its SHA-256,
source hashes and generated profile capture.

`run_offline.py` is the archived trusted scenario driver: create a new owned
answer-free fixture outside all repositories/history, use pinned executables,
run CLI help/version, validate MXC policy, assert actual harmless denials, then
reject an unsupported policy without executing its command. Expected: the table
above, no model prompts and an explicitly ungraded cleanup status. Another
operator must choose new owned paths and attest their local observations.

Exact final checks (Python denotes the owned `validation-venv/bin/python`,
CPython 3.12.12):

```bash
python -m pytest tests/projects/michael_bench/test_local_transport.py tests/projects/michael_bench/test_historical_import.py tests/projects/michael_bench/test_manifests.py -q --basetemp=/Users/mvh/.copilot/session-state/a45ee9a4-394e-4af7-afba-d8f78ae19672/files/local-mxc/verified-tests
python -m tools.validators.check_artifacts
python -m tools.validators.check_python_deps
git diff --check
```

Results: **124 passed**, zero skipped; both validators and whitespace passed.
No deployable native entry point exists, so the unchanged Linux/Docker smoke
and native canaries were not run; this slice is not a smoke/benchmark pass.
Python 3.9.6 initially lacked pytest and cannot import the dependency validator's
`packages_distributions`. Existing root dependencies and CPython 3.12.12 were
restored only in owned state; no root manifest changed.
The first Python 3.9 run also exposed its process-relative `time.monotonic`
epoch; its negative phase durations are **invalid timing evidence**, retained
historically in the bundle. The fix uses `clock_gettime(CLOCK_MONOTONIC)`;
cross-process positive durations and cutoff now have regression coverage.

## Continued supported-mechanism evaluation

The [addendum receipt](addendum.json) and [raw addendum](containment-addendum.tar.gz)
supersede the earlier unknown-tool observation, not the native execution gate:

| Mechanism | Actual result without inference |
| --- | --- |
| Official SDK `session.tools.initializeAndValidate` / `getCurrentMetadata` | Exactly one external `mb_action` stub; no built-in file, shell or delegation tools |
| Native invocation of removed `view` | `not_found`; only `mb_action` offered |
| SDK `permissions.sandbox` / `session.sandbox.getState` | Enabled; no bypass, task network or git/gh auth; credential/keychain paths denied |
| Preserved deny-default profile with `process-fork` denied | Actual `fork()` and `posix_spawn` both failed EPERM |
| External cancellation through a live MXC SDK native handle | Non-forking synthetic task stopped in 0.355s; no warnings; no saved-PID/name signals |
| CLI itself under outer MXC no-fork profile | Native session/tool/policy introspection succeeded; normal exit 0, no warnings |

Important corrections: `--sandbox` alone did **not** enable the SDK-created
session; its initial `getState` reported disabled. The documented per-session
`permissions.sandbox` request fixed this without changing settings.
The native API field does not expose `nestedPty`; the returned effective state,
not a requested setting, is authoritative.

MXC documents generic macOS cleanup as best-effort, including a five-second
scan limit. Its native SDK `kill()`/`wait()` retains an owned process handle;
the no-fork policy is a compatible way to eliminate detached descendants, not
a claim that scanning proves arbitrary-tree quiescence.
`profileOverride` ignores filesystem/network/UI profile generation: the
prototype therefore preserves the entire observed deny-default profile and
explicit credential denials. Outer CLI transport networking is distinct from
the denied task networking; normal CLI authorization state is accessible only
to the trusted transport, never the task.

These are **compatible supported mechanisms**, not an unsupported-MXC finding.
The external tool is still a stub, and the integrated bounded action broker,
whole CLI/task cancellation and crash recovery are not implemented/proven.
No canary or scored attempt ran. The original 40-implementation-turn cap has
been reached; [the scoped block](MB-006c-block.yaml) requests a bounded
continuation rather than silently exceeding it or calling this slice complete.
The conductor may file that block in canonical `.specify/blocks`; this executor
keeps repository writes inside the briefing's closed Touch scope.
