# Claude Code agents (local-only)

This directory exists for **Claude Code** users. The repo's source of truth for agent profiles is [`.github/agents/`](../../.github/agents/) — that's what GitHub Copilot (cloud agent, VS Code, CLI, JetBrains/Eclipse/Xcode) reads.

Claude Code reads from `.claude/agents/` and there's no path override. This directory is **gitignored** so the same files don't show up twice in VS Code's agent picker.

## If you use Claude Code in this repo

You have two options:

### Option A — directory junction (recommended, Windows)

```powershell
pwsh scripts/mirror-agents.ps1
```

Creates a junction so `.claude/agents/` points at `.github/agents/`. One source on disk, both tools see it.

### Option B — symlink (macOS / Linux)

```bash
rm -rf .claude/agents
ln -s ../.github/agents .claude/agents
```

### Option C — manual copy

```powershell
Copy-Item -Recurse -Force .github/agents/* .claude/agents/
```

You'll need to re-run this whenever `.github/agents/` changes.

## If you only use GitHub Copilot

Nothing to do. Leave this directory empty.
