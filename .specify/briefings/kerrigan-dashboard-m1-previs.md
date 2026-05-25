# Briefing: kerrigan-dashboard-m1-previs

## Objective

Produce the pre-visualization for the `kerrigan-dashboard` project: a single static HTML file with embedded CSS and JavaScript that demonstrates the portfolio view, the project detail view (3-pane layout), and three variants of the PR-flow show-stopper animation. This is a design-lock artifact — no production framework, no build tooling, no real data — only the visual contract that all subsequent production milestones must match.

## Motivation (read once, do not copy into code)

Per `.github/skills/ui-design-perspective/SKILL.md` principle 1, every UI project must produce a pre-vis HTML+CSS mockup before any production UI is dispatched. The pre-vis lets the conductor (a) confirm the visual identity is right, (b) see the show-stopper element working before committing to the implementation cost, and (c) anchor every subsequent React component in a concrete visual reference. Three animation variants are required so the conductor can pick one based on how it actually feels rather than a verbal description.

## Acceptance criteria

- **AC-1**: `specs/projects/kerrigan-dashboard/previs/index.html` exists, is a single self-contained file under 2,500 lines (CSS + JS inline), and renders without errors in Chromium-based browsers. — test: `tests/projects/kerrigan_dashboard/test_previs_static.py::test_previs_file_exists_and_self_contained` (validates file exists, no `<link rel="stylesheet" href="http`, no `<script src="http`, no external network deps beyond fonts loaded from `fonts.googleapis.com` if any). Level: unit. Environment: cloud-linux.
- **AC-2**: The pre-vis contains a clearly labelled "Portfolio" view showing at least 5 project cards. Each card displays: project name, repo count, current wave indicator, blocked count, intervention count, last-PR-merged timestamp. Cards visually match the `design-references.md` synthesis: 2 neutrals + 1 brand + 1 accent. — test: `tests/projects/kerrigan_dashboard/test_previs_static.py::test_portfolio_section_contains_cards` (parses HTML, asserts a section with `data-view="portfolio"` containing ≥5 elements with `data-component="project-card"`, each containing the six required fields by `data-field` attribute). Level: unit. Environment: cloud-linux.
- **AC-3**: The pre-vis contains a clearly labelled "Project detail" view with a 3-pane layout: left = plan editor (showing rendered markdown stub, no editing interactivity required), center = DAG canvas (showing ≥6 stage nodes connected by edges, with visible status colors covering planned / dispatched / in-review / blocked / merged), right = chat pane (showing ≥3 stub messages: user, agent, tool-call card). — test: `tests/projects/kerrigan_dashboard/test_previs_static.py::test_project_detail_three_panes` (asserts a section with `data-view="project-detail"` containing exactly 3 children with `data-pane` attributes `plan`, `dag`, `chat`; DAG contains ≥6 elements `data-component="stage-node"` and each status string appears in `data-status` attributes). Level: unit. Environment: cloud-linux.
- **AC-4**: The DAG canvas contains a working PR-flow animation that runs without user interaction. The animation must be implementable in three visually distinct variants (particles-as-dots, particles-as-line-trail, particles-as-glow-trail) toggleable via three buttons in a `<div data-component="variant-picker">` block. At least one variant runs by default on page load. All variants respect `prefers-reduced-motion: reduce` (no motion when set). — test: `tests/projects/kerrigan_dashboard/test_previs_static.py::test_animation_variants_present` (asserts three `<button data-variant="...">` elements with values `dots`, `line`, `glow`; asserts a `@media (prefers-reduced-motion: reduce)` CSS block exists that sets `animation: none` or equivalent on the relevant selectors). Level: unit. Environment: cloud-linux.
- **AC-5**: Design budgets (per `ui-design-perspective` principle 4) are honored: extracted color tokens from CSS define ≤2 neutral colors + 1 brand color + 1 accent color (defined as CSS custom properties on `:root`); type scale has 4 or 5 distinct font-size values total across the document; no animation duration exceeds 2000ms (show-stopper allowance) or 300ms for everything else. — test: `tests/projects/kerrigan_dashboard/test_previs_budgets.py::test_color_type_motion_budgets` (parses `:root` custom property block, counts distinct `font-size` declarations, parses all `animation-duration` / `transition-duration` values and asserts the budget). Level: unit. Environment: cloud-linux.
- **AC-6**: The pre-vis renders correctly at four responsive breakpoints (360px, 768px, 1280px, 1920px) — content remains readable, no horizontal scroll except inside intentional scroll containers, the 3-pane layout collapses gracefully on narrow viewports. — test: `tests/projects/kerrigan_dashboard/test_previs_responsive.py::test_responsive_breakpoints` (Playwright headless Chromium loads `file://.../previs/index.html`, screenshots at four widths, asserts `document.documentElement.scrollWidth <= window.innerWidth` at each breakpoint; saves screenshots to `tests/artifacts/previs-<width>.png`). Level: e2e. Environment: cloud-linux.
- **AC-7**: `specs/projects/kerrigan-dashboard/design-references.md` is updated with: (a) final brand color hex chosen, (b) final accent color hex chosen, (c) final type-size values, (d) which animation variant was selected as the default and the reasoning. The "Open visual decisions" section is replaced with a "Decisions locked" section listing each resolution. — test: `tests/projects/kerrigan_dashboard/test_design_references_updated.py::test_decisions_locked_section_present` (asserts `## Decisions locked` heading exists; asserts the four required items are present; asserts no `## Open visual decisions` heading remains). Level: unit. Environment: cloud-linux.
- **AC-8**: `kerrigan check` runs clean; `pytest -q tests/projects/kerrigan_dashboard/` is green; existing test suite remains green (no regressions).

