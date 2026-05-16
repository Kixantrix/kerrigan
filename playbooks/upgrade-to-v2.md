# Playbook: Upgrade a satellite repo to Kerrigan v2

> For `personal-selfhost`, `vhs-video-stack`, and other repos that use Kerrigan dispatch conventions while keeping their own product codebase.

Use this after the initial bootstrap in [`playbooks/v2-bootstrap.md`](./v2-bootstrap.md). The goal is to remove v1-only surfaces, adopt the `local` + `cloud` profiles, and prove that dispatch works with v2 primitives only.

## 1. Pre-flight

- [ ] Confirm the repo already has the v2 bootstrap files from [`playbooks/v2-bootstrap.md`](./v2-bootstrap.md): `AGENTS.md`, `.github/agents/`, `.github/skills/`, `.claude/agents/`, validators.
- [ ] Inventory v1 carry-overs before deleting anything:
  - old role agents in `.github/agents/role.*.md`
  - v1-only workflows such as `agent-gates.yml`, `auto-grant-autonomy.yml`, `auto-ready-pr.yml`, `auto-trigger-dependents.yml`, `daily-self-improvement.yml`
  - custom dispatch scripts or wrappers
  - v1 labels still used by humans or automation
- [ ] Make sure the satellite has one human owner who can answer migration blocks during the first dispatch test.
- [ ] Keep the migration scoped to repo docs, labels, workflows, and agent/runtime setup. Do **not** rewrite project code as part of this playbook (for example: agent docs and CI wiring are in scope; application features and business logic are not).

### Satellite notes

- **`personal-selfhost`**: identify and plan to remove its `claude-dispatch.sh` fork. v2 should dispatch through the standard `cloud` profile instead of a repo-specific shell wrapper.
- **`vhs-video-stack`**: identify any batch-merge or cascade-merge habits. v2 expects wave-based dispatch, conflict prediction, and structured blocks instead of merge queues hidden in custom process.
- **Future satellites**: if a repo has extra wrappers, map each one to a v2 primitive before deleting it: profile, skill, hook, block, validator, or workflow.

## 2. Install v2 runtime and profiles

- [ ] Run the bootstrap flow from [`playbooks/v2-bootstrap.md`](./v2-bootstrap.md) if the repo has not already pulled the latest v2 files.
- [ ] Mirror agent profiles for Claude Code with `pwsh scripts/mirror-agents.ps1`.
- [ ] Validate the install with `python tools/validators/agents_md.py`.
- [ ] Confirm humans know the new runtime split:
  - `local` plans, routes, and surfaces blocks
  - `cloud` implements one task slice in an isolated PR
  - Claude Code is the primary local runtime

### `personal-selfhost`

- [ ] Delete the `claude-dispatch.sh` fork after the standard v2 files are present.
- [ ] Replace any README or team habit that says "run the forked dispatch script" with "talk to the `kerrigan` profile (for example in Claude Code or VS Code chat), which dispatches to `cloud` when the delegation rubric allows it."
- [ ] Use Claude Code for local planning and human-in-the-loop steps; use the `cloud` profile for task execution instead of shelling out to a custom dispatch wrapper.

### `vhs-video-stack`

- [ ] Remove local instructions that imply agents should stack PRs and batch-merge them manually.
- [ ] Re-orient contributors around planning with `local`, generating ordered tasks, then dispatching safe work in waves.

## 3. Migrate labels

- [ ] Add the four v2 labels from [`AGENTS.md`](../AGENTS.md):
  - `agent:go`
  - `agent:wait`
  - `agent:local`
  - `autonomy:override`
- [ ] Leave old labels in place only long enough to update automation and docs.
- [ ] Update any saved searches, triage notes, or issue templates that still refer to v1 labels.
- [ ] After the first successful v2 dispatch, remove v1 labels that no longer drive automation.

### Label mapping guidance

- Use **`agent:go`** when the agent can proceed autonomously.
- Use **`agent:wait`** when a human decision is required.
- Use **`agent:local`** when the task must run on the human's machine.
- Use **`autonomy:override`** only when a human intentionally bypasses a normal gate.

