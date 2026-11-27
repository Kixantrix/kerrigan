# Deliverables index for kerrigan-dashboard M2–M8

Each line below is one deliverable bullet from `plan.md` (§ Milestones, plus the
smoke extension from § Cross-cutting concerns → Testing strategy and the
workflow from § CI / build), given a stable ID so a plan can say which task
covers it. Text is quoted or lightly shortened from `plan.md`; `plan.md` and
`spec.md` stay authoritative.

Path convention: module names written as `lib/<name>.ts` in `plan.md` live at
`apps/kerrigan-dashboard/src/lib/<name>.ts`.

"Required touch" lists the paths (or the area) the covering task's `touch`
must include, because `plan.md` names them for that deliverable.

| ID | Milestone | Deliverable | Required touch |
|---|---|---|---|
| M2-D1 | M2 | `apps/kerrigan-dashboard/` initialized with Tauri 2 + Vite + React + TS + Tailwind (project layout: `src-tauri/`, `src/`, `package.json`, `tauri.conf.json`) | `apps/kerrigan-dashboard/package.json`, `apps/kerrigan-dashboard/tauri.conf.json` |
| M2-D2 | M2 | Portfolio view component matching pre-vis | — |
| M2-D3 | M2 | `lib/projects.ts` — reads/validates `~/.kerrigan/projects.json` | `apps/kerrigan-dashboard/src/lib/projects.ts` |
| M2-D4 | M2 | `lib/github.ts` — Octokit wrapper that shells to `gh auth token` for auth, with ETag-aware polling | `apps/kerrigan-dashboard/src/lib/github.ts` |
| M2-D5 | M2 | Project card component showing name, repo count, last-PR-merged timestamp, basic counts | — |
| M2-D6 | M2 | CI: new workflow `dashboard-build.yml` — `tauri build` on Windows + macOS + Linux runners; lint + Vitest | `.github/workflows/dashboard-build.yml` |
| M2-D7 | M2 | Smoke: extend the repository smoke scripts (`scripts/smoke.ps1` / `.sh`) to `tauri build` + launch + assert window opens + assert one API call succeeds | `scripts/smoke.ps1`, `scripts/smoke.sh` |
| M3-D1 | M3 | Plan markdown parser (`lib/plan-parser.ts`) extracting stages from H2/H3 headings + optional frontmatter dependencies | `apps/kerrigan-dashboard/src/lib/plan-parser.ts` |
| M3-D2 | M3 | React Flow canvas with custom stage nodes and auto-layout (dagre) | — |
| M3-D3 | M3 | Status taxonomy mapper: derives node status from associated PRs/issues/blocks | — |
| M3-D4 | M3 | Routing between portfolio ↔ project detail | — |
| M3-D5 | M3 | Plan editor pane displays markdown (Tiptap read-only mode) | — |
| M4-D1 | M4 | `lib/acp-client.ts` — spawns `copilot --acp`, manages session lifecycle, parses event stream | `apps/kerrigan-dashboard/src/lib/acp-client.ts` |
| M4-D2 | M4 | ACP event renderers: `message_chunk`, `tool_call`, `tool_result`, `thought` → React components | — |
| M4-D3 | M4 | Input affordance with streaming response display | — |
| M4-D4 | M4 | Error surface for "copilot CLI not installed" / version-too-old | — |
| M5-D1 | M5 | MCP tool `kerrigan.dispatch` in `tools/kerrigan-mcp/` | something under `tools/kerrigan-mcp/` |
| M5-D2 | M5 | MCP tool `kerrigan.plan-update` | something under `tools/kerrigan-mcp/` |
| M5-D3 | M5 | MCP tool `kerrigan.block-resolve` | something under `tools/kerrigan-mcp/` |
| M5-D4 | M5 | MCP tool `kerrigan.conflict-predict` | something under `tools/kerrigan-mcp/` |
| M5-D5 | M5 | Dashboard launches the MCP server as a sidecar and wires it into `copilot --acp` via `--additional-mcp-config` | — |
| M5-D6 | M5 | Dashboard listens to MCP tool-result events and refreshes affected panes | — |
| M6-D1 | M6 | Tiptap in writable mode with markdown extension; preserves markdown formatting on save | — |
| M6-D2 | M6 | Save-on-blur + Ctrl-S handler | — |
| M6-D3 | M6 | Branch strategy: `plan-edits/<timestamp>-<short-sha>` branch per edit session; push opens a GitHub draft PR via Octokit | — |
| M6-D4 | M6 | Conflict detection: block save when an open `agent:go` issue's PR touches the plan file; surface in inbox | — |
| M6-D5 | M6 | Offline queueing: offline edits serialize to `~/.kerrigan/queue/` and replay on reconnect | — |
| M7-D1 | M7 | Particle system: lightweight canvas overlay on the React Flow DAG | — |
| M7-D2 | M7 | Open PRs render an ongoing streaming particle along the PR-node-to-stage-node edge | — |
| M7-D3 | M7 | Merged PRs trigger an absorption animation + node green pulse | — |
| M7-D4 | M7 | Animation respects `prefers-reduced-motion` | — |
| M7-D5 | M7 | Performance budget: 60fps with up to 20 simultaneous particles | — |
| M8-D1 | M8 | Inbox aggregator pulling from all projects: open blocks, `agent:wait + capture` issues, PRs with unresolved review threads, attestation requests | — |
| M8-D2 | M8 | Inbox view (filterable by project, type, age) | — |
| M8-D3 | M8 | Per-item actions: "dispatch" (sends to chat with prefilled prompt), "close with reason", "snooze" | — |
| M8-D4 | M8 | Mobile-capture triage: side panel renders the captured idea + suggests a briefing draft via chat MCP `briefing-gen` tool | — |

## Consumption edges

`A → B` means B consumes A's output (as stated in `plan.md`), so every task
covering B must depend, directly or through other tasks, on every task that
covers A (unless one task covers both).

- Scaffold: `M2-D1 →` every other deliverable except `M5-D1`–`M5-D4`
  (everything else lives in, builds, or runs the app the scaffold creates).
- `M2-D3 → M2-D2`, `M2-D4 → M2-D2`, `M2-D5 → M2-D2` (portfolio renders cards
  with real data from `projects.json` and GitHub).
- `M2-D4 → M3-D3` (status is derived from GitHub PRs/issues).
- `M3-D1 → M3-D2`, `M3-D3 → M3-D2` (the canvas renders the parsed plan with
  status colors).
- `M4-D1 → M4-D2` (renderers consume the ACP event stream).
- Milestone rules from § Sequencing notes: every M4 deliverable → every M5
  deliverable ("M5 depends on M4"); every M3 deliverable → every M6
  deliverable ("M6 depends on M3").
- `M5-D1`, `M5-D2`, `M5-D3`, `M5-D4 → M5-D5` (the sidecar launches the server
  that exposes the tools).
- `M2-D4 → M6-D3` (draft PR opened via Octokit).
- `M6-D3 → M6-D4`, `M6-D3 → M6-D5` (conflict check and offline replay wrap the
  save/push path).
- `M3-D2 → M7-D1` (overlay sits on the React Flow DAG); `M7-D1 → M7-D2`,
  `M7-D1 → M7-D3` (PR particles use the particle system).
- `M8-D1 → M8-D2`, `M8-D2 → M8-D4` (view shows the aggregated feed; triage
  opens from an inbox item); `M5-D1 → M8-D3`, `M5-D1 → M8-D4` (inbox actions
  and triage drive the chat's MCP tools).
