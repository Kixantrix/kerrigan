# Specs

Governing documents and specifications for all work in this repository. Start at the [canonical entry point](../AGENTS.md) for the full agent lifecycle; this folder holds the source-of-truth artifacts.

## Quick reference

| Location | Purpose |
|----------|---------|
| [`constitution.md`](constitution.md) | Non-negotiable principles for all work |
| [`kerrigan-v2/`](kerrigan-v2/) | Active meta-specs: vision, phases, delegation rubric (why the harness works the way it does) |
| [`kerrigan/_archive-v1/`](kerrigan/_archive-v1/) | v1 meta-specs, retained for history |
| [`projects/`](projects/) | Per-project artifacts (`spec.md`, `plan.md`, `tasks.md`, etc.) |
| [`projects/_archive/`](projects/_archive/) | Completed / superseded project artifacts |

Adjacent (not under `specs/`):

| Location | Purpose |
|----------|---------|
| [`../.github/agents/`](../.github/agents/) | v2 agent profiles (`kerrigan.md`, `cloud.md`) + adapters to built-in sub-agents |
| [`../.github/skills/`](../.github/skills/) | Reusable agent skills (agent-skills spec) |
| [`../docs/`](../docs/) | Human-facing documentation |
| [`../playbooks/`](../playbooks/) | Step-by-step operational guides |

## Constitution

[`constitution.md`](constitution.md) defines the highest-level principles. Every other artifact in this folder — and every PR — must align with it.

Short version:

1. Artifact-driven — work lives in repo files.
2. Small, reviewable increments — one task, one PR.
3. Tests included — every AC maps to an automated test.
4. Stack-agnostic — no mandatory language/framework.
5. Agent clarity — agents cite the rule they followed; humans decide ambiguities.
6. Human-in-loop for decisions; agents-in-loop for execution.

## Meta-specs: how the harness works

The current source of truth is [`kerrigan-v2/`](kerrigan-v2/):

- [`000-vision.md`](kerrigan-v2/000-vision.md) — why Kerrigan exists, what it adds on top of Spec Kit
- [`010-phases.md`](kerrigan-v2/010-phases.md) — phased rollout (now complete)
- [`020-delegation-rubric.md`](kerrigan-v2/020-delegation-rubric.md) — cloud vs local routing
- [`phaseN-tasks.yaml`](kerrigan-v2/) — per-phase task plans

v1 material lives under [`kerrigan/_archive-v1/`](kerrigan/_archive-v1/) for context but is not the current spec.

## Project specs

Each project under [`projects/`](projects/) follows the Spec Kit lifecycle (`constitution → specify → plan → tasks → implement`). The minimal living set per project:

- `plan.md` (always)
- `tasks.md` (always)
- `spec.md` (use [`spec-kit-tinyspec`](../.claude/skills/speckit-specify/SKILL.md) for small work; full `/speckit.specify` for larger)

Optional artifacts added as they earn their place: `architecture.md`, `acceptance-tests.md`, `test-plan.md`, `runbook.md`, `cost-plan.md`, `status.json`.

Completed projects are moved to [`projects/_archive/`](projects/_archive/) with a brief rationale.

## Where does this file belong?

```
Is it a non-negotiable principle?               → specs/constitution.md
Is it about how the harness itself works?       → specs/kerrigan-v2/<topic>.md
Is it scoped to one project being built?        → specs/projects/<name>/<artifact>.md
Is it an agent profile or adapter?              → .github/agents/<profile>.md
Is it a reusable skill?                         → .github/skills/<skill-id>/SKILL.md
Is it a step-by-step operational workflow?      → playbooks/<workflow>.md
Is it explanatory docs for humans?              → docs/<topic>.md
```

## Naming conventions

- **Meta-specs** (`kerrigan-v2/`): `<NNN>-<topic>.md` (`010-phases.md`, `020-delegation-rubric.md`). Numbers indicate reading order; increments of 10 leave room for insertion.
- **Project folders**: lowercase-hyphenated (`hello-swarm`, `task-tracker-real`).
- **Standard project artifacts**: exact names (`spec.md`, `plan.md`, `tasks.md`, `architecture.md`, `acceptance-tests.md`, `test-plan.md`, `runbook.md`, `cost-plan.md`, `status.json`). Validators check by name.

## Validation

CI's `verify` workflow enforces:

- Project artifacts exist and have the required sections (see `tools/validators/`).
- Files stay under the quality-bar limits (e.g. ≤800 lines unless `allow:large-file` is labelled).
- Acceptance criteria map to tests (`spec-kit-verify` chain).
- Agent profiles and skills have well-formed frontmatter.

Run locally with `kerrigan check` (or invoke validators directly from `tools/validators/`).

## See also

- [`../AGENTS.md`](../AGENTS.md) — canonical agent entry point
- [`../README.md`](../README.md) — project overview
- [`../docs/architecture/`](../docs/architecture/) — system diagrams and design docs
