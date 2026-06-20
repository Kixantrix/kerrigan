#!/usr/bin/env python3
"""
Parametric headstock outline generator — Guitar playbook test (Track B).

Reads shared/params.yaml and writes exports/headstock.dxf.

Shape: filleted rectangle (headstock_width_mm × headstock_length_mm) on layer
"OUTLINE", plus a reference line on layer "NUT" that marks nut_width_mm at y=0.
Changing any shared parameter and re-running regenerates the DXF.

DXF units: mm  ($INSUNITS = 4).
CNC note: all corner radii equal bit_radius_mm — the router bit clears every
interior corner without requiring a secondary pass.
"""

from __future__ import annotations

import math
from pathlib import Path

import ezdxf
import yaml

ASSET_ROOT = Path(__file__).resolve().parent.parent
PARAMS_FILE = ASSET_ROOT / "shared" / "params.yaml"
EXPORTS_DIR = ASSET_ROOT / "exports"

# ezdxf header variables that embed timestamps; zero them for deterministic output.
_TIMESTAMP_VARS = ("$TDCREATE", "$TDUPDATE", "$TDUCREATE", "$TDUUPDATE")


def load_params(params_file: Path = PARAMS_FILE) -> dict:
    with open(params_file) as fh:
        return yaml.safe_load(fh)


def _bulge_90() -> float:
    """Bulge value for a 90-degree CCW arc in an LWPOLYLINE."""
    return math.tan(math.radians(22.5))  # ≈ 0.4142


def add_rounded_rect(
    msp,
    x: float,
    y: float,
    w: float,
    h: float,
    r: float,
    layer: str = "0",
) -> None:
    """
    Add a closed LWPOLYLINE representing a rounded rectangle to *msp*.

    (x, y) is the bottom-left corner; w/h are width/height; r is corner radius.
    Vertices are ordered counter-clockwise with bulge values encoding the arcs.
    """
    b = _bulge_90()
    # Each group: (x, y, start_width, end_width, bulge)
    # Straight segments have bulge=0; arcs have bulge=b.
    pts = [
        (x + r,         y,           0, 0, 0),  # bottom edge start
        (x + w - r,     y,           0, 0, b),  # bottom-right arc
        (x + w,         y + r,       0, 0, 0),  # right edge start
        (x + w,         y + h - r,   0, 0, b),  # top-right arc
        (x + w - r,     y + h,       0, 0, 0),  # top edge start
        (x + r,         y + h,       0, 0, b),  # top-left arc
        (x,             y + h - r,   0, 0, 0),  # left edge start
        (x,             y + r,       0, 0, b),  # bottom-left arc (closes to first pt)
    ]
    msp.add_lwpolyline(
        pts,
        format="xyseb",
        close=True,
        dxfattribs={"layer": layer},
    )


def build(params: dict | None = None, output_path: Path | None = None) -> Path:
    """
    Generate the headstock DXF.

    Parameters
    ----------
    params:
        Parsed params dict.  Loaded from PARAMS_FILE when *None*.
    output_path:
        Destination .dxf path.  Defaults to EXPORTS_DIR / "headstock.dxf".

    Returns
    -------
    Path
        Absolute path of the written DXF file.
    """
    if params is None:
        params = load_params()

    w = float(params["headstock_width_mm"])
    h = float(params["headstock_length_mm"])
    r = float(params["bit_radius_mm"])
    nut_w = float(params["nut_width_mm"])

    if r * 2 > w or r * 2 > h:
        raise ValueError(
            f"bit_radius ({r} mm) too large for headstock dimensions ({w}×{h} mm)"
        )

    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # millimetres
    # Zero timestamps so repeated runs are geometry-deterministic.
    for var in _TIMESTAMP_VARS:
        if var in doc.header:
            doc.header[var] = 0.0

    msp = doc.modelspace()
    doc.layers.add("OUTLINE")
    doc.layers.add("NUT")

    # Headstock outline: centred on X=0, bottom at Y=0.
    add_rounded_rect(msp, -w / 2, 0.0, w, h, r, layer="OUTLINE")

    # Nut reference line: shows nut_width at the neck junction.
    msp.add_line(
        (-nut_w / 2, 0.0),
        (nut_w / 2, 0.0),
        dxfattribs={"layer": "NUT"},
    )

    out = output_path or (EXPORTS_DIR / "headstock.dxf")
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    return out


if __name__ == "__main__":
    path = build()
    print(f"Generated: {path}")
