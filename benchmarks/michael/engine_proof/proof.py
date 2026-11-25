"""MB-002 only: one Inspect mock task; no provider, general runner, or scoring."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.model import (
    ChatCompletionChoice, ChatMessageAssistant, ModelOutput, ModelUsage, get_model,
)
from inspect_ai.scorer import Score, accuracy, scorer
from inspect_ai.solver import generate, solver, use_tools
from inspect_ai.tool import ToolCall, tool
from inspect_ai.util import sandbox

CONTRACTS = Path(__file__).resolve().parents[1] / "contracts"
sys.path.insert(0, str(CONTRACTS))
from manifests import manifest_reference, validate_bundle

BASE = "def double(n):\n    raise NotImplementedError\n"
REQUIREMENT = "Implement double(n) for integer n in answer.py."
VERIFIER = (
    "import answer\n"
    "assert [answer.double(n) for n in (-7, 0, 13)] == [-14, 0, 26]\n"
)
PROBE = (
    "from pathlib import Path; import json, os\n"
    "paths=['/work/verifier.py','/work/solution.py','/work/.git',"
    "'/work/.git/logs/HEAD','/root/.ssh','/root/.aws',"
    "'/var/run/docker.sock','/work/tests']\n"
    "denied={}\n"
    "for p in paths:\n"
    "    try:\n"
    "        Path(p).read_bytes()\n"
    "    except (FileNotFoundError, PermissionError, IsADirectoryError):\n"
    "        denied[p]=True\n"
    "    else:\n"
    "        denied[p]=False\n"
    "print(json.dumps(denied)); assert all(denied.values())\n"
    "assert not any(Path(p).exists() for p in paths)\n"
    "assert 'MB_SYNTHETIC_SECRET' not in os.environ\n"
)
MODES = ("success", "negative", "runtime_error", "timeout", "cancellation",
         "evaluator_error", "interrupt")


def write(path, data):
    """Atomically persist before work; fsync both file and directory."""
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def containers(run_id):
    ids = docker("ps", "-aq", "--filter", f"label=michael-proof={run_id}")
    return ids.splitlines() if ids else []


def known(value, source):
    return {"status": "known", "value": value, "source": source}


def unknown(reason, source, status="unknown"):
    return {"status": status, "reason": reason, "source": source}


def descriptor(kind, run_id):
    return {"schema_version": 1, "kind": kind, "id": f"mb002-{kind}-{run_id}",
            "revision": "1", "provenance": {"source_id": "MB-002 synthetic Inspect proof"}}


def bundle(run_id, deadline):
    def material(uri, content, audience):
        return {"uri": uri, "sha256": hashlib.sha256(content.encode()).hexdigest(),
                "audience": audience}
    source = "Inspect mockllm; not native provider evidence"
    task = {**descriptor("task", run_id),
            "base": {"uri": "synthetic:answer.py",
                     "sha256": hashlib.sha256(BASE.encode()).hexdigest()},
            "agent_material": [material("synthetic:requirement", REQUIREMENT, "requirement_only")],
            "verifier_material": [material("synthetic:verifier", VERIFIER, "verifier_only")]}
    target = {**descriptor("target", run_id), "requested_identity": "mockllm/mb002",
              "observed_identity": known("mockllm/mb002", source),
              "runtime": known(f"inspect-ai=={version('inspect-ai')}", source)}
    harness = {"id": "inspect-ai-mb002-adapter", "revision": version("inspect-ai"),
               "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    agent = {**descriptor("agent", run_id), "harness": harness,
             "configuration": known({"fixture": "scripted mock tool calls",
                                     "sandbox": "compose.yaml",
                                     "per_tool_safety_seconds": deadline}, source)}
    condition = {**descriptor("condition", run_id),
                 **{name: manifest_reference(value) for name, value in
                    (("task", task), ("target", target), ("agent", agent))},
                 "hosts": {role: unknown("identity not attested", source) for role in
                           ("inference", "agent", "verifier")},
                 "track": "harness_configuration", "retry_policy": "no_automatic_retries",
                 "budgets": {"active_safety_seconds": unknown(
                                 "only per-tool sandbox deadline exercised; no whole-trial cap", source),
                             "attempt_limit": known(1, source),
                             **{key: unknown("not a matched provider control", source, "unsupported")
                                for key in ("response_tokens", "reasoning_tokens")}},
                 "cache_policy": unknown("no inference", source, "not_applicable"),
                 "capabilities": {}, "required_semantics": [],
                 "observability": {"credits": unknown("no billable inference", source,
                                                       "not_applicable")}}
    return validate_bundle(task=task, target=target, agent=agent, condition=condition)


def recovery(directory):
    """Only recover this proof's incomplete start, never resume/replay an agent."""
    start = json.loads((directory / "start.json").read_text())
    if (directory / "bundle.json").exists():
        return json.loads((directory / "bundle.json").read_text())
    owned = containers(start["run_id"])
    if owned:
        docker("rm", "-f", *owned)
    receipt = {"recovered": True, "removed": owned, "remaining": containers(start["run_id"])}
    write(directory / "cleanup.json", receipt)
    data = start["bundle"]
    source = "MB-002 persisted start recovery; controller lost"
    timing = {phase: unknown("controller lost; no completed interval", source)
              for phase in ("setup", "agent_work", "verification", "end_to_end")}
    ready = directory / "ready.json"
    if ready.exists():
        setup = json.loads(ready.read_text())["setup_seconds"]
        timing["setup"] = known({
            "seconds": setup, "scope": "setup", "clock": "monotonic",
            "host_ids": [f"controller:{start['run_id']}"], "coverage": "complete",
        }, f"MB-002 controller monotonic:{start['run_id']}")
    attempt = {"id": start["run_id"], "verdict": "ungraded", "state": "interrupted",
               "stop_reason": "interruption", "verifier": {
                   "status": "not_run", "independent": False, "source": source},
               "events": [{"category": "infrastructure", "code": "controller_interrupted",
                           "source": source}], "usage": {},
               "timing": timing,
               "time_to_verified_completion": unknown("ungraded interruption", source)}
    data["result"] = {**descriptor("result", start["run_id"]),
                      "condition": manifest_reference(data["condition"]), "attempts": [attempt]}
    data = validate_bundle(**data)
    write(directory / "bundle.json", data)
    return data


