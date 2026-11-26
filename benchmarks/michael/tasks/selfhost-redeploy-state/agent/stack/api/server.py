"""Room/PIN API for the call stack. Stores state as JSON under DATA_DIR."""

import json
import os
from pathlib import Path


def _store():
    return Path(os.environ["DATA_DIR"]) / "rooms.json"


def _load():
    path = _store()
    return json.loads(path.read_text()) if path.exists() else {}


def app(method, path, body=None):
    """Minimal request handler: returns (status, json-able body)."""
    if method == "GET" and path == "/healthz":
        Path(os.environ["DATA_DIR"]).mkdir(parents=True, exist_ok=True)
        return 200, {"ok": True}
    if method == "POST" and path == "/rooms":
        rooms = _load()
        rooms[body["name"]] = {"pin": body["pin"]}
        _store().parent.mkdir(parents=True, exist_ok=True)
        _store().write_text(json.dumps(rooms, sort_keys=True))
        return 201, {"name": body["name"]}
    if method == "GET" and path.startswith("/rooms/"):
        room = _load().get(path.split("/", 2)[2])
        return (200, room) if room else (404, {"error": "unknown room"})
    return 404, {"error": "not found"}
