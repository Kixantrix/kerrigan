# MB-009r: native working-day curriculum, MAI versus Sonnet

**Both models passed all five admitted tasks (90/90 independent checks each).
Sonnet completed every task faster: 140.31 seconds total versus MAI's 401.20
seconds, a 2.86x elapsed-time ratio in this round.** This supports choosing
Sonnet for latency on these small implementation/operations/experiment tasks,
not a general capability or price ranking.

One attempt per model/task, MAI then Sonnet, on this macOS laptop with the
same pinned CLI/MXC transport and separate Docker verifier. No subject attempt
needed a retry. All times include native setup, fresh HTTPS/access proof,
agent work, owned cleanup and independent verification; audit/panel time is
excluded. Native token sums include repeated context and cache-hit input;
they are not unique prompt sizes or billable-token claims.

## Per-family results

| Family | Admitted tasks | MAI pass/checks | Sonnet pass/checks | MAI seconds | Sonnet seconds | MAI input/output tokens | Sonnet input/output tokens |
|---|---:|---|---|---:|---:|---:|---:|
| Implement | 3 | 3/3; 71/71 | 3/3; 71/71 | 303.19 | 91.41 | 581,098 / 16,533 | 223,771 / 12,693 |
| Operate | 1 | 1/1; 8/8 | 1/1; 8/8 | 46.01 | 20.30 | 122,376 / 1,103 | 72,213 / 1,143 |
| Experiment | 1 | 1/1; 11/11 | 1/1; 11/11 | 52.00 | 28.60 | 75,399 / 2,101 | 71,474 / 2,734 |
| Understand and plan | 0 | Not evaluated: retired package | Same | N/A | N/A | Unknown | Unknown |
| Review and repair | 0 | Not evaluated: retired package | Same | N/A | N/A | Unknown | Unknown |
| Research, Orchestrate, Design | 0 | Catalog only; no calibrated packages | Same | N/A | N/A | Unknown | Unknown |
| Total evaluated | 5 | 5/5; 90/90 | 5/5; 90/90 | 401.20 | 140.31 | 778,873 / 19,737 | 367,458 / 16,570 |

| Task | Independent checks, each model | MAI seconds | Sonnet seconds | MAI input/output tokens | Sonnet input/output tokens | Native starts MAI/Sonnet |
|---|---|---:|---:|---:|---:|---:|
| validator | 25/25 | 79.59 | 35.06 | 81,904 / 4,469 | 82,675 / 4,488 | 11 / 8 |
| grouping | 6/6 | 90.75 | 16.69 | 314,253 / 4,154 | 42,932 / 2,049 | 25 / 5 |
| status | 40/40 | 132.84 | 39.66 | 184,941 / 7,910 | 98,164 / 6,156 | 15 / 8 |
| selfhost-redeploy-state | 8/8 | 46.01 | 20.30 | 122,376 / 1,103 | 72,213 / 1,143 | 17 / 8 |
| sr-temporal-assay | 11/11 | 52.00 | 28.60 | 75,399 / 2,101 | 71,474 / 2,734 | 10 / 7 |

Each subject received one controller prompt. Native starts (78 MAI, 36
Sonnet) are the natural multi-call tool loop, not controller retries. All
starts/usage/failure projections and the 74 controller prompts across
subjects, admission, calibration and panels are retained. No evaluated
non-pass exists, so evaluated failure-attribution requests correctly number
zero. The rejected blind solution was adjudicated separately as task-caused.

## Admission and native calibration

Before inference, the real native path reproduced every retained Docker
base/reference count, with labeled trusted fixtures, not model successes:

| Package | Base | Reference | Admission decision |
|---|---:|---:|---|
| validator | 22/25 | 25/25 | Admitted with untested-requirement findings |
| grouping | 4/6 | 6/6 | Admitted with untested-requirement findings |
| status | 32/40 | 40/40 | Admitted with untested-requirement findings |
| selfhost-redeploy-state | 4/8 | 8/8 | Admitted with overspecified-test findings |
| sr-temporal-assay | 2/11 | 11/11 | Admitted with untested-requirement findings |
| plan-dashboard-waves | 1/8 | 8/8 | Retired for contradiction |
| review-conflict-predictor | 10/21 | 21/21 | Retired for contradiction and task-caused blind rejection |

