# Test Plan: kerrigan-dashboard

> **Status**: M1 — pre-vis only. Production test plan (integration, E2E, performance) is written during M2+.

## M1 Pre-vis tests

| ID | Test file | Level | Environment | Description |
|---|---|---|---|---|
| M1-T1 | `tests/projects/kerrigan_dashboard/test_previs_static.py` | unit | cloud-linux | File exists, self-contained; portfolio cards; 3-pane layout; animation variants |
| M1-T2 | `tests/projects/kerrigan_dashboard/test_previs_budgets.py` | unit | cloud-linux | Color token budget, font-size count, motion duration budget |
| M1-T3 | `tests/projects/kerrigan_dashboard/test_previs_responsive.py` | e2e | cloud-linux | Playwright: no horizontal overflow at 360/768/1280/1920px |
| M1-T4 | `tests/projects/kerrigan_dashboard/test_design_references_updated.py` | unit | cloud-linux | design-references.md has Decisions locked section |

## Test commands

```bash
# All M1 tests
pytest -q tests/projects/kerrigan_dashboard/

# Responsive (requires Playwright Chromium)
pip install playwright && playwright install chromium
pytest -q tests/projects/kerrigan_dashboard/test_previs_responsive.py
```
