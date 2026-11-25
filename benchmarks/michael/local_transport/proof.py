"""Trusted diagnostics only; deliberately no model execution or grading API."""
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
import uuid

LIMIT = 65536
INPUT_LIMIT = 8192
MODELS = ("mai-code-2", "claude-sonnet-5.5")


def monotonic():
    # Python <3.10 on macOS uses a process-relative time.monotonic epoch.
    return time.clock_gettime(time.CLOCK_MONOTONIC)


class ProofError(RuntimeError):
    pass


def persist(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    with Path(path).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def fresh(path):
    path = Path(path).resolve()
    if any((p / ".git").exists() for p in (path, *path.parents)):
        raise ProofError("diagnostics must be outside repository/history")
    path.mkdir(parents=True, exist_ok=False)
    return path


def environment(state):
    state = Path(state).resolve()
    return {
        "PATH": "/usr/bin:/bin", "HOME": str(state / "home"),
        "TMPDIR": str(state / "tmp"), "COPILOT_HOME": str(state / "cli"),
        "COPILOT_CACHE_HOME": str(state / "cache"),
        "COPILOT_DISABLE_LOGIN_SHELL_ENV": "true",
        "COPILOT_PLUGIN_DIR_ONLY": "true", "COPILOT_MCP_TOOL_CACHE": "false",
        "COPILOT_ALLOW_ALL": "false", "USE_TGREP": "false",
        "COPILOT_LLM_RESPONSE_MAX_BYTES": str(LIMIT),
    }


def fixture(directory):
    directory = fresh(directory)
    for name in ("home", "tmp", "cli", "cache", "task", "denied"):
        (directory / name).mkdir()
    (directory / "denied" / "credential-fixture").write_text("synthetic-not-a-secret\n")
    settings = {
        "extensions": {"mode": "disabled"},
        "sandbox": {
            "enabled": False, "allowBypass": False, "allowDevToolAccess": False,
            "sandboxMcpServers": True, "sandboxLspServers": True,
            "sandboxExtensions": True,
            "auth": {"git": False, "gh": False},
            "userPolicy": {
                "filesystem": {"deniedPaths": [str(directory / "denied")]},
                "network": {"allowOutbound": False, "allowLocalNetwork": False},
                "seatbelt": {"keychainAccess": False, "extraMachLookups": []},
            },
        },
    }
    persist(directory / "cli" / "settings.json", settings)
    return directory


def capture(argv, cwd, directory, *, seconds=10, input_bytes=b"", env=None, native=False):
    if native:
        raise ProofError("native execution gated: effective CLI tools and process tree unproven")
    if not math.isfinite(seconds) or not 0 < seconds <= 180:
        raise ValueError("active seconds must be finite, positive and at most 180")
    if len(input_bytes) > INPUT_LIMIT:
        raise ProofError("input_overflow")
    cwd = Path(cwd).resolve()
    if any((p / ".git").exists() for p in (cwd, *cwd.parents)):
        raise ProofError("diagnostic cwd must be outside repository/history")
    directory = fresh(directory)
    start = {"run_id": uuid.uuid4().hex, "argv": list(argv), "cwd": str(cwd),
             "active_seconds": seconds, "cleanup_seconds": 15,
             "clock": "clock_gettime(CLOCK_MONOTONIC), host-wide",
             "started_monotonic": monotonic(), "wall_started": time.time(),
             "native": False, "verdict": "ungraded"}
    persist(directory / "start.json", start)
    reader, writer = os.pipe()
    watcher = subprocess.Popen(
        [sys.executable, __file__, "watch", str(directory), str(reader)],
        pass_fds=(reader,), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=environment(directory) if env is None else env, start_new_session=True)
    os.close(reader)
    try:
        watcher.communicate(input_bytes, timeout=seconds + 15)
        terminal = directory / "terminal.json"
        if watcher.returncode or not terminal.exists():
            raise ProofError("watcher failed; retain start, no replay or PID recovery")
        return json.loads(terminal.read_text())
    finally:
        os.close(writer)


def watch(directory, controller):
    directory = Path(directory)
    start = json.loads((directory / "start.json").read_text())
    until = start["started_monotonic"] + start["active_seconds"]
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    observed = dict.fromkeys(buffers, 0)
    process = None
    reason = "runtime_error"
    direct_exit = False
    selector = selectors.DefaultSelector()
    selector.register(controller, selectors.EVENT_READ, "controller")
    try:
        payload = sys.stdin.buffer.read(INPUT_LIMIT + 1)
        if len(payload) > INPUT_LIMIT:
            raise ProofError("input_overflow")
        process = subprocess.Popen(
            start["argv"], cwd=start["cwd"], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        persist(directory / "process.json", {"pid": process.pid,
                "ownership": "live Popen child; never recover by recorded PID",
                "launched_monotonic": monotonic()})
        process.stdin.write(payload)
        process.stdin.close()
        for name in buffers:
            selector.register(getattr(process, name), selectors.EVENT_READ, name)
        while True:
            if monotonic() >= until:
                raise ProofError("timeout")
            for key, _ in selector.select(min(0.02, max(0, until - monotonic()))):
                if key.data == "controller":
                    if not os.read(controller, 1):
                        raise ProofError("controller_lost")
                    continue
                chunk = os.read(key.fd, 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                observed[key.data] += len(chunk)
                room = LIMIT - len(buffers[key.data])
                buffers[key.data].extend(chunk[:room])
                if len(chunk) > room:
                    raise ProofError("output_overflow:" + key.data)
            if process.poll() is not None and len(selector.get_map()) == 1:
                reason = "completed" if process.returncode == 0 else "runtime_error"
                break
    except (ProofError, OSError, subprocess.SubprocessError) as exc:
        reason = str(exc)
    finally:
        cleanup_started = monotonic()
        if process is not None:
            # An unreaped direct child pins its PID; no saved-PID or process-name signals.
            if process.poll() is None:
                process.kill()
            try:
                process.wait(timeout=15)
                direct_exit = True
            except subprocess.TimeoutExpired:
                direct_exit = False
            for stream in (process.stdout, process.stderr):
                stream.close()
        selector.close()
        os.close(controller)
        persist(directory / "capture.json", {
            "limit_per_channel": LIMIT,
            "channels": {name: {
                "base64_prefix": base64.b64encode(data).decode(),
                "retained_bytes": len(data), "observed_bytes_lower_bound": observed[name],
            } for name, data in buffers.items()},
        })
        persist(directory / "terminal.json", {
            "run_id": start["run_id"], "stop_reason": reason, "verdict": "ungraded",
            "returncode": process.returncode if process else None,
            "active_seconds": cleanup_started - start["started_monotonic"],
            "cleanup_seconds": monotonic() - cleanup_started,
            "cleanup": {"direct_child_reaped": direct_exit,
                        "whole_process_tree": "unproven", "recoverable": True},
            "observed_model": "unknown", "usage": "unknown", "replayed_actions": 0,
        })


def recover(directory):
    directory = Path(directory)
    start = json.loads((directory / "start.json").read_text())
    receipt = directory / "recovery.json"
    if not receipt.exists():
        persist(receipt, {"run_id": start["run_id"], "verdict": "ungraded",
                         "whole_process_tree": "unproven", "replayed_actions": 0,
                         "signals_sent": 0})
    raise ProofError("whole-process quiescence unproven; no recorded-PID signals or replay")


def mxc_policy(executable, task, denied, command, seconds=5):
    return {
        "version": "1.0.0", "containment": "seatbelt",
        "process": {"commandLine": command, "cwd": str(task), "timeout": seconds * 1000,
                    "env": ["PATH=/usr/bin:/bin"], "inheritDefaultEnv": False},
        "filesystem": {"readwritePaths": [str(task)],
                       "readonlyPaths": [str(Path(executable).resolve().parent)],
                       "deniedPaths": [str(denied)]},
        "network": {"egress": {"default": "deny"},
                    "ingress": {"default": "deny", "hostLoopback": "deny"}},
        "seatbelt": {"keychainAccess": False, "guiAccess": False},
    }


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "watch":
        watch(sys.argv[2], int(sys.argv[3]))
    else:
        raise SystemExit("trusted diagnostic watcher only; no native execution entry point")