Two-family artifact audits used Copilot-served Sonnet/Anthropic and GPT
5.6 Sol/OpenAI. Blind reimplementation used Gemini 4 Neon/Google, a family
other than either subject; six passed and the review package failed.
Audit verdicts gate task admission and never set model pass/fail scores.

Planning's instruction requires every shared-file conflict implied by
acceptance criteria, not just Touch lines. Its oracle/checks omit
M2.2|M2.4 and M2.3|M2.4, although M2.4's Playwright/component-test requirements
also need package.json/lockfile edits. Review's instruction says a nonempty
planning file without any scope signal must never succeed, while
`TestRun::test_no_tasks_produces_empty_waves` and the oracle require success
for `# Tasks\n\nNothing yet.\n`. Both review auditors and independent
adjudication identify that mismatch. These read-only packages were retired,
not silently fixed, skipped as model failures or scored.

## Quality is a separate signal

Blind candidate-versus-oracle panels exclude each subject's family: MAI is
judged by OpenAI/Anthropic; Sonnet by OpenAI/Google. They are not direct
MAI-versus-Sonnet comparisons. There is no defensible quality winner here.

| Task | MAI diff/oracle size | Sonnet diff/oracle size | Candidate preferred, MAI | Candidate preferred, Sonnet |
|---|---:|---:|---:|---:|
| validator | 1.440 | 1.420 | 2/2 judges | 2/2 judges |
| grouping | 0.902 | 0.471 | 2/2 judges | 2/2 judges |
| status | 0.722 | 1.056 | 2/2 judges | 2/2 judges |
| selfhost-redeploy-state | 0.174 | 0.174 | 2/2 judges | 2/2 judges |
| sr-temporal-assay | 0.688 | 0.875 | 2/2 judges | 1/2 judges |

All final artifacts touched one allowed source file; static inspection found
no added debug/TODO markers, Python parse errors or unreachable statements.
Static scope is the collected final artifact, not scratch self-tests, and
these signals are not a comprehensive code review. Nine panels agreed; the
Sonnet experiment panel split. Overall pairwise panel agreement was 9/10.

Calibration used three explicitly trusted, independently Docker-passing
validator variants: an unused debug helper, dead code, and obscured local
identifiers. Three judge families each preferred the oracle on 3/3, with
agreement 1.0. This is only a small seeded sanity check. The original
obscured-name generator returned the oracle unchanged: all three judges
correctly tied, and the initial calibration was not admitted. That fixture,
all nine initial judgments and the corrected judgments remain retained.
The generator now creates a distinct fixture or fails explicitly. GPT's
invalid read-with-data query was denied and preserved; only that query was
rerun with explicit legal read/write syntax, not a changed quality rubric.

## Condition, containment and preservation

Native task runtimes: CPython 3.9 stdlib plus PyYAML 6.0.2, or official Node
24.11.1 with built-in TypeScript stripping. No task shell, pytest, npm,
subprocess, credential access or network. Node's binary is read-only and
actual Node/Python no-fork and unlisted-file denial checks passed. The
independent verifier uses isolated Python 3.12/Node 24 Docker images.
CLI 1.0.115 and MXC SDK 1.1.0 remain pinned.

Every prompt requires fresh actual native verified public HTTPS, explicit
SDK sandbox and sole effective `mb_action`. All roles reuse the same
existing isolated sign-in; this slice started no web-flow login and copied
no credentials. Only trusted transport receives the three documented
public-trust services; evaluated tasks do not. Safety/managed policy and
Keychain/task-network denials remain in force.

Responses use stock CLI defaults: the harness does not inject
`COPILOT_LLM_RESPONSE_MAX_BYTES`. Independent finite containment remains:
1 KiB header, 8 MiB frame, 96 MiB protocol total, 16,384 events, 1 MiB sent
frame/16 MiB sent total and 1 GiB evidence disk. Task limits remain 32 KiB
writable file/channel, 256 KiB/action, 4 MiB aggregate input, 127 agent
actions plus reserved final read, 1 MiB retained output, 30 seconds/run and
3,600 active plus 15 cleanup seconds. Long readonly exports use exact
frozen-size bounds and 4 KiB paged reads. All ten final artifacts were
collected only after proven owned quiescence, matched to native final-read
bytes and independently graded in exact bound images.

