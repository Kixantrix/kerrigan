"""Answer-free sandbox adapter for the gear-mesh design task. Output is untrusted.

Loads the candidate CAD excerpt (design.py, build.py, mesh.py with the staged layout.py and gears.py),
evaluates held-out pairs through the candidate's mesh API, re-evaluates the candidate's design with
a trusted closed-form involute model, and runs the candidate build on rebuilt design variants.
Expected values live only in the trusted rows; `rc_ok` treats 0/None as success, and the instruction
requires only a nonzero exit on failure."""

import contextlib
import csv
import importlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import sys

app = Path(__file__).resolve().parent
CAD = app / "hardware" / "cad"
NAMES = ("layout", "gears", "design", "mesh", "build")
ALPHA = math.radians(20.0)
PAIR_NAMES = [f"knob {n} → sensor {n}" for n in ("I", "II", "III")] + \
    [f"sensor {n} → hand {n}" for n in ("I", "II", "III")] + ["motor → needle"]


def inv(a):
    return math.tan(a) - a


def trusted_backlash(za, zb, m, dist, ta, tb, la, lb, shrink=0.0, fat=0.0):
    d = dist - shrink
    a0 = m * (za + zb) / 2
    aw = math.acos(min(1.0, a0 * math.cos(ALPHA) / d))
    out = []
    for z, t, laser in ((za, ta, la), (zb, tb, lb)):
        f = fat if laser else 0.0
        r = m * z / 2
        out.append((r, r + m + f, r - 1.25 * m + f,
                    (math.pi * m / 2 - t / 2) / (2 * r) + inv(ALPHA) + f / (r * math.cos(ALPHA))))
    (ra_, tipa, roota, psia), (rb_, tipb, rootb, psib) = out
    if d - tipa - rootb <= 0 or d - tipb - roota <= 0:
        return None
    play = 2 * math.pi / zb - 2 * (psib - inv(aw)) - 2 * (psia - inv(aw)) * za / zb
    return play * rb_ if play > 0 else None


def load(root):
    for name in NAMES:
        sys.modules.pop(name, None)
    sys.path[:] = [str(root)] + [p for p in sys.path if not p.startswith(str(app))]
    with contextlib.redirect_stdout(io.StringIO()):
        return {name: importlib.import_module(name) for name in ("layout", "gears", "design", "mesh", "build")}


def num(v):
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return "invalid"
    return round(float(v), 6)


def held_out(M, kind, p, args):
    pair = M.Pair(name="held-out", a="drv", b="drn", za=p["za"], zb=p["zb"], ca=tuple(p["ca"]), cb=tuple(p["cb"]),
                  thin_a=p["thin_a"], thin_b=p["thin_b"], laser_a=p["laser_a"], laser_b=p["laser_b"],
                  module=p["module"])
    if kind == "backlash":
        return {"value": num(M.backlash(pair, shrink=args["shrink"], fat=args["fat"]))}
    if kind == "margin":
        return {"value": num(M.margin(pair, fat=args["fat"]))}
    if kind == "contact_ratio":
        return {"value": num(M.contact_ratio(pair, shrink=args["shrink"]))}
    if kind == "distances":
        return {"nominal": num(pair.nominal_distance), "theoretical": num(pair.theoretical_distance)}
    raise ValueError(kind)


def part_rows(D):
    return {p.name: p for p in D.gears()}


def design_rules(mods):
    """Trusted re-evaluation of the candidate's own design: nominal gears and loose spares."""
    D, L = mods["design"], mods["layout"]
    nominal = part_rows(D)
    spares = {p.name: p for p in D.mesh_tuning_gears()}
    lo, hi = 0.05, 0.45
    result = {"nominal_in_range": [], "typical_reads": [], "loose_fat_runs": []}
    for n in ("I", "II", "III"):
        chain = [f"knob_{n}_{D.Z_KNOB}T", f"gear_sensor_{n}_{D.Z_SENSOR}T", f"gear_hand_{n}_{D.Z_HAND}T"]
        for names in ((chain[0], chain[1]), (chain[1], chain[2])):
            result_pair(result, nominal, spares, names, L.MODULE, lo, hi)
    result_pair(result, nominal, spares, (f"gear_motor_{D.Z_MOTOR}T", f"gear_needle_{D.Z_NEEDLE}T"), L.MODULE, lo, hi)
    return {k: all(v) and len(v) == 7 for k, v in result.items()}


