"""Answer-free sandbox adapter: parses a JSON artifact and emits it, bounded. Output is untrusted."""

import json
from pathlib import Path

app = Path(__file__).resolve().parent
probes = json.loads((app / "probes.json").read_text())


def load(path):
    try:
        value = json.loads((app / path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - malformed artifacts are observations
        return {"$error": type(exc).__name__}
    text = json.dumps(value, allow_nan=False, default=str)
    return value if len(text) <= 6000 else {"$error": "too_large"}


cache = {}
for index, probe in enumerate(probes):
    path = probe["artifact"]
    if path not in cache:
        cache[path] = load(path)
    print(json.dumps({"id": index, "value": cache[path]}, allow_nan=False), flush=True)
