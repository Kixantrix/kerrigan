# Architecture: kerrigan-dashboard

> **Status**: Pre-vis (M1). This document is a work-in-progress stub; production architecture decisions are finalized after design-lock and plan.md is promoted from draft.

## Overview

kerrigan-dashboard is a local desktop application built with Tauri 2 (Rust shell) + React 19 (renderer) + Vite (build). It surfaces the live state of every Kerrigan-managed project and lets the conductor dispatch new work through an embedded Copilot chat powered by the Kerrigan MCP server.

The application has three primary surfaces:
1. **Portfolio view** — card grid of all registered projects; entry point on launch.
2. **Project-detail view** — three-pane layout: plan editor (Tiptap), DAG canvas (React Flow), chat (Copilot ACP stream).
3. **Intervention inbox** — unified cross-project queue of blocks, attestation requests, and critical review threads.

## Components & interfaces

| Component | Layer | Notes |
|---|---|---|
| Tauri shell | Native (Rust) | Window management, `gh auth token` subprocess, local file I/O |
| React renderer | UI | React 19 + Vite + Tailwind — all views rendered here |
| Plan editor | UI | Tiptap v2 with custom mark for stage headings |
| DAG canvas | UI | React Flow 12; nodes = plan stages; edges = dependencies; particles = PR flow |
| Chat pane | UI | Copilot ACP stream consumer; tool-call cards rendered inline |
| Kerrigan MCP server | Service (M5) | Provides `dispatch`, `block-resolve`, `plan-update`, `conflict-predict` |
| GitHub poller | Service | Polls GitHub REST API every 60s via conditional requests; feeds DAG state |
| `~/.kerrigan/projects.json` | Data | Project registry; each entry has name, repos[], plan path |

## Tradeoffs

- **Tauri over Electron**: smaller bundle, native OS integration, no bundled Chromium. Accepted risk: webkitgtk version variation on Linux may require per-distro validation.
- **React Flow over custom SVG**: substantial time savings on DAG layout (dagre/elk auto-layout). Accepted risk: React Flow's license and bundle size; mitigated by the `minZoom`/`maxZoom` guard rails.
- **Polling over webhooks**: simpler auth model (no server to register webhooks with GitHub); accepted latency of up to 60s for PR state updates.
- **Tiptap for plan editing**: rich markdown round-trip, extensible. Fallback is Lexical (isolated behind a thin editor interface from day one).

## Security & privacy notes

- No GitHub tokens are persisted; all auth is ephemeral via `gh auth token` subprocess.
- Dashboard does not handle secrets — it only reads token from the process environment of `gh`.
- Local plan edits are committed to a per-session branch and pushed; no force-push.
- MCP server runs as a local subprocess; its exposed tools are scoped to the four named tools (v1).
