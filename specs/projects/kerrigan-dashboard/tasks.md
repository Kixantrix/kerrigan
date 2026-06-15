# Tasks: kerrigan-dashboard

Tasks decompose [`plan.md`](./plan.md) into single-dispatch units. Each task is one cloud-agent issue with its own briefing packet (in `.specify/briefings/<task-id>.md`).

Format: one task → one PR. "Done when" must be objectively checkable. "Links" cite the AC, plan section, or architecture decision. "Dependencies" use the schema from [`_template/tasks.md`](../_template/tasks.md).

Wave structure (from [`plan.md`](./plan.md#sequencing-notes)):

- **wave-1**: M1 (pre-vis) — single task, in flight as issue #288.
- **wave-2**: M2 tasks (Tauri skeleton + portfolio).
- **wave-3**: M3 + M4 tasks parallel.
- **wave-4**: M5 + M6 tasks parallel.
- **wave-5**: M7 + M8 tasks parallel.
- **wave-6**: M9 deferred (cross-project integrated chat).

Within a milestone, tasks are sequenced by their declared dependencies. The conductor regenerates `.specify/waves.yaml` before each dispatch via `kerrigan-conflict-predictor`.

---

## Milestone 1: Pre-vis (in flight)

- [ ] Task M1.1: Pre-vis HTML + animation prototype
  - Done when: `specs/projects/kerrigan-dashboard/previs/index.html` renders the portfolio view, project detail 3-pane, and three show-stopper variants; `design-references.md` "Open visual decisions" section becomes "Decisions locked"
  - Links: spec.md AC-018, AC-019, AC-020; plan.md M1
  - Tracked as: #288

---

## Milestone 2: Tauri skeleton + portfolio (wave-2)

- [ ] Task M2.1: Tauri 2 + Vite + React + TS + Tailwind project scaffold
  - Done when: `apps/kerrigan-dashboard/` builds via `pnpm tauri build` on Windows/macOS/Linux; `pnpm dev` opens a Tauri window with a placeholder route; Tailwind 4 configured with the design tokens from M1; ESLint + Prettier + tsconfig strict pass
  - Links: plan.md § Project layout, § Tech stack; spec.md AC-001 (cold start)
  - Dependencies:
    - ~external:M1.1 (M1 design tokens consumed)
  - Touch: `apps/kerrigan-dashboard/**`
  - Read-only: everything else
  - Tests: Vitest scaffold sanity + a CI step in M2.5's workflow that runs `pnpm -C apps/kerrigan-dashboard tauri build` and asserts the artifact (the existing repo `scripts/smoke.*` are read-only repo-health checks today; extending them to build/launch the dashboard is owned by M2.5)

- [ ] Task M2.2: `lib/projects.ts` — `~/.kerrigan/projects.json` reader + schema validator
  - Done when: TS module reads, validates (zod), and watches the file; emits typed `ProjectConfig[]`; handles missing/malformed file gracefully (returns empty + surfaces error)
  - Links: spec.md scope bullet on multi-repo aggregation (`### In scope (v1)`), AC-002, AC-014, AC-016
  - Dependencies:
    - external:M2.1
  - Touch: `apps/kerrigan-dashboard/src/lib/projects.ts`, `apps/kerrigan-dashboard/src/lib/projects.test.ts`
  - Tests: Vitest unit (8+ cases incl. malformed JSON, missing file, schema violations, hot-reload)

- [ ] Task M2.3: `lib/github.ts` — Octokit wrapper with `gh auth token` shell-out + ETag polling
  - Done when: module exposes `getRepo`, `listOpenPRs`, `listIssues`, `getPRReviews`; auth resolved per-call via `gh auth token` (zero persistence per AC-017); ETag cache implemented; 304 short-circuits; backoff on 403 rate limit
  - Links: plan.md § Tech stack, plan.md § Security; spec.md AC-017 (no token persistence)
  - Dependencies:
    - external:M2.1
  - Touch: `apps/kerrigan-dashboard/src/lib/github.ts`, sibling test
  - Tests: Vitest unit with `nock`-mocked HTTP (10+ cases); explicit assertion that no token is written to disk

- [ ] Task M2.4: Portfolio view + project card component
  - Done when: route `/` renders the card grid with real data via M2.2 + M2.3; each card displays exactly the fields required by AC-002 — project name, repo count, current wave, block count, intervention count, last-PR-merged timestamp; matches pre-vis design tokens; offline indicator (AC-014) when GitHub unreachable; first paint <1s (AC-001)
  - Links: spec.md AC-001, AC-002, AC-014; plan.md M2
  - Dependencies:
    - external:M2.2
    - external:M2.3
  - Touch: `apps/kerrigan-dashboard/src/routes/portfolio/**`, `apps/kerrigan-dashboard/src/components/ProjectCard/**`
  - Tests: Vitest component tests; Playwright E2E asserting first paint + card render

- [ ] Task M2.5: CI `dashboard-build.yml` workflow (Win/macOS/Linux) + extend smoke scripts
  - Done when: `.github/workflows/dashboard-build.yml` builds the Tauri app on all three OSes; lint + Vitest pass; `scripts/smoke.ps1` / `scripts/smoke.sh` extended (behind an opt-in flag or detection of `apps/kerrigan-dashboard/`) to run `pnpm -C apps/kerrigan-dashboard tauri build` and assert the artifact exists; the matrix invokes the extended smoke; artifact uploaded on tag; required-check name documented in playbooks
  - Links: plan.md § CI / build
  - Dependencies:
    - external:M2.1
  - Touch: `.github/workflows/dashboard-build.yml`, `scripts/smoke.ps1`, `scripts/smoke.sh`
  - Tests: workflow green on a draft PR; verify check shows up in branch protection list; extended smoke produces an artifact on each OS

---

## Milestone 3: Project detail + DAG (wave-3, parallel with M4)

- [ ] Task M3.1: Plan markdown parser (`lib/plan-parser.ts`)
  - Done when: parser extracts stages from H2/H3 headings; supports optional YAML frontmatter declaring stage dependencies (`dependencies: [stage-id, ...]`); returns typed graph (`{nodes, edges}`); handles malformed input gracefully with structured errors
  - Links: spec.md OQ-001 (resolves); plan.md M3
  - Dependencies: none (can start in parallel with M2 finish if needed)
  - Touch: `apps/kerrigan-dashboard/src/lib/plan-parser.ts` + test
  - Tests: Vitest unit (15+ cases incl. nested headings, missing frontmatter, circular deps detected, empty plan)

- [ ] Task M3.2: Status taxonomy + derivation
  - Done when: `lib/status.ts` maps a stage's associated PRs/issues/blocks to one of the spec AC-005 statuses — `planned, dispatched, in-review, blocked, needs-attestation, needs-human-test, merged`; rules documented in module header comment; consumes M2.3 GitHub data + M3.1 stage→issue links
  - Links: plan.md M3; spec.md AC-005
  - Dependencies:
    - external:M3.1
    - external:M2.3
  - Touch: `apps/kerrigan-dashboard/src/lib/status.ts` + test
  - Tests: Vitest table-driven (one case per status from AC-005 + multi-repo aggregation per AC-016)

- [ ] Task M3.3: React Flow DAG canvas + auto-layout
  - Done when: project detail route renders the parsed graph as a React Flow canvas with dagre auto-layout; custom stage nodes show name + status color; pan/zoom works; interactive in <1s for ≤200 nodes
  - Links: spec.md AC-003, AC-004, AC-005; plan.md M3
  - Dependencies:
    - external:M3.1
    - external:M3.2
  - Touch: `apps/kerrigan-dashboard/src/routes/project/**`, `apps/kerrigan-dashboard/src/components/Dag/**`
  - Tests: Playwright E2E navigating portfolio → project; visual-regression on three reference plans

- [ ] Task M3.4: Plan editor pane (read-only Tiptap)
  - Done when: project detail layout has a left pane showing the project's plan as rendered markdown via Tiptap (read-only); selecting a node in the DAG scrolls the PlanEditor so the corresponding stage heading is visible (Playwright asserts `heading.isVisibleInViewport()` within 250ms of click)
  - Links: plan.md M3; spec.md AC-008 (prepares for M6)
  - Dependencies:
    - external:M3.3
  - Touch: `apps/kerrigan-dashboard/src/components/PlanEditor/**`
  - Tests: Vitest component test; Playwright assertion that pane renders and that the click→scroll behavior fires

---

## Milestone 4: Chat pane (wave-3, parallel with M3)

- [ ] Task M4.1: `lib/acp-client.ts` — ACP wrapper around `copilot --acp`
  - Done when: TS module spawns `copilot --acp` subprocess, manages JSON-RPC framing, exposes `sendUserTurn(text) -> AsyncIterable<AcpEvent>`; surfaces "copilot CLI missing / too old" errors with actionable messages; clean shutdown on app close
  - Links: plan.md M4; spec.md AC-010
  - Dependencies:
    - ~external:M2.1 (can scaffold against placeholder app)
  - Touch: `apps/kerrigan-dashboard/src/lib/acp-client.ts` + test
  - Tests: Vitest unit with a mocked ACP server (covers session lifecycle, all event types, error paths)

- [ ] Task M4.2: ACP event renderers + chat pane UI
  - Done when: right-pane chat renders `message_chunk` (streaming), `tool_call`, `tool_result`, `thought` as distinct React components; input affordance with submit + cancel; error surface for offline / missing CLI
  - Links: plan.md M4; spec.md AC-010 (vanilla portion)
  - Dependencies:
    - external:M4.1
  - Touch: `apps/kerrigan-dashboard/src/components/Chat/**`
  - Tests: Vitest component tests for each event type; Playwright smoke that opens chat and exchanges one message against a stub backend

---

## Milestone 5: Kerrigan MCP server + chat-driven actions (wave-4, parallel with M6)

- [ ] Task M5.1: `tools/kerrigan-mcp/` scaffold + `kerrigan.dispatch` tool
  - Done when: `tools/kerrigan-mcp/` is a TypeScript MCP server (Node 22) registered via stdio transport; exposes `kerrigan.dispatch` that wraps the existing dispatch flow (calls `tools/create_issues.py` or its TS equivalent); MCP integration test creates a fixture issue
  - Links: plan.md M5; spec.md AC-010, AC-011
  - Dependencies:
    - external:M4.2
  - Touch: `tools/kerrigan-mcp/**`
  - Tests: MCP integration test against a fixture repo (token via `gh auth token`)

- [ ] Task M5.2: `kerrigan.plan-update` MCP tool
  - Done when: tool applies a structured edit (replace stage, add stage, edit stage deps) to a project's plan.md, commits to a branch, opens a draft PR
  - Links: plan.md M5; spec.md AC-008
  - Dependencies:
    - external:M5.1
  - Touch: `tools/kerrigan-mcp/src/tools/plan-update.ts` + test
  - Tests: integration test against the fixture repo asserting the PR opens with the expected diff

- [ ] Task M5.3: `kerrigan.block-resolve` + `kerrigan.conflict-predict` MCP tools
  - Done when: `block-resolve` marks a block resolved in `.specify/blocks/<task>.yaml`, closes the block issue, and re-arms dependent tasks; `conflict-predict` shells out to the existing `kerrigan-conflict-predictor` over a candidate task list and returns the JSON wave map
  - Links: plan.md M5; spec.md AC-011
  - Dependencies:
    - external:M5.1
  - Touch: `tools/kerrigan-mcp/src/tools/block-resolve.ts`, `tools/kerrigan-mcp/src/tools/conflict-predict.ts`, tests
  - Tests: integration tests for each tool

- [ ] Task M5.4: Sidecar wiring + reactive pane refresh
  - Done when: dashboard spawns the MCP server at startup and passes it to `copilot --acp` via `--additional-mcp-config`; dashboard listens to MCP `tool-result` events over a control channel and refreshes the affected pane (plan editor reloads on `plan-update`, DAG re-renders on `dispatch` / `block-resolve`)
  - Links: plan.md M5
  - Dependencies:
    - external:M5.1
    - external:M5.2
    - external:M5.3
    - external:M4.2
  - Touch: `apps/kerrigan-dashboard/src/lib/mcp-sidecar.ts`, integration glue in chat + DAG components
  - Tests: Playwright E2E — chat dispatches via MCP and the DAG updates without reload

---

## Milestone 6: Plan editor (write) + git round-trip (wave-4, parallel with M5)

- [ ] Task M6.1: Tiptap writable + markdown round-trip
  - Done when: plan editor accepts edits; markdown is preserved byte-equivalent for unchanged regions on save; Ctrl-S + blur both save; undo/redo work
  - Links: plan.md M6; spec.md AC-008
  - Dependencies:
    - external:M3.4
  - Touch: `apps/kerrigan-dashboard/src/components/PlanEditor/**`
  - Tests: Vitest property test asserting markdown round-trip for a corpus of sample plans

- [ ] Task M6.2: Branch-per-edit-session + draft PR open
  - Done when: each editing session opens a branch `plan-edits/<timestamp>-<short-sha>`; save commits + pushes to that branch; first save in a session opens a draft PR via Octokit; subsequent saves push commits to the same branch
  - Links: plan.md M6; spec.md AC-009
  - Dependencies:
    - external:M6.1
    - external:M2.3
  - Touch: `apps/kerrigan-dashboard/src/lib/plan-save.ts`
  - Tests: integration test against a fixture repo asserting branch + PR creation

- [ ] Task M6.3: Conflict detection + offline edit queue
  - Done when: if the plan file is touched by an open PR from an `agent:go`-assigned issue, save is blocked and the conflict surfaces in the inbox preview; offline edits serialize to `~/.kerrigan/queue/` and replay on reconnect
  - Links: plan.md M6; spec.md AC-009, AC-015
  - Dependencies:
    - external:M6.2
  - Touch: `apps/kerrigan-dashboard/src/lib/plan-conflict.ts`, `apps/kerrigan-dashboard/src/lib/plan-queue.ts`
  - Tests: Vitest unit (conflict cases); Playwright E2E for offline → online replay

---

## Milestone 7: PR-flow show-stopper animation (wave-5, parallel with M8)

- [ ] Task M7.1: Canvas particle system overlay
  - Done when: lightweight canvas overlay sits on top of the React Flow DAG; emits particles from a source point to a target point; 60fps with ≤20 simultaneous particles; respects `prefers-reduced-motion` (renders static markers)
  - Links: plan.md M7; spec.md § Show-stopper, AC-020
  - Dependencies:
    - external:M3.3
  - Touch: `apps/kerrigan-dashboard/src/components/PrFlowOverlay/**`
  - Tests: Vitest performance harness (frame timing under load); Playwright visual diff against M1 pre-vis chosen variant

- [ ] Task M7.2: PR → stage particle binding + lifecycle states
  - Done when: open PRs render an ongoing streaming particle along the PR-node-to-stage-node edge; merged PRs trigger an absorption animation + node green pulse; closed/abandoned PRs fade their particle
  - Links: plan.md M7; spec.md AC-006, AC-007
  - Dependencies:
    - external:M7.1
    - external:M3.2
  - Touch: `apps/kerrigan-dashboard/src/components/PrFlowOverlay/binding.ts`
  - Tests: Playwright E2E driving fixture PR states; visual diff

---

## Milestone 8: Intervention inbox (wave-5, parallel with M7)

- [ ] Task M8.1: Cross-project inbox aggregator
  - Done when: `lib/inbox.ts` pulls open blocks, `agent:wait + capture` issues, PRs with unresolved review threads, and attestation requests from all projects in `~/.kerrigan/projects.json`; returns a typed unified feed sorted by age
  - Links: plan.md M8; spec.md AC-012
  - Dependencies:
    - external:M2.3
  - Touch: `apps/kerrigan-dashboard/src/lib/inbox.ts` + test
  - Tests: Vitest unit with fixture GitHub responses (12+ cases)

- [ ] Task M8.2: Inbox view + per-item actions
  - Done when: filterable inbox view (by project, type, age); per-item actions `dispatch` (sends to chat with prefilled prompt), `close with reason`, `snooze` all wired and assertable in Playwright; the "process ≥10 items in ≤2 min" target is a **manual walkthrough metric** (SM-001/SM-002 in spec.md) measured at M8 sign-off, not an automated CI gate
  - Links: plan.md M8; spec.md AC-012, AC-013
  - Dependencies:
    - external:M8.1
    - external:M5.1
  - Touch: `apps/kerrigan-dashboard/src/routes/inbox/**`
  - Tests: Playwright E2E walking through filter + dispatch + close (automated gate); manual walkthrough capturing item-throughput at M8 sign-off (manual gate, recorded in PR description)

- [ ] Task M8.3: Mobile-capture triage side panel
  - Done when: clicking a `capture`-labeled item opens a side panel with the captured text and a "draft briefing" button that calls the MCP `kerrigan.plan-update` tool to insert a briefing-shaped block into a draft PR on the target project (briefing drafting is in v1 scope via `plan-update`; a dedicated `kerrigan.briefing-gen` tool is explicitly out of v1 per spec AC-011)
  - Links: plan.md M8; spec.md AC-013, AC-011
  - Dependencies:
    - external:M8.2
    - external:M5.2
  - Touch: `apps/kerrigan-dashboard/src/components/CaptureTriage/**`
  - Tests: Playwright E2E captures → triage → draft PR via `plan-update`

---

## Milestone 9: Cross-project integrated chat (wave-6, deferred to v2)

- [ ] Task M9.1: Workspace-level chat surface + scoped context model
  - Done when: a global chat entrypoint is available from portfolio/inbox; user can scope chat to `all projects` or selected project subset; chat sessions persist with scope metadata; tool-result refreshes fan out only to affected projects; at least one E2E flow validates cross-project query → actionable result links
  - Links: plan.md M9 (deferred); spec.md Goal and scenarios
  - Dependencies:
    - external:M4.2
    - external:M8.2
    - external:M5.4
  - Touch: `apps/kerrigan-dashboard/src/routes/**`, `apps/kerrigan-dashboard/src/components/Chat/**`, `apps/kerrigan-dashboard/src/lib/**`
  - Tests: Vitest unit for scope selection/session model + Playwright E2E for cross-project chat workflow

---

## Notes for the conductor

- Re-run `kerrigan-conflict-predictor` before each wave dispatch; the `Touch` field above is authoritative for overlap detection.
- Update issue numbers next to each `Tracked as:` line as briefings are written and issues are filed.
- Tasks above are sized for one cloud-agent dispatch each (target ≤6h of agent wall time). If a task balloons, split it during briefing-packet drafting; do not over-stuff briefings.
- All `Done when` conditions must map to an automated test per AGENTS.md § Testing.
