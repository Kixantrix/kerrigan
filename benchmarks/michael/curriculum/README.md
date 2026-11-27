# Michael Bench working-day curriculum (MB-008)

Executed native admission, MAI/Sonnet trials and separate quality results are
in [results-v1.md](results-v1.md) (MB-009r). The native runner now supports all
seven policies and pinned Node 24. Five packages were admitted; two were
retired from that round for instruction/check contradictions.

The multi-file round and its disclosed task revisions are recorded in
[results-v2.md](results-v2.md) (MB-010r). Its native collector binds every
declared artifact after quiescence and hashes both Python and JavaScript
verifier harnesses.

Round 2 is complete: Sonnet passed 8/8 selected tasks and MAI 6/8. The
Orchestrate row retains admitted-and-run v3; v4's `needs_fix` gate was upheld
with zero subject prompts. Later round-3 literal fixes are known task issues,
not extra round-2 samples; regrading the ten existing affected artifacts
changes no binary outcome or partial count.
The later parent catalog's provisional orchestration-v5 is round-3 work too,
not an additional round-2 subject run.

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

| Package | Family | Source | Lang / files | Oracle diff (files, ±lines) | Base | Reference |
|---|---|---|---|---:|---:|---:|
| plan-dashboard-waves-v2 | Understand and plan | kerrigan #306 (public, exact) | JSON / 1 | 1, +45/−4 | 0/10 | 10/10 |
| review-conflict-predictor-v2 | Review and repair (retired) | kerrigan #312 (public, exact) | Python / 1 | 1, +89/−22 | 11/25 | 25/25 |
| review-conflict-predictor-v3 | Review and repair | kerrigan #312 (public, exact) | Python / 1 | 1, +91/−22 | 11/27 | 27/27 |
| research-serverless-cost | Research | personal-selfhost #174 (synthetic) | JSON / 1 | 1, +55/−11 | 1/12 | 12/12 |
| design-alethiometer-case | Design | alethiometer 4528e96 (public branch) | Python+Markdown / 4 | 4, +12/−10 | 3/12 | 12/12 |
| orchestrate-voice-integration | Orchestrate, long | personal-selfhost T012 (synthetic) | TS+JSON / 4 | 4, +99/−10 | 1/13 | 13/13 |
| kerrigan-plan-conflict-queue | Implement, long | kerrigan #365 (public, exact merged PR) | TS / 2 | 2, +396/−4 | 1/20 | 20/20 |
| yv-relevance-instrument | Experiment, long | your-voice #224 app (synthetic) | TS / 3 | 3, +148/−6 | 0/12 | 12/12 |
| emv-thumbnails-gallery | Implement, long | event-media-vault #8 app (synthetic) | JS / 3 | 3, +77/−10 | 2/11 | 11/11 |

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
- The long-horizon set has 4 packages, each multi-file (oracle diff of at
  least 2 files and 80 lines, at least 10 hidden checks). They span 4
  repositories and TypeScript plus JavaScript, and include the your-voice and
  event-media-vault apps. One is an exact merged public PR (#365).
- **Difficulty is agent-native, never estimated human time** (user,
  2026-11-26). `curriculum.task_size(name)` reports the oracle diff (files and
  lines over the writable files), files and lines to read, and hidden checks
  and clauses; Harbor exports carry it as `task_size` metadata. Observed
  difficulty (success rate and median agent seconds over all models and
  attempts) comes from `metrics.observed_difficulty`. No human-time horizon is
  reported. Frozen historical packages may still carry an
  `estimated_human_minutes` field byte-for-byte; `curriculum.meta` drops it and
  nothing reads or displays it.
- **Model gates**: the two-family LLM audits and blind re-implementation are
  left `provisional` for the native executor, as frozen requests in
  `admission.json`. No model was run here.

Native-path gap at the MB-010c preparation baseline (resolved by MB-010r;
see [results-v2.md](results-v2.md)): `replay_trial/curriculum.collect`
reads only `policy["source"]`. For multi-artifact packages, native policies
list every file under `artifacts`, and the native collector must read each
file after quiescence and pass `specs.bundle(files)` to the grader.
`replay_trial.curriculum.sources()` also hashes only `harnesses/*.py`; it
should include `harnesses/*.mjs`. The native closure test was generalized to
accept `artifacts`.

v3 of the review package answers the MB-010r native admission audit of v2 (`MB-010r-review-v2-admission.json`). The oracle now counts only extracted globs: an empty `- Touch:` annotation is no file-scope signal, and the v2 oracle fails the new hidden check. Waves are specified as overlap-only greedy earliest-wave assignment in document order, with dependencies out of scope. The instruction now also states the no-output-on-failure, annotation-union and literal-stderr-form contracts. v1 and v2 stay frozen and retired.

design-alethiometer-case-v2 answers the v1 admission audit (`MB-010r-design-admission.json`). The oracle README now says 36.9/44.6 mm, matching the model's 36.949 mm at 0.1 mm. Document numbers must equal the model value rounded half-up, checked exactly; the old 0.06 mm tolerance masked the error. Model-value checks keep tolerances at or below 0.002 mm. v1 is retired.

kerrigan-plan-conflict-queue-v2 changes only the instruction. The merged #365 oracle keeps a saved entry queued when cleanup fails, so the instruction now states no-loss, at-least-once delivery, and no check requires exactly-once on that path. The native re-audit retained the v1 contradiction; MB-010r excludes it in favor of v2 and preserves its original gate.

yv-relevance-instrument-v2 and emv-thumbnails-gallery-v2 change only the instruction; their oracles and hidden checks are unchanged, and a test asserts this. In yv, the blindness check covers own enumerable string keys, matching `Object.entries`. In emv, the carousel sets `height` to `rowHeight`, and per-image failure isolation covers read, probe, resize and write; a `store.exists` error rejects the whole run. Both v1 packages stay frozen and retired after native re-audit; their admission evidence is cited below.

yv and emv v1 are now retired, citing `MB-010r-yv-relevance-instrument-admission.json` and `MB-010r-emv-thumbnails-gallery-admission.json`. research-serverless-cost-v2 makes the `unknowns` check set-based: exact set, no duplicates, any order. Its instruction, oracle and other checks are unchanged; v1 stays frozen and excluded after both native subjects failed only that order clause. An audit of every array check in the research, plan, design and orchestrate packages found no other order over-specification. The plan conflict pairs and orchestrate defect categories are sorted by their harness, citations and requirement files use contains-all checks, and design and orchestrate lists follow fixed document or protocol order.

orchestrate-voice-integration-v2 rewards genuine extra findings and penalizes invented ones. Its audit recorded one genuine extra beyond the five integration defects: a memory leak, where budget-ended sessions are never deleted (`server.ts:53`). It recorded auth-bypass and race-condition as absent. MB-010r later reproduced a reentrant cancel-ordering weakness, so that race-condition finding is genuine: v3 audits it with a behavioral fix check, while auth-bypass remains absent. V1 and v2 stay frozen and retired. The ledger requires the five integration defects and permits only audited, behaviorally fixed extras; a claimed leak is checked after 40 sessions end. See the native diagnostics and results-v2 for the distinction between a package audit fault and the independent model-caused failures.

## Public anchors provisioning

`anchors_provision.py` provisions the 10 frozen public anchors in
`anchors.json` through Harbor and writes `anchors-verification.json`. The
script uses only the stdlib and subprocess. It fetches each task with a shallow,
blobless sparse checkout at its pinned commit into `.kerrigan/anchors/` (that
directory is gitignored, and no public task content is vendored here). It then
hashes the task tree. anchors.json has no `tree_sha256` yet, so the hash is
recorded. Next, it runs Harbor's built-in `oracle` agent, which must score 1,
and `nop` agent (the base), which must score 0, with `-e docker`. It handles
one anchor at a time and removes that anchor's task images and the builder
cache after each run. `michael-*` images are never touched. Results merge
per anchor, so you can rerun a subset:

```bash
python3 benchmarks/michael/curriculum/anchors_provision.py            # all 10
python3 benchmarks/michael/curriculum/anchors_provision.py --only fix-git instance_ansible
python3 benchmarks/michael/curriculum/anchors_provision.py --fetch-only  # fetch + hash only
```

Requirements: Harbor 0.27.0 (`HARBOR` or `--harbor`, default
`/tmp/harbor-venv/bin/harbor`) and Docker with the compose v2 plugin. Harbor
needs `docker compose`, and this host had to install the plugin under
`~/.docker/cli-plugins`. A disk preflight skips an anchor and records an
`environment-gap` when 4x its compressed image plus 1 GiB exceeds free disk.
Use `--force` to try anyway.

**Host shim, recorded per run:** this host's egress allowlist blocks
`astral.sh`, and its TLS-intercepting proxy breaks uv's bundled roots. Every
Terminal-Bench 2.0 verifier runs `curl https://astral.sh/uv/... | sh; source
$HOME/.local/bin/env`. `--uv-shim auto` therefore bind-mounts, read-only at
`/root/.local/bin`, what that installer would place there. The mount contains
uv 0.9.5 from PyPI (sha256-checked), an `env` file and the host CA bundle
(`SSL_CERT_FILE`, `UV_NATIVE_TLS=1`). No task file, test or image is modified.
Hosts that can reach astral.sh get no shim.

**Licenses:** Terminal-Bench 2.0 is Apache-2.0. `laude-institute/harbor-datasets`
has no license: it has no LICENSE file, and GitHub reports none. Its SWE-bench
Pro tasks adapt `scaleapi/SWE-bench_Pro-os`, which is MIT. We reference tasks
only by URL and pinned commit.

Results for anchors.json revision 2, 2026-11-27, with 2 CPUs, 7.7 GiB RAM, ~7.7 GB free disk, x86_64,
Docker 29.1.3 and Harbor 0.27.0. Times are Harbor trial seconds; image bytes
are the compressed `docker image inspect` size.

| Anchor | Status | Oracle | Base | Image bytes |
|---|---|---|---|---|
| nginx-request-logging | verified | 1 (29 s) | 0 (26 s) | 67,285,778 |
| configure-git-webserver | verified | 1 (57 s) | 0 (24 s) | 72,341,286 |
| pytorch-model-recovery | environment-gap | not run | not run | 6,103,392,088 (Hub) |
| train-fasttext | verified | 1 (212 s) | 0 (32 s) | 509,018,113 |
| fix-git | verified | 1 (28 s) | 0 (21 s) | 158,060,522 |
| SWE-Pro ansible 0ea40e09 | verified | 1 (26 s) | 0 (22 s) | 521,067,424 |
| SWE-Pro openlibrary 00bec1e7 | verified | 1 (23 s) | 0 (18 s) | 960,358,775 |
| SWE-Pro qutebrowser 01d1d149 | verified | 1 (23 s) | 0 (20 s) | 691,826,340 |
| SWE-Pro element-web 1077729a | verified | 1 (121 s) | 0 (120 s) | 1,378,624,156 |
| SWE-Pro tutanota 09c2776c (rev 2) | verified | 1 (119 s) | 0 (57 s) | 1,357,144,012 |

- **pytorch-model-recovery** (`environment-gap`): the prebuilt
  `alexgshaw/pytorch-model-recovery:20251031` image is 6.1 GB compressed
  (amd64 only) because `pip install torch==2.7.1` pulls the CUDA wheels. It
  needs about 25 GB of free Docker disk (estimated) plus 1 CPU and 2 GB RAM,
  but no GPU. This host had ~7.7 GB, so it was not run.
- **Revision 2:** NodeBB was replaced; its record is kept under
  `superseded` in anchors-verification.json and under `revisions` in
  anchors.json. The status was `task-defect`, and Harbor's oracle reward was 0
  (346 s); the base reward was also 0. As packaged at harbor-datasets@c8e8f3fa,
  4 of the 681 required test IDs can never match the names the verifier parser
  emits. Three are truncated at an embedded double quote, for example
  `...ACP default "day`. The fourth lost its trailing space. The oracle passes
  those tests under their full names, so it cannot pass in any environment.
  The evidence is in `oracle_diagnosis`. The replacement follows the same
  rule: the first task by sorted instance name from a JS/TS repo not yet
  represented. The first candidate, protonmail/webclients `01b519cd`, was
  rejected because its image is 5.57 GB compressed, about 23 GB on disk, which
  exceeds this host. The next two protonmail images are 4.7 to 4.8 GB, so the
  repo was skipped. tutao/tutanota `09c2776c` (TypeScript) was then verified.
