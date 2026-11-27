"""Answer-free sandbox adapter: emits a JSON artifact plus order-insensitive views of declared arrays."""

import json
from pathlib import Path

app = Path(__file__).resolve().parent
probes = json.loads((app / "probes.json").read_text())


def load(path):
    try:
        value = json.loads((app / path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - malformed artifacts are observations
        return {"$error": type(exc).__name__}
    return value if len(json.dumps(value, allow_nan=False, default=str)) <= 6000 else {"$error": "too_large"}


def at(value, path):
    for key in path:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def set_view(value):
    if not isinstance(value, list):
        return None
    items = [json.dumps(item, sort_keys=True) for item in value]
    return {"sorted": sorted(json.loads(item) for item in set(items)) if all(
        isinstance(v, (str, int, float)) for v in value) else sorted(set(items)),
            "duplicates": len(items) - len(set(items))}


cache = {}
for index, probe in enumerate(probes):
    path = probe["artifact"]
    if path not in cache:
        cache[path] = load(path)
    value = {"artifact": cache[path], "sets": [set_view(at(cache[path], p)) for p in probe.get("sets", [])]}
    print(json.dumps({"id": index, "value": value}, allow_nan=False, default=str), flush=True)
