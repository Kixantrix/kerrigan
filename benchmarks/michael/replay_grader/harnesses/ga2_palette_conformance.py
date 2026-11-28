"""Answer-free sandbox adapter: calls the candidate palette-conformance module on held-out colors and palettes."""

import json
import math
from pathlib import Path
import sys

app = Path(__file__).resolve().parent
sys.path.insert(0, str(app / "scripts"))


def plain(value):
    """JSON-safe copy of untrusted output; non-finite floats become strings."""
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return repr(value)


def rgb(color):
    return [int(channel) for channel in color]


def conform(module, probe):
    colors = [tuple(c) for c in probe["colors"]]
    supplied = (c for c in colors) if probe.get("generator") else colors
    kwargs = {"tolerance": probe["tolerance"]} if "tolerance" in probe else {}
    result = module.colors_conform(supplied, probe["faction"], **kwargs)
    offending = [rgb(c) for c in result.offending_colors]
    return {"passed": result.passed, "worst": float(result.worst_delta_e),
            "offending": sorted({tuple(c) for c in map(tuple, offending)}), "offending_count": len(offending)}


def run(module, probe):
    op = probe["op"]
    if op == "conform":
        return conform(module, probe)
    if op == "lab":
        return [[float(v) for v in module.rgb_to_lab(*color)] for color in probe["colors"]]
    if op == "delta_e":
        return [float(module.delta_e_cie76(tuple(a), tuple(b))) for a, b in probe["pairs"]]
    if op == "default":
        return float(module.DEFAULT_TOLERANCE)
    raise ValueError(op)


try:
    import ga2.palette_conformance as candidate
except Exception as exc:  # noqa: BLE001 - an unimportable candidate fails every probe
    candidate, failure = None, {"$error": type(exc).__name__}

for index, probe in enumerate(json.loads((app / "probes.json").read_text())):
    if candidate is None:
        value = failure
    else:
        try:
            value = plain(run(candidate, probe))
        except Exception as exc:  # noqa: BLE001
            value = {"$error": type(exc).__name__}
    print(json.dumps({"id": index, "value": value}, allow_nan=False), flush=True)
