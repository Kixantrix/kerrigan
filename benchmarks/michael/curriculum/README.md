# Michael Bench working-day curriculum (MB-008)

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

## Known gaps

- Research, Orchestrate and Design have catalog candidates but no calibrated
  package yet.
- The native trial runner (`replay_trial/`) is still validator-specific:
  `handoff.terminal` expects 25 assertions and the native runtime has no Node.
  New Python packages ship a native policy in the existing shape, but running
  them natively needs the runner to read that policy, and the TS replays need
  a Node-capable native runtime.
- None of this is a model result. No model was run.
