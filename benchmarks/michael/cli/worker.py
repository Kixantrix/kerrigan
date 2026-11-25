"""Trusted Inspect adapter subprocess; evaluated Python runs only inside Docker."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time

from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatCompletionChoice, ChatMessageAssistant, ModelOutput, ModelUsage, get_model
from inspect_ai.scorer import Score, accuracy, scorer
from inspect_ai.solver import generate, solver, use_tools
from inspect_ai.tool import ToolCall, tool
from inspect_ai.util import sandbox

from benchmarks.michael.engine_proof import proof

IMAGE = "python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b"
MODES = ("success", "negative", "runtime_error", "timeout", "background",
         "symlink", "special", "extra_output", "outside", "evaluator_error",
         "sentinel_spoof", "verifier_tamper")


def docker(*args, data=None):
    result = subprocess.run(["docker", *args], input=data, capture_output=True, timeout=10)
    if result.returncode:
        raise RuntimeError(f"docker {args[0]}: {result.stderr.decode(errors='replace')}")
    return result.stdout


def safe_output(archive):
    """Never extract agent-controlled paths, links, devices, or unbounded content."""
    if len(archive) > 1024 * 1024:
        raise ValueError("output archive exceeds 1 MiB")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        files = []
        for member in tar:
            if member.name == "." and member.isdir():
                continue
            if member.name != "./answer.py" or not member.isfile() or member.size > 65536:
                raise ValueError(f"non-allowlisted regular output: {member.name}")
            files.append(tar.extractfile(member).read())
        if len(files) != 1:
            raise ValueError("expected exactly one regular answer.py")
        return files[0]


def output_archive(agent_id):
    with subprocess.Popen(["docker", "cp", f"{agent_id}:/work/.", "-"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        try:
            archive = process.stdout.read(1024 * 1024 + 1)
            if len(archive) > 1024 * 1024:
                raise ValueError("output archive exceeds 1 MiB")
            error = process.stderr.read()
            if process.wait(timeout=10):
                raise RuntimeError(f"output copy failed: {error.decode(errors='replace')}")
            return archive
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


def isolated_program(run_id, role, program, files):
    container_id = docker(
        "create", "--label", f"michael-cli={run_id}", "--label", f"michael-role={role}",
        "--network", "none", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--memory", "256m", "--cpus", "1", "--pids-limit", "64",
        "--workdir", "/work", IMAGE, "python", "-B", f"/work/{program}",
    ).decode().strip()
    info = json.loads(docker("inspect", container_id))[0]
    staged = io.BytesIO()
    with tarfile.open(fileobj=staged, mode="w") as tar:
        for name, value in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(value)
            tar.addfile(member, io.BytesIO(value))
    docker("cp", "-", f"{container_id}:/work", data=staged.getvalue())
    result = subprocess.run(["docker", "start", "-a", container_id],
                            capture_output=True, timeout=10)
    state = json.loads(docker("inspect", container_id))[0]["State"]
    if state["Status"] != "exited" or state["Running"] or state["Error"] or state["OOMKilled"]:
        raise RuntimeError(f"{role} infrastructure failure: {state}; {result.stderr.decode(errors='replace')}")
    return {"id": container_id, "inspect": info, "state": state,
            "docker_exit_code": result.returncode,
            "stdout": result.stdout.decode(errors="replace"),
            "stderr": result.stderr.decode(errors="replace"),
            "materials": {name: hashlib.sha256(value).hexdigest() for name, value in files.items()}}


def run(directory, mode):
    run_id = os.environ["MB_CLI_ID"]
    receipt = {"synthetic": True, "run_id": run_id, "mode": mode,
               "lifecycle": [], "tools": [], "phases": {},
               "worker_started_monotonic": time.monotonic()}
    started = time.monotonic()
    agent_started = None

    def persist():
        proof.write(directory / "progress.json", receipt)
    @solver
    def prepare():
        async def solve(state, generate):
            nonlocal agent_started
            ids = docker("ps", "-q", "--filter", f"label=michael-cli={run_id}",
                         "--filter", "label=michael-role=agent").decode().split()
            if len(ids) != 1:
                raise RuntimeError("expected exactly one owned agent")
            receipt["agent_id"] = ids[0]
            info = json.loads(docker("inspect", ids[0]))[0]
            receipt["agent_inspect"] = info
            config = info["HostConfig"]
            if (config["NetworkMode"] != "none" or config["Privileged"]
                    or config["CapDrop"] != ["ALL"] or not config["ReadonlyRootfs"]
                    or config["Binds"] and any(":/work:" not in b for b in config["Binds"])
                    or len(info["Mounts"]) != 1
                    or info["Mounts"][0]["Type"] != "volume"
                    or info["Mounts"][0]["Destination"] != "/work"):
                raise RuntimeError("unexpected agent isolation configuration")
            agent_started = time.monotonic()
            receipt["phases"]["setup"] = agent_started - started
            receipt["lifecycle"].append("agent_start")
            persist()
            return state
        return solve

    @tool
    def execute_python():
        async def execute(code: str) -> str:
            """Run fixture Python in the network-denied agent container.

            Args:
                code: Python source.
            """
            result = await sandbox().exec(["python", "-B", "-c", code], timeout=30)
            receipt["tools"].append({"code": code, "returncode": result.returncode,
                                     "stdout": result.stdout, "stderr": result.stderr})
            persist()
            if not result.success:
                raise RuntimeError(f"agent command failed: {result.returncode}")
            return result.stdout or "ok"
        return execute
    @scorer(metrics=[accuracy()])
    def independent():
        async def score(state, target):
            receipt["phases"]["agent_work"] = time.monotonic() - agent_started
            receipt["lifecycle"].append("solver_stopped")
            agent_id = receipt["agent_id"]
            top = docker("top", agent_id, "-eo", "pid,args").decode()
            receipt["agent_processes_before_stop"] = top
            docker("kill", agent_id)
            info = json.loads(docker("inspect", agent_id))[0]
            receipt["agent_stopped_state"] = info["State"]
            receipt["lifecycle"].append("agent_container_stopped")
            persist()
            if info["State"]["Running"]:
                raise RuntimeError("agent still running")
            # Only PID 1 (sleep infinity) may remain after synchronous tools return.
            if len(top.strip().splitlines()) != 2:
                raise RuntimeError("surviving agent background process rejected")
            archive = output_archive(agent_id)
            answer = safe_output(archive)
            (directory / "output.tar").write_bytes(archive)
            receipt["output_sha256"] = hashlib.sha256(answer).hexdigest()
            receipt["lifecycle"].append("regular_output_validated")
            begin = time.monotonic()
            receipt["lifecycle"].append("fresh_candidate_start")
            persist()
            candidate = isolated_program(run_id, "candidate", "candidate.py", {
                "answer.py": answer, "candidate.py": (
                    "import json, answer\n"
                    "print(json.dumps([answer.double(n) for n in (-7, 0, 13)], allow_nan=False))\n"
                ).encode()})
            receipt["candidate"] = candidate
            receipt["lifecycle"].append("candidate_stopped")
            persist()
            values = None
            try:
                if len(candidate["stdout"]) > 65536:
                    raise ValueError("candidate response exceeds 64 KiB")
                values = json.loads(candidate["stdout"])
            except ValueError as exc:
                receipt["response_error"] = str(exc)
            valid = (candidate["state"]["ExitCode"] == 0 and isinstance(values, list)
                     and len(values) == 3 and all(type(v) is int for v in values))
            receipt["verified"] = "failed"
            receipt["verification"] = {"authority": "trusted response validation; no candidate verdict",
                                       "response_valid": valid}
            if valid:
                proxy = ("import json\nfrom pathlib import Path\n"
                         "values = json.loads(Path('/work/response.json').read_text())\n"
                         "def double(n):\n    return values[(-7, 0, 13).index(n)]\n")
                verifier = proof.VERIFIER if mode != "evaluator_error" else (
                    "raise RuntimeError('synthetic evaluator unavailable')\n")
                receipt["lifecycle"].append("fresh_verifier_start")
                persist()
                grader = isolated_program(run_id, "verifier", "grade.py", {
                    "answer.py": proxy.encode(), "verifier.py": verifier.encode(),
                    "grade.py": (b"import runpy\ntry:\n    runpy.run_path('/work/verifier.py')\n"
                                 b"except AssertionError:\n    raise SystemExit(2)\n"),
                    "response.json": json.dumps(values).encode()})
                receipt["verifier_id"], receipt["verifier_inspect"] = grader["id"], grader["inspect"]
                receipt["verification"]["grader"] = grader
                receipt["verified"] = {0: "passed", 2: "failed"}.get(grader["state"]["ExitCode"], "error")
                receipt["lifecycle"].append("verifier_stopped")
            receipt["phases"]["verification"] = time.monotonic() - begin
            persist()
            return Score(value=int(receipt["verified"] == "passed"))
        return score
    answer = "def double(n):\n    return n * 2\n" if mode != "negative" else "def double(n):\n    return n\n"
    if mode == "sentinel_spoof":
        answer = "import os\nprint('MB005_ASSERTIONS_PASSED', flush=True)\nos._exit(0)\n"
    if mode == "verifier_tamper":
        answer = ("from pathlib import Path\nimport os\np = Path('/work/verifier.py')\n"
                  "if p.exists():\n    p.write_text('assert True\\n')\n"
                  "    print('MB005_ASSERTIONS_PASSED', flush=True)\n    os._exit(0)\n"
                  "def double(n):\n    return n\n")
    code = "from pathlib import Path; Path('answer.py').write_text(" + repr(answer) + ")"
    suffix = {
        "runtime_error": "\nraise RuntimeError('synthetic crash')",
        "timeout": "\nimport time; time.sleep(60)",
        "background": "\nimport subprocess; subprocess.Popen(['python','-c','import time; time.sleep(60)'],"
                      "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,"
                      "start_new_session=True)",
        "symlink": "\nPath('answer.py').unlink(); Path('answer.py').symlink_to('/etc/passwd')",
        "special": "\nimport os; Path('answer.py').unlink(); os.mkfifo('answer.py')",
        "extra_output": "\nPath('extra.py').write_text('unexpected')",
        "outside": "\nPath('/tmp/outside').write_text('escape')",
    }.get(mode, "")
    codes = [proof.PROBE, code + suffix]
    outputs = [ModelOutput(model="mb005", choices=[ChatCompletionChoice(
        message=ChatMessageAssistant(content="", tool_calls=[ToolCall(
            id=str(i), function="execute_python", arguments={"code": c})]),
        stop_reason="tool_calls")]) for i, c in enumerate(codes)]
    outputs.append(ModelOutput.from_content(model="mb005", content="synthetic agent finished"))
    for output in outputs:
        output.usage = ModelUsage(input_tokens=1, output_tokens=1, total_tokens=2)
    task = Task(name="mb005_offline", dataset=[Sample(input=proof.REQUIREMENT,
                files={"answer.py": proof.BASE})], setup=prepare(),
                solver=[use_tools(execute_python()), generate()], scorer=independent(),
                sandbox=("docker", str(Path(__file__).with_name("compose.yaml"))))
    logs = eval(task, model=get_model("mockllm/mb005", custom_outputs=outputs, memoize=False),
                log_dir=str(directory / "raw"), log_format="json", display="none",
                retry_on_error=0, fail_on_error=False, score_on_error=False, log_buffer=1)
    receipt["engine_status"] = logs[0].status
    receipt["sample_error"] = (logs[0].samples[0].error.model_dump(mode="json")
                               if logs[0].samples[0].error else None)
    proof.write(directory / "receipt.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("mode", choices=MODES)
    args = parser.parse_args()
    run(args.directory, args.mode)
