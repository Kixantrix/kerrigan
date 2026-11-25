"""Real validator public workflow; invoked only within MXC."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
import validator_worker as files

files.POLICY = json.loads(Path(__file__).with_name("validator-task-policy.json").read_bytes())
policy = files.POLICY
raw = sys.stdin.buffer.read(policy["payload"] + 1)
if len(raw) > policy["payload"]:
    raise ValueError("action overflow")
args = json.loads(raw)
op, name = args["op"], args["path"]
if set(args) != ({"op", "path", "data"} if op == "write" else {"op", "path"}):
    raise ValueError("action fields denied")
if op == "read":
    sys.stdout.buffer.write(files.read_source(".", name))
elif op == "write" and name in policy["write"] and isinstance(args["data"], str):
    data = args["data"].encode()
    if len(data) > policy["bytes"]:
        raise ValueError("file overflow")
    with os.fdopen(files.opened(".", name, os.O_WRONLY), "wb") as stream:
        stream.truncate(0)
        stream.write(data)
    print("written")
elif op == "run" and name in policy["write"]:
    files.read_source(".", name)
    os.execv(sys.executable, [sys.executable, "-I", "-B",
                             str(Path(__file__).with_name("task-run.py")), name])
else:
    raise ValueError("operation denied")
