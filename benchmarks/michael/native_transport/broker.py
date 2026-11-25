"""Trusted, single-tool synthetic Docker broker; no model code runs on the host."""
import fcntl
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import time

IMAGE = "python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b"
LIMIT = 65536
TOOL = "mb-broker-action"
REQUIREMENT = "Implement double(n) in solution.py. Use only the sandbox broker.\n"
BASE = "def double(n):\n    raise NotImplementedError\n"


class BoundaryError(RuntimeError):
    pass


def persist(path, value):
    path = Path(path)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def capture(argv, until, data=None, limit=LIMIT):
    """Bound both channels while draining concurrently; never use a shell."""
    if time.monotonic() >= until:
        raise BoundaryError("deadline")
    process = subprocess.Popen(argv, stdin=subprocess.PIPE if data else subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    try:
        if data:
            process.stdin.write(data)
            process.stdin.close()
        with selectors.DefaultSelector() as selector:
            for name in buffers:
                selector.register(getattr(process, name), selectors.EVENT_READ, name)
            while selector.get_map():
                if time.monotonic() >= until:
                    raise BoundaryError("deadline")
                for key, _ in selector.select(min(0.05, until - time.monotonic())):
                    chunk = os.read(key.fd, 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    room = limit - len(buffers[key.data])
                    buffers[key.data].extend(chunk[:room])
                    if len(chunk) > room:
                        raise BoundaryError(f"output_overflow:{key.data}")
        process.wait(timeout=max(0.01, until - time.monotonic()))
        return {"returncode": process.returncode,
                **{key: value.decode("utf-8", errors="replace") for key, value in buffers.items()}}
    except BoundaryError as exc:
        exc.capture = {"limit_bytes_per_channel": limit,
                       "retained_bytes": {name: len(value) for name, value in buffers.items()}}
        raise
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=2)
        process.stdout.close()
        process.stderr.close()


def docker(*args, until, data=None):
    result = capture(["docker", *args], until, data)
    if result["returncode"]:
        raise BoundaryError(f"docker:{args[0]}:{result['stderr']}")
    return result["stdout"]


def container_name(run_id):
    if not re.fullmatch("[0-9a-f]{32}", run_id):
        raise BoundaryError("invalid resource identity")
    return f"mb-native-{run_id}"


def remove(run_id, until):
    name = container_name(run_id)
    found = docker("ps", "-aq", "--filter", f"name=^/{name}$",
                   "--filter", f"label=mb-native={run_id}", until=until).split()
    if found:
        docker("rm", "-f", *found, until=until)
    remaining = docker("ps", "-aq", "--filter", f"label=mb-native={run_id}", until=until).split()
    if remaining:
        raise BoundaryError("owned sandbox survived cleanup")
    return {"removed": found, "remaining": remaining}


def create(run_id, until):
    name = container_name(run_id)
    docker("run", "-d", "--name", name, "--label", f"mb-native={run_id}",
           "--network", "none", "--read-only", "--cap-drop", "ALL",
           "--security-opt", "no-new-privileges", "--memory", "256m",
           "--memory-swap", "256m", "--cpus", "1", "--pids-limit", "64",
           "--log-driver", "none", "--tmpfs", "/work:rw,size=16m",
           "--tmpfs", "/tmp:rw,size=4m", "--workdir", "/work",
           IMAGE, "sleep", str(max(1, int(until - time.monotonic()) + 15)), until=until)
    info = json.loads(docker("inspect", name, until=until))[0]
    config = info["HostConfig"]
    if (config["NetworkMode"] != "none" or not config["ReadonlyRootfs"]
            or config["Privileged"] or config["CapDrop"] != ["ALL"]
            or config["Memory"] != 256 * 1024 * 1024 or config["PidsLimit"] != 64
            or config["NanoCpus"] != 1000000000 or info["Mounts"]
            or set(config["Tmpfs"]) != {"/work", "/tmp"}):
        raise BoundaryError("unexpected Docker isolation")
    material = json.dumps({"REQUIREMENT.txt": REQUIREMENT, "solution.py": BASE}).encode()
    docker("exec", "-i", name, "python", "-B", "-c",
           "import json,sys,os\nfrom pathlib import Path\n"
           "for n,v in json.load(sys.stdin).items():\n"
           " p=Path('/work')/n;p.write_text(v);p.chmod(0o666 if n=='solution.py' else 0o444)\n"
           "os.chmod('/work',0o755)", until=until, data=material)
    return {"name": name, "inspect": info, "materials": {
        "REQUIREMENT.txt": REQUIREMENT, "solution.py": BASE}}


def action(run_id, directory, request, until):
    if len(json.dumps(request).encode()) > 16384:
        raise BoundaryError("input_overflow")
    journal = Path(directory) / "actions.jsonl"
    with journal.open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        entries = [json.loads(line) for line in stream]
        if len(entries) >= 16:
            raise BoundaryError("action_budget")
        identity = request.get("action_id") if isinstance(request, dict) else None
        if not isinstance(identity, str) or not re.fullmatch("[a-z0-9-]{1,64}", identity):
            raise BoundaryError("invalid action identity")
        if any(entry["action_id"] == identity for entry in entries):
            raise BoundaryError("duplicate action; no replay")

        def record(state, **extra):
            stream.write(json.dumps({"action_id": identity, "state": state,
                                    "monotonic": time.monotonic(), **extra}) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

        record("started", request=request)
        try:
            op = request.get("op")
            expected = {"action_id", "op"}
            if op in ("read", "write"):
                expected.add("path")
            if op == "write":
                expected.add("content")
            if set(request) != expected or op not in ("read", "write", "run"):
                raise BoundaryError("invalid action schema")
            if op in ("read", "write") and request["path"] not in ("REQUIREMENT.txt", "solution.py"):
                raise BoundaryError("path denied")
            if op == "write" and request["path"] != "solution.py":
                raise BoundaryError("write denied")
            if op == "write" and (not isinstance(request["content"], str)
                                 or len(request["content"].encode()) > 8192):
                raise BoundaryError("input_overflow")
            if op == "run":
                command = ["python", "-B", "/work/solution.py"]
                data = None
            else:
                command = ["python", "-B", "-c",
                           "import os,json,sys\nr=json.load(sys.stdin)\n"
                           "flags=os.O_NOFOLLOW|(os.O_RDONLY if r['op']=='read' else os.O_WRONLY|os.O_TRUNC)\n"
                           "fd=os.open('/work/'+r['path'],flags)\n"
                           "if r['op']=='read':\n print(os.read(fd,8193).decode(),end='')\n"
                           "else:\n os.write(fd,r['content'].encode())\n"
                           "os.close(fd)"]
                data = json.dumps(request).encode()
            result = capture(["docker", "exec", "-i", "--user", "65534:65534",
                              container_name(run_id), *command], min(until, time.monotonic() + 10), data)
            if result["returncode"]:
                raise BoundaryError(f"execution_failed:{result['returncode']}:{result['stderr']}")
            record("completed", result=result)
            return result
        except (BoundaryError, OSError, UnicodeError) as exc:
            record("rejected", error=str(exc), capture=getattr(exc, "capture", None))
            if str(exc) == "deadline" or str(exc).startswith("output_overflow"):
                docker("kill", container_name(run_id), until=time.monotonic() + 2)
            raise


def serve(run_id, directory, until):
    """Narrow stdio MCP JSON-RPC surface, no resource/prompt/shell tools."""
    import sys
    schema = {"type": "object", "properties": {
        "action_id": {"type": "string"}, "op": {"enum": ["read", "write", "run"]},
        "path": {"enum": ["REQUIREMENT.txt", "solution.py"]}, "content": {"type": "string"}},
        "required": ["action_id", "op"], "additionalProperties": False}
    while raw := sys.stdin.buffer.readline(16385):
        if len(raw) > 16384 or not raw.endswith(b"\n"):
            raise BoundaryError("MCP input overflow")
        request_id = None
        try:
            request = json.loads(raw)
            request_id = request.get("id")
            method = request["method"]
            if method == "notifications/initialized":
                continue
            if method == "initialize":
                version = request["params"]["protocolVersion"]
                if version not in ("2024-11-05", "2025-03-26", "2025-06-18"):
                    raise BoundaryError("unsupported MCP protocol")
                result = {"protocolVersion": version, "capabilities": {"tools": {}},
                          "serverInfo": {"name": "mb-broker", "version": "1"}}
            elif method == "tools/list":
                result = {"tools": [{"name": "action", "description": REQUIREMENT, "inputSchema": schema}]}
            elif method == "tools/call" and request["params"]["name"] == "action":
                value = action(run_id, directory, request["params"]["arguments"], until)
                result = {"content": [{"type": "text", "text": json.dumps(value)}]}
            else:
                raise BoundaryError("method/tool denied")
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        except (BoundaryError, KeyError, ValueError, TypeError) as exc:
            response = {"jsonrpc": "2.0", "id": request_id,
                        "error": {"code": -32602, "message": str(exc)}}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    import sys
    serve(sys.argv[1], sys.argv[2], float(sys.argv[3]))
