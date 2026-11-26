# Michael Bench working-day curriculum (MB-008)

Executed native admission, MAI/Sonnet trials and separate quality results are
in [results-v1.md](results-v1.md) (MB-009r). The native runner now supports all
seven policies and pinned Node 24. Five packages were admitted; two were
retired from that round for instruction/check contradictions.

`catalog.json` lists 44 candidate tasks mined from Kixantrix repositories,
covering all eight spec families. Each candidate records source repo, exact
base/reference SHAs (verified against GitHub), whether the reference is merged
or lives on a research branch, outcome-evidence type, privacy class, toolchain,
required environment, grader-image status and estimated agent minutes.
HOBL and WindowsDeveloperConfig are excluded by user direction.

| Family | Candidates | Calibrated package(s) |
|---|---:|---|
| Implement | 9 | `validator`, `grouping`, `status` |
| Experiment | 7 | `sr-temporal-assay` |
| Review and repair | 6 | `review-conflict-predictor` |
| Operate | 6 | `selfhost-redeploy-state` |
| Understand and plan | 5 | `plan-dashboard-waves` |
| Research | 4 | none yet |
| Orchestrate | 4 | none yet |
| Design | 3 | none yet |

22 candidates are long-horizon (more than 30 estimated minutes). Toolchains
that don't fit the current grader images (Godot, Android/Gradle, Rust on
Windows, multi-service stacks) record the image or environment they need in
`grader_image`, rather than being dropped.

## Calibrated packages

Packages live in `benchmarks/michael/tasks/<name>/` (`tasks/curriculum.py`).
Each one has an exact-base `agent/` export with a generated `policy.json`, a
public `TASK.md`, verifier-only `hidden/` (reference and trusted probe/clause
rows), a frozen task-contract `manifest.json`, a `native-policy.json` in the
existing native-trial shape, and a `calibration.json` Docker receipt.

| Package | Source | Privacy | Base | Reference |
|---|---|---|---|---|
| sr-temporal-assay | personal-selfhost research branch | private-synthetic-fixture | 2/11 | 11/11 |
| selfhost-redeploy-state | vhs-video-stack | private-synthetic-fixture | 4/8 | 8/8 |
| review-conflict-predictor | kerrigan #312 | public (exact base) | 10/21 | 21/21 |
| plan-dashboard-waves | kerrigan #306 | public (exact base) | 1/8 | 8/8 |
| grouping (Docker grader) | kerrigan #405 | public | 4/6 | 6/6 |
| status (Docker grader) | kerrigan #409 | public | 32/40 | 40/40 |

Grading uses only the independent Docker observation grader
(`replay_grader/`). The candidate runs with no network, a read-only root, no
mounts and dropped capabilities. Probes and answer-free harnesses enter the
sandbox; clauses, references and check names never do. Plans and diagnoses are
graded by deterministic required-facts and constraint checklists with closed
vocabularies. Residual judgment is recorded in `task.json` under
`residual_rubric`, never model-judged.

Private sources are re-synthesized as stdlib fixtures: no private code,
hostnames, credentials, footage or datasets are included. Gridiron and
alethiometer references are on unmerged research branches, which is disclosed
as `history_status`.

## Reproduce

```bash
docker build --pull=false -t michael-replay-grader:mb006j benchmarks/michael/replay_grader
docker build --pull=false -t michael-replay-grader-node:mb008 -f benchmarks/michael/replay_grader/Dockerfile.node benchmarks/michael/replay_grader
python -m benchmarks.michael.replay_grader.calibrate grouping status sr-temporal-assay \
  selfhost-redeploy-state review-conflict-predictor plan-dashboard-waves
python -m pytest tests/projects/michael_bench/test_curriculum.py tests/projects/michael_bench/test_replay_grader.py -q
```

## Public benchmark practice (no human in the evals)

