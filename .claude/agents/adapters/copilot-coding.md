# Adapter: GitHub Copilot coding agent

**Runtime:** GitHub (cloud, Actions-backed ephemeral container).
**Invocation:** An issue assigned to `@copilot`, or `/speckit.taskstoissues`, or `/kerrigan.dispatch`.
**Writes:** One branch, one PR per session.

## Use when

This is the default target of the `cloud` profile. Don't invoke it directly in most cases — dispatch through `/kerrigan.dispatch` so you get the briefing-packet + conflict-predictor path.

Direct invocation (bypass) is fine for one-off small tasks where the briefing overhead isn't worth it.

## How the `cloud` profile uses it

1. `local` profile generates a briefing packet.
2. `/kerrigan.dispatch` (or `/speckit.taskstoissues`) creates a GH issue with the briefing in the body and assigns `@copilot`.
3. Copilot coding agent spins up an ephemeral container, checks out a new branch, reads the issue (which includes `AGENTS.md` + briefing).
4. Our `.github/agents/cloud.md` is loaded as a custom agent — it tells Copilot to treat the briefing as its scope, self-verify, and open one PR.
5. The PR flows into the distributed verification chain.

## One issue, one branch, one PR

Don't try to make Copilot coding agent do multiple tasks in one session. If you need multi-task work, dispatch multiple tasks. That's what the conflict predictor is for.

## Limits you should know

- No rebase. If the PR goes stale, the `kerrigan-auto-rebase` workflow (Phase 2) comments `@copilot rebase` or dispatches a fresh task.
- One PR per issue — if the PR is wrong, you dispatch a replacement, you don't iterate the same PR forever.
- Paid premium requests are counted. Budget is surfaced as a sticky PR comment (Phase 3).
