"""Closed credential-free MB-005 CLI, not a live provider/session adapter."""

import argparse
from copy import deepcopy
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

from benchmarks.michael.contracts.manifests import manifest_reference, validate_bundle
from benchmarks.michael.engine_proof import proof
from benchmarks.michael.ledger_report.api import Ledger, compare
from benchmarks.michael.cli.worker import IMAGE, MODES, STREAM_LIMIT

HERE = Path(__file__).resolve().parent
RESERVE = 15


class ReserveExceeded(Exception):
    """Terminal persistence requires explicit recovery if its reserve is exhausted."""


def reserve_exceeded(signum, frame):
    raise ReserveExceeded("cleanup/evidence reserve exhausted; recover the retained start")


def command(*args, until):
    remaining = until - time.monotonic()
    if remaining <= 0:
        raise RuntimeError("cleanup reserve exhausted")
    value = subprocess.run(["docker", *args], capture_output=True, timeout=remaining)
    if value.returncode:
        raise RuntimeError(value.stderr.decode(errors="replace"))
    return value.stdout.decode().strip()


def owned_processes(run_id):
    """Only inspect membership in our unique inherited marker; never retain environment."""
    marker = f"MB_CLI_ID={run_id}".encode()
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if marker in (entry / "environ").read_bytes().split(b"\0"):
                state = (entry / "stat").read_text().rsplit(")", 1)[1].split()[0]
                if state != "Z":
                    found.append(int(entry.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            # Other users' processes cannot inherit our newly generated random marker.
            continue
    return found


def cleanup(run_id):
    until = time.monotonic() + RESERVE
    receipt = {"run_id": run_id, "killed_pids": [], "errors": []}
    try:
        while pids := owned_processes(run_id):
            if time.monotonic() >= until:
                raise RuntimeError("owned processes did not quiesce")
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGKILL)
                    receipt["killed_pids"].append(pid)
                except ProcessLookupError:
                    pass
            time.sleep(0.02)
        receipt["remaining_processes"] = owned_processes(run_id)
        for kind, listing in (("containers", ("ps", "-aq")), ("volumes", ("volume", "ls", "-q"))):
            ids = command(*listing, "--filter", f"label=michael-cli={run_id}", until=until).split()
            receipt[f"removed_{kind}"] = ids
            if ids:
                operation = ("rm", "-f") if kind == "containers" else ("volume", "rm")
                command(*operation, *ids, until=until)
            receipt[f"remaining_{kind}"] = command(
                *listing, "--filter", f"label=michael-cli={run_id}", until=until).split()
            if receipt[f"remaining_{kind}"]:
                raise RuntimeError(f"owned {kind} survived cleanup")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        receipt["errors"].append(str(exc))
    return receipt


def frozen(arm, seconds):
    data = deepcopy(proof.bundle("mb005-stable", 30))
    source = "MB-005 synthetic derivation of MB-002 constants; not native model evidence"
    for name in data:
        data[name]["id"] = f"mb005-synthetic-{name}" + (f"-{arm}" if name in ("target", "condition") else "")
        data[name]["provenance"] = {"source_id": source}
    target = data["target"]
    target["requested_identity"] = f"synthetic-fake-{arm}"
    target["observed_identity"] = proof.known("mockllm/mb005", source)
    agent = data["agent"]
    binding = hashlib.sha256()
    for path in (HERE / "__main__.py", HERE / "worker.py", HERE / "compose.yaml", Path(proof.__file__)):
        binding.update(path.name.encode() + b"\0" + path.read_bytes())
    agent["harness"] = {"id": "mb005-inspect-adapter", "revision": "1", "sha256": binding.hexdigest()}
    agent["configuration"] = proof.known(
        {"engine": "inspect-ai==0.3.292", "image": IMAGE, "fixture": "scripted fake",
         "whole_trial_seconds": seconds, "cleanup_reserve_seconds": RESERVE,
         "stream_limit_bytes_per_channel": STREAM_LIMIT,
         "allowlisted_output": ["answer.py"], "network": "none",
         "verification": "stopped agent/candidate; separate trusted response grader"}, source)
    condition = data["condition"]
    condition["track"] = "practical_system"
    condition["budgets"]["active_safety_seconds"] = proof.known(seconds, source)
    for name in ("task", "target", "agent"):
        condition[name] = manifest_reference(data[name])
    return validate_bundle(**data)


def elapsed(seconds, run_id, phase="end_to_end", coverage="complete"):
    return proof.known({"seconds": seconds, "scope": phase, "clock": "monotonic",
                        "host_ids": [f"controller:{run_id}"], "coverage": coverage},
                       f"MB-005 controller monotonic:{run_id}")


def artifacts(directory):
    for path in [directory, *directory.rglob("*")]:
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return [{"uri": path.relative_to(directory).as_posix(),
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(directory.rglob("*")) if path.is_file()
            and path.name not in {"ledger.jsonl", "report.json", "terminal.json"}
            and "home" not in path.relative_to(directory).parts]


def recover(directory):
    start = json.loads((directory / "start.json").read_text())
    run_id = start["run_id"]
    if not re.fullmatch("[0-9a-f]{32}", run_id):
        raise ValueError("invalid owned recovery ID")
    ledger = Ledger(directory / "ledger.jsonl")
    trial_state = ledger.snapshot()[run_id]
    if len(trial_state["starts"]) == len(trial_state["attempts"]):
        return 3
    receipt = cleanup(run_id)
    proof.write(directory / ("recovery-cleanup.json" if (directory / "cleanup.json").exists()
                             else "cleanup.json"), receipt)
    if receipt["errors"]:
        raise RuntimeError(f"recovery cleanup failed: {receipt['errors']}")
    trial = ledger.snapshot()[run_id]
    if len(trial["starts"]) > len(trial["attempts"]):
        ledger.checkpoint(run_id, "a1", event_id="recovery",
                          event={"category": "infrastructure", "code": "controller_interrupted",
                                 "source": "MB-005 recovery; no replay"},
                          timing={}, artifacts=artifacts(directory))
        ledger.recover(run_id)
    proof.write(directory / "terminal.json", ledger.snapshot()[run_id])
    return 3


def trial(directory, arm, mode, seconds):
    directory.mkdir(parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex
    data = frozen(arm, seconds)
    ledger = Ledger(directory / "ledger.jsonl")
    ledger.start(run_id, data, attempt_id="a1", origin="synthetic")
    proof.write(directory / "start.json", {"run_id": run_id, "mode": mode, "bundle": data,
                                         "deadline_seconds": seconds, "cleanup_reserve": RESERVE})
    started = time.monotonic()
    stop, process, interrupted = None, None, False
    events = []
    def handle(signum, frame):
        nonlocal interrupted
        interrupted = True
    previous = {sig: signal.signal(sig, handle) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        env = {key: os.environ[key] for key in ("PATH", "DOCKER_CONFIG") if key in os.environ}
        home = directory / "home"
        home.mkdir()
        env.update(HOME=str(home), MB_CLI_ID=run_id, PYTHONPATH=str(HERE.parents[2]))
        with (directory / "controller.log").open("wb") as output:
            process = subprocess.Popen(
                [sys.executable, "-m", "benchmarks.michael.cli.worker", str(directory), mode],
                env=env, cwd=home, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            last = None
            while True:
                now = time.monotonic()
                if interrupted or now - started >= seconds:
                    stop = "interruption" if interrupted else "timeout"
                    break
                progress = directory / "progress.json"
                if progress.exists():
                    raw = progress.read_bytes()
                    if raw != last:
                        last = raw
                        checkpoint = directory / f"checkpoint-{len(events)}.json"
                        checkpoint.write_bytes(raw)
                        event = {"category": "runtime", "code": "controller_observation",
                                 "source": "MB-005 immutable progress checkpoint"}
                        ledger.checkpoint(run_id, "a1", event_id=f"e{len(events)}", event=event,
                                          timing={"end_to_end": elapsed(now - started, run_id,
                                                                       coverage="partial")},
                                          artifacts=[{"uri": checkpoint.name,
                                                      "sha256": hashlib.sha256(raw).hexdigest()}])
                        events.append(event)
                if process.poll() is not None:
                    break
                time.sleep(0.05)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        stop = "runtime_error"
        proof.write(directory / "controller-error.json", {"error": str(exc)})
    finally:
        signal.setitimer(signal.ITIMER_REAL, RESERVE)
        safety = cleanup(run_id)
        if process is not None:
            process.wait(timeout=1)
        proof.write(directory / "cleanup.json", safety)
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    receipt_path = directory / "receipt.json"
    progress_path = directory / "progress.json"
    receipt = json.loads((receipt_path if receipt_path.exists() else progress_path).read_text()) if (
        receipt_path.exists() or progress_path.exists()) else {}
    verified = receipt.get("verified", "not_run")
    if (not receipt_path.exists() or process is None or process.returncode != 0
            or receipt.get("engine_status") != "success" or receipt.get("sample_error")):
        verified = "not_run"
    limits = []
    for role in ("candidate", "verifier"):
        capture_path = directory / f"{role}-capture.json"
        if capture_path.exists():
            limit = json.loads(capture_path.read_text()).get("output_limit")
            if limit is not None:
                limits.append(limit)
                events.append({"category": "safety", "code": f"{role}_output_limit_{limit['channel']}",
                               "source": f"MB-005 streaming cap: {limit['limit_bytes']} bytes per channel"})
    if stop is None and limits:
        stop = "safety_stop"
        verified = "error" if any(limit["role"] == "verifier" for limit in limits) else "not_run"
    if stop is None:
        stop = {"passed": "success", "failed": "agent_finished", "error": "evaluator_error"}.get(
            verified, "runtime_error")
    if safety["errors"]:
        stop, verified = "runtime_error", "not_run"
    if stop in ("timeout", "interruption"):
        verified = "not_run"
    duration = time.monotonic() - started
    timing = {phase: elapsed(value, run_id, phase) for phase, value in receipt.get("phases", {}).items()}
    if "setup" in timing:
        timing["setup"] = elapsed(receipt["phases"]["setup"] +
                                 receipt["worker_started_monotonic"] - started, run_id, "setup")
    timing["end_to_end"] = elapsed(duration, run_id)
    for phase in ("queue", "provisioning", "setup", "agent_work", "verification"):
        timing.setdefault(phase, proof.unknown("phase not separately measured", "MB-005 controller"))
    usage = {"credits": proof.unknown("no paid inference", "MB-005", "not_applicable")}
    for path in (directory / "raw").glob("*.json"):
        try:
            raw = json.loads(path.read_text())
            samples = raw.get("samples", [])
        except json.JSONDecodeError:
            samples = []
        if not samples:
            usage["synthetic_total_tokens"] = proof.unknown(
                "incomplete raw engine log; no final sample telemetry", f"raw:{path.name}")
            events.append({"category": "infrastructure", "code": "incomplete_engine_log",
                           "source": f"raw:{path.name}; original bytes retained"})
            continue
        for model, values in samples[0]["model_usage"].items():
            for metric, value in values.items():
                if isinstance(value, (int, float)):
                    usage[f"synthetic_{metric}"] = proof.known(value, f"raw:{path.name}:{model}")
    events.append({"category": "safety" if stop in ("timeout", "safety_stop") else "runtime", "code": stop,
                   "source": "MB-005 outer controller; not native engine stop"})
    attempt = {"id": "a1", "verdict": {"passed": "passed", "failed": "failed"}.get(verified, "ungraded"),
               "state": "interrupted" if stop == "interruption" else
                        "completed" if stop in ("success", "agent_finished", "evaluator_error") else "stopped",
               "stop_reason": stop, "verifier": {"status": verified,
                   "independent": verified in ("passed", "failed", "error"),
                   "source": "MB-005 trusted grading outside candidate execution boundary"},
               "events": events, "timing": timing, "usage": usage,
               "time_to_verified_completion": timing["end_to_end"] if stop == "success" else
                   proof.unknown("no verified completion; deadline is not duration", "MB-005")}
    result = {"schema_version": 1, "kind": "result", "id": f"mb005-result-{run_id}", "revision": "1",
              "provenance": {"source_id": "MB-005 synthetic derived terminal",
                             "artifact_base_uri": directory.as_uri(),
                             "artifacts": artifacts(directory)},
              "condition": manifest_reference(data["condition"]), "attempts": [attempt]}
    proof.write(directory / "evidence.json", {"synthetic": True, "artifacts": artifacts(directory),
        "derivation": {"task": manifest_reference(data["task"]),
                       "condition": manifest_reference(data["condition"]),
                       "raw_engine_evidence_unchanged": True},
        "safety": {"whole_trial_seconds": seconds, "cleanup_reserve_seconds": RESERVE,
                   "cutoff": stop == "timeout", "observed_seconds": duration, "cleanup": safety}})
    observed = len(ledger.snapshot()[run_id]["checkpoints"])
    for index, event in enumerate(events[observed:]):
        ledger.checkpoint(run_id, "a1", event_id=f"artifacts-{index}", event=event,
                          timing={}, artifacts=artifacts(directory))
    ledger.finalize(run_id, result)
    proof.write(directory / "terminal.json", ledger.snapshot()[run_id])
    signal.setitimer(signal.ITIMER_REAL, 0)
    return run_id, data, result


def preflight():
    if version("inspect-ai") != "0.3.292":
        raise ValueError("requires inspect-ai==0.3.292")
    config = os.environ.get("DOCKER_CONFIG")
    if not config or (Path(config) / "config.json").exists():
        raise ValueError("DOCKER_CONFIG must name a credential-free directory without config.json")
    until = time.monotonic() + 10
    command("info", until=until)
    command("compose", "version", until=until)
    command("image", "inspect", IMAGE, until=until)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("run", "compare", "recover"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--mode", choices=MODES, default="success")
    parser.add_argument("--seconds", type=float, default=45)
    args = parser.parse_args()
    prior_alarm = signal.signal(signal.SIGALRM, reserve_exceeded)
    try:
        if not math.isfinite(args.seconds) or not 0.1 <= args.seconds <= 90:
            raise ValueError("whole-trial seconds must be finite and between 0.1 and 90")
        directory = args.directory.resolve()
        preflight()
        if args.operation == "recover":
            code = recover(directory)
        elif args.operation == "run":
            _, _, result = trial(directory, "A", args.mode, args.seconds)
            code = 0 if result["attempts"][0]["stop_reason"] == "success" else 3 if (
                result["attempts"][0]["stop_reason"] in ("timeout", "interruption", "safety_stop")) else 2
        else:
            directory.mkdir(parents=True, exist_ok=False)
            ledger = Ledger(directory / "ledger.jsonl")
            cohorts, suite = {}, []
            for arm in ("A", "B"):
                trial_id, data, result = trial(directory / arm, arm, args.mode, args.seconds)
                ledger.start(trial_id, data, attempt_id="a1", origin="synthetic")
                for checkpoint in Ledger(directory / arm / "ledger.jsonl").snapshot()[trial_id]["checkpoints"]:
                    ledger.checkpoint(trial_id, "a1", event_id=checkpoint["event_id"],
                                      event=checkpoint["event"], timing=checkpoint["timing"],
                                      artifacts=[{**a, "uri": f"{arm}/{a['uri']}"} for a in checkpoint["artifacts"]])
                ledger.finalize(trial_id, result)
                cohorts[f"synthetic-{arm}"] = [trial_id]
                suite = [manifest_reference(data["task"])]
            report = compare(ledger, cohorts=cohorts, suite=suite)
            proof.write(directory / "report.json", report)
            code = 0 if all(c["completion_coverage"] == 1 for c in report["cohorts"].values()) else 2
        print(json.dumps({"synthetic": True, "directory": str(directory), "exit_status": code}))
        return code
    except (OSError, ValueError, RuntimeError, ReserveExceeded, subprocess.SubprocessError) as exc:
        print(f"MB-005 error: {exc}", file=sys.stderr)
        return 4
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior_alarm)


if __name__ == "__main__":
    sys.exit(main())