def result_pair(result, nominal, spares, names, m, lo, hi):
    a, b = (nominal[n] for n in names)
    sa, sb = (spares.get(n + "_L", nominal[n]) if nominal[n].kind == "scs" else nominal[n] for n in names)
    dist = math.dist(a.placements[0][:2], b.placements[0][:2])
    la, lb = a.kind == "scs", b.kind == "scs"
    bl = trusted_backlash(a.teeth, b.teeth, m, dist, a.backlash, b.backlash, la, lb)
    result["nominal_in_range"].append(bl is not None and lo <= bl <= hi)
    typ = trusted_backlash(a.teeth, b.teeth, m, dist, a.backlash, b.backlash, la, lb, 0.05, 0.03)
    result["typical_reads"].append(typ is not None and typ >= lo)
    loose = trusted_backlash(sa.teeth, sb.teeth, m, dist, sa.backlash, sb.backlash, la, lb, 0.0, 0.065)
    result["loose_fat_runs"].append(loose is not None and loose >= lo)


def spares_shape(mods):
    D = mods["design"]
    nominal = part_rows(D)
    laser = {n for n, p in nominal.items() if p.kind == "scs"}
    spares = {p.name: p for p in D.mesh_tuning_gears()}
    assembled = {p.name for p in D.all_parts()}
    return {
        "names_match": set(spares) == {n + "_L" for n in laser},
        "laser_cut": all(p.kind == "scs" for p in spares.values()),
        "same_teeth": all(spares[n + "_L"].teeth == nominal[n].teeth for n in laser if n + "_L" in spares),
        "thinner": bool(spares) and all(spares[n + "_L"].backlash > nominal[n].backlash for n in laser
                                        if n + "_L" in spares),
        "outline_matches_thinning": all(
            spares[n + "_L"].outline == mods["gears"].gear_polygon(D.MODULE, nominal[n].teeth,
                                                                   backlash=spares[n + "_L"].backlash)
            for n in laser if n + "_L" in spares),
        "not_assembled": not (set(spares) & assembled),
        "assembly_names": sorted(assembled),
    }


def pairs_shape(mods):
    D, M = mods["design"], mods["mesh"]
    nominal = part_rows(D)
    got = {}
    for p in M.pairs():
        a, b = nominal.get(p.a), nominal.get(p.b)
        ok = (a is not None and b is not None and p.za == a.teeth and p.zb == b.teeth
              and abs(p.thin_a - a.backlash) < 1e-12 and abs(p.thin_b - b.backlash) < 1e-12
              and p.laser_a == (a.kind == "scs") and p.laser_b == (b.kind == "scs")
              and abs(p.nominal_distance - math.dist(a.placements[0][:2], b.placements[0][:2])) < 1e-9)
        got[p.name] = {"driver": p.a, "driven": p.b, "consistent": ok,
                       "centre_minus_theoretical": num(p.nominal_distance - p.theoretical_distance)}
    loose = {p.name: (p.thin_a, p.thin_b) for p in M.pairs(D.GEAR_BACKLASH_LOOSE)}
    lb = D.GEAR_BACKLASH_LOOSE
    loose_ok = len(loose) == 7 and all(
        all(abs(t - lb) < 1e-12 for t, laser in zip(th, (pp.laser_a, pp.laser_b)) if laser)
        for pp in M.pairs(D.GEAR_BACKLASH_LOOSE) for th in [(pp.thin_a, pp.thin_b)])
    return {"pairs": got, "loose_pairs_use_loose_thinning": loose_ok}


def run_build(mods, argv):
    B = mods["build"]
    out = io.StringIO()
    sys.argv = ["build.py", *argv]
    crashed = False
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = B.main()
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except Exception:  # noqa: BLE001
        code, crashed = None, True
    return {"rc_ok": (code == 0 or code is None) and not crashed, "crashed": crashed,
            "rc_nonzero": isinstance(code, int) and not isinstance(code, bool) and code != 0 and not crashed}


