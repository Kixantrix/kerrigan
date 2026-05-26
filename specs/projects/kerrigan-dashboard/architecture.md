# Architecture: kerrigan-dashboard

## Overview

Local-first desktop application (Tauri 2 shell wrapping a React 19 + Vite frontend) that visualizes work across all of the user's Kerrigan-coordinated projects. It is a single-user, single-machine tool — there is no backend service. All persistent state lives in two places: the user's GitHub repositories (the source of truth) and `~/.kerrigan/` on the local filesystem (configuration + caches).

The app interacts with three external systems:

1. **GitHub** — read via Octokit with ETag-aware conditional polling, write via `gh` CLI shell-out where useful. Authentication is borrowed on-demand from `gh auth token`; no token is ever persisted by the dashboard itself.
2. **GitHub Copilot CLI** — `copilot --acp` subprocess provides the chat experience. The CLI handles its own auth, model, and policy concerns; the dashboard just streams events.
3. **Local Kerrigan MCP server** — a Node 22 / TypeScript sidecar process started by the dashboard at launch. It exposes four tools to the chat agent (`kerrigan.dispatch`, `kerrigan.plan-update`, `kerrigan.block-resolve`, `kerrigan.conflict-predict`) and emits tool-result events back to the dashboard over a control channel so panes can refresh reactively.

Constraints from [`spec.md`](./spec.md): cold-start <1s, no credential persistence (AC-017), offline-tolerant (AC-014, AC-015), exactly one show-stopper visual (AC-020).

## Components & interfaces

```
+----------------------------------------------------------------+
| Tauri shell (Rust)                                             |
|  - window/lifecycle, tauri allowlist (fs + shell, locked down) |
|  - spawns: kerrigan-mcp sidecar, copilot --acp on demand       |
+----------------------------------------------------------------+
| Frontend (React 19 + Vite + Tailwind 4)                        |
|                                                                |
|  routes/portfolio  routes/project        routes/inbox          |
|       |                  |                    |                |
|  components/             components/    components/            |
|   ProjectCard             Dag             InboxItem            |
|                           PlanEditor      CaptureTriage        |
|                           Chat                                 |
|                           PrFlowOverlay (show-stopper)         |
|                                                                |
|  lib/                                                          |
|   projects.ts     - read+validate ~/.kerrigan/projects.json    |
|   github.ts       - Octokit + ETag cache + gh-auth shell-out   |
|   plan-parser.ts  - markdown -> {nodes, edges}                 |
|   status.ts       - PR/issue/block -> node status              |
|   acp-client.ts   - spawn+manage copilot --acp                 |
|   mcp-sidecar.ts  - spawn+wire kerrigan-mcp                    |
|   plan-save.ts    - per-session branch, push, draft PR         |
|   plan-queue.ts   - offline edit queue + replay                |
|   inbox.ts        - cross-project aggregator                   |
+----------------------------------------------------------------+
| Sidecar: tools/kerrigan-mcp/ (Node 22 / TypeScript)            |
|  MCP server over stdio                                         |
|  tools: dispatch, plan-update, block-resolve, conflict-predict |
+----------------------------------------------------------------+
```

Inter-process channels:

- `Tauri shell ↔ Frontend`: Tauri command + event bridge (no extra surface).
- `Frontend ↔ copilot --acp`: ACP JSON-RPC over the subprocess stdio. Wrapped by `lib/acp-client.ts`.
- `Frontend ↔ kerrigan-mcp`: MCP stdio. The MCP config is passed to `copilot --acp` via `--additional-mcp-config` so the chat agent can call our tools. The dashboard also subscribes to a side-channel control stream from the sidecar for cache-invalidation events.
- `Sidecar ↔ GitHub`: same Octokit/gh-auth path as the frontend; sidecar performs writes (issues, PRs) on the user's behalf.

## Data flow (conceptual)

