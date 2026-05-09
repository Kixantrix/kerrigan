---
name: kerrigan-dispatch
description: "Orchestrate wave-aware GitHub issue dispatch: run conflict-predictor → briefing-generator → taskstoissues, with prereq-artifact checks and per-wave gating."
argument-hint: "Optional: --force (skip wave-merge gate), --task TASK_ID (dispatch single task)"
compatibility: "Requires spec-kit project structure with .specify/ directory, tasks.md, and plan.md"
metadata:
  author: kerrigan
  source: .claude/skills/kerrigan-dispatch/SKILL.md
user-invocable: true
disable-model-invocation: false
---

## User Input

```text
$ARGUMENTS
```

Parse arguments from user input:
- `--force` — skip the wave-merge gate (wave N+1 dispatches even if wave N PRs are not yet merged)
- `--task TASK_ID` — dispatch a single task only (e.g. `--task T-001`)

You **MUST** consider user input before proceeding.

---

## Overview

`/kerrigan.dispatch` is a thin orchestration wrapper over `/speckit-taskstoissues`. It adds:

1. **Conflict prediction** — groups tasks into parallel-safe waves via `tools/conflict_predictor.py`
2. **Briefing generation** — creates per-task briefing packets via `tools/briefing_generator.py`
3. **Prereq-artifact checks** — refuses to dispatch a task whose declared `prereq_artifacts` don't exist on its `base_branch` yet
4. **Wave-aware gating** — dispatches wave 1, then waits for wave 1 PRs to merge before dispatching wave 2 (unless `--force`)

---

## Step 1 — Locate required files

Run the prerequisites check and locate `tasks.md` and `plan.md`:

```bash
python .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks 2>/dev/null \
  || python .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks 2>/dev/null \
  || echo '{"feature_dir": ".", "tasks": "tasks.md"}'
```

Fall back to `tasks.md` and `plan.md` in the repo root if the script is unavailable. All paths must be absolute.

Confirm both files exist before proceeding. If either is missing, stop and report:

```
ERROR: <file> not found. Run /speckit-tasks first to generate tasks.md.
```

---

## Step 2 — Run conflict predictor

```bash
python tools/conflict_predictor.py --tasks <tasks_path> --output .specify/waves.yaml
```

**On non-zero exit:** stop immediately and surface the full stderr output:

```
ERROR: conflict_predictor.py failed with exit code <N>:
<stderr output>
Dispatch aborted. Fix the error above and retry.
```

**On success:** read `.specify/waves.yaml`. It has the structure:

```yaml
waves:
  - wave: 1
    tasks: [T-001, T-002]
    depends_on_artifacts_from: []   # optional — list of paths that must exist on base_branch
  - wave: 2
    tasks: [T-003]
    depends_on_artifacts_from: []
```

Report the wave plan:

```
Wave plan written to .specify/waves.yaml:
  Wave 1: T-001, T-002  (parallel)
  Wave 2: T-003
```

If `--task` was supplied, verify the task appears in the wave plan. If it does not, warn the user and proceed anyway (the task will be dispatched as a single-task wave).

---

## Step 3 — Run briefing generator

```bash
python tools/briefing_generator.py \
  --plan <plan_path> \
  --tasks <tasks_path> \
  --output-dir .specify/briefings
```

If `--task` was supplied, add `--task <TASK_ID>`.

**On non-zero exit:** stop immediately and surface the full stderr output:

```
ERROR: briefing_generator.py failed with exit code <N>:
<stderr output>
Dispatch aborted. Fix the error above and retry.
```

**On success:** list the generated briefing files:

```
Briefings generated:
  .specify/briefings/t-001.md
  .specify/briefings/t-002.md
  .specify/briefings/t-003.md
```

---

## Step 4 — Get Git remote

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> ONLY PROCEED TO NEXT STEPS IF THE REMOTE IS A GITHUB URL.
> UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL.

---

## Step 5 — Dispatch waves

Process waves in order (wave 1 first, wave 2 after, etc.). If `--task` was supplied, only dispatch that task.

For **each wave**:

### 5a — Wave-merge gate (AC-9)

Before dispatching wave N (where N > 1), check whether all PRs from wave N-1 have been merged.

