# MB-006c: local MXC proof, native canaries still gated

## Round-three local-inference preparation

`local-inventory.json` freezes the setup session's metadata-only handoff.
Installed bytes are not RAM estimates; fresh manifest hashes and matching file
sizes do not certify fresh tensor integrity. The selected Inkling model remains
provisional, and no local-model inference has run in this condition.

`local_inference.mjs` and `local_window.mjs` are offline-tested OpenAI-compatible
adapter components. The native owner now routes their sole tool through the
same proven CLI inventory and MXC action broker; `local_trial.py` prefreeses
task/policy/runtime/condition, starts ledger slots, collects exact artifacts,
and refuses Docker grading without a matching post-window release receipt.
A real HTTP synthetic test exercises actual native gate/actions/cleanup, not
an operational local-model benchmark. Do not use them
against the operational endpoint until the parent approves and announces the
exact interval and namespace and the setup session acknowledges it.

The frozen window permits at most three hours, sequential requests, unchanged
native settings/cache policy, and 15 seconds of cleanup reserve. Readiness uses
only `/health` and `/v1/models`; fresh per-task session IDs and exact
request/response IDs provide correlation,
not authenticated exclusivity. Mixed-content snapshot/flight endpoints are not
read. Non-idle boundaries or ambiguous identity stop admission; closing our
HTTP connection is not proof that the backend drained. A failed request or
ambiguous native usage closes further admissions in that window; it is not
silently retried. Release must separately
observe health idle, otherwise ownership cleanup remains unproven.

Input JSON is capped at 64 KiB for conservative headroom. This is a stricter
condition limit and a byte heuristic, not an exact rendered-token certificate:
MTPLX's Anthropic count route differs from native chat canonicalization.
Generated tools cannot execute without known native input/output/total usage
within 229,376 / 16,384 / 262,144 tokens. Missing final usage also prevents
certifying completion; unknown usage remains unknown in the receipt.

Local timing and energy are **shared with background workloads**. Metadata-only
process-name/CPU/RSS, load and memory-pressure snapshots do not authorize
altering Gridiron. Pressure is read from the
unprivileged `kern.memorystatus_vm_pressure_level` dispatch flags (normal=1,
warning=2, critical=4); the free-percentage heuristic alone is not a pressure
certificate. Stable warning is conditionally admissible when explicitly frozen
with `allowWarning`; it is labeled contended/non-isolated. A fresh three-sample
pressure/swap/health baseline precedes real requests. Critical or unknown
pressure, increasing baseline swap, sustained boundary swap growth, endpoint
contention and server errors stop admission. A normal observation is labeled
no known background workload, not exclusive hardware. End-to-end HTTP token rate uses a monotonic clock and includes
prefill. Optional own-response `mtplx_stats` supplies native uncached prefill and
decode rates/times; missing fields remain unknown. Derived `timings` defaults
are not used as measurement evidence. Reasoning is included in completion
tokens and decode rates; native TTFT may be the first thought, not answer.
Peak model memory and energy remain unknown unless actually measured.
No containers, VMs or builds are permitted during the window. Exact artifacts
must be collected first; Docker grading waits until release, and reported
completion excludes the post-window verification queue.

Round-three sandbox scratch is monitored at tool boundaries and on a 100 ms
timer, with a 1 MiB / 128-entry threshold. This is **not a filesystem hard
quota**: transient overshoot is possible before observation and cutoff.
Descriptor-bound scans reject aliases without following candidate-controlled
links; disposal occurs only after native handles are reaped. The 32 KiB
write limit applies to broker operations, not a kernel-enforced temporary-file
size limit. These restrictions remain a disclosed difference from an
unrestricted stock CLI.

The first round-three source epoch had a misleading hardcoded `self_test.py`
tool description even for tasks whose writable self-test is `self_test.mjs`.
Sonnet's first orchestration-v5 attempt was stopped at that nonexistent path,
remained ungraded, and was independently attributed to the harness. The
corrected epoch derives its description and runnable paths from the actual
policy without widening any allowlist. The faulted slot and five preceding
verified passes are retained; its replacement uses a new disclosed slot.
`mbr3-tooltip-verification.json` binds the native regression checks, fresh
calibration and immutable primary-selection plan. Matrix regeneration with
`--source-epoch-plan <owned>/mbr3-tooltip-v2/primary-plan.json` requires every
selected attempt to be complete, validates the excluded harness attribution,
and labels the two source epochs separately instead of silently pooling them.

