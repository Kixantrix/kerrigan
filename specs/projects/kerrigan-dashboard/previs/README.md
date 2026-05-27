# kerrigan-dashboard · Pre-vis (M1)

This is the design-lock pre-visualization for the kerrigan-dashboard project — a single self-contained `index.html` file (HTML + CSS + JS, no build tooling, no framework) that demonstrates the portfolio card grid, the project-detail three-pane layout (plan accordion · DAG canvas · chat), and three variants of the PR-flow show-stopper animation (dots, line trail, glow trail). Open `index.html` directly in any Chromium-based browser; no server required.

**Surfaces (M1 design-lock refinement):**
- **Portfolio view** — 5 project cards with health pills, wave badges, and all 6 required `data-field` attributes. No vertical document scroll at 1280×800 or 1920×1080.
- **Project Detail view** — 3-pane CSS grid (Plan 38% · DAG 37% · Chat 25%); fits viewport without document scroll at 1280×800 and 1920×1080.
- **Plan pane accordion** — milestones collapsed by default as one-line rows; click expands; only one milestone open at a time; auto-expands the `in-review` milestone (M3) on load.
- **DAG canvas** — 6 stage nodes covering all status variants; Status | Waves mode toggle in the toolbar (Waves mode colors nodes by wave and overlays translucent group rectangles); three PR-flow animation variants.
- **Blocks drawer** — right-edge slide-in overlay (⚡ header button); lists open blocks with task-id, project, reason, recommendation, and Resolve CTA.
- **Capture inbox drawer** — right-edge slide-in overlay (📥 header button); lists unassigned mobile captures with title, age, and Triage CTA.
- **Chat pane** — uses only v1 MCP tools: `kerrigan.dispatch`, `kerrigan.plan-update`, `kerrigan.block-resolve`, `kerrigan.conflict-predict`.

See [`../spec.md`](../spec.md) for the full product spec and acceptance criteria, and [`../design-references.md`](../design-references.md) for the locked visual decisions this mockup implements.
