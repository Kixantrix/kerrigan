@copilot please iterate the pre-vis on this branch with the following changes. Treat this as the design-lock refinement pass before M1 merges — keep the existing structure, don't rebuild.

## Hard invariant: NO SCROLL

At 1280×800 and 1920×1080, every top-level view (Portfolio, Project Detail) must fit in the viewport without vertical scroll. Overflow goes to drawers/tabs/accordion collapse — never scroll. Add Playwright assertions at `tests/projects/kerrigan_dashboard/test_previs_responsive.py` (or extend existing) that `document.documentElement.scrollHeight <= window.innerHeight + 1` for both viewports on both views.

## Spec fix (BLOCKER — do this first)

The chat panel currently shows a `kerrigan.status` tool call. AC-011 of `specs/projects/kerrigan-dashboard/spec.md` caps v1 MCP tools at exactly four: `kerrigan.dispatch, kerrigan.plan-update, kerrigan.block-resolve, kerrigan.conflict-predict`. Replace the example tool call with `kerrigan.plan-update` returning current plan state. No other tool names in v1 pre-vis.

## Layout changes

### Project Detail panes (1280+)
- Plan pane: widen at the expense of DAG. Target ratio ~ Plan 38% · DAG 37% · Chat 25%. Chat width is sacrosanct at 25%.
- DAG retains all node states; no functional change.

### Plan pane → accordion
- Milestones collapsed by default, render as one-line rows: `M3 ▸ Plan editor · 5/7 tasks · in-review`.
- Click expands inline; only one milestone open at a time (closing-others behavior).
- On initial load: auto-expand the milestone whose status is `in-review`, else `dispatched`, else first `planned`.
- Expanded milestone shows task list: `● ID · short title · AC-NNN refs · PR# (if dispatched)` — one row per task, no wrapping.
- Free vertical room from collapsed siblings is what makes the open one fit without scroll.

### Strip redundant status signals
- Project Detail header: remove the trio of status chips (`1 block / healthy / needs attest`) — duplicates Portfolio cards + DAG colors.
- Subtitle counter "2 need intervention" — remove.
- `merged Xh ago` timestamps: keep on Portfolio cards only; remove from Project Detail header.
- Wave info on Portfolio cards: keep. Remove standalone wave repetition elsewhere.

### New drawers (skeleton only — pre-vis fidelity, not full functionality)

Both are right-edge slide-in drawers. Activated by header icon buttons. Drawers overlay content; they don't push panes.

1. **Blocks drawer**: list of open `.specify/blocks/*.yaml` items across the portfolio. Each entry: task-id · project · reason · recommendation · "Resolve" CTA. Empty state: "No blocks. Carry on."
2. **Capture inbox drawer**: list of `is:open label:agent:wait label:capture no:assignee` items (mobile captures). Each entry: title · age · "Triage" CTA (refine → dispatch / close). Empty state: "Inbox clear."

Both drawers must obey the no-scroll rule (their *contents* may scroll inside the drawer; the underlying view does not).

### Wave conflict view → DAG canvas mode toggle

Add a toggle in the DAG canvas toolbar: `Status | Waves`. In Waves mode, color nodes by wave (Wave 1, 2, 3, 4 distinct hues; merged stays distinct), and overlay translucent rectangles grouping nodes in the same wave. Don't add a new pane.

## Files in scope

- `specs/projects/kerrigan-dashboard/previs/index.html`
- `specs/projects/kerrigan-dashboard/previs/README.md` (update AC mapping for the new surfaces)
- `tests/projects/kerrigan_dashboard/test_previs_static.py` (assert no `kerrigan.status` string in HTML; assert presence of drawer markup)
- `tests/projects/kerrigan_dashboard/test_previs_responsive.py` (no-scroll assertion at 1280 and 1920 on both views; existing 360/768 assertions stay)
- `tests/artifacts/previs-*.png` — regenerate

## Out of scope

- Functional logic (this stays a static HTML mockup).
- Adding new MCP tools to AC-011 — the four are the cap.
- Touching anything outside `specs/projects/kerrigan-dashboard/previs/` and the test files listed.
- Mobile (360) layout changes — capture-only path is correct as-is.

## Done when

- All Playwright responsive tests green (including new no-scroll assertions at 1280/1920).
- `kerrigan check` passes.
- No `kerrigan.status` string anywhere in the HTML or chat fixtures.
- Plan accordion: open one, closes others; only one open milestone at a time.
- Blocks drawer + Capture drawer both reachable from header buttons; both render with sample data and an empty state.
- DAG Status|Waves toggle works.
- Updated screenshots committed.

Push to this same branch.