- Query open PRs in the repository that were created by the previous wave's issue dispatch. Look for PRs whose title or body references the wave N-1 task IDs.
- If any wave N-1 PR is still open **and** `--force` was **not** supplied:

  ```
  WAVE GATE: Wave <N-1> has open PRs — wave <N> will not dispatch until they merge.
  Open PRs:  #<number> (<task-id>): <title>
  
  To override: rerun with --force
  Halting dispatch after wave <N-1>.
  ```

  Stop here. Do not dispatch wave N or later waves.

- If `--force` was supplied, skip the gate and proceed.

### 5b — Prereq-artifact check per task (AC-7, AC-8)

For each task in the current wave, read the task's wave entry for a `prereq_artifacts` list. The `prereq_artifacts` field (if present) is a list of objects:

```yaml
prereq_artifacts:
  - path: src/models/user.py
    base_branch: main
```

For each prereq artifact, verify it exists on the declared `base_branch`:

```bash
git cat-file -e <base_branch>:<path> 2>/dev/null
```

If the command exits non-zero (file not found on branch):

1. Emit a block file at `.specify/blocks/<task-id>.yaml`:

   ```yaml
   task_id: <task-id>
   emitted_by: kerrigan
   emitted_at: <ISO-8601 UTC timestamp>
   reason: prereq-missing
   severity: high
   summary: "Prereq artifact '<path>' not found on branch '<base_branch>'."
   details: |
     The task declares that '<path>' must exist on '<base_branch>' before dispatch.
     Run `git cat-file -e <base_branch>:<path>` to verify.
     This typically means the PR that creates this file has not been merged yet.
   decision_needed: |
     Merge the PR that creates '<path>' into '<base_branch>', then re-run /kerrigan.dispatch.
     Or override the base_branch for this task if the path will land on a different branch.
   options:
     - id: A
       description: "Merge the prerequisite PR into <base_branch>, then rerun /kerrigan.dispatch."
       implication: "Dispatch proceeds in the correct order."
     - id: B
       description: "Rerun with --force to skip this check."
       implication: "Issue is created but the cloud agent may fail if the file is absent."
   recommendation: A
   minimum_human_input: "Merge the prerequisite PR or confirm --force override."
   ```

2. Report to the user:

   ```
   BLOCKED: <task-id> — prereq artifact '<path>' not found on '<base_branch>'.
   Block written to .specify/blocks/<task-id>.yaml
   Skipping <task-id>; continuing with remaining tasks.
   ```

3. Skip this task (do not create a GitHub issue for it). Continue with the next task.

### 5c — Create GitHub issue (AC-5)

For each non-blocked task, read its briefing packet from `.specify/briefings/<task-id-lowercase>.md`.

Create a GitHub issue using the GitHub MCP server with:

- **title**: `<task-id>: <task description>`
- **body**: the full content of the briefing packet (`.specify/briefings/<task-id-lowercase>.md`)
- **labels**: `agent:go` (if the label exists in the repository)

Report each created issue:

```
Created issue #<number>: <task-id> — <title>
```

If issue creation fails, surface the error immediately:

```
ERROR: Failed to create issue for <task-id>: <error message>
```

Do not swallow errors. If any issue fails to create, report it and continue with the remaining tasks.

---

## Step 6 — Summary report

After all waves are processed, print a summary:

```
/kerrigan.dispatch complete.

Wave 1 (dispatched):
  ✓ #<n>  T-001 — <title>
  ✓ #<n>  T-002 — <title>

Wave 2 (held — wave 1 PRs still open):
  ⏸  T-003 — waiting for wave 1 PRs to merge

Blocked (prereq missing):
  ✗  T-004 — .specify/blocks/t-004.yaml

Rerun /kerrigan.dispatch (or /kerrigan.dispatch --force) when wave 1 PRs are merged.
```

---

## Error-handling rules

1. **Never swallow errors.** If any sub-tool exits non-zero, print the full stderr and abort the current operation.
2. **Prereq failures are task-scoped.** A single blocked task does not abort the whole wave — skip it and continue.
3. **Wave gate is dispatch-scoped.** If the gate fires, stop dispatching further waves but still summarize what was dispatched.
4. **Tool not found.** If `tools/conflict_predictor.py` or `tools/briefing_generator.py` is not found, emit:

   ```
   ERROR: <tool> not found. Ensure you are running from the repo root and the tools/ directory exists.
   Dispatch aborted.
   ```
