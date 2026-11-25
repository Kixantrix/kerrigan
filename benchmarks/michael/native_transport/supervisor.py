"""Independent Linux supervisor: durable starts, bounded output, no recovery replay."""
import ctypes
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import threading
import time
import uuid

from broker import BoundaryError, LIMIT, create, persist, remove


def descendants(root):
    parents = {}
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rsplit(")", 1)[1].split()
            parents[int(path.parent.name)] = (int(fields[1]), fields[0], fields[19])
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    owned = {root}
    while added := {pid for pid, (parent, _, _) in parents.items() if parent in owned} - owned:
        owned |= added
    return {pid: parents[pid][2] for pid in owned - {root} if parents[pid][1] != "Z"}


def terminate(until):
    killed = []
    while pids := descendants(os.getpid()):
        if time.monotonic() >= until:
            raise BoundaryError("process cleanup deadline")
        for pid in pids:
            try:
                fd = os.pidfd_open(pid)
                try:
                    ticks = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
                    if ticks == pids[pid]:
                        signal.pidfd_send_signal(fd, signal.SIGKILL)
                        killed.append(pid)
                finally:
                    os.close(fd)
            except ProcessLookupError:
                pass
            except FileNotFoundError:
                pass
        time.sleep(0.02)
    return {"killed": killed, "remaining": descendants(os.getpid())}