- **Harbor/Terminal-Bench layout** (`harbor.py`, `harbor/<task>/`): every
  calibrated package exports to `instruction.md`, `task.toml` (schema 1.4),
  `environment/Dockerfile`, `solution/solve.sh` (oracle) and `tests/test.sh`.
  It uses a separate, no-network verifier, declares the candidate as an
  artifact, runs a non-root agent and pins public base images by digest.
  Harbor 0.27.0's own `Task` model parses all 7, and `harbor lint --select ALL`
  reports 0 findings. Inside the verifier, `harbor_grade.py` runs the harness
  as UID 65534 with probes only; clauses stay root-only. The importer/runner
  (`load`, `artifacts`, `verify`, `admission`) runs any separate-verifier
  Harbor task with no network and capabilities dropped. Harbor reward counts
  equal the trusted Docker grader's counts for all 7.
- **PR mining** (`mining/mine.py`): SWE-bench-schema instances with base
  commit, PR title as the problem statement, merged non-test diff as the
  oracle, and test diff. FAIL_TO_PASS and PASS_TO_PASS come from contained,
  no-network pytest runs on base+tests and on the reference. On 16 recent
  kerrigan PRs, 14 are admissible candidates (`mining/kerrigan-instances.json`).
  #312 reproduces exactly: 6 F2P and 50 P2P. PRs without tests are marked
  `needs_generated_verifier`.
- **Automated admission** (`automation.py`, `admit.py`, `admission.json`):
  the executed gates are oracle passes and base fails. The model gates are two
  LLM audits from different families (leakage, untested requirement,
  over-specified test, contradiction) and a blind re-implementation by a third
  family, with adjudication of rejections. They are frozen, hash-bound
  requests with strict verdict schemas. Fixed rules decide whether a task is
  admitted, needs a fix or is retired. Verdicts gate admission only and never
  score models.
- **Failure attribution**: frozen attribution requests whose verdicts label a
  failure as model-, task- or harness-caused. Two attributor families must
  agree with confidence 0.7 or more. Task and harness causes route to fix and
  rerun; disagreement reruns once and is never counted as a model failure.
- **Quality, reported separately from pass/fail**: deterministic, parse-only
  signals are diff size relative to the oracle, files outside the task, debug
  statements and TODOs beyond the oracle, unreachable code, parse errors and
  tests added. A blind pairwise panel compares the candidate against the
  oracle, needs two or more judge families and excludes the model under
  test's family. It is calibrated on seeded degraded variants of
  known-good fixes and reports judge accuracy and agreement.
- **Anchor subset** (`anchors.json`): 5 Terminal-Bench 2.0 and 5 SWE-bench Pro
  tasks, pinned to Harbor registry git commits and reported separately.
- **Metrics** (`metrics.py`): resolved rate with Wilson CI, pass@k and pass^k,
  cost, tokens and wall time per resolved task (unknown stays unknown), and a
  METR-style 50% time horizon.

`verification.json` records commands, test counts, image IDs, calibration,
admission and mining results.

## Known gaps at the MB-008 preparation baseline

- Native runner and model-gate gaps below were addressed by MB-009r; see
  [results-v1.md](results-v1.md) for executed outcomes and remaining limits.
- Research, Orchestrate and Design have catalog candidates but no calibrated
  package yet.
- The native trial runner (`replay_trial/`) is still validator-specific:
  `handoff.terminal` expects 25 assertions and the native runtime has no Node.
  New Python packages ship a native policy in the existing shape, but running
  them natively needs the runner to read that policy, and the TS replays need
  a Node-capable native runtime.
- Model-dependent gates (LLM audits, blind re-implementation, attribution,
  quality panel and its calibration run) are defined and validated but not
  executed here: running models is out of this slice's scope. All 7 packages
  are therefore `provisional`, not `admitted`. Mined PR instances still need
  packaging into Harbor tasks and these gates.
- Anchors are pinned but not yet run. Their environments need large
  third-party images and network access during setup. Many Terminal-Bench
  tasks use shared verification, which `verify` refuses because the verifier
  would share the agent sandbox; a shared-mode runner is still to be added.
  SWE-bench Pro difficulty labels are not in the registry, so the subset is
  not a verified HARD subset.
- None of this is a model result. No model was run.

## MB-010c: harder, broader curriculum (v2)

