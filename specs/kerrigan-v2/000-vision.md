# Kerrigan v2 — Vision (2026 edition)

> Status: Draft. Living document.
> Core decision: **Kerrigan v2 sits on top of GitHub Spec Kit.** We don't replace its lifecycle; we add the delegation + verification glue it doesn't prescribe.

## Why v2

Two years of field use (`vhs-video-stack`, `personal-selfhost`) surfaced repeat failure modes in Kerrigan v1:

- Heavy setup (labels, workflows, prompts, validators) before the first PR.
- 10 role agents collapse in practice into "local conductor" and "cloud executor". The rest are noise.
- Cascade merges — Copilot can't rebase, waves are manual.
- Validators count sections and LOC but don't check that acceptance criteria run as tests.
- Specs get written once and rot. Plans and goals are what actually stay useful.
- SDK service locked us to Copilot; `personal-selfhost` forked a parallel Claude Code dispatcher.

Meanwhile the ecosystem standardised underneath us:

- **`AGENTS.md`** — Agentic AI Foundation (Linux Foundation), 60k+ repos, read by Copilot cloud agent / Copilot CLI / VS Code / JetBrains / Claude Code / Codex / Cursor / Jules / Aider / Junie / Amp / Warp / Goose / Phoenix.
- **GitHub Spec Kit v0.7.4** (90k⭐, April 2026) — spec-driven lifecycle (`constitution → specify → plan → tasks → implement`) with optional `clarify / analyze / checklist / taskstoissues`. Extension + preset architecture. 50+ community extensions. Has a preset system so we can customize templates without forking.
- **Agent Skills** open spec (`agentskills` org) — reusable capability packages in `.github/skills/`, `.claude/skills/`, `.agents/skills/`.
- **GH Copilot custom agents** — `.github/agents/<name>.md` with YAML frontmatter; the same file is loaded by Copilot cloud agent, Copilot VS Code, JetBrains, Eclipse, Xcode, and Copilot CLI.
- **Claude Code subagents** — richer frontmatter (`tools`, `model`, `isolation: worktree`, `hooks`, `skills`, `permissionMode`) with built-in `Explore`, `Plan`, and `general-purpose` subagents.
- **2026 Anthropic engineering direction** — "Scaling managed agents: decoupling the brain from the hands", "Harness design for long-running application development", "Effective harnesses for long-running agents", "Beyond permission prompts", "Claude Code auto mode". Consensus: *the harness matters more than the prompt*.

### What this means for Kerrigan

1. **Don't build a parallel lifecycle.** Adopt spec-kit. Its lifecycle + extension system + 30-agent support is better than anything we'd build.
2. **Don't build a parallel agent taxonomy.** The axis is **local vs cloud**, not role.
3. **Don't reinvent verification.** Spec-kit already has verification extensions (`verify`, `verify-tasks`, `qa`, `ci-guard`); use them and add our own gap-fillers as extensions, not as new frameworks.
4. **Don't fight specs rotting.** Either use `spec-kit-tinyspec` for small work, or use `spec-kit-sync` / `spec-kit-reconcile` / `spec-kit-retrospective` to keep specs honest. Specs that serve a purpose stay; the rest get tinyspec'd.
5. **Kerrigan's value is the harness**, not the schema: local↔cloud delegation, conflict prediction, briefing packets, satellite bootstrap, 2026-shaped conventions layered *on top of* spec-kit.

## The new shape: Local Conductor → Cloud Swarm

```
   ┌─────────────────────────────────────────────────────────┐
   │  YOU — VS Code chat / Copilot CLI / Claude Code /       │
   │        github.com mobile — all load AGENTS.md +         │
   │        spec-kit slash commands + kerrigan extensions    │
   └─────────────────┬───────────────────────────────────────┘
                     │ natural language, no mandated labels
                     ▼
   ┌─────────────────────────────────────────────────────────┐
   │  LOCAL agent profile  (.github/agents/local.md)          │
   │  - runs spec-kit: /speckit.plan /tasks /analyze          │
   │  - decides cloud vs local per task (delegation rubric)   │
   │  - drafts briefing packets                               │
   │  - dispatches via /speckit.taskstoissues                 │
   │  - uses Claude Code's built-in Explore + Plan subagents │
   └─────────┬────────────────────────┬──────────────────────┘
             │                        │
             ▼                        ▼
   ┌─────────────────────┐  ┌─────────────────────────────────┐
   │ CLOUD agent profile │  │ Built-in subagents (thin        │
   │ (.github/agents/    │  │  adapters)                      │
   │  cloud.md)          │  │  - Claude Code Explore (read)   │
   │ runs on:            │  │  - Claude Code Plan mode        │
   │  - Copilot cloud    │  │  - GH Copilot review agent      │
   │  - Claude Code team │  │  - Copilot coding agent         │
   │ in worktree/        │  └─────────────────────────────────┘
   │ container; runs     │
   │ /speckit.implement  │
   │ for one task slice  │
   └─────────┬───────────┘
             │
             ▼
   ┌─────────────────────────────────────────────────────────┐
   │  DISTRIBUTED VERIFICATION (no dedicated verifier agent) │
   │  - cloud agent self-tests before opening PR            │
   │  - CI runs: unit + integration + smoke                 │
   │  - spec-kit extensions: verify, verify-tasks, ci-guard │
   │  - Copilot review agent on PR (GH built-in)             │
   │  - human checks scenario coverage only                  │
   └─────────────────────────────────────────────────────────┘
```