def report_vs_trusted(mods, root):
    """Full build: the report's gear-mesh rows against a trusted recomputation, and the order."""
    D, L = mods["design"], mods["layout"]
    build = run_build(mods, ["--no-render"])
    out = root.parent / "out"
    report = json.loads((out / "build_report.json").read_text(encoding="utf-8"))
    rows = {r.get("pair"): r for r in report.get("gear_mesh", []) if isinstance(r, dict)}
    nominal = part_rows(D)
    loose = {p.name: p for p in D.gears(D.GEAR_BACKLASH_LOOSE)}
    spec = {f"knob {n} → sensor {n}": (f"knob_{n}_{D.Z_KNOB}T", f"gear_sensor_{n}_{D.Z_SENSOR}T") for n in ("I", "II", "III")}
    spec.update({f"sensor {n} → hand {n}": (f"gear_sensor_{n}_{D.Z_SENSOR}T", f"gear_hand_{n}_{D.Z_HAND}T")
                 for n in ("I", "II", "III")})
    spec["motor → needle"] = (f"gear_motor_{D.Z_MOTOR}T", f"gear_needle_{D.Z_NEEDLE}T")
    errors, missing = {}, []
    for name, (na, nb) in spec.items():
        r = rows.get(name)
        if r is None:
            missing.append(name)
            continue
        a, b, la_, lb_ = nominal[na], nominal[nb], loose[na], loose[nb]
        dist = math.dist(a.placements[0][:2], b.placements[0][:2])
        args = (a.teeth, b.teeth, L.MODULE, dist)
        kinds = (a.kind == "scs", b.kind == "scs")
        want = {
            "centre_mm": dist, "theoretical_mm": L.MODULE * (a.teeth + b.teeth) / 2,
            "backlash_mm": trusted_backlash(*args, a.backlash, b.backlash, *kinds),
            "backlash_fat_mm": trusted_backlash(*args, a.backlash, b.backlash, *kinds, 0.0, 0.065),
            "backlash_loose_fat_mm": trusted_backlash(*args, la_.backlash, lb_.backlash, *kinds, 0.0, 0.065),
        }
        worst = 0.0
        for key, value in want.items():
            got = r.get(key, "missing")
            got = 0.0 if got is None else got
            if isinstance(got, bool) or not isinstance(got, (int, float)):
                worst = max(worst, 1e9)
                continue
            worst = max(worst, abs(got - (0.0 if value is None else value)))
        errors[name] = round(worst, 6)
    return {"build": build, "missing_rows": missing, "max_row_error": max(errors.values()) if errors else None}


def order(mods, root):
    build = run_build(mods, ["--no-render"])
    path = root.parent / "out" / "sendcutsend_order.csv"
    with open(path, newline="", encoding="utf-8") as f:
        parts = sorted({row.get("part", "") for row in csv.DictReader(f)})
    return {"build": build, "order_parts": parts}


def variant(index, edits):
    root = Path("/work") / f"variant-{index}" / "hardware" / "cad"
    root.mkdir(parents=True)
    for name in NAMES:
        shutil.copyfile(CAD / f"{name}.py", root / f"{name}.py")
    for file, const, value in edits:
        path = root / file
        text = path.read_text(encoding="utf-8")
        text, n = re.subn(rf"^{const}\s*=\s*[^#\n]+", f"{const} = {value}", text, count=1, flags=re.M)
        if n != 1:
            raise ValueError(f"missing top-level {const}")
        path.write_text(text, encoding="utf-8")
    return root


def flagged(mods):
    M = mods["mesh"]
    with contextlib.redirect_stdout(io.StringIO()):
        msgs = [m for m in M.problems(M.report()) if isinstance(m, str)]
    return sorted({n for n in PAIR_NAMES for m in msgs if n in m})


def assembly(mods):
    D, G = mods["design"], mods["gears"]
    parts = D.all_parts()
    return {"names": sorted(p.name for p in parts),
            "outlines_match": all(p.outline == G.gear_polygon(D.MODULE, p.teeth, backlash=p.backlash)
                                  for p in parts if p.teeth),
            "laser_use_gear_backlash": all(abs(p.backlash - D.GEAR_BACKLASH) < 1e-12 for p in parts
                                           if p.kind == "scs" and p.teeth),
            "knob_nominal": sorted({p.backlash for p in parts if p.kind == "bought"}) == [0.08]}


def observe(index, probe):
    op = probe["op"]
    if op == "held_out":
        mods = load(CAD)
        return held_out(mods["mesh"], probe["kind"], probe["pair"], probe.get("args", {}))
    if op == "design_rules":
        return design_rules(load(CAD))
    if op == "spares":
        return spares_shape(load(CAD))
    if op == "assembly":
        return assembly(load(CAD))
    if op == "pairs":
        return pairs_shape(load(CAD))
    if op == "check":
        root = variant(index, probe["edits"]) if probe["edits"] else variant(index, [])
        mods = load(root)
        if probe.get("break_interference"):
            mods["build"].interference = lambda parts, lid_angles=(0.0,): ["case_lid × hinge_pin: 0.3 mm³"]
        out = run_build(mods, ["--check"])
        if probe.get("flagged"):
            out["flagged"] = flagged(mods)
        return out
    if op == "report":
        root = variant(index, [])
        return report_vs_trusted(load(root), root)
    if op == "order":
        root = variant(index, [])
        return order(load(root), root)
    raise ValueError(op)


probes = json.loads((app / "probes.json").read_text())
for index, probe in enumerate(probes):
    try:
        value = observe(index, probe)
    except Exception as exc:  # noqa: BLE001
        value = {"error": type(exc).__name__}
    print(json.dumps({"id": index, "value": value}, allow_nan=False, default=str), flush=True)
