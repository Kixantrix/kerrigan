# AGENTS.md

> Canonical entry point for every AI agent in this repo.
> Standard: [agents.md](https://agents.md) (Agentic AI Foundation / Linux Foundation).
> Lifecycle: [GitHub Spec Kit](https://github.com/github/spec-kit).
> Read this file first. Everything else is linked from here.

## What this repo is

**Kerrigan** is a stack-agnostic coding-swarm harness built **on top of** GitHub Spec Kit. Spec Kit provides the lifecycle (`constitution → specify → plan → tasks → implement`); Kerrigan adds the delegation + verification glue on top:

- 2 agent profiles (`kerrigan` = interactive conductor + shaper, `cloud` = executor) + thin adapters for built-in sub-agents
- Local→cloud routing rubric (by capability, not role)
- Conflict prediction before parallel cloud dispatch
- Briefing-packet compression to cut dispatch tokens
- Distributed verification (cloud self-test → CI → Copilot code review → kerrigan addresses feedback → human reviews direction)
- Structured blocks, capability manifests, smoke-test mandate, budget surfacing
- **Review philosophy**: humans verify *direction and spec alignment*, not technical quality. Technical quality is the agent + CI + Copilot review chain's job. Human review happens after all automated checks are green.

Current milestone: **[v2 rollout](specs/kerrigan-v2/010-phases.md)** — v2 complete.

## How to start

Pick an agent profile and talk to it in natural language. Selection happens by *who you're chatting with*, not by labels.

| When you want to | Talk to | Where |
|---|---|---|
| Plan work, dispatch tasks, make decisions, shape the harness | `kerrigan` | VS Code chat · Claude Code · Copilot CLI · github.com (mobile) |
| Implement one task slice, open one PR | `cloud` | GitHub Copilot cloud agent (default for `@copilot`-assigned issues) · Claude Code worktree session |

`kerrigan` is the only interactive profile — the single agent the human talks to. It handles both project work (planning and dispatching) and harness work (maintaining `.github/`, validators, workflows, specs). `cloud` is the executor profile that runs in ephemeral environments to implement one slice at a time.

Agent profiles: [`.github/agents/`](./.github/agents/). GitHub Copilot (cloud agent, VS Code, CLI, JetBrains/Eclipse/Xcode) reads them directly. Claude Code reads from `.claude/agents/` — see [`.claude/agents/README.md`](./.claude/agents/README.md) for the optional mirror setup.

Built-in sub-agents `kerrigan` can delegate to (thin adapters in [`.github/agents/adapters/`](./.github/agents/adapters/)):

- Claude Code `Explore` — read-only code exploration (Haiku; fast, cheap).
- Claude Code `Plan` mode — planning without edits.
- GitHub Copilot code-review agent — automatic PR review.
- GitHub Copilot coding agent — cloud PR execution (the `cloud` profile targets this).

## Spec Kit commands (primary UX)

Once Spec Kit is installed ([playbook](playbooks/v2-bootstrap.md)), the standard slash commands are:

- `/speckit.constitution` — project principles
- `/speckit.specify` — what to build (skip for small work; see `spec-kit-tinyspec`)
- `/speckit.plan` — how to build (living artifact; primary)
- `/speckit.tasks` — actionable tasks
- `/speckit.analyze` — cross-artifact consistency
- `/speckit.taskstoissues` — convert tasks to GH issues (dispatch entry point)
- `/speckit.implement` — execute (cloud profile's main command)

Kerrigan adds:

- `/kerrigan.dispatch` — wraps `taskstoissues` with conflict-prediction + briefing-packet generation (Phase 1).

## Principles

See [`specs/constitution.md`](./specs/constitution.md) for the full list. Short version:

1. Artifact-driven — work lives in repo files.
2. Small, reviewable increments — one task, one PR.
3. Tests included — every AC maps to an automated test.
4. Stack-agnostic — no mandatory language/framework.
5. Agent clarity — agents cite the rule they followed; humans decide ambiguities.
6. Human-in-loop for decisions; agents-in-loop for execution.

## Project conventions

- **Spec-kit artifacts** live in `.specify/` and per-feature folders under that. Don't hand-edit `.specify/` templates; use presets.
- **Living docs:** `plan.md` (always), `tasks.md` (always). `spec.md` is optional — use `spec-kit-tinyspec` for small work.
- **Acceptance criteria → tests**: enforced by `spec-kit-verify` + `spec-kit-verify-tasks` (Phase 2).
- **Smoke test** (`scripts/smoke.sh` / `.ps1`): required for every deployable project. Gates PR merge.
- **Blocks** are structured: a blocked agent writes `.specify/blocks/<task-id>.yaml` and stops. The `kerrigan` profile surfaces blocks; unrelated tasks keep moving.
- **Waves**: the `kerrigan` profile computes parallel-safe waves before dispatch (`.specify/waves.yaml`) via `kerrigan-conflict-predictor` (Phase 1).

## Skills

Reusable agent knowledge lives in [`.github/skills/`](./.github/skills/) (open [agent-skills](https://github.com/agentskills/agentskills) spec). Agent profiles preload skills by ID in their frontmatter. Stack-specific skills live in [`skills/README.md`](./skills/README.md).


## Testing

- Canonical guide: [`docs/test-strategy.md`](./docs/test-strategy.md).
- Kerrigan chooses tests on two axes: level (`unit → integration → smoke → e2e → scenario`) and environment.
- Environment taxonomy: `cloud-linux`, `cloud-windows`, `cloud-macos`, `cloud-self-hosted-<name>`, `local-attested-<class>`, `manual-human`.
- `local-attested-*` ACs require attestation handoff before completion.

## Labels (v2)

Four total, not fifteen. **None of these are enforced automatically.** The functional gate for cloud execution is `@copilot` assignment on the issue. The labels are *annotations* the `local` profile (and humans) read to understand intent and state across sessions.

- `agent:go` — annotation: this issue is ready to dispatch (or has been dispatched). Used by `kerrigan` to find work that's been triaged.
- `agent:wait` — annotation: intentionally undispatched; waiting on a dependency, a wave, or human input. `kerrigan` should not auto-assign Copilot here.
- `agent:local` — annotation: this task needs the human's machine (device I/O, OS-specific, paid secret). Don't assign to cloud Copilot.
- `autonomy:override` — annotation: human has explicitly approved an exception to a default-cautious routing rule.

v1 role labels are archived. v2 uses these four annotations only.

## Runtimes

- **Primary cloud delegate:** GitHub Copilot cloud agent (one issue → one ephemeral container → one branch → one PR).
- **Primary local runtime:** Claude Code (`isolation: worktree` built-in, rich hook/memory model).
- **Pluggable:** anything that reads `AGENTS.md` (Codex, Cursor, Jules, Aider, Amp, Junie, Kilo Code, Warp, Goose, Gemini CLI, Factory, Phoenix, …).

Platform-specific files (`CLAUDE.md`, `.github/copilot-instructions.md`) redirect here rather than duplicate content.

## Auto-mode guidance

Claude Code supports three `permissionMode` values in agent frontmatter. Choose based on the risk profile of the work, not on convenience. `permissionMode` is the machine-readable equivalent — set it in the agent's YAML frontmatter so the decision is auditable and consistent across sessions.

| Project / context | Recommended mode | Reason |
|---|---|---|
| Greenfield project (no users yet, no production traffic) | `auto` | No blast radius; fastest iteration; mistakes are cheap to revert. |
| Sandboxed examples (`examples/`, `docs/`, isolated throwaway repos) | `auto` | Self-contained, no shared state; a bad edit is trivially undone. |
| Test-only work (adding/updating tests, no production code changed) | `auto` | Tests are reversible; CI will surface any breakage before merge. |
| Prototype / spike branch (explicitly discardable) | `auto` | Branch is not expected to merge; human reviews before promoting. |
| Production code (any path that ships to real users) | `acceptEdits` | Human confirms every file write; reduces risk of silent regressions. |
| Shared infrastructure (CI workflows, branch protection, secrets config) | `acceptEdits` | Mistakes propagate across all contributors and branches instantly. |
| Security-sensitive work (auth, crypto, permissions, secret handling) | `acceptEdits` | One wrong edit can introduce a vulnerability; confirmation gates are worth the friction. |
| Any task that `R-local.human-judgment` matches in the delegation rubric | `acceptEdits` (at minimum) | The rubric already identified this task needs human in the loop per step — don't bypass that gate. |

**Defaults in this repo:**
- `kerrigan` profile → `permissionMode: default` (planning/dispatch + light harness edits; rarely touches feature code).
- `cloud` profile → `permissionMode: acceptEdits` (executor; always touches files but must be confirmed).

**When to consider `auto` for the `cloud` profile:** only when the linked issue is labeled `agent:go` *and* the task's context falls in the `auto`-safe rows above *and* the branch is not `main`. The `autonomy:override` label signals human approval for an exception.

> Cross-reference: for routing decisions (cloud vs local), see `.github/skills/delegation-rubric/SKILL.md`. The `auto`-vs-`acceptEdits` decision is orthogonal — it governs *how much supervision* the agent has once routed, not *where* it runs.

## Validation & CI

- `kerrigan check` (Phase 1+) runs all validators locally. Today: see [`tools/validators/`](./tools/validators/).
- Required PR checks: validators + unit/integration tests + smoke (where declared) + spec-kit verify chain (Phase 2) + Copilot review.
- Branch protection (Phase 2+): `verify` workflow must be green to merge.

## Where things live

| Purpose | Path |
|---|---|
| Agent profiles | `.github/agents/` (Claude Code: opt-in mirror via `.claude/agents/`) |
| Skills | `.github/skills/`, `skills/` |
| Spec-kit state | `.specify/` |
| Meta-specs (why Kerrigan works) | `specs/kerrigan-v2/` (active), v1 history in `specs/kerrigan/_archive-v1/` |
| Project work | `specs/projects/<name>/` |
| Examples | `examples/` |
| Validators | `tools/validators/` |
| CI workflows | `.github/workflows/` |
| Playbooks | `playbooks/` |
| Feedback from agents in the field | `feedback/` |

## Monorepo / subprojects

Subprojects with their own conventions may include a nested `AGENTS.md`. Agents use the closest one (standard `AGENTS.md` nesting rule).

## Contributing

**Humans:** Start with [`README.md`](./README.md), then [`specs/kerrigan-v2/000-vision.md`](./specs/kerrigan-v2/000-vision.md). Feedback from agents goes in [`feedback/agent-feedback/`](./feedback/agent-feedback/).

**Agents:** Read this file, then the closest nested `AGENTS.md`, then your briefing packet (your primary brief — don't re-derive from the whole repo). If blocked, write `.specify/blocks/<task-id>.yaml` and stop.
