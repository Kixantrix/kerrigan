"""Answer-free sandbox adapter: runs the candidate assay on held-out synthetic sequences."""

import importlib.util
import json
import math
from pathlib import Path
import random

app = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("temporal_mech", app / "assay/temporal_mech.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
HELD_OUT = {"A": (2.25, 11), "B": (-1.75, 5)}


def sequence(shift, seed, frames=6, width=64):
    """Trusted generator, independent of the candidate's make_sequence."""
    rng = random.Random(seed)
    raw = [rng.random() for _ in range(width)]
    base = [(raw[i - 1] + 2 * raw[i] + raw[(i + 1) % width]) / 4 for i in range(width)]

    def at(position):
        left = math.floor(position)
        frac = position - left
        return base[left % width] * (1 - frac) + base[(left + 1) % width] * frac
    return [[at(x - shift * t) for x in range(width)] for t in range(frames)]


def finite(value):
    return value if isinstance(value, float) and math.isfinite(value) else None


def assay():
    report = {"mse": {}, "zero": {}, "scaled": {}, "diagnosis": None}
    for name, (shift, seed) in HELD_OUT.items():
        frames = sequence(shift, seed)
        report["zero"][name] = sum(
            sum((a - b) ** 2 for a, b in zip(frames[t - 1], frames[t])) / len(frames[t])
            for t in range(1, len(frames))) / (len(frames) - 1)
        results = {}
        for model in ("warp-linear", "warp-nearest", "self-offset"):
            for flow in ("block", "coarse"):
                for oracle in (True, False):
                    key = f"{model}|{flow}|{'on' if oracle else 'off'}"
                    try:
                        value = candidate.run_assay(model, [list(f) for f in frames], flow, oracle, shift)
                        results[key] = finite(float(value["mse"]))
                    except Exception as exc:  # noqa: BLE001
                        results[key] = {"$error": type(exc).__name__}
        report["mse"][name] = results
        report["scaled"][name] = {key: value * 4 for key, value in results.items()
                                  if isinstance(value, float)}
    diagnosis = getattr(candidate, "DIAGNOSIS", None)
    if isinstance(diagnosis, dict):
        report["diagnosis"] = {
            "root_cause": diagnosis.get("root_cause") if isinstance(diagnosis.get("root_cause"), str) else None,
            "invalid_results": sorted(str(v) for v in diagnosis.get("invalid_results") or [])[:16],
            "retracted_conclusions": sorted(str(v) for v in diagnosis.get("retracted_conclusions") or [])[:16]}
    return report


probes = json.loads((app / "probes.json").read_text())
try:
    value = assay()
except Exception as exc:  # noqa: BLE001
    value = {"error": type(exc).__name__}
for index, _ in enumerate(probes):
    print(json.dumps({"id": index, "value": value}, allow_nan=False, default=str), flush=True)
