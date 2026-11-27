"""Offline observation grading; candidate bytes are never imported by this process."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import tarfile
import time
import uuid

from benchmarks.michael.tasks import packages
from benchmarks.michael.replay_grader.policy import cases, clause_passes
from benchmarks.michael.replay_grader import specs

HERE = Path(__file__).resolve().parent
IMAGE = "michael-replay-grader:mb006j"
LABEL = "michael-replay-grader"
SOURCE_LIMIT = 262144
OUTPUT_LIMIT = 131072
FRAME_LIMIT = 8192
POLICY_FILES = ("api.py", "owner.py", "policy.py", "harness.py", "bootstrap.py", "Dockerfile",
                "specs.py", "ts_policy.py", "clauses.py", "harness_ts.mjs", "bootstrap.mjs", "Dockerfile.node")
CONTROLLER_FD = None


class GraderError(RuntimeError):
    pass


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def persist(path, data):
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        stream.write(encoded(data))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def command(args, *, seconds=15, payload=None, limit=OUTPUT_LIMIT):
    """Bound both pipes in aggregate, and reap only this owned CLI child."""
    with subprocess.Popen(args, stdin=subprocess.PIPE if payload is not None else subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        output = {process.stdout: bytearray(), process.stderr: bytearray()}
        end = time.monotonic() + seconds
        try:
            with selectors.DefaultSelector() as selector:
                # Let create finish registration even on controller loss. It cannot
                # execute code; subsequent operations observe EOF before start.
                monitor = CONTROLLER_FD if args[:2] != ["docker", "create"] else None
                if monitor is not None:
                    selector.register(monitor, selectors.EVENT_READ)
                for stream in output:
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ)
                pending = memoryview(payload) if payload is not None else None
                if pending is not None:
                    os.set_blocking(process.stdin.fileno(), False)
                    selector.register(process.stdin, selectors.EVENT_WRITE)
                while any(key.fileobj != monitor for key in selector.get_map().values()):
                    remaining = end - time.monotonic()
                    if remaining <= 0:
                        raise GraderError("timeout")
                    for key, _ in selector.select(remaining):
                        if key.fileobj == monitor:
                            raise GraderError("controller_lost")
                        elif key.fileobj is process.stdin:
                            count = os.write(process.stdin.fileno(), pending[:65536])
                            pending = pending[count:]
                            if not pending:
                                selector.unregister(process.stdin)
                                process.stdin.close()
                        else:
                            chunk = os.read(key.fd, 8192)
                            if not chunk:
                                selector.unregister(key.fileobj)
                            else:
                                output[key.fileobj].extend(chunk)
                                if sum(map(len, output.values())) > limit:
                                    raise GraderError("output_overflow")
                process.wait(timeout=max(0.001, end - time.monotonic()))
        except BaseException:
            process.kill()
            process.wait()
            raise
        return process.returncode, bytes(output[process.stdout]), bytes(output[process.stderr])


def docker(*args, **kwargs):
    code, stdout, stderr = command(["docker", *args], **kwargs)
    if code:
        raise GraderError(f"docker_error:{code}:{stderr[:512].decode(errors='replace')}")
    return stdout


def owned(run_id):
    if not re.fullmatch(r"[a-f0-9]{32}", run_id):
        raise ValueError("invalid owned run ID")
    ids = docker("ps", "-aq", "--no-trunc", "--filter", f"label={LABEL}={run_id}").decode().splitlines()
    if any(not re.fullmatch(r"[a-f0-9]{64}", item) for item in ids):
        raise GraderError("invalid owned container inventory")
    return ids


def cleanup(run_id):
    ids = owned(run_id)
    if ids:
        docker("rm", "-f", *ids)
    remaining = owned(run_id)
    if remaining:
        raise GraderError("owned cleanup incomplete")
    return {"removed": ids, "remaining": remaining, "proven": True}


def recover(directory):
    """Remove only label-owned containers; never restart/replay candidate actions."""
    start = json.loads((Path(directory) / "start.json").read_bytes())
    receipt = cleanup(start["run_id"])
    persist(Path(directory) / "recovery.json", receipt)
    if (Path(directory) / "owner.json").exists():
        terminal = Path(directory) / "terminal.json"
        report = Path(directory) / "report.json"
        if (not terminal.exists() or not report.exists()
                or json.loads(terminal.read_bytes()).get("run_id") != start["run_id"]
                or json.loads(terminal.read_bytes()).get("report_sha256") != sha(report.read_bytes())):
            raise GraderError("owner/proof lost: sandbox removed, owner quiescence unproven")
    return receipt


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise GraderError("duplicate observation key")
        value[key] = item
    return value


def observations(raw, rows, valid=None):
    valid_value = valid or specs.SPECS["validator"]["valid"]
    if len(raw) > OUTPUT_LIMIT or not raw.endswith(b"\n"):
        raise GraderError("truncated_or_oversized_observations")
    lines = raw.splitlines()
    if len(lines) != len(rows):
        raise GraderError("missing_or_extra_observations")
    result = []
    for index, (line, row) in enumerate(zip(lines, rows)):
        if len(line) > FRAME_LIMIT:
            raise GraderError("observation_frame_overflow")
        try:
            item = json.loads(line, object_pairs_hook=unique_object)
        except (ValueError, RecursionError, UnicodeError) as exc:
            raise GraderError("malformed_observation") from exc
        if (not isinstance(item, dict) or set(item) != {"id", "value"}
                or type(item["id"]) is not int or item["id"] != index):
            raise GraderError("invalid_or_duplicate_observation_id")
        value = item["value"]
        if not valid_value(row, value):
            raise GraderError("invalid_observation_value")
        result.append(value)
    return result


def policy_files(task="validator"):
    names = list(POLICY_FILES)
    for name in [specs.spec(task)["harness"], *specs.spec(task).get("support", [])]:
        if name not in names:
            names.append(name)
    return {name: sha((HERE / name).read_bytes()) for name in names}


def bindings(source, task="validator"):
    agent, verifier, descriptor, frozen = specs.package(task)
    if descriptor != frozen:
        raise GraderError("frozen package mismatch")
    policy = policy_files(task)
    return {"task": task, "source_sha256": sha(source), "package_sha256": packages.bundle_digest(agent),
            "verifier_material_sha256": packages.inventory(verifier),
            "policy_files_sha256": policy, "verifier_policy_sha256": sha(encoded(policy))}


def _create_default(spec, name, run_id, image_id):
    docker("create", "-i", "--name", name, "--label", f"{LABEL}={run_id}", "--network", "none",
           "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
           "--memory", "128m", "--memory-swap", "128m", "--cpus", "1", "--pids-limit", "32",
           "--ulimit", "nofile=64:64", "--ulimit", "fsize=1048576:1048576",
           "--log-driver", "none", "--tmpfs", "/work:rw,noexec,nosuid,size=16m,mode=1777",
           "--user", "65534:65534", "--workdir", "/work", image_id,
           *(["python", "-I", "-B", "-c", (HERE / "bootstrap.py").read_text()]
             if spec["runtime"] == "python" else
             ["node", "--max-old-space-size=96", "--input-type=module", "-e",
              (HERE / "bootstrap.mjs").read_text()]))
    info = json.loads(docker("inspect", name))[0]
    config = info["HostConfig"]
    if (info["Mounts"] or config["Binds"] or config["Privileged"]
            or config["NetworkMode"] != "none" or not config["ReadonlyRootfs"]
            or config["CapDrop"] != ["ALL"]):
        raise GraderError("containment_configuration_mismatch")
    return {key: config[key] for key in
            ("NetworkMode", "ReadonlyRootfs", "CapDrop", "SecurityOpt",
             "Memory", "MemorySwap", "NanoCpus", "PidsLimit", "Tmpfs", "Binds")}


ANCHOR_CAPS = ["CHOWN", "DAC_OVERRIDE", "FOWNER", "FSETID", "KILL", "NET_BIND_SERVICE", "SETGID", "SETUID"]


def _create_anchor(spec, name, run_id, image_id):
    """Harbor anchors: the task's own image, root, writable container layer, no network.

    Root and a writable (discarded) container layer are what the original Harbor
    verifier gives the task's tests (service start, logs, package metadata). Still
    no network, no mounts, minimal capabilities, no-new-privileges, bounded resources.
    """
    docker("create", "-i", "--name", name, "--label", f"{LABEL}={run_id}", "--network", "none",
           "--cap-drop", "ALL", *[arg for cap in ANCHOR_CAPS for arg in ("--cap-add", cap)],
           "--security-opt", "no-new-privileges:true",
           "--memory", spec["memory"], "--memory-swap", spec["memory"], "--cpus", "1",
           "--pids-limit", "512", "--ulimit", "nofile=8192:8192", "--log-driver", "none",
           "--user", "0:0", "--workdir", spec["workdir"], image_id,
           spec["python"], "-I", "-B", "-c", (HERE / "bootstrap.py").read_text())
    info = json.loads(docker("inspect", name))[0]
    config = info["HostConfig"]
    added = sorted(cap.removeprefix("CAP_") for cap in config["CapAdd"] or [])
    if (info["Mounts"] or config["Binds"] or config["Privileged"] or config["NetworkMode"] != "none"
            or config["CapDrop"] != ["ALL"] or added != sorted(ANCHOR_CAPS)):
        raise GraderError("containment_configuration_mismatch")
    return {key: config.get(key) for key in
            ("NetworkMode", "ReadonlyRootfs", "CapDrop", "CapAdd", "SecurityOpt",
             "Memory", "MemorySwap", "NanoCpus", "PidsLimit", "Tmpfs", "Binds")}


def grade(source, directory, *, seconds=10, task="validator"):
    specs.spec(task)
    if not isinstance(source, bytes) or not 0 < len(source) <= SOURCE_LIMIT:
        raise ValueError("candidate source byte limit")
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 < seconds <= 30:
        raise ValueError("candidate execution budget must be finite and <=30 seconds")
    # Harbor anchors run the task's own test suite; their package declares a larger floor.
    seconds = max(seconds, specs.spec(task).get("candidate_seconds", 0))
    directory = Path(directory).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex
    with (directory / "source.bin").open("wb") as stream:
        stream.write(source)
        stream.flush()
        os.fsync(stream.fileno())
    persist(directory / "start.json", {"run_id": run_id, "seconds": seconds, "task": task,
                                       "source_sha256": sha(source)})
    reader, writer = os.pipe()
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "benchmarks.michael.replay_grader.owner",
             str(directory), str(reader)], pass_fds=(reader,), start_new_session=True,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=packages.ROOT)
        os.close(reader)
        reader = None
        process.wait(timeout=seconds + 120)
        terminal = directory / "terminal.json"
        if process.returncode or not terminal.exists():
            raise GraderError("owner/proof lost; cleanup unknown")
        proof = json.loads(terminal.read_bytes())
        report = json.loads((directory / "report.json").read_bytes())
        if (proof["run_id"] != run_id or proof["report_sha256"] != sha((directory / "report.json").read_bytes())):
            raise GraderError("owner terminal binding mismatch")
        return report
    except (GraderError, OSError, ValueError, subprocess.SubprocessError) as exc:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        report = {"run_id": run_id, "status": "ungraded", "verdict": None,
                  "counts": None, "assertions": [], "error": str(exc),
                  "cleanup": {"proven": False, "error": "owner/proof lost"}}
        persist(directory / "report.json", report)
        return report
    finally:
        os.close(writer)
        if reader is not None:
            os.close(reader)


def _grade(source, directory, *, seconds=10):
    global CONTROLLER_FD
    start = json.loads((directory / "start.json").read_bytes())
    run_id, task = start["run_id"], start.get("task", "validator")
    report = {"run_id": run_id, "task": task, "status": "ungraded", "verdict": None,
              "assertions": [], "counts": None, "timings": {},
              "timing_scope": "same trusted owner host, monotonic seconds; no model or task-completion time"}
    phase = "staging"
    begin = time.monotonic()
    try:
        spec = specs.spec(task)
        report["bindings"] = bindings(source, task)
        rows = spec["rows"]()
        groups = list(dict.fromkeys(row["group"] for row in rows))
        if {group: sum(row["group"] == group for row in rows) for group in groups} != spec["denominators"]:
            raise GraderError("trusted policy denominator mismatch")
        image = json.loads(docker("image", "inspect", spec["image"]))[0]
        report["image_id"] = image["Id"]
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as tar:
            for name, data in {
                **spec["extra"](),
                **specs.unbundle(task, source),
                spec["harness_target"]: (HERE / spec["harness"]).read_bytes(),
                "probes.json": encoded([row["probe"] for row in rows]),
            }.items():
                entry = tarfile.TarInfo(name)
                entry.size, entry.mode = len(data), 0o444
                tar.addfile(entry, io.BytesIO(data))
        report["candidate_archive_sha256"] = sha(archive.getvalue())
        name = f"mb-replay-{run_id}"
        if spec["runtime"] == "harbor":
            report["containment"] = _create_anchor(spec, name, run_id, image["Id"])
        else:
            report["containment"] = _create_default(spec, name, run_id, image["Id"])
        report["timings"][phase] = time.monotonic() - begin
        phase, begin = "candidate_execution", time.monotonic()
        deadline = begin + seconds
        persist(directory / "execution.json", {"run_id": run_id, "deadline_monotonic": deadline})
        code, stdout, stderr = command(["docker", "start", "-ai", name],
                                       seconds=max(.001, deadline - time.monotonic()),
                                       payload=archive.getvalue())
        report["candidate_output"] = {"stdout_bytes": len(stdout), "stderr_bytes": len(stderr),
                                       "stderr_excerpt": stderr[:2048].decode(errors="replace")}
        state = json.loads(docker("inspect", name))[0]["State"]
        report["candidate_state"] = {key: state[key] for key in ("Running", "ExitCode", "OOMKilled")}
        if state["Running"]:
            raise GraderError("candidate_still_running")
        if state["OOMKilled"]:
            raise GraderError("candidate_oom")
        if code or state["ExitCode"]:
            raise GraderError(f"candidate_exit:{code}:{state['ExitCode']}")
        report["observation_sha256"] = sha(stdout)
        report["stderr_sha256"] = sha(stderr)
        report["timings"][phase] = time.monotonic() - begin
        phase, begin = "verification", time.monotonic()
        values = observations(stdout, rows, spec["valid"])
        for row, value in zip(rows, values):
            checks = [{"clause": clause, "passed": clause_passes(value, clause)}
                      for clause in row["clauses"]]
            report["assertions"].append({"original_id": row["original_id"], "group": row["group"],
                                         "passed": all(c["passed"] for c in checks),
                                         "observed": value, "checks": checks})
        report["counts"] = {
            group: {"passed": sum(a["passed"] for a in report["assertions"] if a["group"] == group),
                    "total": sum(a["group"] == group for a in report["assertions"])}
            for group in groups}
        report["verdict"] = "pass" if all(a["passed"] for a in report["assertions"]) else "fail"
        report["status"] = "graded"
    except (GraderError, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        report["error"] = f"{type(exc).__name__}:{str(exc)[:1024]}"
    finally:
        CONTROLLER_FD = None
        report["timings"][phase] = time.monotonic() - begin
        begin = time.monotonic()
        try:
            report["cleanup"] = cleanup(run_id)
        except (GraderError, OSError, ValueError, subprocess.SubprocessError) as exc:
            report["cleanup"] = {"proven": False, "error": str(exc)[:1024]}
            report["status"], report["verdict"] = "ungraded", None
        report["timings"]["cleanup"] = time.monotonic() - begin
        for missing in ("staging", "candidate_execution", "verification"):
            report["timings"].setdefault(missing, None)
        persist(directory / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--task", default="validator", choices=sorted(specs.SPECS))
    args = parser.parse_args()
    with args.source.open("rb") as stream:
        source = stream.read(SOURCE_LIMIT + 1)
    report = grade(source, args.receipt, task=args.task)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["verdict"] == "pass" else 1)


if __name__ == "__main__":
    main()
