# Plan: kerrigan-dashboard

> Each milestone ends with green CI on `main` and a usable surface for the conductor. We ship vertical slices, not horizontal layers.

## Project layout

```
specs/projects/kerrigan-dashboard/
  spec.md                  # the contract (already drafted)
  design-references.md     # visual exemplars (already drafted)
  plan.md                  # this file
  tasks.md                 # generated from this plan
  previs/index.html        # static HTML+CSS+JS mockup (M1 deliverable)
apps/kerrigan-dashboard/   # Tauri app (created in M2)
  src-tauri/               # Rust shell
  src/                     # React + Vite frontend
  package.json
  tauri.conf.json
tools/kerrigan-mcp/        # Kerrigan MCP server (M5)
  src/                     # TypeScript MCP server
  package.json
```

The Tauri app lives under `apps/` so it can coexist with future apps without renaming. The MCP server is under `tools/` alongside our other tools.

## Tech stack (locked from spec)

| Layer | Choice | Rationale |
|---|---|---|
| Shell | Tauri 2 | Smaller than Electron; Rust core; native webview; cross-platform. |
| Frontend | React 19 + Vite | Standard, fast HMR, large ecosystem. |
| Language | TypeScript strict | Per `coding-style.md`. |
| DAG canvas | React Flow 12 | Battle-tested for node-edge UIs; auto-layout via dagre. |
| Plan editor | Tiptap | Block editor with markdown round-trip; AI Toolkit available later. |
| Chat transport | `copilot --acp` subprocess | Authentic Copilot; ACP is purpose-built for embedding. |
| MCP server | TypeScript (Node 22) | Same language as frontend; minimal serialization friction. |
| GitHub API | Octokit | Reference client; ETag support for conditional polling. |
| Auth | `gh auth token` shell-out | Zero token persistence; reuses user's GH CLI session. |
| Styling | Tailwind 4 + design tokens | Per `ui-design-perspective` budgets. |
| Testing | Vitest (unit), Playwright (E2E) | Standard, fast, well-supported in Tauri. |

## Milestones

### M1 — Pre-vis + design lock (no production code)

**Goal**: Static visual prototype that proves the show-stopper animation works and the three-pane layout reads cleanly. Conductor signs off before any production UI is written.

**Deliverables**:
- `previs/index.html` — single static HTML file with embedded CSS+JS. Portfolio view + project detail view + working PR-flow animation prototype with three particle variants (per `design-references.md`).
- `previs/assets/` — any fonts, icons, or images needed.
- Final brand color, exact type scale, motion timings recorded in `design-references.md`.

**Acceptance**: AC-018, AC-019, AC-020. Pre-vis renders correctly in Chrome/Edge/Safari/Firefox; show-stopper animation visible and tasteful.

**Exit criteria**: human sign-off in PR comment.

### M2 — Tauri skeleton + portfolio (read-only)

**Goal**: App launches, reads `~/.kerrigan/projects.json`, renders the portfolio card grid with real data from GitHub. No project detail view yet.

**Deliverables**:
- `apps/kerrigan-dashboard/` initialized with Tauri 2 + Vite + React + TS + Tailwind.
- Portfolio view component matching pre-vis.
- `lib/projects.ts` — reads/validates `~/.kerrigan/projects.json`.
- `lib/github.ts` — Octokit wrapper that shells to `gh auth token` for auth, with ETag-aware polling.
- Project card component showing name, repo count, last-PR-merged timestamp, basic counts (block/intervention placeholders).
- CI: build on Windows + macOS + Linux runners; lint + Vitest unit tests.

**Acceptance**: AC-001, AC-002, AC-014 (offline indicator), AC-017 (no token persistence).

**Exit criteria**: launching the app shows real projects within 1s; CI green on three OSes.

### M3 — Project detail + DAG (read-only)

**Goal**: Clicking a project card opens the project detail view with plan parsed into a DAG. Status colors live. Plan editor pane shows the markdown read-only.

**Deliverables**:
- Plan markdown parser (`lib/plan-parser.ts`) extracting stages from H2/H3 headings + optional frontmatter dependencies. Resolves OQ-001.
- React Flow canvas with custom stage nodes and auto-layout (dagre).
- Status taxonomy mapper: derives node status from associated PRs/issues/blocks.
- Routing between portfolio ↔ project detail.
- Plan editor pane displays markdown (Tiptap read-only mode in this milestone).
- Vitest tests for the parser; Playwright test for the navigation flow.

**Acceptance**: AC-003, AC-004, AC-005, AC-016 (multi-repo PR aggregation in node status derivation).

**Exit criteria**: every project's plan visualizes correctly; status colors match real PR state.

### M4 — Chat pane (ACP, no MCP tools yet)

