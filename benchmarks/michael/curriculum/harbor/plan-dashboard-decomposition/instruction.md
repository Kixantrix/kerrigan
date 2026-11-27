# Understand and plan: decompose dashboard milestones M2–M8 into dispatchable tasks

You are the conductor for `kerrigan-dashboard`, a local Tauri desktop app.
`spec.md` (the contract) and `plan.md` (milestones M1–M8) are written; M1
(pre-vis, task `M1.1`) is already in flight and must not be planned again.
Decompose milestones M2–M8 into tasks that can each be dispatched to one cloud
agent (one task → one issue → one PR), declare what each task touches, order
them into parallel-safe waves, route each one with the delegation rubric, and
map acceptance criteria to tests.

## Inputs (read-only)

- `planning/spec.md`, `planning/plan.md` — exact project files at this point.
  When they disagree, `spec.md` wins.
- `planning/deliverables.md` — every M2–M8 deliverable from `plan.md` with a
  stable ID, the paths `plan.md` names for it, and the consumption edges.
- `planning/repo-tree.txt` — every file in the repository at this point.
- `planning/rules/delegation-rubric.md`, `test-ladder.md`,
  `test-environment.md` — the harness rules for routing, test level and test
  environment.
- `planning/rules/conflict_predictor.py` — the repository's wave predictor;
  its `globs_overlap` defines when two touch sets conflict.

## Output: `PLAN.json` (the only writable file)

    {
      "tasks": [
        {
          "id": "<unique task id, e.g. M3.2>",
          "milestone": "M2" | ... | "M8",
          "title": "<short title>",
          "covers": ["<deliverable id>", ...],
          "touch": ["<repo-relative path or dir/**>", ...],
          "depends_on": ["<task id>", ...],
          "routing_rule": "<rubric rule id>",
          "estimate_hours": <number>,
          "tests": [{"level": "<level>", "environment": "<environment>"}, ...]
        }
      ],
      "waves": [["<task id>", ...], ...],
      "acceptance": [{"ac": "AC-NNN", "task": "<task id>", "level": "<level>", "environment": "<environment>"}],
      "mcp_tools": ["<MCP tool name>", ...]
    }

Extra keys are allowed and ignored. Order of tasks, of ids inside a wave and of
list entries is free, except that `waves` is in dispatch order.

### Tasks

- Task ids are unique non-empty strings; `milestone` is one of `M2`…`M8`.
  Do not create a task for M1; `depends_on` may name `M1.1` (it is ignored).
- Every deliverable ID in `deliverables.md` is covered by at least one task;
  `covers` uses only those IDs, and a task covers only deliverables of its
  own milestone.
- `plan.md` says every milestone after M1 decomposes into multiple tasks:
  each of M2–M8 has at least two tasks.
- Size: each task covers 1–3 deliverables, has 1–8 `touch` entries and an
  `estimate_hours` number greater than 0 and at most 6.
- `tests` lists at least one test for the task's "done" condition; every
  entry uses the closed vocabularies below, and at least one entry has an
  environment other than `manual-human`.

### Touch sets

- Each entry is either a concrete repo-relative file path or a directory
  followed by `/**`. No other wildcards, no leading `/` or `./`, no `..`, no
  backslashes, no whitespace.
- New files may only be created under `apps/kerrigan-dashboard/`,
  `tools/kerrigan-mcp/`, or as `.github/workflows/dashboard-build.yml`. Every
  other entry must name a file (or, for `dir/**`, a directory) that exists in
  `repo-tree.txt`.
- For every deliverable with a "Required touch" in `deliverables.md`, each
  task covering it has touch entries that overlap every listed path
  ("something under `tools/kerrigan-mcp/`" means an entry overlapping
  `tools/kerrigan-mcp/**`).
- Overlap is `globs_overlap` from `conflict_predictor.py`: two entries overlap
  when either matches the other under `fnmatch`.

### Dependencies and waves

- `depends_on` names task ids from this plan (or `M1.1`); no task depends on
  itself.
- For every consumption edge `A → B` in `deliverables.md`, every task covering
  B (that does not also cover A) depends on every task covering A, directly or
  transitively through `depends_on`.
- `waves` contains every task exactly once and nothing else. Each task is in a
  later wave than every task it depends on, and no two tasks in the same wave
  have overlapping touch entries.
- Use as few waves as the constraints allow: no task may be placeable in an
  earlier wave, i.e. for every earlier wave either one of its dependencies is
  in that wave or later, or it overlaps a task already in that wave. The plan
  has at most 10 waves.

### Routing

- `routing_rule` is a rule ID defined in `delegation-rubric.md`
  (`R-cloud-default` when no other rule fires).
- A task whose `covers` contains only pure-logic deliverables (`M3-D1`
  parser, `M3-D3` status mapper) cites `R-cloud-default`.
- A task owning an acceptance entry whose environment is `local-attested-*`
  cites a rule starting with `R-local`.

### Acceptance criteria

- `acceptance` maps exactly the ACs listed on the "Acceptance" lines of
  milestones M2–M8 in `plan.md` (each at least once, no others). Each entry's
  `task` is a task in a milestone whose Acceptance line lists that AC. At most
  one entry per (AC, task) pair.
- `level` is one of `unit`, `integration`, `smoke`, `e2e`, `scenario`
  (`test-ladder.md`). `environment` is one of `cloud-linux`, `cloud-windows`,
  `cloud-macos`, `cloud-self-hosted-<name>`, `local-attested-<class>`,
  `manual-human` (`test-environment.md`), where `<name>`/`<class>` is lowercase
  letters, digits and hyphens.
- Test-ladder classification used for grading: AC-008 and AC-012 are
  pure-logic ACs (never `e2e` or `scenario`); AC-003, AC-006 and AC-007 are
  interface-driven user flows (always `e2e`).
- `scenario` is only used with a `local-attested-*` or `manual-human`
  environment. AC-001 through AC-017 all have automatable test oracles, so
  none of their entries uses `manual-human`.

### MCP tools

- `mcp_tools` lists exactly the MCP tool names your tasks implement in
  `tools/kerrigan-mcp/`, written as in `spec.md` (e.g. `kerrigan.dispatch`).
  It must respect the v1 tool scope that `spec.md` sets.

## Grading

Everything above is checked deterministically from `PLAN.json` against the
provided inputs. Not graded: titles, the wording of anything, which valid
decomposition you choose, extra keys, dependencies beyond the required ones
(as long as wave rules hold), routing choices other than the rules stated
under Routing, and test levels other than the classification stated above.
Rules in the skill files that this file does not restate (for example routing
or level justifications, or presence of an environment in a project manifest)
are guidance only and are not graded.

Read/write and tool/network boundaries are in policy.json. No network,
history or other repository files are available.


---
Work in `/app`. Only `/app/PLAN.json` is collected for grading (declared artifact); the verifier runs separately with no network.
