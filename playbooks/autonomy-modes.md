# Autonomy modes

Goal: allow agents to open PRs directly when helpful, while retaining an easy “pause / on-demand” switch.

## Mode A — On-demand (recommended default)
- Agents may only open PRs when the linked issue is labeled `agent:go`.
- If not labeled, CI fails with an autonomy gate message.

## Mode B — Autonomous sprint
- Label a single tracking issue/milestone as `agent:sprint`.
- Agents may open PRs referencing that tracking issue until the milestone is met.
- After the milestone PR merges, agents should stop.

## Mode C — Hybrid
- Spec + Architecture roles may propose PRs anytime.
- SWE/Testing/Deployment require `agent:go`.

## Overrides
- Add PR label `autonomy:override` (human-only) to bypass the gate.
- Add PR label `allow:large-file` to bypass large-file checks (use sparingly).

Implementation details live in `.github/workflows/agent-gates.yml` and `tools/validators/`.
