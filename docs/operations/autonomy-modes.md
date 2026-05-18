# Autonomy modes

Goal: allow agents to open PRs directly when helpful, while retaining an easy "pause / on-demand" switch.

## v2 Workflow Coverage

**v2** replaces several v1 automation workflows with consolidated infrastructure:

| Replaced (v1) | Replaced by (v2) |
|---|---|
| `agent-gates.yml` | `verify.yml` + branch protection rules |
| `auto-grant-autonomy.yml` | Label-based automation in `verify.yml` |
| `auto-ready-pr.yml` | Branch protection auto-merge settings |
| `auto-trigger-dependents.yml` | Wave-based dispatch (`kerrigan dispatch`) |
| `daily-self-improvement.yml` | `kerrigan check` cron (when configured) |

See [`verify.yml`](../../.github/workflows/verify.yml) for the current enforcement workflow.

## Automation Features

Kerrigan includes automation workflows to reduce manual intervention:
- **Auto-assign reviewers**: Based on role labels (role:swe, role:testing, etc.)
- **Auto-assign issues**: Issues with role labels auto-assign to configured users
- **Auto-generate issues**: Create issues from tasks.md with `<!-- AUTO-ISSUE -->` markers

See `.github/automation/README.md` for setup instructions.

## Mode A — On-demand (recommended default)
- Agents may only open PRs when the linked issue is labeled `agent:go`.
- If not labeled, CI fails with an autonomy gate message.

## Mode B — Autonomous sprint
- Label a single tracking issue/milestone as `agent:sprint`.
- Agents may open PRs referencing that tracking issue until the milestone is met.
- After the milestone PR merges, agents should stop.
- **Automation**: PRs linked to sprint issues automatically receive `agent:go` label.

## Mode C — Hybrid
- Spec + Architecture roles may propose PRs anytime.
- SWE/Testing/Deployment require `agent:go`.

## Overrides
- Add PR label `autonomy:override` (human-only) to bypass the gate.
- Add PR label `allow:large-file` to bypass large-file checks (use sparingly).

## Implementation details

Autonomy-mode enforcement is handled by branch protection rules and `.github/workflows/verify.yml`. The `verify.yml` workflow runs validators (`kerrigan check`) on every PR targeting `main`.

Labels used:
- **`agent:go`**: grants an agent permission to open/merge a PR for the linked issue
- **`agent:sprint`**: marks a tracking issue as an active sprint; agents may open PRs referencing it
- **`autonomy:override`**: human-only label that bypasses autonomy checks on a PR
- **`allow:large-file`**: bypasses the quality-bar large-file check (use sparingly)
