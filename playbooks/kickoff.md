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

Use [session operations](session-operations.md): direct app sessions are primary, with an explicit `cloud` executor on a capability-appropriate host. `kerrigan` carries the accepted outcome forward:

1. Run the file-conflict predictor and also check shared device/process resources.
2. Generate a briefing per coherent slice in `.specify/briefings/<task-id>.md`, with ownership/base/dependency/stop-condition addendum.
3. Start bounded worker sessions and obtain acknowledgment before implementation.
4. Keep routine questions, blockers, and verified completion accountable to the coordinator.

The optional issue adapter `/kerrigan.dispatch` (wraps `/speckit.taskstoissues`) still creates issues and assigns `@copilot` in parallel-safe waves. Each accepted slice has one implementation owner, one branch, and one PR; the worker never edits scope. Existing gates are unchanged.

## 4) Resolve blocks

When a `cloud` task emits `.specify/blocks/<task-id>.yaml`, `kerrigan` resolves routine decisions from evidence/options and surfaces only meaningful direction, risk, privacy, authority, or material unapproved-cost decisions. Unrelated tasks keep moving.

## 5) Human approvals

Humans verify **direction and spec alignment**, not technical quality (CI + Copilot review handle that). Touch points:

- Approve scope / non-goals in `spec.md` (or the tinyspec equivalent).
- Approve architectural decisions before they merge.
- Approve `autonomy:override` exceptions to default-cautious routing.

See [`AGENTS.md`](../AGENTS.md#auto-mode-guidance) for when to require `acceptEdits` vs `auto`.
