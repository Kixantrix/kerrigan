# Kerrigan v2 — Rollout Phases

> Each phase is independently valuable. Ship → use → feedback → next.
> v2 stands on top of GitHub Spec Kit; we don't build a parallel lifecycle.

## Phase 0 — Foundation (this PR wave)

**Goal:** adopt spec-kit as the core, cut v1's agent roster to 2 profiles + adapters, make "pick an agent, talk" work in VS Code / Claude Code / Copilot CLI / github.com.

**Deliverables:**

- Install spec-kit: `specify init --here --ai copilot --ai claude` at the repo root. Generates `.specify/`, slash commands for Copilot + Claude, `AGENTS.md` skeleton.
- Merge spec-kit's `AGENTS.md` with the kerrigan-specific content: repo-level principles, delegation rubric pointer, runtime matrix, 4 labels. Keep ≤200 lines.
- `.github/agents/local.md` — conductor profile. Universal Copilot-custom-agent frontmatter + Claude-Code-extended fields. Points at spec-kit slash commands as its primary tools.
- `.github/agents/cloud.md` — executor profile. Same format. Defaults to running `/speckit.implement` inside a worktree/container.
- `.github/agents/adapters/` — thin one-page pointers to Claude Code's `Explore` and `Plan` built-ins and to GH Copilot's built-in review/coding agents. No prompt bodies — just "when to delegate to this built-in".
- `.github/agents/kerrigan.md` — meta profile (swarm shaper). Rewrite frontmatter, trim body.
- `.claude/agents/` symlinks (PowerShell junctions via `scripts/mirror-agents.ps1`) to `.github/agents/`.
- Retire the remaining v1 role-prompt files in favor of the v2 profiles + skills/extensions.
- Add 4 v2 labels (`agent:go`, `agent:wait`, `agent:local`, `autonomy:override`). Leave v1 labels in place; migrate in Phase 4.
- Starter skills in `.github/skills/` (agent-skills spec): `briefing-packet`, `block-report`, `smoke-test`, `delegation-rubric`.
- Validator `tools/validators/agents_md.py` — checks `AGENTS.md` exists and `.github/agents/*.md` have valid frontmatter + required fields (`name`, `description`).
- `CLAUDE.md` and `.github/copilot-instructions.md` → one-line redirects to `AGENTS.md`.
- Quick-start playbook `playbooks/v2-bootstrap.md`: the 3-command new-repo and satellite bootstrap.

**Exit criteria:**

- Opening a fresh checkout in VS Code, Claude Code, and Copilot CLI all resolve the same agent list.
- `specify init --here --ai copilot && kerrigan preset add` (preset stubbed as a git-apply patch until Phase 1) produces a working skeleton in a fresh repo.
- A manual dispatch via `/speckit.taskstoissues` lands a first cloud PR.

## Phase 1 — The kerrigan preset + first extension

**Goal:** package the opinionated choices as a real spec-kit preset so satellites get them in one command.

**Deliverables:**

- `preset/kerrigan/` — a spec-kit preset. Overrides templates for `plan.md`, `tasks.md`, PR body, AC format. Terminology stays neutral (stack-agnostic). Submitted to the spec-kit community catalog once stable; used locally first.
- Default extensions bundled by the preset:
  - `spec-kit-worktree-parallel` — worktree isolation.
  - `spec-kit-pr-bridge` — PR bodies from spec artifacts.
  - `spec-kit-checkpoint` — mid-implementation commits (prevents giant end-of-task diffs).
  - `spec-kit-tinyspec` — lightweight single-file workflow for small work. Addresses spec-rot.
  - `spec-kit-brownfield` — satellite bootstrap helper.
- `kerrigan-conflict-predictor` — our first custom spec-kit extension. Python, read-only. Before `/speckit.taskstoissues`, reads `tasks.md` (or `tasks.yaml` if present) + file globs, outputs parallel-safe waves to `.specify/waves.yaml`. CLI: `kerrigan plan`.
- `kerrigan-briefing` — second custom extension. Generates `.specify/briefings/<task-id>.md` from `plan.md` + task slice + referenced skills. Attached to the dispatched GH issue body.
- `/kerrigan.dispatch` slash command — thin wrapper over `/speckit.taskstoissues` that first runs `kerrigan-conflict-predictor` + `kerrigan-briefing`.
- CLI entry `kerrigan check` — runs all validators + `specify check`.

**Exit criteria:**

- A greenfield repo: `specify init --here --ai copilot && specify preset add kerrigan` then talking to the `local` profile produces a plan, tasks, and dispatches a wave of 3 parallel-safe cloud tasks.
- Satellites (`personal-selfhost`, `vhs-video-stack`) can adopt via two commands.

## Phase 2 — Trust (distributed verification)

**Goal:** every PR is defensible before human review. No single "verifier" agent — verification distributed across cloud-agent self-test, CI, spec-kit verify extensions, and Copilot review.

**Deliverables:**

