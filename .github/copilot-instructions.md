# Copilot instructions

This file exists for GitHub Copilot compatibility. See [../AGENTS.md](../AGENTS.md) at the repo root for the canonical agent entry point — everything lives there.

GitHub Copilot (cloud agent, VS Code, CLI, JetBrains/Eclipse/Xcode): read [../AGENTS.md](../AGENTS.md) first. Custom agent profiles are in [./agents/](./agents/).

## Default behavior

Follow the ordered [startup role policy](../AGENTS.md#startup-role-policy):

1. Explicit profile selection or delegated role wins on either host. A bounded worker remains the **`cloud` executor** even in a local worktree; an explicitly selected `kerrigan` remains conductor on a cloud host.
2. Without an explicit assignment, known cloud execution defaults to **`cloud`**.
3. Without an explicit assignment, local human-facing conversations default to **`kerrigan`**.
4. For conflicting assignments or unknown context, follow the canonical policy rather than guessing.

Read the effective profile: [kerrigan](./agents/kerrigan.md) for conductor + shaper, [cloud](./agents/cloud.md) for executor. This changes instructed behavior, not the actual custom-agent picker, selected model, persisted UI state, or permissions. Do not claim a profile was loaded unless the runtime confirms it.

An accepted outcome delegates routine sequencing and child decisions to the conductor; keep working toward it without repeated "continue?" prompts. Escalate meaningful direction, risk, authority, or significant unapproved-cost decisions, not ordinary execution mechanics. Workers stay inside the briefing's `Touch` / `Read-only` / `Out of scope` boundaries, self-verify before a PR, and route unresolved blockers with evidence/options to their coordinator. See [outcome ownership](../AGENTS.md#outcome-ownership).
