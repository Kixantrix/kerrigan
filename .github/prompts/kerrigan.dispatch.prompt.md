---
mode: agent
description: "Orchestrate wave-aware GitHub issue dispatch: conflict-predictor → briefing-generator → taskstoissues, with prereq checks and per-wave gating."
---

# /kerrigan.dispatch

Orchestrate a wave-aware, briefing-attached GitHub issue dispatch for the current feature.

## What you will do

1. **Run conflict predictor** → `.specify/waves.yaml`
2. **Run briefing generator** → `.specify/briefings/<task-id>.md`
3. **Dispatch issues wave-by-wave** — wave 1 first; wave 2+ only after wave 1 PRs are merged (unless `--force` is passed)
4. **Check prereq artifacts** before each task — refuse to dispatch if a declared prereq file is absent from its `base_branch`
5. **Attach briefings** to each issue body

## Arguments

```
[--force]          Skip the wave-merge gate (dispatch all waves immediately)
[--task TASK_ID]   Dispatch a single task only (e.g. --task T-001)
```

## Step-by-step

### 1 — Locate files

Confirm `tasks.md` and `plan.md` exist (search from repo root). Stop with a clear error if either is missing.

### 2 — Run conflict predictor

```bash
python tools/conflict_predictor.py --tasks <tasks_path> --output .specify/waves.yaml
```

On non-zero exit: print the full stderr and abort. Do not continue.

Report the wave plan once written.

### 3 — Run briefing generator

```bash
python tools/briefing_generator.py \
  --plan <plan_path> \
  --tasks <tasks_path> \
  --output-dir .specify/briefings
```

Add `--task <TASK_ID>` if the `--task` argument was supplied.

On non-zero exit: print the full stderr and abort. Do not continue.

### 4 — Verify GitHub remote

```bash
git config --get remote.origin.url
```

Stop if the remote is not a GitHub URL.

> [!CAUTION]
> UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL.

### 5 — Dispatch waves (in order)

For each wave (or the single requested task):

#### 5a — Wave-merge gate

Before wave N (N > 1), check that all wave N-1 PRs are merged. If any are still open **and `--force` was not supplied**:

```
WAVE GATE: Wave <N-1> has open PRs — wave <N> will not dispatch until they merge.
Open PRs:  #<number> (<task-id>): <title>
To override: rerun with --force
```

Stop. Do not dispatch wave N or later waves.

#### 5b — Prereq-artifact check

For each task, check each entry in its `prereq_artifacts` list (from `waves.yaml`, if present):

```bash
git cat-file -e <base_branch>:<path>
```

If the exit code is non-zero (file not on branch):

1. Write `.specify/blocks/<task-id>.yaml` with `reason: prereq-missing` (see block schema in `.github/skills/block-report/SKILL.md`).
2. Report the block to the user.
3. Skip this task — continue with the next.

#### 5c — Create issue

For each non-blocked task, create a GitHub issue via the GitHub MCP server:

- **title**: `<task-id>: <description>`
- **body**: full content of `.specify/briefings/<task-id-lowercase>.md`
- **labels**: `agent:go` (if the label exists)

Surface any creation error immediately — do not swallow.

### 6 — Summary

Print a final summary listing dispatched issues, held waves, and blocked tasks.

## Error-handling rules

- Non-zero exit from any sub-tool → print full stderr → abort (for tool failures) or skip task (for prereq failures).
- Never swallow errors.
- Prereq failures are task-scoped: one blocked task does not abort the whole wave.
- Wave gate is wave-scoped: stop dispatching further waves but still summarize what was dispatched.