The next source epoch returns bounded, action-charged `not_found` feedback for
reads/runs of nonexistent relative task paths. A metadata-only descriptor walk
rejects traversal and aliases without reading file contents. Existing files
outside the allowlist and paths outside the task root still cut off. This
corrects a policy cutoff after MAI invented `briefs/T012-L2-session.md`; the
actual manifest names `briefs/L2-orchestration.md`. Preserve the invented-path
behavior and original harness-policy cutoff, disclose its fresh replacement,
and report both old-policy and CLI-parity counts. No replacement has run yet.

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

## MB-006d: integrated boundary, failed canaries

`runner.py` exports fresh outside-history tasks; the independently running
`owner.mjs` alone holds live MXC CLI/task handles. Only `mb_action` exists in the
actual SDK inventory. Its fixed `worker.py` performs **all** reads/writes inside
MXC, rejects symlinks, and execs candidate Python in the same no-fork process.
Limits are 8 unique actions, 8,192 input bytes/action, 32,768 aggregate action
bytes, 65,536 retained bytes/channel and 512 native frames/events. Starts precede
execution. EOF after actual controller death, cancellation and deadline all
kill live owned handles; warnings/missing acknowledgements cannot prove cleanup.
Recovery only reads protected receipts: no PID signals, replay or model launch.

The integrated proof is in [verification.json](verification.json) and
[integrated evidence](integrated-evidence.tar.gz). Actual fork/detached spawn,
credential/keychain, network, TTY and securityd denials passed; broker duplicate,
symlink and output-limit cases passed. Controller **SIGKILL**, attempted task
`setsid`, external cancellation and deadline left CLI/task handles reaped with
no warnings. Human local-platform attestation remains pending.

| One controller canary per pin | Active / cleanup | Observed native starts (lower bound) | Result |
| --- | --- | --- | --- |
| `mai-code-2` | 5.824s / 0.105s | 2 | Native TLS failed; stream cap stopped CLI; no action |
| `claude-sonnet-5.5` | 6.362s / 0.088s | 3 | Native TLS failed; stream cap stopped CLI; no action |

Native call-start events name the requested pins, but backend execution identity
and usage/cost remain **unknown**. The first failure was
`native trust store read was incomplete and provided no usable roots`.
CLI-internal streaming retries occurred despite zero controller retries: this
violated the intended no-retry condition and is preserved, not relabeled success.
The revised owner stops on the first native failure/retry event or model mismatch;
that correction has no fresh canary validation because both slots are spent.

Offline-only evaluation of the documented `SSL_CERT_FILE`/`NODE_EXTRA_CA_CERTS`
settings with the public OS PEM and a SHA-pinned Mozilla PEM still failed native
HTTPS with `bad certificate format`. No Keychain item, private auth state,
shared setting or system trust configuration was read/copied/changed.
The explicit PEM is **not a proven workaround**. Model preparation now also
requires a positive bound `transportReady` receipt; none existed at MB-006d
closure. The MB-006e receipt below does not restore either spent slot.
The remaining decision is in [MB-006d-block.yaml](MB-006d-block.yaml).

Native byte-exact captures remain private in owned state. Published projections
omit native system/instruction text and HTTP bodies/headers; hashes, counts,
monotonic times, actual inventory/policy and all observed model starts/failures/
retries are retained. Original partial/negative receipts remain historical.
No scored tasks, substitution, further canary or GitHub PR/merge ran.

> **MB-006e, non-inference:** native HTTPS works with the pinned public PEM and
> the smallest tested trusted-CLI IPC grant: `com.apple.SecurityServer`,
> `com.apple.trustd`, `com.apple.trustd.agent`. No-fork, `securityd`/Keychain-file
> denials and the separate task profile remain intact. See `tls-diagnosis.json`
> and `tls-evidence.tar.gz` for source/config-bound controls and current native
> verification. Unknown/malformed/proxy/failure responses cannot establish
> readiness; every future invocation must also verify HTTPS in its own live
> confined session before sending a prompt. Both old slots remain spent.
> No additional inference, model identity proof or platform attestation is claimed.

### MB-006f: corrected-condition attempts, not completed readiness

