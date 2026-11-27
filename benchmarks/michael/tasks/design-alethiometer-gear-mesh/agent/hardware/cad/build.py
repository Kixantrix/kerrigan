"""Build every output for the brass alethiometer (gear-train excerpt).

    python build.py            # checks + SendCutSend order + build report
    python build.py --check    # checks only

Outputs go to hardware/out/ (committed so the parts can be ordered without Python).
The full build also exports DXF/STEP and renders with cadquery; those steps and the 3-D
interference sweep are not part of this excerpt.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import design as D

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"

# SendCutSend minimum part size (instant quote) and a conservative min web for laser
SCS_MIN = (0.25 * 25.4, 0.375 * 25.4)
DENSITY = {"brass": 8.5e-3}           # g/mm³


def log(msg: str) -> None:
    print(msg, flush=True)


def _area(pts) -> float:
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def interference(parts, lid_angles=(0.0,)) -> list[str]:
    """3-D solid interference between every pair of placed parts (cadquery; not in this excerpt)."""
    return []


def manufacturability(parts) -> list[str]:
    notes = []
    for p in parts:
        if p.kind != "scs" or not p.outline:
            continue
        xs, ys = [x for x, _ in p.outline], [y for _, y in p.outline]
        w, h = sorted((max(xs) - min(xs), max(ys) - min(ys)))
        if w < SCS_MIN[0] or h < SCS_MIN[1]:
            notes.append(f"{p.name}: {w:.1f}×{h:.1f} mm is under SendCutSend's minimum part size")
    return notes


def weight_report(parts) -> tuple[list[dict], float]:
    rows = []
    for p in parts:
        if not p.outline:
            continue
        grams = _area(p.outline) * D.T040 * DENSITY["brass"] * len(p.placements) * p.qty
        rows.append(dict(part=p.name, qty=len(p.placements) * p.qty, grams=round(grams, 2), material=p.material))
    return rows, sum(r["grams"] for r in rows)


def export_fabrication(parts) -> list[dict]:
    """One SendCutSend line per laser-cut part; writes out/sendcutsend_order.csv."""
    order = [dict(file=f"{p.name}__{p.material.split()[0]}__qty{max(1, len(p.placements)) * p.qty}.dxf",
                  part=p.name, qty=max(1, len(p.placements)) * p.qty, material=p.material)
             for p in parts if p.kind == "scs"]
    with open(OUT / "sendcutsend_order.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "part", "qty", "material"])
        w.writeheader()
        w.writerows(order)
    return order


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="checks only")
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    parts = D.all_parts()
    log(f"built {len(parts)} part types in {time.time() - t0:.1f}s")
    log(json.dumps(D.summary(), indent=1))

    tools = D.tooling()
    notes = manufacturability(parts + tools)
    log("manufacturability: " + ("OK" if not notes else ""))
    for n in notes:
        log("  ! " + n)

    t1 = time.time()
    problems = interference(parts)
    log(f"interference check ({time.time() - t1:.0f}s): " + ("none" if not problems else ""))
    for pr in problems:
        log("  X " + pr)

    rows, grams = weight_report(parts)
    log(f"estimated weight: {grams:.0f} g")
    if args.check:
        return 1 if problems else 0

    OUT.mkdir(exist_ok=True)
    order = export_fabrication(parts + tools)
    report = dict(summary=D.summary(), weight_g=round(grams), interference=problems,
                  manufacturability=notes, sendcutsend_files=len(order))
    (OUT / "build_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    log(f"exported {len(order)} SendCutSend files")
    log(f"done in {time.time() - t0:.0f}s")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