**Goal**: Right-pane chat backed by `copilot --acp`. Vanilla Copilot — no Kerrigan tools yet. Proves the embedding works end-to-end.

**Deliverables**:
- `lib/acp-client.ts` — TypeScript wrapper around the ACP protocol. Spawns `copilot --acp` subprocess, manages session lifecycle, parses event stream.
- ACP event renderers: `message_chunk`, `tool_call`, `tool_result`, `thought` → React components.
- Input affordance with streaming response display.
- Error surface for "copilot CLI not installed" / version-too-old.
- Vitest tests with a mocked ACP server; Playwright smoke that opens chat and sends one message.

**Acceptance**: AC-010 (vanilla portion).

**Exit criteria**: conductor can converse with Copilot inside the dashboard.

### M5 — Kerrigan MCP server + chat-driven actions

**Goal**: The chat agent gains four tools backed by a local MCP server. Conversation can dispatch tasks, update plans, resolve blocks, predict conflicts.

**Deliverables**:
- `tools/kerrigan-mcp/` — TypeScript MCP server exposing:
  - `kerrigan.dispatch` — wraps existing `tools/create_issues.py` flow (or its TS equivalent).
  - `kerrigan.plan-update` — applies a structured edit to a project's plan file + commits.
  - `kerrigan.block-resolve` — marks a block resolved + closes its issue + reopens dependent tasks.
  - `kerrigan.conflict-predict` — calls existing `kerrigan-conflict-predictor` over a candidate task set.
- Dashboard launches the MCP server as a sidecar and wires it into the `copilot --acp` invocation via `--additional-mcp-config`.
- Dashboard listens to MCP tool-result events and refreshes affected panes (plan editor reloads, DAG re-renders).
- Integration tests: simulate a chat sequence that dispatches a task; verify GitHub issue created.

**Acceptance**: AC-010 (full), AC-011.

**Exit criteria**: a single chat turn ("dispatch the rest of phase 4") creates GitHub issues and the DAG updates without user reload.

### M6 — Plan editor (write) + git round-trip

**Goal**: Plan editor pane becomes writable. Saves commit to a per-edit-session branch and push. Conflict surface for concurrent agent edits.

**Deliverables**:
- Tiptap in writable mode with markdown extension; preserves markdown formatting on save.
- Save-on-blur + Ctrl-S handler.
- Branch strategy: each edit session creates `plan-edits/<timestamp>-<short-sha>` branch; push triggers GitHub PR draft via Octokit. (Decision per recommendation in prior conversation.)
- Conflict detection: if the plan file is touched by an open `agent:go`-assigned issue's PR, block save and surface in inbox.
- Offline queueing: edits made offline serialize to `~/.kerrigan/queue/` and replay on reconnect.

**Acceptance**: AC-008, AC-009, AC-015.

**Exit criteria**: conductor edits a plan, saves, sees a draft PR open in GitHub.

### M7 — PR-flow show-stopper animation

**Goal**: The promised visual lands. PRs flow into plan stages as particles.

**Deliverables**:
- Particle system: lightweight canvas overlay on the React Flow DAG.
- Open PRs render an ongoing streaming particle along the PR-node-to-stage-node edge.
- Merged PRs trigger an absorption animation + node green pulse.
- Animation respects `prefers-reduced-motion`.
- Performance budget: 60fps with up to 20 simultaneous particles.

**Acceptance**: AC-006, AC-007, AC-020.

**Exit criteria**: matches the pre-vis show-stopper variant chosen in M1. Conductor reaction: "this is the unique element of the dashboard."

### M8 — Intervention inbox + mobile-capture triage

**Goal**: Cross-project unified inbox. Mobile captures triagable in two clicks.

**Deliverables**:
- Inbox aggregator pulling from all projects: open blocks, `agent:wait + capture` issues, PRs with unresolved review threads, attestation requests parsed from task ACs.
- Inbox view (filterable by project, type, age).
- Per-item actions: "dispatch" (sends to chat with prefilled prompt), "close with reason", "snooze".
- Mobile-capture triage: side panel renders the captured idea and offers a "draft briefing" action that calls the in-scope `kerrigan.plan-update` MCP tool (M5.2) to insert a briefing-shaped block into a draft PR on the target project. A dedicated `kerrigan.briefing-gen` tool is out of v1 scope per spec AC-011 and is deferred to a future spec amendment.

**Acceptance**: AC-012, AC-013.

**Exit criteria**: conductor processes ≥10 inbox items in ≤2 minutes during walkthrough.

### M9 — Cross-project integrated chat (deferred to v2)

**Goal**: Add a workspace-level chat surface that can operate across multiple projects without forcing a single-project context first.