## Scope

- **Touch**:
  - `specs/projects/kerrigan-dashboard/previs/index.html` (new — single self-contained file)
  - `specs/projects/kerrigan-dashboard/previs/README.md` (new — one paragraph: what this is, how to view it, links back to spec.md)
  - `specs/projects/kerrigan-dashboard/design-references.md` (update — replace "Open visual decisions" with "Decisions locked")
  - `tests/projects/__init__.py` (new — if directory doesn't exist)
  - `tests/projects/kerrigan_dashboard/__init__.py` (new)
  - `tests/projects/kerrigan_dashboard/test_previs_static.py` (new — covers AC-1, AC-2, AC-3, AC-4)
  - `tests/projects/kerrigan_dashboard/test_previs_budgets.py` (new — covers AC-5)
  - `tests/projects/kerrigan_dashboard/test_previs_responsive.py` (new — covers AC-6, Playwright)
  - `tests/projects/kerrigan_dashboard/test_design_references_updated.py` (new — covers AC-7)
  - `.github/test-mapping.yml` (add a mapping entry for the new tests directory)
- **Read-only**:
  - `specs/projects/kerrigan-dashboard/spec.md`
  - `specs/projects/kerrigan-dashboard/plan.md`
  - `specs/projects/kerrigan-dashboard/design-references.md` (read for context; only the locked decisions section gets edited)
  - `.github/skills/ui-design-perspective/SKILL.md`
- **Out of scope** (hard limits — emit a block if AC requires going outside):
  - Any production application code (`apps/kerrigan-dashboard/` must not be created in this task)
  - Any framework dependencies (no React, no Vue, no Svelte — vanilla HTML+CSS+JS only)
  - Any build tooling (no Vite, no Webpack, no npm install)
  - Tauri scaffolding (deferred to M2)
  - The Kerrigan MCP server (deferred to M5)
  - Real data integration (no GitHub API calls; all data is fixture-stubbed)
  - Any external CDN dependencies (the pre-vis must be self-contained except optionally a single Google Fonts `<link>` for typography)
  - Plan-parser implementation (`lib/plan-parser.ts` — that's M3)

## Prior decisions

- Stack for production: Tauri 2 + React 19 + Vite + Tailwind + React Flow 12 + Tiptap. Pre-vis is intentionally framework-free so the visual contract is portable. (`plan.md` § Tech stack)
- Show-stopper: PR-flow animation, particles flowing from PR cards into stage nodes. Three variants required for conductor selection. (`spec.md` § Show-stopper)
- Five design references: Linear, Vercel, Retool Workflows, Warp/Cursor, GitHub Projects. (`design-references.md`)
- Brand color leans cool indigo `#5965F2` OR near-cyan `#22D3EE` — pick during pre-vis. (`design-references.md`)
- Status taxonomy (locked in spec AC-005): planned, dispatched, in-review, blocked, needs-attestation, needs-human-test, merged.
- Tests live in `tests/projects/<project-name>/` — repo convention.
- Vanilla HTML+CSS+JS for pre-vis — repo convention from `ui-design-perspective`.

## Relevant skills (preload)

- ui-design-perspective
- briefing-packet
- smoke-test

## Test commands

```bash
# Unit + budget tests
pytest -q tests/projects/kerrigan_dashboard/

# E2E responsive test (requires Playwright + Chromium installed)
pip install playwright && playwright install chromium
pytest -q tests/projects/kerrigan_dashboard/test_previs_responsive.py

# Validators
python -m tools.validators.check_test_mapping
```

## Deliverables checklist

- [ ] `previs/index.html` — portfolio view, project-detail view, 3 animation variants, responsive
- [ ] `previs/README.md` — one paragraph, how to view, link to spec
- [ ] `design-references.md` — "Decisions locked" section replacing "Open visual decisions"
- [ ] Four new pytest files, all green
- [ ] `.github/test-mapping.yml` extended
- [ ] Screenshots in `tests/artifacts/previs-<width>.png` at 360/768/1280/1920
- [ ] Conductor walkthrough: open the file directly in a browser, switch between three animation variants, resize to mobile width — everything works