The human separately authorized local-executor attestation and exactly two new
controller prompts. `mb006f-authorization.json` freezes the source/approval hash
and one slot per selected pin in the owned `mb006f/slots` namespace; old slots
are untouched. Modified/stale approvals and reused slots fail closed. The
authorized local executor (not a human observer) attests the exact preserved
macOS evidence plus fresh source-bound native HTTPS, task denial and owned
controller-loss/deadline proofs in `mb006f-attestation.json` and
`mb006f-safety.tar.gz`.

Both actual sessions passed strict effective SDK sandbox/single-tool inventory
and verified native HTTPS before their one prompt. MAI then Sonnet each emitted
one observed native start, but reached the unchanged 65,536-byte CLI stdout cap
before any `mb_action` executed. Active/cleanup seconds were 3.863/0.055 and
2.820/0.048 respectively; both owned exits were proved before proceeding.
`mb006f-outcomes.json`, `mb006f-canaries.tar.gz` and `mb006f-audit.json` preserve
all observed starts, safe stream-shape counts and source/config/runtime/CA
bindings. Native system/instruction text, raw streams and credential state are
not published.

Both new slots are spent, with no controller retry or substitution. No native
retry event was observed; events beyond the overflow cutoff are unknown.
Observed streaming output is not independent backend identity or completed
task verification. Usage/cost remain unknown, and all results are ungraded.
The next capability gap is a separately reviewed bounded native event-stream
configuration that can complete the tool loop without relaxing containment or
quietly enlarging this budget. Any additional prompts or scoring need new
authorization; none are enabled by this receipt.

### MB-006g: offline-only, separate protocol condition

The schema-bound choice is to preserve all pushed events: supported
`SessionOpenEventOptions.streaming` controls deltas, while event-log `types`
filters pull/history reads, not the existing push channel. No guessed
subscription filter or event suppression is used.

`protocol.mjs` now separates native framing from candidate output: at most
1,024 header bytes, 131,072 body bytes/frame, 2,097,152 total native stdout
bytes and 512 delivered frames. The frame bound accommodates the observed
34,282-byte native system message and the labeled 90,000-byte synthetic case;
the aggregate permits sixteen maximum frames, not an unbounded tool loop.
Task stdout/stderr remain 65,536 bytes/channel, eight actions, 8,192 bytes/action
and 32,768 aggregate action input. CLI stderr and sent input also retain their
old 65,536-byte bounds. This is a new condition, not MB-006f compatibility.

Framing copies at most one body plus a 1,024-byte header, independently of
chunk coalescing; retained decoded messages are bounded by the aggregate wire
budget and event count. This bounds protocol-owned state, not OS process RSS.
Action buffers remain separately bounded. All owner-written raw streams,
action/ownership receipts and terminal metadata share a 16,777,216-byte disk
budget. Malformed/truncated/oversized frames or aggregate/event/disk overflow
stop the owner; explicit unparsed-byte lower bounds prevent cutoff tails from
being represented as clean completion. No lifecycle/model/error/retry/usage/
permission/tool event is filtered. First failure halts the same chunk before
later retry/tool callbacks can run.

`mb006g-verification.json`, `mb006g-offline.tar.gz` and
`mb006g-safety.tar.gz` preserve source/schema/hash/count bindings. Private
MB-006d/f byte streams were replayed without inference. Labeled synthetic
CLI/task handles exercised the actual owner/parser/broker write/run/result/
idle path, fragmentation, duplicate actions, failure/retry cutoff, side-channel
denial and unchanged task-output cutoff; they do not prove native task execution.
Fresh native non-inference HTTPS, task denials and controller-loss/deadline
cleanup passed. All four historical slots and old archives remain unchanged,
and MB-006f's source-bound authorization is stale. No new prompt, slot or
ready-to-infer authorization was emitted. A live model tool loop under this
new condition remains unvalidated and requires separate authorization.

### MB-006h: native Sonnet tool loop observed; MAI still bounded out

After direct human approval, MB-006h froze one new controller prompt per pin,
MAI then Sonnet, under unchanged MB-006g protocol limits and unchanged task/
action limits. The final-source local-executor attestation, fresh native
HTTPS/denial/cutoff proof and exact allowance are in `mb006h-attestation.json`,
`mb006h-safety.tar.gz` and `mb006h-authorization.json`. These do not modify any
of the four earlier spent slots.

MAI stopped on its first native `model.call_failure`: **"Native model HTTP
response exceeds the 65536-byte limit"**. This is the separately configured
native HTTP response bound (`COPILOT_LLM_RESPONSE_MAX_BYTES=65536`), not the
new 2 MiB protocol budget. No task action ran. Active/cleanup seconds were
3.746/0.073. Private offline inspection of all received bytes retained the
additional `model.model_call_failure` in the cutoff tail, with no second start
or retry event observed. Events never received after cutoff remain unknown.

