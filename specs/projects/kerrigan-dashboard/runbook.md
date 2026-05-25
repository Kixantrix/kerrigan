# Runbook: kerrigan-dashboard

> **Status**: Pre-vis (M1). Production runbook is written during M2 (Tauri shell scaffold).

## Overview

kerrigan-dashboard is a local desktop application distributed as a Tauri binary. There is no server component and no cloud deployment; the app runs on the conductor's machine.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth login`)
- `@github/copilot` CLI installed globally (≥ minimum version supporting `--acp`)
- Git installed with user identity configured
- `~/.kerrigan/projects.json` with at least one project entry

## Running (M1 pre-vis only)

Open the pre-vis prototype directly in any Chromium-based browser:

```bash
open specs/projects/kerrigan-dashboard/previs/index.html
```

No server, no dependencies, no build step required.

## Production launch (M2+)

```bash
# Build (cross-platform via Tauri)
cd apps/kerrigan-dashboard
npm run tauri build

# Run in dev mode
npm run tauri dev
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| DAG canvas blank | `gh auth` not configured | Run `gh auth login` |
| Chat pane unresponsive | Copilot CLI not found on PATH | Install `@github/copilot` CLI |
| Stale data on portfolio | GitHub API unreachable | Check network; cached state shown automatically |