### Three rules that change everything

1. **Delegate by location, not role.** Any task runs either `local` (needs your machine — device I/O, OS, paid secrets) or `cloud` (everything else). The local profile is the conductor; the cloud profile is the executor. No scout/builder/verifier split.
2. **Parallelize only what can't conflict.** The conductor computes file-overlap before dispatch and batches tasks into non-overlapping waves. Dependent PRs auto-rebase on merge.
3. **Verify everywhere, not once.** Every layer verifies what it can: cloud agent self-tests → CI runs tests + spec-kit verify → Copilot review → human checks scenarios. No single agent owns "verification".

## Four goals → what each means

### 1. Easier to use

- **2 agent profiles + thin adapters.** `.github/agents/local.md` and `.github/agents/cloud.md`. Adapters for Claude Code's `Explore` + `Plan` and for GH Copilot's built-in review/coding agents — one file each, no prompts, just metadata pointing at the built-ins.
- **Spec-kit slash commands are the primary UX.** `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.taskstoissues` — already supported across 30+ agents. We add one kerrigan slash command (`/kerrigan.dispatch`) as a thin wrapper over `taskstoissues`.
- **One-command bootstrap**: `specify init --here --ai copilot` then `kerrigan preset add` installs our preset + extensions.
- **`AGENTS.md` at repo root** is the primary contract. `CLAUDE.md` and `.github/copilot-instructions.md` redirect to it.
- **Labels shrink to 4.** `agent:go`, `agent:wait`, `agent:local`, `autonomy:override`. Agent selection happens by *which agent you talk to*, not by role labels.
- **Works on mobile.** Talk to the local agent via github.com chat on mobile; it dispatches cloud work; you watch PRs in the mobile PR list.

### 2. Lower friction for bigger tasks

- **Spec-kit's `/speckit.taskstoissues`** handles the cloud dispatch path for free.
- **`kerrigan-conflict-predictor`** (one custom spec-kit extension) — before `taskstoissues`, computes file-overlap across pending tasks and groups them into parallel-safe waves. Writes the wave plan to `.specify/waves.yaml`.
- **`kerrigan-auto-rebase`** — GitHub Action: on `main` merge, find stale agent PRs, request rebase via `@copilot rebase` or dispatch a fresh cloud task. Replaces manual wave wrangling.
- **`kerrigan-briefing`** (custom spec-kit extension) — compresses `plan.md` + relevant task slice + referenced skills into a single briefing file attached to the dispatched issue. Reduces tokens on the cloud side.
- **Community extensions we adopt as defaults**: `spec-kit-worktree-parallel`, `spec-kit-pr-bridge`, `spec-kit-checkpoint`.
- **Cloud-first routing.** Local agent defaults to cloud dispatch unless the task's capability needs trip a `local` rule (see delegation rubric, phase 2).

### 3. Trustworthy tests at all scales

- **Spec-kit's acceptance structure** (specify → tasks with AC) is our base. We add a validator that every AC has a passing test before merge.
- **Adopt `spec-kit-verify` + `spec-kit-verify-tasks` + `spec-kit-ci-guard` + `spec-kit-qa`** as default extensions for the kerrigan preset.
- **Smoke test mandate for deployable projects.** `scripts/smoke.*` runs end-to-end; required PR check. This is our one check `spec-kit` doesn't cover directly.
- **Test-capability matrix** (kerrigan extension) — tests declare `cloud_ok | local_required | manual` with a reason. Prevents silent skip.
- **Distributed verification chain** (see diagram). Cloud agent, CI, spec-kit-verify, Copilot review, and human each verify a slice — nothing falls between.

### 4. Agents know their limits