Each package has a distinct self-sealed condition and exclusive ordered
slots. Subject conditions retain their executed source snapshots; later
quality instruction/calibration corrections have separate source bindings.
No old approval or six spent canary slots was reset. All 127 pre-existing
tracked JSON/JSONL/archive artifacts and task-package bytes match foundation
`289a6c0`. Earlier tool-preview truncation, audit-schema failures and invalid
tool-format attempts remain diagnostics, not evaluated model failures.

The archive contains 154 native start bindings. All v2-v5 bindings have
exact archived source bytes (137 complete bindings), including every
subject trial, completed gate/panel and final-source native proof. Seventeen
initial v1 diagnostic bindings retain their hashes but lack original bytes
for five source paths (85 missing references); these are disclosed, not
reconstructed or claimed as complete proof. Raw native protocol, account/
quota fields, auth state and third-party binaries/dependency source are
excluded. Safe projections preserve lifecycle/start/failure/usage counters.

## Limits and evidence

This is n=1 per model/task, five short curated tasks, not a time-horizon
estimate. MAI always ran first, service/cache state is not controlled, and
public historical code may already be familiar. Sonnet also participated
in audits in separate fresh sessions; remote retention/exposure is unknown.
No contamination-free claim is made. Backend identity, dollar price, credits
and power are not independently measured; unknown is not zero. Native
reported model IDs/tokens/cost fields are retained with cost units unknown.

The ten public anchors remain a stretch gap: their third-party task images
and setup dependencies were not provisioned; shared-verification
Terminal-Bench environments are refused by the separate-verifier path.
Supporting them requires a separately contained shared-mode runner, not
relaxing this task sandbox. SWE-bench Pro difficulty labels are absent from
the pinned registry, so this is not a verified HARD subset.

[Verification and metrics](MB-009r-verification.json) and
[safe source/outcome/ledger/gate/panel archive](MB-009r-evidence.tar.gz)
contain member SHA-256s, exact conditions, native runtime/CA/image bindings,
per-task ledger comparisons and command results. `$OWNED` is the session-owned
local-mxc state; `$PYTHON` is its `validation-venv/bin/python` (Python 3.12.12).

| Check | Command | Result |
|---|---|---|
| Focused unit/integration/native flow | `MB006K_OWNED=$OWNED $PYTHON -m pytest -q tests/projects/michael_bench/{test_local_transport.py,test_historical_import.py,test_manifests.py,test_replay_trial.py,test_curriculum.py,test_curriculum_native.py} -k 'not fresh_calibration_matches_retained_counts'` | 268 passed |
| Independent grader | `$PYTHON -m pytest -q tests/projects/michael_bench/test_replay_grader.py` | 38 passed; 1 documented skip |
| Artifact validator | `$PYTHON tools/validators/check_artifacts.py` | Passed |
| Dependency validator | `$PYTHON tools/validators/check_python_deps.py` | Initial namespace false positive preserved; passed on 62 files after parent `060b8c9` |
| Namespace regression | `$PYTHON -m pytest -q tests/test_check_python_deps.py` | 10 passed |
| Repository smoke | `PATH=$OWNED/validation-venv/bin:$PATH KERRIGAN_SMOKE_DASHBOARD=0 bash scripts/smoke.sh` | 14/14 passed; unrelated dashboard build disabled |
| Native owner syntax | `/opt/homebrew/bin/node --check benchmarks/michael/local_transport/{limits,owner,validator_admission,curriculum_admission}.mjs` (one invocation per file) | All passed |
| Diff whitespace | `git diff --check` | Passed |

Archive SHA-256:
`05e4a08906347fe64fc0a4fea07dff01b3871dc8159fee54cedf3bb08dac7963`.
Verification SHA-256:
`eea00ddba5a3eea59a06012a49d366646b8a287183b15513e36997f732272288`.

Official Node provenance:
`https://nodejs.org/dist/v24.11.1/`, archive checked against official
SHASUMS256.txt; binary SHA-256
`4255a388254ca4319e2f95f1da375d5deaddf25baf9c7c85070b67f9543b15d0`.
No global installation, shared settings edit or extra model service.