**Deliverables**:
- Global chat route (or drawer) reachable from portfolio/inbox views.
- Context selector allowing `all projects` or explicit project scopes.
- Session model for chat threads with scope metadata (`global` vs project-bound).
- Tool-call refresh fan-out: tool results invalidate only affected projects/panes.
- Prompt templates for multi-project intents (triage, dispatch, status synthesis).

**Acceptance**: v2 AC amendment required (new ACs for multi-project chat scope, thread persistence, and context safety).

**Exit criteria**: conductor can ask one global question (for example, "what needs intervention across all projects?") and receive a scoped, actionable response with links back to affected projects.

### M10 — Maintenance & enhancements (ongoing)

**Goal**: A living milestone for post-M8 maintenance and dogfood-driven enhancements. Unlike M1–M8 (discrete, sequential), **M10 is open-ended** — new tasks are appended as work is identified (bugs caught while dogfooding, UX refinements, runtime/harness fixes the dashboard surfaces about itself).

**Convention**: dispatch every M10 task as an `M10.x:`-prefixed issue so it links to this stage. That makes the dashboard show its **own** in-flight status (`dispatched` / `in-review` / `merged`) — exercising, on itself, the exact pipeline used to track other projects.

**Deliverables (representative; this list extends over time)**:
- Status accuracy: merged-status data source, milestone↔work auto-linkage, matcher precision.
- Project detail: per-stage PR details panel, sub-milestone grouping, DAG left-to-right spine, legend.
- Runtime: Tauri fs + `gh auth` wiring, offline-reason surfacing, dev-browser harness.
- Cockpit: MCP sidecar, chat-pane mount.

**Acceptance**: each `M10.x` task ships with its own tests + green CI. No single exit criterion.

**Exit criteria**: none — M10 stays open for the life of the project; it is the maintenance lane.

## Cross-cutting concerns

### Testing strategy

- **Unit (Vitest)**: parsers, status derivation, ACP client framing, MCP tool handlers.
- **Integration**: MCP server tests with a real `copilot --acp` subprocess against a fixture repo.
- **E2E (Playwright)**: launches Tauri app, drives portfolio → project → chat flows. Headed in CI for screenshots on failure.
- **Smoke (`scripts/smoke.ps1` / `.sh`)**: `tauri build` + launch + assert window opens + assert one API call succeeds. Required for PR merge per AGENTS.md.
- **Coverage target**: 80% per repo testing standard.

### Security

- AC-017: no token persistence. Auth always via on-demand `gh auth token` shell-out.
- No remote endpoints; the app makes outbound calls only to `api.github.com` and `*.githubusercontent.com`.
- MCP server binds to a Unix socket / named pipe (no network port).
- Tauri allowlist locked to the minimum filesystem + shell scopes required.
- Renderer process has no `tauri.shell.execute` capability except via vetted commands.

### Performance

- First paint of portfolio: < 1s on cold start (AC-001). Achieved via SSR-like prerender in Tauri.
- DAG interactive: < 1s for ≤200 nodes. React Flow virtualization handles larger.
- Polling: ETag-aware; default 60s interval; adaptive backoff.
- Animation: 60fps with ≤20 particles (M7 budget).

### CI / build

- Existing repo workflows handle lint, unit, integration.
- New workflow `dashboard-build.yml` runs `tauri build` on three OSes; uploads artifacts on tag.
- Branch protection: `verify` workflow + new `dashboard-build` must be green to merge.

## Risk register

(See spec.md § Risks. Tracking the same risks here for cross-reference during plan revisions.)

## Sequencing notes

- M1 is a single dispatch (pre-vis is one file). All other milestones decompose into multiple tasks under `tasks.md`.
- M2–M3 are sequential (skeleton then features).
- M4 (chat) can parallelize with M3 (DAG) — different code areas. Acceptable wave parallelism.
- M5 depends on M4. M6 depends on M3.
- M7 depends on M3. Can run in parallel with M5/M6 in a later wave.
- M8 depends on M5 (uses MCP tools internally).
- M9 depends on M4 + M8 and is intentionally deferred to v2.
- M10 is the ongoing maintenance lane — no dependency, never "done"; tasks are appended as work is identified.

Approximate wave structure (`.specify/waves.yaml` generated during `/kerrigan.dispatch`):

```
wave-1: M1 (pre-vis)
wave-2: M2 (Tauri skeleton + portfolio)
wave-3: M3 (DAG) + M4 (chat)            # parallel
wave-4: M5 (MCP) + M6 (plan editor)     # parallel
wave-5: M7 (show-stopper) + M8 (inbox)  # parallel
wave-6: M9 (cross-project chat, v2)     # deferred
ongoing: M10 (maintenance & enhancements)  # living lane, appended over time
```

## Tasks

See [`tasks.md`](./tasks.md) — generated after this plan stabilizes.