def run(directory, mode="success", deadline=2):
    if mode not in MODES or deadline <= 0:
        raise ValueError("invalid fixture mode or deadline")
    directory.mkdir(parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex
    os.environ["MB_PROOF_ID"] = run_id
    os.environ["MB_SYNTHETIC_SECRET"] = "synthetic-noncredential-isolation-canary"
    data = bundle(run_id, deadline)
    write(directory / "start.json", {"run_id": run_id, "mode": mode, "bundle": data,
                                     "started_wall_ns": time.time_ns()})
    started = time.monotonic()
    phases = {}
    receipt = {"mode": mode, "engine_version": version("inspect-ai"), "run_id": run_id,
               "lifecycle": [], "tool_results": []}
    stop = "agent_finished"
    verified = "not_run"
    setup_end = None
    agent_start = None

    @solver
    def prepare():
        async def solve(state, generate):
            nonlocal setup_end, agent_start
            ids = containers(run_id)
            if len(ids) != 1:
                raise RuntimeError(f"expected one owned sandbox, found {ids}")
            info = json.loads(docker("inspect", ids[0]))[0]
            receipt["sandbox"] = {key: info[key] for key in ("Id", "Mounts")}
            receipt["sandbox"]["HostConfig"] = {
                key: info["HostConfig"][key] for key in
                ("NetworkMode", "CapDrop", "SecurityOpt", "Privileged", "Binds")}
            config = receipt["sandbox"]["HostConfig"]
            if (info["Mounts"] or config["Privileged"] or config["NetworkMode"] != "none"
                    or config["CapDrop"] != ["ALL"]):
                raise RuntimeError("sandbox isolation configuration failed")
            setup_end = time.monotonic()
            phases["setup"] = setup_end - started
            receipt["setup_seconds"] = phases["setup"]
            agent_start = setup_end
            receipt["lifecycle"].append("agent_start")
            write(directory / "ready.json", receipt)
            return state
        return solve

    @tool
    def execute_python():
        async def execute(code: str) -> str:
            """Execute Python inside the isolated task sandbox.

            Args:
                code: Python source to execute.
            """
            nonlocal stop
            result = await sandbox().exec(
                ["timeout", "--signal=KILL", str(deadline), "python", "-c", code],
                timeout=deadline + 10,
            )
            receipt["tool_results"].append({"code": code, "returncode": result.returncode,
                                             "stdout": result.stdout, "stderr": result.stderr})
            if not result.success:
                stop = "timeout" if result.returncode in (124, 137) else "runtime_error"
                phases["agent_work"] = time.monotonic() - agent_start
                receipt["lifecycle"].append("agent_stop_error")
                raise RuntimeError(f"owned sandbox tool {stop}: {result.returncode}")
            return result.stdout or "ok"
        return execute

    @solver
    def stopped():
        async def solve(state, generate):
            nonlocal stop
            phases["agent_work"] = time.monotonic() - agent_start
            receipt["lifecycle"].append("agent_stop")
            if mode == "cancellation":
                stop = "cancellation"
                raise asyncio.CancelledError("synthetic controller cancellation after agent stop")
            return state
        return solve

    @scorer(metrics=[accuracy()])
    def held_out():
        async def score(state, target):
            nonlocal verified, stop
            assert receipt["lifecycle"][-1] == "agent_stop"
            begin = time.monotonic()
            try:
                await sandbox().write_file("/work/verifier.py", VERIFIER)
                receipt["lifecycle"].append("verifier_injected")
                command = ["python", "/work/verifier.py"]
                if mode == "evaluator_error":
                    command = ["python", "/work/missing_evaluator.py"]
                result = await sandbox().exec(command, timeout=10)
                receipt["verification"] = {"returncode": result.returncode,
                                           "stdout": result.stdout, "stderr": result.stderr}
                if mode == "evaluator_error":
                    verified, stop = "error", "evaluator_error"
                    raise RuntimeError("synthetic evaluator unavailable")
                verified = "passed" if result.success else "failed"
                stop = "success" if result.success else "agent_finished"
                return Score(value=1 if result.success else 0)
            finally:
                phases["verification"] = time.monotonic() - begin
        return score

    codes = [PROBE, "from pathlib import Path; Path('answer.py').write_text("
             + repr("def double(n):\n    return n * 2\n" if mode != "negative"
                    else "def double(n):\n    return n\n") + ")"]
    if mode == "runtime_error":
        codes[1] = "raise RuntimeError('synthetic agent crash')"
    if mode in ("timeout", "interrupt"):
        codes[1] = "import time; time.sleep(60)"
    outputs = [
        ModelOutput(model="mb002", choices=[ChatCompletionChoice(
            message=ChatMessageAssistant(content="", tool_calls=[
                ToolCall(id=str(index), function="execute_python", arguments={"code": code})]),
            stop_reason="tool_calls")]) for index, code in enumerate(codes)
    ]
    outputs.append(ModelOutput.from_content(model="mb002", content="agent stopped"))
    for output in outputs:
        output.usage = ModelUsage(input_tokens=1, output_tokens=1, total_tokens=2)
    model = get_model("mockllm/mb002", custom_outputs=outputs, memoize=False)
    task = Task(name="mb002_offline", dataset=[Sample(input=REQUIREMENT, files={"answer.py": BASE})],
                setup=prepare(), solver=[use_tools(execute_python()), generate(), stopped()],
                scorer=held_out(), sandbox=("docker", str(Path(__file__).with_name("compose.yaml"))))
    try:
        logs = eval(task, model=model, log_dir=str(directory / "raw"), log_format="json",
                    display="none", retry_on_error=0, fail_on_error=False, score_on_error=False,
                    log_buffer=1)
        log = logs[0]
        sample = log.samples[0] if log.samples else None
        receipt["engine_status"] = log.status
        receipt["engine_error"] = log.error.model_dump(mode="json") if log.error else None
        receipt["sample_error"] = sample.error.model_dump(mode="json") if sample and sample.error else None
        if (log.status != "success" or (sample and sample.error)) and stop == "agent_finished":
            raise RuntimeError(f"unclassified Inspect failure: {receipt['sample_error'] or log.error}")
    finally:
        owned = containers(run_id)
        if owned:
            docker("rm", "-f", *owned)
        write(directory / "cleanup.json", {"removed_after_engine": owned,
                                           "remaining": containers(run_id)})
    phases["end_to_end"] = time.monotonic() - started
    source = f"MB-002 controller monotonic:{run_id}"
    timing = {phase: known({"seconds": seconds, "scope": phase, "clock": "monotonic",
                            "host_ids": [f"controller:{run_id}"], "coverage": "complete"}, source)
              for phase, seconds in phases.items()}
    for phase in ("queue", "provisioning", "setup", "agent_work", "verification"):
        timing.setdefault(phase, unknown("separate phase not observed", source))
    sample = log.samples[0] if log.samples else None
    raw_source = f"raw:{Path(log.location).name}; Inspect mockllm synthetic"
    raw = json.loads(Path(log.location).read_text())
    write(directory / "events.json", {
        "source": raw_source, "synthetic": True,
        "events": [event for event in raw["samples"][0]["events"]
                   if event["event"] in ("model", "tool", "error", "sample_limit")],
        "model_usage": raw["samples"][0]["model_usage"],
        "stop": {"code": stop, "source": "MB-002 controller attribution",
                 "engine_sample_error": receipt["sample_error"]},
    })
    usage = {}
    if sample:
        for model_name, counters in sample.model_usage.items():
            for key in ("input_tokens", "output_tokens", "total_tokens"):
                usage[f"synthetic_{key}"] = known(getattr(counters, key), raw_source)
    verdict = {"passed": "passed", "failed": "failed",
               "error": "ungraded", "not_run": "ungraded"}[verified]
    attempt = {"id": run_id, "verdict": verdict,
               "state": "stopped" if stop in ("timeout", "runtime_error", "cancellation") else "completed",
               "stop_reason": stop, "verifier": {"status": verified, "independent": verified != "not_run",
                                                "source": "post-agent held-out scorer"},
               "events": [{"category": "runtime", "code": stop, "source": raw_source}],
               "timing": timing, "usage": usage,
               "time_to_verified_completion": timing["end_to_end"] if stop == "success"
               else unknown("no independently verified completion", source)}
    data["result"] = {**descriptor("result", run_id),
                      "condition": manifest_reference(data["condition"]), "attempts": [attempt]}
    data = validate_bundle(**data)
    write(directory / "receipt.json", receipt)
    write(directory / "bundle.json", data)
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--mode", choices=MODES, default="success")
    parser.add_argument("--deadline", type=float, default=2)
    parser.add_argument("--recover", action="store_true")
    args = parser.parse_args()
    if args.recover:
        recovery(args.directory)
    else:
        run(args.directory, args.mode, args.deadline)
