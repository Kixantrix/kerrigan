# Cloud-agent PR loop

This playbook standardizes the recurring dispatch/review/merge loop for cloud-agent PRs.

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

- `tools/pr-doctor.ps1` — one-shot PR diagnostics (state, checks, action_required runs, thread counts, last review). Example: `./tools/pr-doctor.ps1 270`
- `tools/pr-resolve-threads.ps1` — list and resolve unresolved review threads (supports `-DryRun` and confirmation). Example: `./tools/pr-resolve-threads.ps1 270 -DryRun`
- `tools/pr-rerun-pending.ps1` — rerun stalled workflow runs where conclusion is `action_required`. Example: `./tools/pr-rerun-pending.ps1 270`
- `tools/pr-redispatch.ps1` — post a multi-line re-dispatch comment and re-arm auto-merge. Example: `./tools/pr-redispatch.ps1 270`

## Common stalls and how to clear them

- **Workflow stalled in `action_required`**
  - Symptom: checks never move even though the PR branch has a recent agent push.
  - Clear: run `./tools/pr-rerun-pending.ps1 <pr-number>`.

- **Auto-merge silently dropped**
  - Symptom: all checks are green but PR remains open with no merge queued.
  - Clear: run `./tools/pr-redispatch.ps1 <pr-number>` (or `gh pr merge <pr> --auto --squash`) to re-arm auto-merge.

- **Unresolved review threads block merge**
  - Symptom: CI is green but merge never executes.
  - Clear: inspect with `./tools/pr-doctor.ps1 <pr-number>` and resolve threads via `./tools/pr-resolve-threads.ps1 <pr-number>`.
