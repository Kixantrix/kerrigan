# Acceptance tests: kerrigan-dashboard

Each test below maps to one AC from [`spec.md`](./spec.md) and the corresponding task in [`tasks.md`](./tasks.md). Tests are sized at the unit / integration / E2E level appropriate to the AC and are owned by the milestone that introduces the feature.

Test locations (created by the corresponding tasks):

- `apps/kerrigan-dashboard/src/**/*.test.ts(x)` — Vitest unit + component
- `apps/kerrigan-dashboard/tests/e2e/**.spec.ts` — Playwright E2E
- `tools/kerrigan-mcp/test/**.test.ts` — MCP integration
- `tests/projects/kerrigan_dashboard/**.py` — pre-vis + cross-cutting checks
- `scripts/smoke.ps1` / `.sh` — build + launch smoke

## AC-001: Cold start <1s to portfolio view

- [ ] **Given** the app is launched from cold **When** the window appears **Then** the portfolio view is rendered within 1s measured from process start (Task M2.4 — Playwright `e2e/portfolio.spec.ts` `cold-start-under-1s`)

## AC-002: Portfolio lists every project from `~/.kerrigan/projects.json`

- [ ] **Given** a `~/.kerrigan/projects.json` fixture with three projects **When** the portfolio renders **Then** three cards appear each showing name, repo count, current wave, block count, intervention count, last-PR-merged timestamp (Task M2.4 — `portfolio.spec.ts` `renders-all-projects`)

## AC-003: Portfolio → project detail navigation <500ms

- [ ] **Given** a rendered portfolio card **When** the card is clicked **Then** the project detail view replaces the portfolio within 500ms (Task M3.3 — `project-detail.spec.ts` `nav-under-500ms`)

## AC-004: DAG renders one node per plan stage

- [ ] **Given** a fixture plan with N H2 stage headings **When** the project detail opens **Then** the React Flow canvas renders exactly N nodes (Task M3.3 — `dag.spec.ts` `one-node-per-stage`, parser covered by `plan-parser.test.ts`)

## AC-005: DAG node status color taxonomy

- [ ] **Given** stages mapped to each status (planned, dispatched, in-review, blocked, needs-attestation, needs-human-test, merged) **When** the DAG renders **Then** each node shows the matching color from the locked taxonomy (Task M3.2 + M3.3 — `status.test.ts` table + `dag.spec.ts` `colors-by-status`)

## AC-006: PR opened → particle within 5s of poll detection

- [ ] **Given** a tracked repo with a fixture "open PR" event **When** the poll cycle completes **Then** a particle animates from a PR card into the matching stage node within 5s (Task M7.2 — `pr-flow.spec.ts` `open-pr-emits-particle`, fake clock for poll interval)

## AC-007: PR merged → absorb + green pulse

- [ ] **Given** a particle in flight for a PR **When** the PR transitions to merged **Then** the particle absorbs into the node and the node pulses green (Task M7.2 — `pr-flow.spec.ts` `merge-absorb-and-pulse`)

## AC-008: Plan editor round-trip with no fidelity loss

- [ ] **Given** a corpus of sample plan markdown files **When** loaded into Tiptap and saved unchanged **Then** the saved output is byte-equivalent to the input (Task M6.1 — property test `plan-editor.test.ts` `round-trip-byte-equivalent`)

## AC-009: Save commits to per-session branch + DAG re-renders <2s

- [ ] **Given** an active editing session **When** Ctrl-S or blur fires **Then** a commit is pushed to `plan-edits/<timestamp>-<sha>` and the DAG re-renders within 2s of save completion (Task M6.2 — `plan-save.spec.ts` `commits-and-rerenders`)

## AC-010: Chat pane spawns `copilot --acp` and streams to rich components

- [ ] **Given** a project is opened **When** the chat pane mounts **Then** a `copilot --acp` subprocess is spawned and `message_chunk`, `tool_call`, `tool_result`, `thought` events render as distinct React components (Task M4.1 + M4.2 — `acp-client.test.ts` with mock ACP, `chat.spec.ts` `rich-renderers`)

## AC-011: MCP tools invocation refreshes the relevant pane

- [ ] **Given** the chat agent invokes `kerrigan.dispatch`, `kerrigan.plan-update`, `kerrigan.block-resolve`, or `kerrigan.conflict-predict` **When** the tool returns **Then** the affected pane (DAG / plan editor / inbox) refreshes without manual reload (Task M5.4 — `mcp-sidecar.spec.ts` `tool-result-refreshes-pane` for each tool)

## AC-012: Inbox aggregates across all projects

