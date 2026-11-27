"""Real validator public workflow; invoked only within MXC."""
import json
import os
from pathlib import Path
import sys
import re
sys.path.insert(0, str(Path(__file__).parent))
import validator_worker as files

files.POLICY = json.loads(Path(__file__).with_name("validator-task-policy.json").read_bytes())
policy = files.POLICY
raw = sys.stdin.buffer.read(policy["payload"] + 1)
if len(raw) > policy["payload"]:
    raise ValueError("action overflow")
args = json.loads(raw)
op, name = args["op"], args["path"]
scratch = (policy.get("scratchDirectory") == ".scratch" and
           isinstance(name, str) and name.startswith(".scratch/") and
           all(re.fullmatch(r"[A-Za-z0-9_.-]+", part) and part not in (".", "..")
               for part in name.split("/")))
if scratch:
    policy = {**policy, "read": [*policy["read"], name],
              "write": [*policy["write"], name], "run": [*policy["run"], name]}
    files.POLICY = policy
if set(args) != ({"op", "path", "data"} if op == "write" else
                 {"op", "path", "offset"} if op == "read" and "offset" in args else {"op", "path"}):
    raise ValueError("action fields denied")
if op == "read":
    read_policy = {**policy, "bytes": max(policy["bytes"], policy.get("readonlySizes", {}).get(name, 0))}
    data = files.read_source(".", name, policy=read_policy)
    offset = args.get("offset", 0)
    if type(offset) is not int or not 0 <= offset <= 4194304:
        raise ValueError("invalid read offset")
    chunk = int(os.environ.get("MB_CURRICULUM_READ_CHUNK", "0"))
    if chunk:
        data = data[offset:offset + chunk]
    elif len(data) > policy["bytes"]:
        marker = b"\n[readonly file truncated to channel limit]\n"
        data = data[:policy["bytes"] - len(marker)] + marker
    sys.stdout.buffer.write(data)
elif op == "write" and name in policy["write"] and isinstance(args["data"], str):
    data = args["data"].encode()
    if len(data) > policy["bytes"]:
        raise ValueError("file overflow")
    if scratch:
        parent = Path(name).parent
        current = Path(".scratch")
        for part in parent.parts[1:]:
            current /= part
            current.mkdir(exist_ok=True)
            if current.is_symlink() or not current.is_dir():
                raise ValueError("scratch parent denied")
    with os.fdopen(files.opened(".", name, os.O_WRONLY | os.O_CREAT), "wb") as stream:
        stream.truncate(0)
        stream.write(data)
    print("written")
elif op == "run" and name in policy["write"]:
    if name not in policy.get("run", policy["write"]):
        raise ValueError("non-executable artifact")
    files.read_source(".", name)
    if Path(name).suffix in (".ts", ".mjs", ".js"):
        runtime = json.loads(Path(__file__).with_name("node-runtime.json").read_bytes())
        os.execv(runtime["path"], [runtime["path"], "--disable-warning=ExperimentalWarning", name])
    os.execv(sys.executable, [sys.executable, "-I", "-B",
                             str(Path(__file__).with_name("task-run.py")), name])
else:
    raise ValueError("operation denied")
