#!/usr/bin/env python3
"""
Brass headstock logo generator — Guitar playbook test (Track B).

Reads shared/params.yaml and writes exports/brass_logo.dxf.

The logo is a rectangular frame (outer + inner closed LWPOLYLINE) centred on
the headstock X-axis and positioned within the headstock footprint minus
logo_margin_mm.  Wall thickness is chosen to satisfy SendCutSend brass rules:

    wall ≥ min_feature_mm + kerf_mm / 2

A BRASS_INFO text annotation records the declared material thickness.

DXF units: mm  ($INSUNITS = 4).
Material: brass, thickness = params["brass_thickness"].
"""

from __future__ import annotations

from pathlib import Path

import ezdxf
import yaml

ASSET_ROOT = Path(__file__).resolve().parent.parent
PARAMS_FILE = ASSET_ROOT / "shared" / "params.yaml"
EXPORTS_DIR = ASSET_ROOT / "exports"

_TIMESTAMP_VARS = ("$TDCREATE", "$TDUPDATE", "$TDUCREATE", "$TDUUPDATE")

# Logo frame wall thickness.  Must satisfy:  wall ≥ min_feature_mm + kerf/2.
# 2.0 mm >> 0.508 mm (min feature) + 0.15 mm (half kerf) = 0.658 mm minimum.
WALL_MM = 2.0


def load_params(params_file: Path = PARAMS_FILE) -> dict:
    with open(params_file) as fh:
        return yaml.safe_load(fh)


def _add_rect(msp, cx: float, cy: float, w: float, h: float, layer: str = "0") -> None:
    """Add a plain closed rectangular LWPOLYLINE centred at (cx, cy)."""
    x0, y0 = cx - w / 2, cy - h / 2
    x1, y1 = cx + w / 2, cy + h / 2
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


def build(params: dict | None = None, output_path: Path | None = None) -> Path:
    """
    Generate the brass logo DXF.

    Parameters
    ----------
    params:
        Parsed params dict.  Loaded from PARAMS_FILE when *None*.
    output_path:
        Destination .dxf path.  Defaults to EXPORTS_DIR / "brass_logo.dxf".

    Returns
    -------
    Path
        Absolute path of the written DXF file.

    Raises
    ------
    ValueError
        If the wall thickness fails the brass manufacturability gate or if logo
        dimensions become non-positive after applying wall thickness.
    """
    if params is None:
        params = load_params()

    hs_w = float(params["headstock_width_mm"])
    hs_h = float(params["headstock_length_mm"])
    margin = float(params["logo_margin_mm"])
    min_feat = float(params["min_feature_mm"])
    kerf = float(params["kerf_mm"])

    # --- Manufacturability gate (SendCutSend brass rules) ---
    # Each cut edge loses kerf/2 of material.  The narrowest strip (wall) must
    # be at least min_feature_mm wide after accounting for kerf.
    required_wall = min_feat + kerf / 2
    if WALL_MM < required_wall:
        raise ValueError(
            f"Wall {WALL_MM} mm < required {required_wall:.3f} mm "
            f"(min_feature={min_feat} mm, kerf={kerf} mm)"
        )

    # --- Logo bounding box ---
    # Outer rectangle: fits inside headstock footprint minus margin on each side.
    logo_w = hs_w - 2 * margin
    # Use lower 50 % of headstock height so the logo sits near the nut.
    logo_h = hs_h * 0.5

    # Position: centred on X; bottom edge at y = margin (clear of headstock edge).
    cx = 0.0
    cy = margin + logo_h / 2

    # Inner rectangle: shrunk by WALL_MM on each side.
    inner_w = logo_w - 2 * WALL_MM
    inner_h = logo_h - 2 * WALL_MM

    if inner_w <= 0:
        raise ValueError(f"Logo width too small for wall: inner_w={inner_w:.3f} mm")
    if inner_h <= 0:
        raise ValueError(f"Logo height too small for wall: inner_h={inner_h:.3f} mm")

    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # millimetres
    for var in _TIMESTAMP_VARS:
        if var in doc.header:
            doc.header[var] = 0.0

    msp = doc.modelspace()
    doc.layers.add("LOGO_OUTER")
    doc.layers.add("LOGO_INNER")
    doc.layers.add("BRASS_INFO")

    _add_rect(msp, cx, cy, logo_w, logo_h, layer="LOGO_OUTER")
    _add_rect(msp, cx, cy, inner_w, inner_h, layer="LOGO_INNER")

    # Material annotation.
    msp.add_text(
        f"BRASS {params['brass_thickness']}",
        dxfattribs={"layer": "BRASS_INFO", "height": 3.0},
    ).set_placement((cx, -8.0))

    out = output_path or (EXPORTS_DIR / "brass_logo.dxf")
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    return out


if __name__ == "__main__":
    path = build()
    print(f"Generated: {path}")