- [ ] **Given** fixtures across three projects with open blocks, attestation requests, `agent:wait + capture` issues, and PRs with unresolved review threads **When** the inbox loads **Then** all items appear in the unified feed (Task M8.1 — `inbox.test.ts` `aggregates-across-projects`)

## AC-013: Inbox items link to source + disappear when resolved

- [ ] **Given** an inbox item of each type **When** clicking the item **Then** navigation lands on the source DAG node / PR / issue; **When** the source is resolved **Then** the item disappears on next sync (Task M8.2 — `inbox.spec.ts` `links-and-removes-on-resolve`)

## AC-014: Offline indicator + no crash

- [ ] **Given** the GitHub API is unreachable **When** the portfolio loads **Then** cached state is displayed with a visible "offline — last synced HH:MM" indicator and no app crash (Task M2.4 — `portfolio.spec.ts` `offline-indicator`, with intercepted network)

## AC-015: Offline edit queue + conflict surface

- [ ] **Given** the app is offline **When** the user edits and saves a plan **Then** the edit serializes to `~/.kerrigan/queue/`; **When** connectivity returns **Then** the edit replays; **When** the remote plan diverged **Then** an inbox item surfaces (Task M6.3 — `plan-queue.test.ts` + `plan-conflict.spec.ts`)

## AC-016: Multi-repo PR aggregation on DAG

- [ ] **Given** a project entry with three repos and PRs in each **When** the DAG renders **Then** the union of all PRs informs node status (Task M3.2 — `status.test.ts` `multi-repo-aggregation`)

## AC-017: No persistent credential storage

- [ ] **Given** the app runs through a full session including GitHub API calls **When** the app data directory is scanned post-shutdown **Then** no GitHub token, OAuth secret, or session cookie is present (Task M2.3 — `github.test.ts` `no-token-on-disk` asserts no token is written during API calls; a Playwright post-shutdown scan of `~/.kerrigan/` is added in M2.4 as part of the offline-indicator E2E and fails the build if any string matches `ghp_`, `github_pat_`, or `gho_`)

## AC-018: Pre-vis HTML exists and matches design references

- [ ] **Given** the merged M1 deliverable **When** opening `specs/projects/kerrigan-dashboard/previs/index.html` in a modern browser **Then** the portfolio + project detail + show-stopper variants render and visually match `design-references.md` (Task M1.1 — `tests/projects/kerrigan_dashboard/test_previs_static.py`)

## AC-019: Color / type / motion budgets

- [ ] **Given** the pre-vis HTML and the production app CSS **When** the budget checker scans declared tokens **Then** ≤2 neutrals + 1 brand + 1 accent, 4–5 type sizes, all transitions ≤300ms (show-stopper allowed ≤2s exception) (Task M1.1 + M2.1 — `tests/projects/kerrigan_dashboard/test_previs_budgets.py` and a CSS-token lint rule in `apps/kerrigan-dashboard/`)

## AC-020: Exactly one show-stopper element

- [ ] **Given** the rendered dashboard in any view **When** screening for high-weight visual elements (motion + saturation + size) **Then** exactly one element qualifies — the PR-flow animation (Task M1.1 + M7.1 — manual checkpoint at M1 sign-off + `pr-flow.spec.ts` `single-show-stopper`)

## Cross-cutting tests

- [ ] **Smoke (current state)**: `scripts/smoke.ps1` / `.sh` perform read-only repo health checks (validators, no build/launch). They gate PR merge today.
- [ ] **Smoke (after M2.5)**: M2.5 extends `scripts/smoke.*` so that when `apps/kerrigan-dashboard/` is present they additionally run `pnpm -C apps/kerrigan-dashboard tauri build`, assert the artifact exists, and (on the OSes where it's feasible in CI) launch the binary and assert one GitHub API call succeeds. The extended smoke continues to gate PR merge per [AGENTS.md](../../../AGENTS.md).
- [ ] **Build matrix**: `dashboard-build.yml` runs on Windows / macOS / Linux runners; lint + Vitest + extended smoke pass on each.
- [ ] **Coverage**: ≥80% line coverage on `apps/kerrigan-dashboard/src/lib/**` and `tools/kerrigan-mcp/src/**` (the logic-heavy modules) per repo testing standard.

## Notes

- ACs that span multiple milestones (e.g., AC-010 covers M4 vanilla + M5 MCP wiring) get one test per milestone slice rather than one monolithic test.
- Visual / motion ACs (AC-019, AC-020) blend automated linting with a manual sign-off checkpoint at M1 — the M7 production implementation re-asserts via Playwright visual diff against the M1 chosen variant.
- The pre-vis tests under `tests/projects/kerrigan_dashboard/` are filed in the existing Python test tree so they run inside the current `verify` workflow without waiting for the Tauri app to land.