- **Capability manifest per agent profile** in frontmatter:
  ```yaml
  ---
  name: cloud
  description: Executor; runs /speckit.implement for one task slice in a cloud container
  tools: [Read, Edit, Write, Bash]
  needs: [cloud-env]   # kerrigan-specific
  blocks_on: [ambiguous_ac, missing_secret, local_required, out_of_budget]
  ---
  ```
- **Structured block output** (`.specify/blocks/<task-id>.yaml`). Blocked agent stops and writes a block; conductor surfaces; other tasks keep moving. Implemented as a kerrigan extension so spec-kit's `/speckit.analyze` sees it.
- **Cloud-vs-local delegation rubric** documented. Agent cites the rule it matched when routing a task.
- **Budget surfacing.** Cloud dispatch reports Copilot premium requests + Actions minutes as a sticky PR comment. Over-budget → block.

## Non-goals

- **Don't fork spec-kit.** Use it as a dependency. Kerrigan = preset + a few extensions + 2 agent profiles + AGENTS.md + playbooks.
- **Don't build a verifier agent.** Verification is distributed across cloud agent + CI + spec-kit extensions + Copilot review + human. No dedicated role.
- **Don't mandate specs for everything.** Small work uses `spec-kit-tinyspec`. Medium/large work uses full spec-kit. `plan.md` + goals are always valuable; `spec.md` is optional where the project is too small to warrant it.
- **Don't mandate one vendor.** Copilot cloud agent is the primary delegate. Claude Code is the primary local runtime. Anything that reads `AGENTS.md` works.
- **Don't pretend multi-agent write coordination is solved.** Parallelize reads (scout-via-Explore, `/speckit.analyze`) and non-overlapping writes (conflict predictor). Single-thread the rest.

## How v2 relates to v1 and spec-kit

| Concern | v1 Kerrigan | Spec Kit | v2 Kerrigan |
|---|---|---|---|
| Entry file | scattered | `AGENTS.md` + `.specify/` | **`AGENTS.md`** (spec-kit compatible) |
| Principles | `specs/constitution.md` | `/speckit.constitution` | **spec-kit constitution**; keep `specs/constitution.md` linked from `AGENTS.md` |
| Spec | `spec.md` (rots) | `/speckit.specify` | **optional**: `tinyspec` for small, full spec for large |
| Plan | `plan.md` (lives) | `/speckit.plan` | **`/speckit.plan`** — primary artifact |
| Tasks | `tasks.md` (prose) | `/speckit.tasks` | **`/speckit.tasks`** + `kerrigan-conflict-predictor` |
| AC → test | ad-hoc | `/speckit.analyze` + verify ext | **spec-kit-verify + spec-kit-verify-tasks** (preset default) |
| Role agents | 10 `role.*.md` | agent-agnostic | **2 profiles** (`local`, `cloud`) + built-in-subagent adapters |
| Skills | 2 inline folders | community catalog | **agent-skills spec** + `.github/skills/` |
| Cloud dispatch | SDK service | `/speckit.taskstoissues` | **`/speckit.taskstoissues`** (wrapped by `/kerrigan.dispatch`) |
| Local runtime | copy/paste prompts | agent-native | **VS Code chat / Claude Code / Copilot CLI**, same profiles |
| Labels | ~15 | — | 4 |
| Verification | triage + validators | verify/verify-tasks/ci-guard/qa exts | **preset defaults** + smoke mandate |
| Conflict handling | manual waves | worktree-parallel ext | **kerrigan-conflict-predictor + kerrigan-auto-rebase** |
| Drift | — | sync/reconcile/retrospective exts | **preset defaults** |

Kerrigan v2 is: **spec-kit preset + 3–4 custom extensions + 2 agent profiles + AGENTS.md + playbooks + satellite bootstrap.** Everything else is borrowed.

## Success criteria

1. A new repo bootstraps in one command (`specify init --here --ai copilot && kerrigan preset add`) and has a cloud agent producing its first PR within 5 minutes.
2. A single human supervises ≥3 parallel cloud agents without touching git locally.
3. A PR reaches human review only after cloud agent self-tests, CI, spec-kit verify, and Copilot review are all green — human checks scenarios only.
4. Moving to a satellite: `specify init --here --ai copilot && kerrigan preset add` and the agents + skills are live. No prompt copy-paste.
5. On mobile: assign work, read PR status, merge via github.com — laptop optional.
6. The three recurring v1 complaints (cascade merges, can't rebase, autonomy-label fatigue) drop off.

## How we get there

See [010-phases.md](./010-phases.md).
