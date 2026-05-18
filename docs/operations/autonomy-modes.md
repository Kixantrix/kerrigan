# Autonomy modes

Kerrigan v2 uses a single operating mode.

## Execution gate

Cloud execution is opt-in per issue: the linked issue must carry `agent:go` before a cloud agent should implement and open a PR.

## Merge gate (review response flow)

After a cloud PR is opened, merge is gated by required review-thread resolution in branch protection. In practice, kerrigan reviews `@copilot` PR comments, asks the cloud agent to push fixes to the same branch, and resolves threads until merge can proceed.

See [`.github/agents/kerrigan.md` — "Review response flow"](../../.github/agents/kerrigan.md#review-response-flow).
