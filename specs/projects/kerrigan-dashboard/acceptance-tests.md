# Acceptance Tests: kerrigan-dashboard (M1 — pre-vis)

This document defines the acceptance tests for the kerrigan-dashboard M1 pre-vis milestone.
All ACs map to automated pytest tests in `tests/projects/kerrigan_dashboard/`.

## AC-1 — Pre-vis file exists and is self-contained

**Test**: `tests/projects/kerrigan_dashboard/test_previs_static.py::TestPrevisFileExistsAndSelfContained::test_previs_file_exists_and_self_contained`

- **Given**: the repository branch contains `specs/projects/kerrigan-dashboard/previs/index.html`
- **Then**: the file exists, has ≤2500 lines, contains no external CSS or JS links other than an optional `fonts.googleapis.com` stylesheet

## AC-2 — Portfolio view with ≥5 project cards

**Test**: `tests/projects/kerrigan_dashboard/test_previs_static.py::TestPortfolioSectionContainsCards::test_portfolio_section_contains_cards`

- **Given**: the pre-vis HTML is parsed
- **Then**: a `<section data-view="portfolio">` exists containing ≥5 `[data-component="project-card"]` elements, each with `data-field` attributes for: `name`, `repo-count`, `wave`, `blocked-count`, `intervention-count`, `last-pr-merged`

## AC-3 — Project-detail 3-pane layout

**Tests**: `tests/projects/kerrigan_dashboard/test_previs_static.py::TestProjectDetailThreePanes`

- **Given**: the pre-vis HTML is parsed
- **Then**: a `<section data-view="project-detail">` exists with exactly 3 children carrying `data-pane` values `plan`, `dag`, `chat`
- **And**: the DAG pane contains ≥6 `[data-component="stage-node"]` elements whose `data-status` attributes collectively cover `planned`, `dispatched`, `in-review`, `blocked`, `merged`
- **And**: the chat pane contains ≥3 stub messages

## AC-4 — Animation variants

**Tests**: `tests/projects/kerrigan_dashboard/test_previs_static.py::TestAnimationVariantsPresent`

- **Given**: the pre-vis HTML is parsed
- **Then**: a `[data-component="variant-picker"]` element exists containing exactly 3 `<button data-variant="...">` elements with values `dots`, `line`, `glow`
- **And**: the CSS includes a `@media (prefers-reduced-motion: reduce)` block that sets `animation: none`

## AC-5 — Design budgets

**Tests**: `tests/projects/kerrigan_dashboard/test_previs_budgets.py::TestColorTypeBudgets` and `::TestMotionBudgets`

- **Given**: the pre-vis CSS is parsed
- **Then**: `:root` defines ≤2 neutral color custom properties + 1 brand + 1 accent
- **And**: 4 or 5 distinct `font-size` pixel values appear across the document
- **And**: no `animation-duration` exceeds 2000ms; no `transition-duration` exceeds 300ms

## AC-6 — Responsive at four breakpoints

**Test**: `tests/projects/kerrigan_dashboard/test_previs_responsive.py::TestResponsiveBreakpoints::test_responsive_breakpoints`

- **Given**: the pre-vis is loaded in Playwright headless Chromium at viewport widths 360px, 768px, 1280px, 1920px
- **Then**: `document.documentElement.scrollWidth <= window.innerWidth` at each breakpoint (no horizontal overflow)
- **And**: screenshots saved to `tests/artifacts/previs-<width>.png`

## AC-7 — Design references updated

**Tests**: `tests/projects/kerrigan_dashboard/test_design_references_updated.py::TestDesignReferencesUpdated`

- **Given**: `specs/projects/kerrigan-dashboard/design-references.md` is read
- **Then**: the file contains a `## Decisions locked` heading
- **And**: it does not contain `## Open visual decisions`
- **And**: the locked section documents brand color hex, accent color hex, type scale values, and the chosen default animation variant

## AC-8 — No regressions

- **Test**: `pytest -q tests/projects/kerrigan_dashboard/` is fully green
- **Test**: `pytest -q tests/` (excluding projects/) shows no regressions vs. the pre-M1 baseline