Results v1 saturated (both models 5/5), so v2 adds harder, multi-file work and
fills the empty families. Every package has a Harbor export with
`harbor lint --select ALL` reporting 0 findings, and Harbor admission where the
oracle passes and the base fails. Each also has a retained Docker calibration
receipt and a fresh-clone reproduction. Base → reference independent checks:

| Package | Family | Source | Lang / files | Human min | Base | Reference |
|---|---|---|---|---:|---:|---:|
| plan-dashboard-waves-v2 | Understand and plan | kerrigan #306 (public, exact) | JSON / 1 | 15 | 0/10 | 10/10 |
| review-conflict-predictor-v2 | Review and repair | kerrigan #312 (public, exact) | Python / 1 | 25 | 11/25 | 25/25 |
| research-serverless-cost | Research | personal-selfhost #174 (synthetic) | JSON / 1 | 45 | 1/12 | 12/12 |
| design-alethiometer-case | Design | alethiometer 4528e96 (public branch) | Python+Markdown / 4 | 45 | 3/12 | 12/12 |
| orchestrate-voice-integration | Orchestrate, long | personal-selfhost T012 (synthetic) | TS+JSON / 4 | 90 | 1/13 | 13/13 |
| kerrigan-plan-conflict-queue | Implement, long | kerrigan #365 (public, exact merged PR) | TS / 2 | 90 | 1/20 | 20/20 |
| yv-relevance-instrument | Experiment, long | your-voice #224 app (synthetic) | TS / 3 | 90 | 0/12 | 12/12 |
| emv-thumbnails-gallery | Implement, long | event-media-vault #8 app (synthetic) | JS / 3 | 75 | 2/11 | 11/11 |

- **Retired v1** (`retired.json`): `plan-dashboard-waves` and
  `review-conflict-predictor` remain byte-for-byte frozen but are recorded as
  `retired` in admission. v2 fixes each contradiction the MB-009r audits
  found. The plan oracle now includes the M2.2|M2.4 and M2.3|M2.4 manifest
  conflicts and checks the exact conflict set. The review instruction scopes
  fail-loud to files that contain task lines, matching the historical
  prose-only success. v2 also removes the over-specified stderr-path and
  missing-file wording checks, adds CLI, partial-annotation and finding-shape
  checks, and requires nonempty exclusion reasons.
- **Multi-artifact candidates**: a package can declare `grader.candidates`.
  The candidate is then a canonical bundle, sorted JSON `{path: text}`
  (`specs.bundle`/`unbundle`). The Docker grader rejects any bundle whose
  file set differs from the declaration. Harbor exports declare every file
  as an artifact and use `harbor_grade_multi.py`. Existing single-artifact
  exports are byte-identical.
- **Node scenario harness** (`harnesses/scenarios.mjs`): trusted, answer-free
  `scenarios.mjs` fixtures, such as fake fs, GitHub, blob stores and held-out
  data, drive the candidate modules. Only observations leave the sandbox.
- **No model judge.** Research, plan, design and orchestration answers are
  graded by numeric tolerances, closed vocabularies, exact sets, required
  citations, honest-unknown checks and perturbation tests (for example, the
  hinge relief is re-evaluated with other screw lengths). Your-voice expected
  values come from an independent Python implementation of its spec.
- The long-horizon set has 4 packages, each 75–90 estimated human minutes and
  multi-file. They span 4 repositories and TypeScript plus JavaScript, and
  include the your-voice and event-media-vault apps. One is an exact merged
  public PR (#365). The estimated human minutes are recorded for METR-style
  horizon reporting.
- **Model gates**: the two-family LLM audits and blind re-implementation are
  left `provisional` for the native executor, as frozen requests in
  `admission.json`. No model was run here.

Native-path gap (outside this slice's scope): `replay_trial/curriculum.collect`
reads only `policy["source"]`. For multi-artifact packages, native policies
list every file under `artifacts`, and the native collector must read each
file after quiescence and pass `specs.bundle(files)` to the grader.
`replay_trial.curriculum.sources()` also hashes only `harnesses/*.py`; it
should include `harnesses/*.mjs`. The native closure test was generalized to
accept `artifacts`.
