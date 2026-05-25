# Cost Plan: kerrigan-dashboard

> **Status**: Pre-vis (M1). Full cost estimates finalized after M2 (Tauri shell) and M5 (MCP server).

## Overview

kerrigan-dashboard is a local-only application with no hosting costs. Cost is measured in Copilot agent-request budget and GitHub Actions minutes.

## Agent budget estimate (full project — M1–M6)

| Milestone | Estimated requests | Notes |
|---|---|---|
| M1 Pre-vis | 1 task × ~30 req | Single cloud-agent dispatch |
| M2 Tauri Shell | 1 task × ~50 req | Scaffold + wiring |
| M3 Plan Parser | 1 task × ~40 req | Library + unit tests |
| M4 DAG Canvas | 2 tasks × ~60 req | React Flow integration + animation |
| M5 MCP Server | 2 tasks × ~80 req | MCP protocol + 4 tools |
| M6 Chat Pane | 1 task × ~50 req | ACP stream consumer |
| **Total (est.)** | **~420 requests** | |

## GitHub Actions minutes estimate

| Workflow | Est. per run | Frequency | Monthly est. |
|---|---|---|---|
| verify.yml | 3 min | Per PR (~10 PRs) | 30 min |
| Playwright E2E | 2 min | Per PR | 20 min |
| **Total** | | | **~50 min/month** |

## Cost controls

- No cloud infra — local Tauri binary, no server.
- GitHub API polling uses conditional requests (ETags); free-tier rate limits not expected to be exceeded for ≤50 projects at 60s poll interval.
