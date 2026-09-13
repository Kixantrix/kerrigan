# CLAUDE.md

This file exists for Claude Code compatibility. See [AGENTS.md](./AGENTS.md) at the repo root for the canonical agent entry point — everything lives there.

Claude Code: when starting a session in this repo, read [AGENTS.md](./AGENTS.md) first. Agent profiles live in [`.github/agents/`](./.github/agents/). For Claude Code, mirror them into `.claude/agents/` — see [`.claude/agents/README.md`](./.claude/agents/README.md).

Follow its [startup role policy](./AGENTS.md#startup-role-policy): explicit selection or delegated worker assignment wins on either host; otherwise known cloud execution defaults to `cloud`, and local human-facing conversations default to `kerrigan`. These are behavioral defaults, not a claim that the runtime selected a custom agent or changed permissions. Follow [outcome ownership](./AGENTS.md#outcome-ownership) for routine sequencing and coordinator-first blocker handling.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at `.specify/` and the feature plan at `plan.md` (if present).
<!-- SPECKIT END -->
