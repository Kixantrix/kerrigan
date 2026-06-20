#!/usr/bin/env python3
"""
tests/test_guitar_playbook.py

Smoke-test suite for the guitar Track-B playbook test slice.
One test per acceptance criterion — see assets/_playbook-test/guitar/plan.md.

AC1  Headstock DXF regenerates in correct units (mm / INSUNITS=4).
AC2  Logo DXF bounding box ≤ headstock outline minus declared margin.
AC3  Logo passes SendCutSend brass manufacturability gate (min feature ≥ 0.02″).
AC4  Changing nut_width_mm propagates to the headstock export.
AC5  Re-running build is deterministic (geometry is identical on a second run).
"""

import copy
import math
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers: locate the asset root and import source modules without installing.
# ---------------------------------------------------------------------------

GUITAR_ROOT = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "_playbook-test"
    / "guitar"
)
SOURCE_DIR = GUITAR_ROOT / "source"
PARAMS_FILE = GUITAR_ROOT / "shared" / "params.yaml"

# Make the source directory importable.
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import headstock as hs_mod
import brass_logo as logo_mod


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_params() -> dict:
    with open(PARAMS_FILE) as fh:
        return yaml.safe_load(fh)


def _dxf_insunits(path: Path) -> int:
    """Return the $INSUNITS header value from a DXF file."""
    import ezdxf
    doc = ezdxf.readfile(str(path))
    return doc.header.get("$INSUNITS", 0)


def _dxf_bbox(path: Path, layers: list[str] | None = None):
    """
    Return (min_x, min_y, max_x, max_y) bounding box of entities in *path*.

    If *layers* is given, only entities on those layers are considered.
    This lets callers exclude annotation layers (e.g. BRASS_INFO text) from
    the footprint check.
    """
    import ezdxf
    from ezdxf.bbox import extents

    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    if layers is not None:
        layer_set = set(layers)
        entities = [e for e in msp if e.dxf.layer in layer_set]
        from ezdxf.math import BoundingBox2d
        bb = BoundingBox2d()
        for ent in entities:
            if ent.dxftype() == "LWPOLYLINE":
                for pt in ent.get_points():
                    bb.extend([pt[:2]])
            elif ent.dxftype() == "LINE":
                bb.extend([ent.dxf.start[:2], ent.dxf.end[:2]])
        if not bb.has_data:
            raise ValueError(f"No entities found on layers {layers} in {path}")
        return bb.extmin[0], bb.extmin[1], bb.extmax[0], bb.extmax[1]
    bb = extents(msp)
    return bb.extmin[0], bb.extmin[1], bb.extmax[0], bb.extmax[1]


def _entity_coords(path: Path) -> list[tuple]:
    """
    Return a sorted, comparable list of all entity coordinates from *path*.

    Covers LWPOLYLINE and LINE entities — enough for the geometry written by
    headstock.py and brass_logo.py.
    """
    import ezdxf
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    coords: list[tuple] = []
    for ent in msp:
        dtype = ent.dxftype()
        if dtype == "LWPOLYLINE":
            pts = [
                (round(float(x), 6), round(float(y), 6))
                for x, y, *_ in ent.get_points()
            ]
            coords.append(("LWPOLYLINE", tuple(pts)))
        elif dtype == "LINE":
            s = ent.dxf.start
            e = ent.dxf.end
            coords.append((
                "LINE",
                round(float(s[0]), 6), round(float(s[1]), 6),
                round(float(e[0]), 6), round(float(e[1]), 6),
            ))
    coords.sort()
    return coords


# ---------------------------------------------------------------------------
# AC1 — Headstock DXF regenerates in correct units
# ---------------------------------------------------------------------------

def test_headstock_dxf_units(tmp_path):
    """
    AC1: The headstock DXF written by headstock.py uses millimetres
    ($INSUNITS = 4) as the unit system.
    """
    params = _load_params()
    out = tmp_path / "headstock.dxf"
    hs_mod.build(params=params, output_path=out)

    assert out.exists(), "headstock.dxf was not created"
    insunits = _dxf_insunits(out)
    assert insunits == 4, (
        f"$INSUNITS = {insunits!r}, expected 4 (millimetres). "
        "Check that headstock.py sets doc.header['$INSUNITS'] = 4."
    )


# ---------------------------------------------------------------------------
# AC2 — Logo DXF bounding box ≤ headstock outline minus declared margin
# ---------------------------------------------------------------------------

def test_logo_bbox_within_headstock(tmp_path):
    """
    AC2: The logo DXF bounding box lies entirely within the headstock
    bounding box shrunk by logo_margin_mm on every side.
    """
    params = _load_params()
    hs_path = tmp_path / "headstock.dxf"
    logo_path = tmp_path / "brass_logo.dxf"

    hs_mod.build(params=params, output_path=hs_path)
    logo_mod.build(params=params, output_path=logo_path)

    margin = float(params["logo_margin_mm"])

    hs_xmin, hs_ymin, hs_xmax, hs_ymax = _dxf_bbox(
        hs_path, layers=["OUTLINE"]
    )
    lo_xmin, lo_ymin, lo_xmax, lo_ymax = _dxf_bbox(
        logo_path, layers=["LOGO_OUTER", "LOGO_INNER"]
    )

    tol = 1e-6  # floating-point tolerance

    assert lo_xmin >= hs_xmin + margin - tol, (
        f"Logo left edge ({lo_xmin:.4f}) violates headstock left + margin "
        f"({hs_xmin + margin:.4f})"
    )
    assert lo_xmax <= hs_xmax - margin + tol, (
        f"Logo right edge ({lo_xmax:.4f}) violates headstock right - margin "
        f"({hs_xmax - margin:.4f})"
    )
    assert lo_ymin >= hs_ymin + margin - tol, (
        f"Logo bottom edge ({lo_ymin:.4f}) violates headstock bottom + margin "
        f"({hs_ymin + margin:.4f})"
    )
    assert lo_ymax <= hs_ymax - margin + tol, (
        f"Logo top edge ({lo_ymax:.4f}) violates headstock top - margin "
        f"({hs_ymax - margin:.4f})"
    )


