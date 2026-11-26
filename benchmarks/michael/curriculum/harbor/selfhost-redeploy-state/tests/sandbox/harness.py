"""Answer-free sandbox adapter: drives the disposable stack with the candidate config."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

app = Path(__file__).resolve().parent
work = Path("/work/stack")
shutil.copytree(app / "stack/api", work / "api")
shutil.copy(app / "stack/compose.json", work / "compose.json")
spec = importlib.util.spec_from_file_location("supervisor", app / "stack/supervisor.py")
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)


def tree_digest():
    digest = hashlib.sha256()
    for path in sorted((work / "api").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(str(path.relative_to(work)).encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def step(function, *args):
    try:
        return function(*args)
    except Exception as exc:  # noqa: BLE001 - failures are observations
        return {"$error": type(exc).__name__}


def scenario():
    report = {"health": {}, "room": {}}
    config = json.loads((work / "compose.json").read_text())
    service = config.get("services", {}).get("api", {})
    report["service"] = {key: service.get(key) for key in ("image", "entrypoint", "ports", "environment")}
    before = tree_digest()
    state = Path("/work/state")
    stack = supervisor.Stack(work / "compose.json", state)
    resolved = step(stack.resolve, "api", "/data")
    kind, data = resolved if isinstance(resolved, tuple) else ("error", None)
    report["data_mount"] = {"kind": kind}
    code = step(stack.resolve, "api", "/app")
    report["code_mount"] = ([code[0], str(code[1].relative_to(work))] if isinstance(code, tuple)
                            and code[1].is_relative_to(work) else None)
    if kind == "named":
        # Existing production data already present in the declared volume.
        data.mkdir(parents=True, exist_ok=True)
        (data / "rooms.json").write_text(json.dumps({"lobby": {"pin": "1177"}}))
    if step(stack.up) is None:
        step(stack.request, "api", "POST", "/rooms", {"name": "standup", "pin": "4821"})
        if step(stack.deploy) is None:
            report["health"]["after_deploy"] = step(stack.request, "api", "GET", "/healthz")[0]
            report["room"]["after_deploy"] = list(step(stack.request, "api", "GET", "/rooms/standup"))
            report["room"]["preexisting"] = list(step(stack.request, "api", "GET", "/rooms/lobby"))
        if step(stack.recreate) is None:
            report["health"]["after_recreate"] = step(stack.request, "api", "GET", "/healthz")[0]
            report["room"]["after_recreate"] = list(step(stack.request, "api", "GET", "/rooms/standup"))
    report["code_tree_unchanged"] = tree_digest() == before
    return report


probes = json.loads((app / "probes.json").read_text())
try:
    value = scenario()
except Exception as exc:  # noqa: BLE001
    value = {"error": type(exc).__name__}
for index, _ in enumerate(probes):
    print(json.dumps({"id": index, "value": value}, allow_nan=False, default=str), flush=True)
