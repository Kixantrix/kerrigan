"""Answer-free sandbox adapter: runs the candidate ML-01 harness on held-out household data."""

import hashlib
import importlib
import json
import math
from pathlib import Path
import sys

app = Path(__file__).resolve().parent
sys.path.insert(0, str(app / "apps/taste-engine/src"))
REPORT = app / "apps/taste-engine/eval/reports/ml-01-baselines.json"
DATA = json.loads((app / "heldout.json").read_text())


def module(name):
    return importlib.import_module(f"taste_engine.eval.{name}")


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


def fresh(name):
    data = DATA["datasets"][name]
    return json.loads(json.dumps(data["events"])), json.loads(json.dumps(data["titles"])), data["cutoff"]


def split_probe(probe):
    events, _, cutoff = fresh(probe["dataset"])
    train, test = module("split").temporal_split(events, cutoff)
    rows = sorted(json.dumps([e["viewer"], e["title"], e["ts"], e["rating"]]) for e in train)
    return {"train_size": len(rows),
            "train_sha256": hashlib.sha256("\n".join(rows).encode()).hexdigest(),
            "test": {str(viewer): sorted(titles) for viewer, titles in dict(test).items() if titles}}


def rank_probe(probe):
    events, titles, cutoff = fresh(probe["dataset"])
    train = [event for event in events if event["ts"] < cutoff]
    rank = getattr(module("baselines"), probe["ranker"])
    return {viewer: list(rank(viewer, json.loads(json.dumps(train)), titles, probe["k"]))
            for viewer in probe["viewers"]}


def run(probe):
    op = probe["op"]
    if op == "split":
        return split_probe(probe)
    if op == "rank":
        return rank_probe(probe)
    if op == "metric":
        function = getattr(module("metrics"), probe["function"])
        return [function(*case) for case in probe["cases"]]
    if op == "sign_test":
        return [module("benchmark").sign_test(*case) for case in probe["cases"]]
    if op == "benchmark":
        return module("benchmark").run_benchmark(*fresh(probe["dataset"]))
    if op == "report":
        return json.loads(REPORT.read_text())
    raise ValueError(op)


for index, probe in enumerate(json.loads((app / "probes.json").read_text())):
    try:
        value = plain(run(probe))
    except Exception as exc:  # noqa: BLE001
        value = {"$error": type(exc).__name__}
    print(json.dumps({"id": index, "value": value}, allow_nan=False), flush=True)
