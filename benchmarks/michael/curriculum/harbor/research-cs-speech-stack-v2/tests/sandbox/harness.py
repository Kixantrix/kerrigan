"""Answer-free sandbox adapter: emits a JSON artifact plus order-insensitive views of declared arrays.

v2 adds ``any_of``: for each declared {"path": [...], "options": [[...], ...]}, whether the array at
``path`` contains every item of at least one option (any sufficient set of items)."""

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


def any_of(value, options):
    return isinstance(value, list) and any(all(item in value for item in option) for option in options)


cache = {}
for index, probe in enumerate(probes):
    path = probe["artifact"]
    if path not in cache:
        cache[path] = load(path)
    value = {"artifact": cache[path], "sets": [set_view(at(cache[path], p)) for p in probe.get("sets", [])],
             "any_of": [any_of(at(cache[path], c["path"]), c["options"]) for c in probe.get("any_of", [])]}
    print(json.dumps({"id": index, "value": value}, allow_nan=False, default=str), flush=True)