## 4. Retire v1 workflows and custom dispatch surfaces

- [ ] Remove or archive v1 workflows replaced by `verify.yml` + branch protection:
  - `agent-gates.yml`
  - `auto-grant-autonomy.yml`
  - `auto-ready-pr.yml`
  - `auto-trigger-dependents.yml`
  - `daily-self-improvement.yml`
- [ ] Confirm the remaining workflow surface matches v2 assumptions: validators, tests, smoke checks, and PR review.
- [ ] Delete repo-specific dispatch glue once its v2 equivalent is in place.

### `personal-selfhost`

- [ ] Remove the `claude-dispatch.sh` fork from the repo and any docs that point to it.
- [ ] If the fork encoded routing behavior, move that behavior to the standard v2 routing flow instead of replacing it with another script.

### `vhs-video-stack`

- [ ] Retire any process that depends on batch-merging multiple agent PRs in one sweep.
- [ ] Switch dispatch planning to wave-based execution so only non-conflicting tasks move in parallel.
- [ ] Use the conflict predictor before parallel dispatch rather than resolving "cascade merge" fallout afterward.

## 5. Test dispatch with v2 primitives

- [ ] Pick one low-risk task and run it end-to-end with v2 only.
- [ ] Start from the `kerrigan` profile and have it plan, route, and dispatch.
- [ ] Verify the task routes by capability, not by old repo role names.
- [ ] Confirm the result opens one reviewable PR, not a stacked or batch-merged bundle.
- [ ] If the task blocks, require a structured block file instead of ad-hoc chat instructions.

### Dispatch test expectations

- **`personal-selfhost`** passes when it completes a task without `claude-dispatch.sh`, using Claude Code locally and the `cloud` profile for remote execution.
- **`vhs-video-stack`** passes when it dispatches by wave, uses conflict prediction up front, and avoids the old batch-merge/cascade-rebase loop.

## Key v2 reference documents (Phase 3 artifacts)

These Phase 3 "trustworthy autonomy" references are the ones most likely to answer "why did the agent route or block this way?":

- [Delegation rubric](../specs/kerrigan-v2/050-delegation-rubric.md) — capability taxonomy and routing rules for `local` vs `cloud`
- [Block schema](../.specify/schemas/block.schema.json) — machine-readable contract for `.specify/blocks/<task-id>.yaml`
- [Block-report skill](../.github/skills/block-report/SKILL.md) — practical block shape and authoring rules
- [Claude Code hooks](../.claude/hooks/README.md) — `PreToolUse` guard, `Stop` verify chain, and repo-level hook configuration

## Troubleshooting

**The repo still depends on a custom dispatch script.**  
Do not port the script forward unchanged. First identify which v2 primitive replaces each behavior: `local`/`cloud` routing, labels, hooks, briefing packets, or blocks. Delete the wrapper once those are in place.

**Humans keep using v1 labels out of habit.**  
Update issue templates, saved views, and team docs first; then remove the old labels after the first successful v2 run.

**Claude Code does not see the mirrored agents.**  
Re-run `pwsh scripts/mirror-agents.ps1`, then confirm `.claude/agents/` points at the shared profile files.

**A task that should be local gets sent to cloud.**  
Check the [delegation rubric](../specs/kerrigan-v2/050-delegation-rubric.md) and make sure the task description explicitly mentions the required local capability (`device-io.*`, `os.*`, `paid-service.*`, or `human-judgment`).

**A blocked task produced ad-hoc notes instead of a structured block.**  
Require the agent instructions or review gate to enforce emission of `.specify/blocks/<task-id>.yaml` that matches the [block schema](../.specify/schemas/block.schema.json) and the [block-report skill](../.github/skills/block-report/SKILL.md).

**Parallel dispatch creates merge conflicts.**  
Do not fall back to batch merge. Re-plan the work as waves and use the conflict predictor before dispatching concurrent tasks.

**The repo removed v1 workflows but lost safety checks.**  
Before deleting more automation, make sure the v2 replacement is present: validators, smoke test, `verify` workflow, branch protection, and Copilot review where applicable.