def watch(directory, controller_fd):
    directory = Path(directory)
    start = json.loads((directory / "start.json").read_text())
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0):
        raise OSError(ctypes.get_errno(), "cannot establish child subreaper")
    began = time.monotonic()
    until = began + start["active_seconds"]
    state = {"run_id": start["run_id"], "state": "running", "verdict": "ungraded",
             "supervisor_pid": os.getpid(), "started_monotonic": began,
             "requested_model": start["requested_model"], "observed_model": "unknown",
             "effective_native_inventory": "unknown", "usage": "unknown",
             "native": start["native"], "events": []}
    process = None
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    lost, cleaning = False, False

    def stop(signum, frame):
        if not cleaning:
            raise BoundaryError("controller_lost" if lost else "cancelled")

    def monitor_controller():
        nonlocal lost
        try:
            os.read(controller_fd, 1)
        except OSError:
            if cleaning:
                return
            raise
        lost = True
        os.kill(os.getpid(), signal.SIGTERM)

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    persist(directory / "progress.json", state)
    try:
        threading.Thread(target=monitor_controller, daemon=True).start()
        sandbox = create(start["run_id"], until)
        persist(directory / "sandbox.json", sandbox)
        state["setup_seconds"] = time.monotonic() - began
        command = [arg.replace("{run_id}", start["run_id"]).replace("{directory}", str(directory))
                   .replace("{deadline}", str(until)) for arg in start["argv"]]
        state["command_started_monotonic"] = time.monotonic()
        persist(directory / "progress.json", state)
        process = subprocess.Popen(command, cwd=start["cwd"], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, bufsize=0)
        with selectors.DefaultSelector() as selector:
            for name in buffers:
                selector.register(getattr(process, name), selectors.EVENT_READ, name)
            while True:
                if time.monotonic() >= until:
                    raise BoundaryError("timeout")
                for key, _ in selector.select(0.02):
                    chunk = os.read(key.fd, 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    room = LIMIT - len(buffers[key.data])
                    buffers[key.data].extend(chunk[:room])
                    if len(chunk) > room:
                        raise BoundaryError(f"output_overflow:{key.data}")
                    persist(directory / "output.json", {
                        name: bytes(value).decode(errors="replace") for name, value in buffers.items()})
                if process.poll() is not None and not selector.get_map():
                    state["stop_reason"] = "completed" if process.returncode == 0 else "runtime_error"
                    break
    except (BoundaryError, OSError, subprocess.SubprocessError) as exc:
        state["stop_reason"] = str(exc)
    finally:
        cleaning = True
        cleanup_began = time.monotonic()
        reserve = cleanup_began + 15
        state["active_seconds"] = cleanup_began - began
        cleanup = {}
        try:
            cleanup["processes"] = terminate(reserve)
            cleanup["sandbox"] = remove(start["run_id"], reserve)
        except (BoundaryError, OSError, subprocess.SubprocessError) as exc:
            cleanup["error"] = str(exc)
        if process is not None:
            process.poll()
            process.stdout.close()
            process.stderr.close()
        while True:
            try:
                if os.waitpid(-1, os.WNOHANG)[0] == 0:
                    break
            except ChildProcessError:
                break
        os.close(controller_fd)
        state.update(state="stopped", returncode=process.returncode if process else None,
                     cleanup=cleanup, cleanup_seconds=time.monotonic() - cleanup_began,
                     end_to_end_seconds=time.monotonic() - began)
        persist(directory / "output.json", {
            name: bytes(value).decode(errors="replace") for name, value in buffers.items()})
        persist(directory / "terminal.json", state)
    return state


def run(argv, cwd, directory, seconds=180, requested_model="synthetic-fake", native=False):
    if not 0 < seconds <= 180:
        raise ValueError("active budget must be positive and at most 180")
    if native:
        raise BoundaryError("native launch gated: actual inventory and access proof required")
    cwd = Path(cwd).resolve()
    if any((parent / ".git").exists() for parent in (cwd, *cwd.parents)):
        raise BoundaryError("transport workspace must be outside repository/history")
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    persist(directory / "start.json", {
        "run_id": uuid.uuid4().hex, "argv": argv, "cwd": str(Path(cwd).resolve()),
        "active_seconds": seconds, "cleanup_seconds": 15, "requested_model": requested_model,
        "native": native, "verdict": "ungraded", "wall_started": time.time()})
    reader, writer = os.pipe()
    watcher = subprocess.Popen([sys.executable, __file__, "watch", str(directory), str(reader)],
                               pass_fds=(reader,), start_new_session=True,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    os.close(reader)
    try:
        watcher.wait(timeout=seconds + 16)
        if watcher.returncode or not (directory / "terminal.json").exists():
            raise BoundaryError("watcher failed; retained start requires explicit recovery")
        return json.loads((directory / "terminal.json").read_text())
    finally:
        os.close(writer)


def recover(directory):
    directory = Path(directory)
    terminal = directory / "terminal.json"
    if terminal.exists():
        result = json.loads(terminal.read_text())
        if "error" in result["cleanup"]:
            raise BoundaryError(f"retained terminal has incomplete cleanup: {result['cleanup']['error']}")
        if (result["cleanup"].get("processes", {}).get("remaining") != {}
                or result["cleanup"].get("sandbox", {}).get("remaining") != []):
            raise BoundaryError("retained terminal lacks durable cleanup proof; quiescence is unproven")
        return result
    start = json.loads((directory / "start.json").read_text())
    progress = directory / "progress.json"
    if not progress.exists():
        raise BoundaryError("retained start lacks supervisor receipt; quiescence is unproven")
    pid = json.loads(progress.read_text())["supervisor_pid"]
    if Path(f"/proc/{pid}").exists():
        raise BoundaryError("recorded supervisor PID is present; ownership/quiescence is unproven")
    recovery = directory / "recovery.json"
    if not recovery.exists():
        cleanup = remove(start["run_id"], time.monotonic() + 15)
        persist(recovery, {"run_id": start["run_id"], "state": "quiescence_unproven",
                          "verdict": "ungraded", "sandbox_cleanup": cleanup,
                          "reason": "supervisor_lost_without_durable_process_cleanup",
                          "replayed_actions": 0})
    raise BoundaryError("supervisor lost; process quiescence is unproven; retained start requires attestation")


if __name__ == "__main__":
    watch(sys.argv[2], int(sys.argv[3]))