Sonnet completed actual `mb_action` write/run/result/idle, with native MXC task
stdout `5\n`, in 4.357 active/0.041 cleanup seconds. Its three native starts
were natural calls within one controller prompt, not replacement prompts or
observed retries. Native usage reports `model=claude-sonnet-5.5` and
`responseModel=claude-sonnet-5-5`, 18,808 input and 184 output tokens across
the three calls, with retry/attempt indices zero. Reported native cost counters
are preserved without inventing monetary units; independent backend identity
and fiat cost are not established.

`mb006h-outcomes.json`, `mb006h-audit.json` and `mb006h-canaries.tar.gz`
contain safe source/config/runtime/CA-bound projections. Account-wide quota
snapshots, hidden native instructions, raw streams and auth state are excluded.
Both owned exits were proved before proceeding; all six slots are now spent.
This establishes one controlled Sonnet readiness loop, not a scored historical
task or a comparative result. MAI readiness remains blocked by its native HTTP
bound. No post-start tuning, retry, extra prompt or scoring was performed.

### MB-006i: offline proposed cross-layer budget, not inference readiness

`budgets.json` now supplies the process-local model-response setting and native
protocol budgets; `proof.py` and that file are included in execution source
hashes. No allowance was added. Both frozen f/h approvals are source-stale.
All six spent slots and h's genuine Sonnet readiness / MAI harness cutoff are
preserved. These are **proposed limits**, not a new authorized live condition.

| Layer | Finite limit | Accounting / rationale |
|---|---:|---|
| Native model HTTP response | 128 KiB | `COPILOT_LLM_RESPONSE_MAX_BYTES`, isolated child environment only |
| Native frame header / JSON body | 1 KiB / 8 MiB | Nine 128 KiB responses in one cumulative snapshot, 6x JSON escaping plus 128 KiB metadata |
| Native received protocol | 96 MiB | Nine snapshots (sum 1..9), six other copies/response, 6x escaping plus 8 MiB control headroom |
| Native frames/events | 16,384 | Nine calls with 128-byte mean deltas, 64 metadata events/call plus 512 setup events; smaller deltas may intentionally hit the cap |
| Native sent frame / total | 1 MiB / 16 MiB | Eight max-sized tool results plus setup; separate from candidate input |
| Task input / total / actions | 8 KiB / 32 KiB / 8 | Unchanged; reasoning and native controls cannot consume or expand this allowance |
| Task stdout/stderr, CLI stderr | 64 KiB/channel | Unchanged; max tool-result JSON/base64/escaping fits the separately bounded sent frame |
| Owner evidence disk | 1 GiB | At least 7x received+sent wire bounds plus 16 MiB task/config/record headroom, including terminal serialization |

This envelope admits nine natural model calls (eight actions plus final turn),
not arbitrary full-context output or an assertion that the CLI emits at most
six copies. Oversized snapshots, more copies, finer streaming or unexpected
metadata still fail closed; lifecycle/failure/retry/model/usage/tool/permission
events remain unfiltered. The envelope is tested with a labeled synthetic SDK
through the unchanged owner/broker algorithm: nine large escaped streams and
cumulative snapshots, usage/starts, full task output, and first-failure cutoff.
It does not replay inference or establish native model-response parsing.
Parsed retention is bounded by wire bytes and event count, with at most one
8 MiB frame plus header in the parser; this is **not an OS RSS guarantee**.

Supported-semantics boundary: the preserved h native failure establishes that
the process-local setting enforces a native HTTP-response byte ceiling, not
candidate output or RPC aggregate traffic. Installed `copilot-rpc.ts` documents
`gitHubFetch.bodyLimitBytes` separately and push event options expose streaming,
not filtering. It does not expose the model-response environment parser or
whether that counter applies before/after content decoding. Static inspection
of the pinned opaque executable found neither UTF-8 nor UTF-16 literals; an
embedded apparent Zstandard marker was not a valid complete frame. No guessed
defaults, decoding semantics, new variables, filtering or TLS changes are
claimed. Exact native counting/acceptance of the proposed response ceiling and
end-to-end MAI readiness remain **unvalidated**; a separately authorized native
check would be required. No live request, prompt, slot or scoring is authorized
by this offline correction.
