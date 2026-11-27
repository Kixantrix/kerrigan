"""Answer-free sandbox adapter: evaluates the candidate stack model and parses its documents."""

import importlib.util
import json
from pathlib import Path
import re

app = Path(__file__).resolve().parent
NUM = r"([0-9]+(?:\.[0-9]+)?)"
NUMBER = r"\d+(?:\.\d+)?"
# Agent-visible base documents with every number masked, the base numbers, and the positions of the
# numbers derived from the changed model (everything else must be preserved).
DOCS = {"hardware/ASSEMBLY.md": {"derived": [8, 12], "masked": "# Assembly sheet (excerpt)\n\nAbove the dial (measured from the top of P#): cannon tip +#, needle +#, hand III +#,\nhand II +#, hand I +#, cap +# (top of cap +#). The crystal's underside sits at +#.\nYou never measure these: every height is set by a shoulder or a flush end on the turned parts.\n\n#. Lower P# over the cannon and onto every shaft tip. Screw the four **M#×# M-F**\n   standoffs through P# into the gear standoffs.\n", "numbers": ["2", "0.35", "0.45", "1.61", "2.34", "3.07", "3.46", "4.47", "7.0", "4", "2", "2", "6", "2"]}, "hardware/BOM.md": {"derived": [5, 20], "masked": "# Bill of materials (excerpt)\n\n| Part | Material | Qty | Notes |\n|---|---|---|---|\n| `case_upper_shell` | Brass # .#\" | # | **Bent**: top face with crystal window and #-slot grille ring, # flanges # mm. Knob notches. |\n| `case_lid` | Brass # .#\" | # | **Bent**: # flanges # mm (just above SCS's .#\" minimum). |\n\n| Hardware | Qty | Spares | Use |\n|---|---|---|---|\n| M# brass hex standoff, **male-female # mm** (+# mm thread) | # | # | Gear posts (P# → P#) |\n| M# brass hex standoff, **male-female # mm** (+# mm thread) | # | # | Hand posts (P# → crystal) |\n| M# × # brass slotted countersunk screw, DIN # | # | # | Hinge body leaf through the case wall |\n", "numbers": ["260", "040", "1", "90", "8", "18.2", "260", "040", "1", "8", "7.62", "292", "2", "8", "3", "4", "3", "1", "2", "2", "6", "3", "4", "3", "2", "1.6", "6", "963", "4", "2"]}, "hardware/README.md": {"derived": [3, 4, 16, 17, 18, 19], "masked": "# Brass alethiometer hardware (excerpt)\n\n## The instrument\n\n- **Size** # × # mm (an octagon with # mm chamfers). The body is # mm tall,\n  # mm with the lid closed.\n\n## Height stack\n\n| Height (mm) | Layer |\n|---|---|\n| # – # | **P#**, movement base plate (bearings) |\n| # – # | **gear space**, four # mm levels |\n| # – # | **P#**, dial plate + sticker |\n| # – # | needle, hands III, II, I, cap |\n| # – # | crystal spiders, crystal, top face |\n| # – # | lid |\n", "numbers": ["112.9", "112.9", "16", "38.0", "45.6", "17.1", "18.7", "1", "19.2", "27.2", "2", "26.7", "28.3", "2", "28.8", "32.8", "34.3", "38.0", "38.0", "45.6"]}}


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
                                       ("body_height", "closed_height", "crystal_clearance",
                                        "upper_shell_flange", "crystal_underside_above_p2"))
        out["report_relief_consistent"] = abs(reported.get("p2_hinge_relief", 1e9)
                                              - float(m.p2_hinge_relief())) < 0.01
    except Exception as exc:  # noqa: BLE001
        out["report_consistent"] = False
        out["report_relief_consistent"] = False
    # Relief must follow the documented geometry from the constants (screw length and clearance rule
    # perturbed); a lower bound, so deeper-but-clearing reliefs are accepted.
    relief = []
    for screw, clearance in ((c["HINGE_BODY_SCREW_LEN"], c["RELIEF_CLEARANCE"]), (8.0, c["RELIEF_CLEARANCE"]),
                             (4.0, c["RELIEF_CLEARANCE"]), (c["HINGE_BODY_SCREW_LEN"], 0.8)):
        m.HINGE_BODY_SCREW_LEN, m.RELIEF_CLEARANCE = screw, clearance
        try:
            depth = float(m.p2_hinge_relief())
        except Exception:  # noqa: BLE001
            depth = float("-inf")
        need = max(screw - c["T040"], c["T063"] + c["HINGE_NUT_H"]) + clearance
        relief.append(depth >= need - 1e-9)
    out["relief_ok"] = relief

    # The depth must follow the documented geometry, not a constant that happens to clear: it moves
    # one-for-one with the screw length while the tips dominate and with the clearance rule, and does
    # not move with the screw length while the strip and nuts dominate.
    def depth(screw, clearance):
        m.HINGE_BODY_SCREW_LEN, m.RELIEF_CLEARANCE = screw, clearance
        try:
            return float(m.p2_hinge_relief())
        except Exception:  # noqa: BLE001
            return None
    base_screw, base_clear = c["HINGE_BODY_SCREW_LEN"], c["RELIEF_CLEARANCE"]
    d6, d8, dc = depth(base_screw, base_clear), depth(base_screw + 2.0, base_clear), depth(base_screw, base_clear + 0.4)
    d40, d35 = depth(4.0, base_clear), depth(3.5, base_clear)
    known = None not in (d6, d8, dc, d40, d35)
    out["relief_tracks"] = [known and abs((d8 - d6) - 2.0) < 1e-6, known and abs((dc - d6) - 0.4) < 1e-6,
                            known and abs(d40 - d35) < 1e-6]
    m.HINGE_BODY_SCREW_LEN, m.RELIEF_CLEARANCE = base_screw, base_clear
    out["fixed"] = {"T_HAND": getattr(m, "T_HAND", None), "GEAR_PITCH_Z": getattr(m, "GEAR_PITCH_Z", None),
                    "LEVELS": [round(v, 6) for v in getattr(m, "LEVELS", [])]}
    readme = (app / "hardware/README.md").read_text(encoding="utf-8")
    bom = (app / "hardware/BOM.md").read_text(encoding="utf-8")
    assembly = (app / "hardware/ASSEMBLY.md").read_text(encoding="utf-8")
    texts = {"hardware/README.md": readme, "hardware/BOM.md": bom, "hardware/ASSEMBLY.md": assembly}
    layout, preserved = [], []
    for name, info in sorted(DOCS.items()):
        text = texts[name]
        numbers = re.findall(NUMBER, text)
        layout.append(re.sub(NUMBER, "#", text) == info["masked"])
        preserved.append(len(numbers) == len(info["numbers"]) and all(
            numbers[i] == info["numbers"][i] for i in range(len(numbers)) if i not in info["derived"]))
    out["docs_layout_kept"] = all(layout)
    out["docs_fixed_numbers_kept"] = all(preserved)
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
