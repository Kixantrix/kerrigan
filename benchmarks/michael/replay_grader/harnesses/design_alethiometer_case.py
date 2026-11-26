"""Answer-free sandbox adapter: evaluates the candidate stack model and parses its documents."""

import importlib.util
import json
from pathlib import Path
import re

app = Path(__file__).resolve().parent
NUM = r"([0-9]+(?:\.[0-9]+)?)"


def load():
    spec = importlib.util.spec_from_file_location("stack", app / "hardware/stack.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def first(pattern, text, flags=0):
    match = re.search(pattern, text, flags)
    return [float(g) for g in match.groups()] if match else None


def observe():
    out = {}
    m = load()
    c = {k: getattr(m, k, None) for k in ("T040", "T063", "LID_H", "GEAR_STANDOFF", "HAND_STANDOFF",
                                         "CARRIER_STANDOFF", "CARRIER_SPACER", "CARRIER_T", "CAP_TOP_ABOVE_P2",
                                         "HINGE_BODY_SCREW_LEN", "HINGE_NUT_H", "RELIEF_CLEARANCE",
                                         "MIN_CRYSTAL_CLEARANCE")}
    out["constants"] = c
    out["catalog"] = list(getattr(m, "STANDOFF_CATALOG", ()))
    # Trusted recomputation from the candidate's own constants.
    p2_top = c["T040"] + c["CARRIER_SPACER"] + c["CARRIER_T"] + c["CARRIER_STANDOFF"] + c["T063"] \
        + c["GEAR_STANDOFF"] + c["T063"]
    frame = p2_top + c["HAND_STANDOFF"] + c["T040"]
    top = frame + c["T063"] + c["T040"]
    lower_h = (p2_top - c["GEAR_STANDOFF"] - c["T063"]) + 0.5 + 2.5
    out["model"] = {"body_height": round(top, 3), "closed_height": round(top + c["LID_H"], 3),
                    "crystal_clearance": round(frame - (p2_top + c["CAP_TOP_ABOVE_P2"]), 3),
                    "crystal_seat": round(frame - c["T040"], 3),
                    "crystal_underside_above_p2": round(frame - p2_top, 3),
                    "upper_shell_flange": round(top - (lower_h - 2.0), 3)}
    try:
        reported = m.report()
        out["report_consistent"] = all(abs(reported.get(k, 1e9) - out["model"][k]) < 0.01 for k in
                                       ("body_height", "closed_height", "crystal_clearance"))
    except Exception as exc:  # noqa: BLE001
        out["report_consistent"] = False
    relief = []
    for screw in (c["HINGE_BODY_SCREW_LEN"], 8.0, 4.0):
        m.HINGE_BODY_SCREW_LEN = screw
        depth = float(m.p2_hinge_relief())
        need = max(screw - c["T040"], c["T063"] + c["HINGE_NUT_H"]) + c["RELIEF_CLEARANCE"]
        relief.append(depth >= need - 1e-9)
    out["relief_ok"] = relief
    readme = (app / "hardware/README.md").read_text(encoding="utf-8")
    bom = (app / "hardware/BOM.md").read_text(encoding="utf-8")
    assembly = (app / "hardware/ASSEMBLY.md").read_text(encoding="utf-8")
    out["docs"] = {
        "readme_heights": first(rf"body is {NUM} mm tall,\s*{NUM} mm with the lid closed", readme),
        "readme_crystal_row": first(rf"\|\s*{NUM}\s*[–-]\s*{NUM}\s*\|\s*crystal spiders", readme),
        "readme_lid_row": first(rf"\|\s*{NUM}\s*[–-]\s*{NUM}\s*\|\s*lid", readme),
        "bom_flange": first(rf"case_upper_shell.*?8 flanges {NUM} mm", bom),
        "bom_hand_posts": first(rf"male-female {NUM} mm\*\*[^\n]*Hand posts", bom),
        "bom_gear_posts": first(rf"male-female {NUM} mm\*\*[^\n]*Gear posts", bom),
        "assembly_underside": first(rf"crystal's underside sits at \+{NUM}", assembly),
        "assembly_standoff": first(rf"M2×{NUM} M-F", assembly),
    }
    return out


probes = json.loads((app / "probes.json").read_text())
try:
    value = observe()
except Exception as exc:  # noqa: BLE001
    value = {"error": type(exc).__name__}
for index, _ in enumerate(probes):
    print(json.dumps({"id": index, "value": value}, allow_nan=False, default=str), flush=True)
