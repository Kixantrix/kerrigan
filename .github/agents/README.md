# Agent profiles

Kerrigan v2 defines agents by **location**, not role.

- [`local.md`](./local.md) — **conductor**. Plans, decides, dispatches. Runs in your chat (VS Code / Claude Code / Copilot CLI / github.com).
- [`cloud.md`](./cloud.md) — **executor**. Implements one task slice in a cloud container or isolated worktree. Opens one PR.
- [`kerrigan.md`](./kerrigan.md) — **swarm shaper** (meta). Maintains the harness itself.
- [`adapters/`](./adapters/) — thin pointers to built-in sub-agents (Claude Code `Explore` / `Plan`, GH Copilot review / coding agent).

## Format

All profiles use the GitHub Copilot custom-agent format (YAML frontmatter + Markdown body). Claude Code reads extended fields in the same frontmatter (`model`, `isolation`, `hooks`, `skills`, etc.) and ignores what Copilot doesn't recognize, and vice versa — **one file, all runtimes**.

Kerrigan-specific capability-manifest fields (`role`, `needs`, `verifies_before_pr`, `delegates`, `budget`, `blocks_on`) are ignored by both runtimes but read by kerrigan tooling (validators, conflict predictor, delegation rubric).

## Mirroring to `.claude/agents/`

Claude Code looks in `.claude/agents/` by default. `scripts/mirror-agents.ps1` creates a directory junction on Windows; on POSIX use `ln -s .github/agents .claude/agents`.

## See also: prompts/

Agent profiles (this directory) are **not** the same as prompt templates:

- **Agent profiles** (`local.md`, `cloud.md`, `kerrigan.md`) — runtime configurations loaded by GitHub Copilot or Claude Code to configure the agent session. They declare identity, permissions (`permissionMode`), skills, delegation rules, and capability manifests. They answer *"who is this agent and how should it run?"*
- **Prompt templates** (`prompts/`) — reusable Markdown files loaded by URL into a GitHub issue or CLI invocation. They contain task-specific instructions the agent executes once started. They answer *"what should the agent do right now?"*

A typical flow: the runtime loads `cloud.md` (agent profile) to start the agent → the issue body references `prompts/implementation-swe.md` (prompt template) to tell it what to implement.

See [`../../prompts/README.md`](../../prompts/README.md) for the full prompt library.

## See also

- [../../AGENTS.md](../../AGENTS.md) — canonical entry point
- [../../specs/kerrigan-v2/000-vision.md](../../specs/kerrigan-v2/000-vision.md) — why two profiles
- [../skills/](../skills/) — skills profiles preload
- [../../prompts/README.md](../../prompts/README.md) — prompt template library
