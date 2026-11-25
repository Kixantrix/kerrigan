# MB-002: Inspect offline compatibility proof

**Selected for this synthetic slice:** Inspect AI 0.3.292, its native
`mockllm` provider, solver/tool loop, Docker sandbox, scorer, and JSON logs.
Harbor was not installed or assessed. This is not a general runner or a scored
MAI Code 2 / Claude Sonnet 5.5 comparison.

## Reproduce in cloud Linux

Requires a working Docker daemon and Docker Compose. Do not use Inspect's
`local` sandbox or in-process agent bridge as a substitute.

```bash
python -m venv benchmarks/michael/engine_proof/.venv
benchmarks/michael/engine_proof/.venv/bin/pip install -r benchmarks/michael/engine_proof/requirements.txt
benchmarks/michael/engine_proof/.venv/bin/python benchmarks/michael/engine_proof/proof.py /tmp/mb002-unique-run
benchmarks/michael/engine_proof/.venv/bin/python -m pytest tests/projects/michael_bench/test_historical_import.py tests/projects/michael_bench/test_manifests.py tests/projects/michael_bench/test_engine_proof.py -q
```

The output directory must not already exist. Engine/sandbox installation may
need network access; evaluated code has none. The image is digest-pinned in
`compose.yaml`. This execution host needed a workspace-only Compose v2.40.3
plugin from the official Docker release (`docker-compose-linux-x86_64`),
stored in `.docker/cli-plugins/`; `DOCKER_CONFIG` pointed to that empty workspace
configuration rather than a user's Docker credentials. No daemon or privilege
configuration was changed. Existing root dependencies were restored in the
virtual environment solely for repository dependency validation.

Each run writes a fsynced start before engine execution, frozen validated
task/target/agent/condition/result references, `receipt.json`, `events.json`,
unmodified Inspect JSON under `raw/`, and an owned-container cleanup receipt.
Use `proof.py <directory> --recover` only after its controller has stopped.
Recovery removes containers bearing that start's unique label and records
interrupted/ungraded, never replays tools. Repeating recovery retains the result.

## What executed evidence establishes

Only the requirement and unfinished `answer.py` enter a disposable container.
Executed reads of verifier, solution, tests, history, home credential paths,
and the Docker socket fail. Docker inspection confirms no mounts, no privilege,
all capabilities dropped, and network denial; a synthetic controller secret
canary is absent inside the container. The scripted agent executes only
synchronous sandbox commands. The scorer writes held-out assertions after the
agent's stop, never through `Sample.files`, model input, or a tool response.
Both a correct patch and an incorrect patch receive independent verification.

Runtime error and per-tool GNU `timeout` kill retain native errors and measured
elapsed time without a completion duration. Solver cancellation is a real
`CancelledError` after agent stop: Inspect describes it as an **unattributed
cancellation sample error**, which remains intact alongside this fixture's
controller attribution. A killed controller is tested while Docker reports
its sleeping Python worker running; recovery removes that owned sandbox and
leaves verification not run. No sandbox tests are silently skipped.

Timing uses one controller's monotonic clock: setup (including provisioning),
agent work, verification, and end-to-end through engine teardown/cleanup.
Queue and separate provisioning remain unknown, not zero or derived residuals.
Interrupted recovery preserves measured setup but cannot reconstruct agent
elapsed or completion. The deadline is explicitly **per tool**, not a claimed
whole-trial active budget. Only independent success has time-to-completion.

Inspect's overall successful evaluation status can contain failed samples.
The adapter examines sample errors, preserves raw model/tool/request/error
events, and exports separately attributed terminal state. Mock token usage
is explicitly supplied synthetic counters (one input/output token per reply),
not live usage or retokenization. Credits and inference controls remain
unavailable/not applicable. An initial default mock-usage attempt failed trying
to fetch tokenizer data; supplying explicit counters removed that dependency.

## Reusable primitives and remaining boundaries

Reuse Inspect's sample staging, isolated `sandbox().exec`, tool loop, post-solver
scorer, and raw logs. Keep controller-attributed timing, recovery, and terminal
mapping separate from native evidence. This fixed fixture does not establish
adversarial process quiescence, general recovery/ledger/reporting, historical
replay calibration, full-trial deadline enforcement, native Copilot session
isolation, provider identity, live token/cache/reasoning semantics, or credits.
Those remain gated; no subsequent roadmap task is implemented here.

Official docs were checked through upstream source on November 25, 2026
(the documentation hostname did not resolve on this host):
[agent bridge](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/docs/agent-bridge.qmd),
[sandboxing](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/docs/sandboxing.qmd).
The installed version and executed receipts, not those docs, establish this fit.
See [executed commands, timings, raw digests, and cleanup](verification.md).