```
projects.json --> lib/projects.ts -----+
                                       |
                                       v
                            +----------+----------+
GitHub (PRs/issues/blocks)->| lib/github.ts (poll)|--> status derivation
                            +----------+----------+        |
                                       |                   v
plan.md (per project) ----> lib/plan-parser.ts ----> DAG render
                                                          ^
                                                          |
chat input --> acp-client --> Copilot CLI --> tool_call --+
                                                |
                                                v
                                        kerrigan-mcp tools
                                          |        |
                                          v        v
                                   GitHub writes   plan.md edit + PR
                                          |        |
                                          v        v
                                  control event back to frontend
                                          |
                                          v
                              pane refresh (DAG / editor / inbox)
```

Polling cadence: 60s default, adaptive on rate-limit pressure (AC-014 backoff). ETag cache short-circuits 304s. Writes are immediate and trigger a fast-path refresh of just the affected pane.

## Tradeoffs

| Decision | Chosen | Rejected | Why |
|---|---|---|---|
| Shell | Tauri 2 | Electron | Smaller bundle, Rust core, native webview; fits a single-user local tool. |
| Frontend | React 19 + Vite | SolidJS, Svelte | Largest ecosystem for the niche libs we need (React Flow, Tiptap). |
| DAG | React Flow 12 + dagre | Cytoscape, custom canvas | Battle-tested node/edge UI; auto-layout in the box; fits "≤200 nodes interactive in <1s" budget. |
| Plan editor | Tiptap | Lexical, CodeMirror | Best markdown round-trip story; AI Toolkit path available. Lexical kept as swap-in behind a thin interface. |
| Chat | `copilot --acp` subprocess | Embed web view of github.com/copilot, write our own client against the OpenAI API | ACP is purpose-built for embedding; authentic Copilot; no API key juggling; auth follows the user's `gh` session. |
| MCP transport | Local stdio sidecar | Local HTTP server | No port exposure; tighter security; aligns with Copilot CLI's MCP config model. |
| Auth | `gh auth token` shell-out per call | OAuth flow with token at rest | Zero persistence (AC-017); reuses the user's existing `gh` setup. |
| Save model | Branch-per-edit-session + draft PR | Direct commit to main | Plays nicely with branch protection and parallel agent edits; conflicts surfaced cleanly. |
| Offline writes | Local queue in `~/.kerrigan/queue/` | Block writes when offline | Conductor can capture intent and replay; preserves the always-responsive feel. |

## Security & privacy notes

- **Credentials**: zero persistence. The app never writes a GitHub token, OAuth secret, or session cookie to disk. Every API call resolves auth fresh via `gh auth token`. Verified by AC-017 test + a post-shutdown scan of the data directory.
- **Tauri allowlist**: locked to the minimum required scopes:
  - `fs`: read-write on `~/.kerrigan/`, read on any project's git working copy paths declared in `projects.json`.
  - `shell.execute`: only for vetted commands (`gh auth token`, `git`, `copilot --acp`); no arbitrary shell.
  - No network capability granted to the renderer; all outbound HTTP goes through the Rust core via Octokit.
- **MCP server boundary**: binds to stdio only — no TCP/UDP listener, no Unix socket exposed beyond the parent process.
- **Plan edit safety**: writes always go to a branch (never directly to `main`). The conflict detector blocks save when an `agent:go` issue's PR touches the same plan file.
- **External calls**: limited to `api.github.com` and `*.githubusercontent.com`. No telemetry endpoints, no third-party analytics.
- **Subprocess sandboxing**: Copilot CLI runs as a child process inheriting only the user's environment minus `KERRIGAN_*` variables that may contain configured paths.
- **Static scan in CI**: `dashboard-build.yml` runs `gitleaks` and a custom check that fails the build if any `gh auth token` output is logged, written to a file, or passed to a non-allowlisted process.

## Open questions

- Whether to ship the kerrigan-mcp server as a separate binary or bundle it inside the Tauri sidecar process. Decision deferred to M5 spike.
- Whether plan-edit branches should target `main` directly or a per-project `plan-edits` integration branch. Decision deferred to M6 spike.
