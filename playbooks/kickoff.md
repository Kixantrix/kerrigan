# Kickoff playbook (start a new project)

> v2 flow. See [`AGENTS.md`](../AGENTS.md) for the canonical agent entry point.

## 0) Decide routing

Default: **cloud**. Use the delegation rubric (`.github/skills/delegation-rubric/SKILL.md`) to decide whether the work must run locally (`agent:local`) instead — device I/O, OS-specific, paid secrets the cloud doesn't have, or human judgment in-the-loop.

## 1) Create project folder

Create: `specs/projects/<project-name>/`

Spec Kit will populate the standard artifacts. The minimal living set is:
- `plan.md` (always)
- `tasks.md` (always)
- `spec.md` (use `spec-kit-tinyspec` for small work; full `/speckit.specify` for larger)

Other artifacts (`architecture.md`, `acceptance-tests.md`, `test-plan.md`, `runbook.md`, `cost-plan.md`, `status.json`) are added only when they earn their place.

## 2) Run spec-kit through `kerrigan`

Chat with the `kerrigan` profile and drive the standard Spec Kit commands:

1. `/speckit.specify` — what to build (skip for small work).
2. `/speckit.clarify` — only when ambiguity is real.
3. `/speckit.plan` — how to build.
4. `/speckit.tasks` — actionable, dependency-ordered tasks.
5. `/speckit.analyze` — cross-artifact consistency check.

## 3) Dispatch

Ask `kerrigan` to run `/kerrigan.dispatch` (wraps `/speckit.taskstoissues`). It will:

1. Run the conflict predictor → write `.specify/waves.yaml`.
2. Generate one briefing packet per task in `.specify/briefings/<task-id>.md`.
3. Open one GitHub issue per task, labelled `agent:go`.
4. Assign `@copilot` to issues in the first parallel-safe wave.

Each cloud task: one issue → one branch → one PR. Never edits scope.

## 4) Resolve blocks

When a `cloud` task emits `.specify/blocks/<task-id>.yaml`, `kerrigan` surfaces the block with the minimum human input needed. Unrelated tasks keep moving.

## 5) Human approvals

Humans verify **direction and spec alignment**, not technical quality (CI + Copilot review handle that). Touch points:

- Approve scope / non-goals in `spec.md` (or the tinyspec equivalent).
- Approve architectural decisions before they merge.
- Approve `autonomy:override` exceptions to default-cautious routing.

See [`AGENTS.md`](../AGENTS.md#auto-mode-guidance) for when to require `acceptEdits` vs `auto`.
