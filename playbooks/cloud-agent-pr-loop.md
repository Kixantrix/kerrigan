# Cloud-agent PR loop

Use this playbook for the recurring cloud-agent PR loop after a cloud push.

## Lifecycle

```text
dispatch
  -> cloud push
  -> action_required
  -> rerun
  -> CI green
  -> Copilot review
  -> resolve threads
  -> auto-merge
```

## Helper scripts

- `tools/pr-doctor.ps1 <pr-number>`: one-shot PR diagnostic snapshot.
  - Example: `./tools/pr-doctor.ps1 270`
- `tools/pr-resolve-threads.ps1 <pr-number>`: list and resolve unresolved review threads.
  - Example: `./tools/pr-resolve-threads.ps1 270 -Confirm:$false`
- `tools/pr-rerun-pending.ps1 <pr-number>`: rerun workflow runs stuck with `action_required`.
  - Example: `./tools/pr-rerun-pending.ps1 270`
- `tools/pr-redispatch.ps1 <pr-number>`: post redispatch comment and re-arm auto-merge.
  - Example: `./tools/pr-redispatch.ps1 270`

## Common stalls and how to clear them

### 1) `action_required` runs

Symptom: CI appears idle, but checks are blocked.

Clear:

1. Run `./tools/pr-doctor.ps1 <pr>`.
2. Confirm runs listed in the `ACTION_REQUIRED WORKFLOW RUNS` section.
3. Run `./tools/pr-rerun-pending.ps1 <pr>` to rerun those runs.

### 2) Dropped auto-merge

Symptom: checks are green but PR is not merging.

Clear:

1. Re-arm auto-merge with `gh pr merge <pr> --auto --squash`.
2. Or run `./tools/pr-redispatch.ps1 <pr>` (posts comment + re-arms).

### 3) Unresolved review threads silently blocking merge

Symptom: all checks are green but merge still waits.

Clear:

1. Run `./tools/pr-doctor.ps1 <pr>` to see resolved vs unresolved counts.
2. Run `./tools/pr-resolve-threads.ps1 <pr> -DryRun` to preview unresolved threads.
3. Resolve with `./tools/pr-resolve-threads.ps1 <pr>`.

## Quick loop checklist

1. Diagnose: `./tools/pr-doctor.ps1 <pr>`
2. Rerun blocked workflows: `./tools/pr-rerun-pending.ps1 <pr>`
3. Re-dispatch critical feedback: `./tools/pr-redispatch.ps1 <pr>`
4. Resolve advisory/handled threads: `./tools/pr-resolve-threads.ps1 <pr>`
5. Verify auto-merge remains armed after updates.