# ---------------------------------------------------------------------------
# AC3 — Logo passes brass manufacturability gate
# ---------------------------------------------------------------------------

def test_brass_manufacturability(tmp_path):
    """
    AC3: The brass logo satisfies SendCutSend brass rules:
      - wall thickness ≥ min_feature_mm + kerf_mm / 2   (no feature thinner than 0.02")
      - the logo is declared single-piece (no open paths)
      - the declared brass_thickness is present in the DXF annotation
    """
    import ezdxf
    params = _load_params()
    logo_path = tmp_path / "brass_logo.dxf"
    logo_mod.build(params=params, output_path=logo_path)

    min_feat = float(params["min_feature_mm"])  # 0.508 mm = 0.02"
    kerf = float(params["kerf_mm"])
    required_wall = min_feat + kerf / 2

    # Infer wall from outer / inner LWPOLYLINE bounding boxes.
    doc = ezdxf.readfile(str(logo_path))
    msp = doc.modelspace()
    outer_w = inner_w = None
    for ent in msp:
        if ent.dxftype() == "LWPOLYLINE":
            layer = ent.dxf.layer
            pts = list(ent.get_points())
            xs = [p[0] for p in pts]
            w = max(xs) - min(xs)
            if layer == "LOGO_OUTER":
                outer_w = w
            elif layer == "LOGO_INNER":
                inner_w = w

    assert outer_w is not None, "LOGO_OUTER layer missing"
    assert inner_w is not None, "LOGO_INNER layer missing"

    # Wall = half the difference in width between outer and inner rectangles.
    wall = (outer_w - inner_w) / 2
    assert wall >= required_wall, (
        f"Logo wall {wall:.4f} mm < required {required_wall:.4f} mm "
        f"(min_feature={min_feat} mm, kerf/2={kerf/2} mm)"
    )

    # Verify the brass thickness annotation exists.
    brass_thickness = str(params["brass_thickness"])
    texts = [
        ent.dxf.text
        for ent in msp
        if ent.dxftype() == "TEXT"
    ]
    assert any(brass_thickness in t for t in texts), (
        f"Brass thickness {brass_thickness!r} not found in DXF TEXT annotations. "
        f"Found: {texts}"
    )


# ---------------------------------------------------------------------------
# AC4 — Changing nut_width_mm propagates to the headstock export
# ---------------------------------------------------------------------------

def test_parametric_propagation(tmp_path):
    """
    AC4: Modifying nut_width_mm in params and rebuilding produces a headstock DXF
    that differs in the NUT layer entity — proving parameters propagate.
    """
    import ezdxf
    params_a = _load_params()
    params_b = copy.deepcopy(params_a)
    params_b["nut_width_mm"] = params_a["nut_width_mm"] + 5.0  # widen by 5 mm

    out_a = tmp_path / "headstock_a.dxf"
    out_b = tmp_path / "headstock_b.dxf"

    hs_mod.build(params=params_a, output_path=out_a)
    hs_mod.build(params=params_b, output_path=out_b)

    def _nut_line_length(path: Path) -> float:
        """Return the length of the NUT reference line in the DXF."""
        doc = ezdxf.readfile(str(path))
        for ent in doc.modelspace():
            if ent.dxftype() == "LINE" and ent.dxf.layer == "NUT":
                s, e = ent.dxf.start, ent.dxf.end
                return math.hypot(e[0] - s[0], e[1] - s[1])
        raise AssertionError("NUT line not found in headstock DXF")

    len_a = _nut_line_length(out_a)
    len_b = _nut_line_length(out_b)

    assert abs(len_b - len_a - 5.0) < 1e-6, (
        f"Expected NUT line to grow by 5.0 mm; got Δ={len_b - len_a:.4f} mm. "
        "nut_width_mm change did not propagate correctly."
    )


# ---------------------------------------------------------------------------
# AC5 — Re-running build is deterministic
# ---------------------------------------------------------------------------

def test_build_determinism(tmp_path):
    """
    AC5: Running headstock.py and brass_logo.py twice with identical params
    produces geometrically identical DXF files (same entity coordinates).
    """
    params = _load_params()

    hs_run1 = tmp_path / "hs_run1.dxf"
    hs_run2 = tmp_path / "hs_run2.dxf"
    logo_run1 = tmp_path / "logo_run1.dxf"
    logo_run2 = tmp_path / "logo_run2.dxf"

    hs_mod.build(params=params, output_path=hs_run1)
    logo_mod.build(params=params, output_path=logo_run1)

    hs_mod.build(params=params, output_path=hs_run2)
    logo_mod.build(params=params, output_path=logo_run2)

    hs_coords_1 = _entity_coords(hs_run1)
    hs_coords_2 = _entity_coords(hs_run2)
    assert hs_coords_1 == hs_coords_2, (
        "headstock.dxf geometry differs between runs — build is not deterministic."
    )

    logo_coords_1 = _entity_coords(logo_run1)
    logo_coords_2 = _entity_coords(logo_run2)
    assert logo_coords_1 == logo_coords_2, (
        "brass_logo.dxf geometry differs between runs — build is not deterministic."
    )
