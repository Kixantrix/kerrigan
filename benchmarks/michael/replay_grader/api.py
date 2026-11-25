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
import tarfile
import time
import uuid

from benchmarks.michael.tasks import packages
from benchmarks.michael.replay_grader.policy import cases, clause_passes

HERE = Path(__file__).resolve().parent
IMAGE = "michael-replay-grader:mb006j"
LABEL = "michael-replay-grader"
SOURCE_LIMIT = 262144
OUTPUT_LIMIT = 131072
FRAME_LIMIT = 8192
POLICY_FILES = ("api.py", "policy.py", "harness.py", "bootstrap.py", "Dockerfile")


class GraderError(RuntimeError):
    pass


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(args, *, seconds=15, payload=None, limit=OUTPUT_LIMIT):
    """Bound both pipes in aggregate, and reap only this owned CLI child."""
    with subprocess.Popen(args, stdin=subprocess.PIPE if payload is not None else subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        output = {process.stdout: bytearray(), process.stderr: bytearray()}
        end = time.monotonic() + seconds
        try:
            with selectors.DefaultSelector() as selector:
                for stream in output:
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ)
                pending = memoryview(payload) if payload is not None else None
                if pending is not None:
                    os.set_blocking(process.stdin.fileno(), False)
                    selector.register(process.stdin, selectors.EVENT_WRITE)
                while selector.get_map():
                    remaining = end - time.monotonic()
                    if remaining <= 0:
                        raise GraderError("timeout")
                    for key, _ in selector.select(remaining):
                        if key.fileobj is process.stdin:
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
    (Path(directory) / "recovery.json").write_bytes(encoded(receipt))
    return receipt


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise GraderError("duplicate observation key")
        value[key] = item
    return value


def observations(raw, rows):
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
        if row["probe"]["op"] == "parse":
            valid = value is None or (isinstance(value, dict) and len(value) <= 64
                                     and all(isinstance(k, str) and isinstance(v, str)
                                             for k, v in value.items()))
        else:
            valid = isinstance(value, list) and len(value) <= 64 and all(
                isinstance(v, str) for v in value)
        if not valid:
            raise GraderError("invalid_observation_value")
        result.append(value)
    return result


def bindings(source):
    agent = packages.agent_files("validator")
    verifier = packages.verifier_files("validator")
    frozen = json.loads((packages.HERE / "validator/manifest.json").read_bytes())
    if packages.descriptor("validator") != frozen:
        raise GraderError("frozen package mismatch")
    policy = {name: sha((HERE / name).read_bytes()) for name in POLICY_FILES}
    return {"source_sha256": sha(source), "package_sha256": packages.bundle_digest(agent),
            "verifier_material_sha256": packages.inventory(verifier),
            "policy_files_sha256": policy, "verifier_policy_sha256": sha(encoded(policy))}


def grade(source, directory, *, seconds=10):
    if not isinstance(source, bytes) or not 0 < len(source) <= SOURCE_LIMIT:
        raise ValueError("candidate source byte limit")
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 < seconds <= 30:
        raise ValueError("candidate execution budget must be finite and <=30 seconds")
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex
    report = {"run_id": run_id, "status": "ungraded", "verdict": None,
              "assertions": [], "counts": None, "timings": {},
              "timing_scope": "same controller host, monotonic seconds; no model or task-completion time"}
    (directory / "start.json").write_bytes(encoded({"run_id": run_id}))
    phase = "staging"
    begin = time.monotonic()
    try:
        report["bindings"] = bindings(source)
        rows = cases()
        if len(rows) != 25 or sum(row["group"] == "preservation" for row in rows) != 15:
            raise GraderError("trusted policy denominator mismatch")
        image = json.loads(docker("image", "inspect", IMAGE))[0]
        report["image_id"] = image["Id"]
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as tar:
            for name, data in {
                "tools/validators/agents_md.py": source,
                "harness.py": (HERE / "harness.py").read_bytes(),
                "probes.json": encoded([row["probe"] for row in rows]),
            }.items():
                entry = tarfile.TarInfo(name)
                entry.size, entry.mode = len(data), 0o444
                tar.addfile(entry, io.BytesIO(data))
        report["candidate_archive_sha256"] = sha(archive.getvalue())
        name = f"mb-replay-{run_id}"
        docker("create", "-i", "--name", name, "--label", f"{LABEL}={run_id}", "--network", "none",
               "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
               "--memory", "128m", "--memory-swap", "128m", "--cpus", "1", "--pids-limit", "32",
               "--ulimit", "nofile=64:64", "--ulimit", "fsize=1048576:1048576",
               "--log-driver", "none", "--tmpfs", "/work:rw,noexec,nosuid,size=16m,mode=1777",
               "--user", "65534:65534", "--workdir", "/work", image["Id"],
               "python", "-I", "-B", "-c", (HERE / "bootstrap.py").read_text())
        info = json.loads(docker("inspect", name))[0]
        config = info["HostConfig"]
        if (info["Mounts"] or config["Binds"] or config["Privileged"]
                or config["NetworkMode"] != "none" or not config["ReadonlyRootfs"]
                or config["CapDrop"] != ["ALL"]):
            raise GraderError("containment_configuration_mismatch")
        report["containment"] = {key: config[key] for key in
                                 ("NetworkMode", "ReadonlyRootfs", "CapDrop", "SecurityOpt",
                                  "Memory", "MemorySwap", "NanoCpus", "PidsLimit", "Tmpfs", "Binds")}
        report["timings"][phase] = time.monotonic() - begin
        phase, begin = "candidate_execution", time.monotonic()
        code, stdout, stderr = command(["docker", "start", "-ai", name], seconds=seconds,
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
        values = observations(stdout, rows)
        for row, value in zip(rows, values):
            checks = [{"clause": clause, "passed": clause_passes(value, clause)}
                      for clause in row["clauses"]]
            report["assertions"].append({"original_id": row["original_id"], "group": row["group"],
                                         "passed": all(c["passed"] for c in checks),
                                         "observed": value, "checks": checks})
        report["counts"] = {
            group: {"passed": sum(a["passed"] for a in report["assertions"] if a["group"] == group),
                    "total": sum(a["group"] == group for a in report["assertions"])}
            for group in ("preservation", "regression")}
        report["verdict"] = "pass" if all(a["passed"] for a in report["assertions"]) else "fail"
        report["status"] = "graded"
    except (GraderError, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        report["error"] = f"{type(exc).__name__}:{str(exc)[:1024]}"
    finally:
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
        (directory / "report.json").write_bytes(encoded(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    with args.source.open("rb") as stream:
        source = stream.read(SOURCE_LIMIT + 1)
    report = grade(source, args.receipt)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["verdict"] == "pass" else 1)


if __name__ == "__main__":
    main()
