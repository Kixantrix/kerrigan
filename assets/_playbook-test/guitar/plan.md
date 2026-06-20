# Plan — Guitar playbook test (Track B)

> Toolchain choice and design notes for `assets/_playbook-test/guitar/`.

## Toolchain choice

**Python + ezdxf** (headless, code-first, no GUI required).

| Candidate | Decision |
|---|---|
| **build123d** | Default per playbook; skipped here because the test slice is 2D-only and build123d's install footprint (OCC kernel) is heavy for a CI environment. |
| **CadQuery** | Same trade-off as build123d — full 3D kernel for a 2D cut template is overkill. |
| **ezdxf** | ✅ Chosen — pure-Python, headless, deterministic DXF read/write; no native dependencies; minimal install (`pip install ezdxf`). Sufficient for 2D CNC outlines and brass laser templates. Upgrade to build123d when 3D solids / STEP exports are needed. |
| **OpenSCAD** | No Python API; harder to assert programmatically. |

Record: `ezdxf>=1.4.4`, added to `requirements.txt`.

## Component breakdown

| Component | Source | Export | Notes |
|---|---|---|---|
| Headstock outline | `source/headstock.py` | `exports/headstock.dxf` | Filleted rectangle; layers OUTLINE + NUT |
| Brass logo | `source/brass_logo.py` | `exports/brass_logo.dxf` | Frame; layers LOGO_OUTER + LOGO_INNER |

## Shared parameters (`shared/params.yaml`)

All linear values in mm.

| Parameter | Default | Role |
|---|---|---|
| `nut_width_mm` | 43.0 | Neck width at nut; drives headstock bottom reference |
| `headstock_length_mm` | 190.0 | Overall headstock length |
| `headstock_width_mm` | 80.0 | Maximum headstock width |
| `headstock_thickness_mm` | 15.0 | Blank thickness (metadata) |
| `stock_thickness_mm` | 15.0 | CNC stock thickness |
| `bit_radius_mm` | 3.175 | Router bit radius (1/8"); used for corner fillets |
| `logo_margin_mm` | 5.0 | Clearance between logo edge and headstock outline |
| `brass_thickness` | `"0.5mm"` | SendCutSend stocked thickness |
| `min_feature_mm` | 0.508 | 0.02" brass minimum feature (SendCutSend rule) |
| `kerf_mm` | 0.3 | Laser kerf midpoint estimate |

## Tolerances

- Corner fillets = `bit_radius_mm` (no sharp corners narrower than the bit).
- Logo wall thickness = 2.0 mm >> `min_feature_mm + kerf/2` = 0.658 mm.
- DXF units: mm (`$INSUNITS = 4`).

## Acceptance criteria → tests

| AC | Test in `tests/test_guitar_playbook.py` |
|---|---|
| Headstock DXF regenerates in correct units | `test_headstock_dxf_units` |
| Logo bbox ≤ headstock minus margin | `test_logo_bbox_within_headstock` |
| Logo passes brass gate (min feature ≥ 0.02″) | `test_brass_manufacturability` |
| Changing `nut_width_mm` propagates to DXF | `test_parametric_propagation` |
| Re-running build is deterministic | `test_build_determinism` |

## Out of scope

Body, neck, fretboard, other parts; real vendor orders; CNC execution; anything
outside `assets/_playbook-test/guitar/`.