- Adopt `spec-kit-verify`, `spec-kit-verify-tasks`, `spec-kit-ci-guard`, `spec-kit-qa` in the kerrigan preset.
- `scripts/smoke.sh` + `.ps1` mirror convention. `.github/workflows/smoke.yml` — required PR check for projects that declare a smoke script.
- `kerrigan-test-capability-matrix` extension — tests declare `cloud_ok | local_required | manual` + reason. Validator fails CI if `local_required` doesn't cite an allowlisted capability.
- `.github/workflows/verify.yml` — runs `spec-kit-verify` + smoke + test-capability-matrix validator. Gates merge.
- Cloud agent profile updated: must pass `/speckit.implement` self-tests before `gh pr create`. If they fail, emit a block instead of opening a PR.
- Enable GH Copilot code review on all PRs (repo setting); document in playbook.
- Branch protection: require `verify` workflow green.
- Example AC → test traceability in one project (`examples/task-tracker-real`).

**Exit criteria:**

- A PR that claims an AC without a test fails `spec-kit-verify` with a clear message.
- A `local_required` test without a cited capability fails validator.
- Same commit tested twice on CI gives identical output (determinism via pinned `.tool-versions`).

## Phase 3 — Trustworthy autonomy (local/cloud routing + limits)

**Goal:** agents route correctly, cite the rule they used, and emit structured blocks rather than guess.

**Deliverables:**

- `specs/kerrigan-v2/050-delegation-rubric.md` — the capability taxonomy (`device-io.*`, `os.*`, `paid-service.*`, `human-judgment`, `cloud-env`) and routing rules.
- Capability manifest fields added to both agent profiles (`needs`, `blocks_on`, `budget`).
- `kerrigan-route` extension — given a task, decides cloud/local and cites the matched rule. Writes decision into the briefing packet.
- Budget telemetry: workflow posts Copilot premium requests + Actions minutes as a sticky PR comment. Over-budget → agent emits block.
- Block schema at `.specify/schemas/block.schema.json`; validator ensures blocks resolve or get `block:acknowledged`.
- Claude Code hooks (where locally run): `PreToolUse` rejects `Bash(sudo ...)` in cloud-routed tasks; `Stop` runs the verify chain locally.
- Auto-mode guidance in `AGENTS.md`: which projects are safe with Claude Code `auto`, which require `acceptEdits`.

**Exit criteria:**

- Task needing a paid-API secret that isn't configured emits a block naming the exact secret.
- Local profile refuses to dispatch a `local_required` task to cloud and explains why.

## Phase 4 — Cleanup & satellite migration

**Goal:** remove the v1 surface area that v2 replaces; migrate `personal-selfhost` and `vhs-video-stack` to v2.

**Deliverables:**

- Delete the remaining v1 role-prompt files.
- Retire workflows replaced by v2: `agent-gates.yml`, `auto-grant-autonomy.yml`, `auto-ready-pr.yml`, `auto-trigger-dependents.yml` (merged into `verify.yml` + branch protection), `daily-self-improvement.yml` (replaced by kerrigan cron).
- Retire `services/sdk-agent/` and the v1 `prompts/` library — spec-kit's `/speckit.taskstoissues` plus `tools/create_issues.py` cover the common path; the SDK investigation concluded that fully-autonomous CI-triggered Copilot needs self-hosted-runner infrastructure outside this repo's scope (see archived `specs/projects/_archive/copilot-sdk-integration/`).
- Retire v1 labels; migration script `scripts/migrate-v1-to-v2.{ps1,sh}`.
- `playbooks/upgrade-to-v2.md` — step-by-step for `personal-selfhost` (delete its `claude-dispatch.sh` fork; use `cloud` profile + Claude Code runtime) and `vhs-video-stack` (migrate batch-merge habits to wave-based dispatch).
- Archive `specs/kerrigan/000–080*.md` as v1 history; `specs/kerrigan-v2/` becomes source of truth.
- Consolidate validators behind `kerrigan check`.

**Exit criteria:**

- `personal-selfhost` runs an end-to-end task using only v2 primitives — no dispatch fork, no label wrangling.
- `vhs-video-stack` reports zero new "cascade merge" or "can't rebase" feedback entries in a month of v2 use.
- `kerrigan check` runs the full validator suite in <30s.

## Dependencies & sequencing

```
Phase 0 ── Phase 1 ── Phase 2 ── Phase 3 ── Phase 4
   │         │          │          │          │
   └─ spec-  └─ preset  └─ needs   └─ needs   └─ cleanup
      kit +     + cflct    P1        P2 verify   v1 + move
      2 agts    predict    extns     chain       satellites
      + AGTS    + brief    + smoke
```

Phase 0 is the only phase that stands fully alone. Each subsequent phase depends on its predecessors' artifacts.

## What we're *not* doing

- No custom lifecycle. Spec-kit is the lifecycle.
- No custom agent taxonomy beyond the local/cloud split.
- No dedicated verifier agent. Verification distributed.
- No new inference server, queue, or dispatch daemon. GH Actions + Copilot cloud agent + Claude Code are enough.
- No mandatory spec for every task. `tinyspec` for small work.
- No forking spec-kit, Claude Code, or Copilot. If a 2026 primitive changes, we track it — not patch around it.
