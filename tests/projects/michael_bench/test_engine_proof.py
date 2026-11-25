"""AC-MB-002/003/004/005 slice: integration, cloud-linux, synthetic only."""

import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

PROOF = Path(__file__).resolve().parents[3] / "benchmarks/michael/engine_proof/proof.py"
sys.path.insert(0, str(PROOF.parent.parent / "contracts"))
from manifests import validate_bundle


def invoke(path, *args):
    subprocess.run([sys.executable, str(PROOF), str(path), *args],
                   check=True, timeout=90)


def read(path, name):
    return json.loads((path / name).read_text())


@pytest.mark.parametrize("mode,stop,verdict", [
    ("success", "success", "passed"), ("negative", "agent_finished", "failed"),
    ("runtime_error", "runtime_error", "ungraded"), ("timeout", "timeout", "ungraded"),
    ("cancellation", "cancellation", "ungraded"),
    ("evaluator_error", "evaluator_error", "ungraded"),
])
def test_real_sandbox_lifecycle_exports(mode, stop, verdict, tmp_path):
    path = tmp_path / mode
    invoke(path, "--mode", mode, "--deadline", "1")
    bundle = validate_bundle(**read(path, "bundle.json"))
    attempt = bundle["result"]["attempts"][0]
    assert (attempt["stop_reason"], attempt["verdict"]) == (stop, verdict)
    receipt = read(path, "receipt.json")
    sandbox = receipt["sandbox"]
    assert sandbox["Mounts"] == []
    assert sandbox["HostConfig"]["NetworkMode"] == "none"
    assert sandbox["HostConfig"]["Binds"] is None
    assert sandbox["HostConfig"]["Privileged"] is False
    assert sandbox["HostConfig"]["CapDrop"] == ["ALL"]
    assert sandbox["HostConfig"]["SecurityOpt"] == ["no-new-privileges:true"]
    assert all(json.loads(receipt["tool_results"][0]["stdout"]).values())
    if verdict in ("passed", "failed") or stop == "evaluator_error":
        assert receipt["lifecycle"] == ["agent_start", "agent_stop", "verifier_injected"]
        assert attempt["timing"]["verification"]["status"] == "known"
    else:
        assert "verifier_injected" not in receipt["lifecycle"]
        assert attempt["verifier"]["status"] == "not_run"
    events = read(path, "events.json")
    models = [e for e in events["events"] if e["event"] == "model"]
    assert events["synthetic"] is True and "mockllm synthetic" in events["source"]
    assert models and models[0]["call"]["request"]
    assert models[0]["output"]["usage"]["total_tokens"] == 2
    assert any(e["event"] == "tool" for e in events["events"])
    assert list((path / "raw").glob("*.json"))
    assert read(path, "cleanup.json")["remaining"] == []
    assert attempt["timing"]["end_to_end"]["value"]["seconds"] > 0
    assert attempt["timing"]["agent_work"]["value"]["seconds"] > 0
    assert attempt["timing"]["queue"]["status"] == "unknown"
    assert attempt["time_to_verified_completion"]["status"] == (
        "known" if verdict == "passed" else "unknown")
    if stop == "timeout":
        assert receipt["tool_results"][1]["returncode"] in (124, 137)
        assert 1 <= attempt["timing"]["agent_work"]["value"]["seconds"] < 15
    if stop == "cancellation":
        assert "unattributed cancellation" in receipt["sample_error"]["message"]


def test_killed_controller_recovers_ungraded_without_replaying(tmp_path):
    path = tmp_path / "interrupted"
    process = subprocess.Popen([sys.executable, str(PROOF), str(path),
                                "--mode", "interrupt", "--deadline", "60"])
    try:
        expires = time.monotonic() + 40
        while not (path / "ready.json").exists():
            assert process.poll() is None, "controller exited before sandbox setup"
            assert time.monotonic() < expires, "sandbox setup deadline"
            time.sleep(0.1)
        run_id = read(path, "start.json")["run_id"]
        container_id = read(path, "ready.json")["sandbox"]["Id"]
        while True:
            running = subprocess.check_output(
                ["docker", "top", container_id, "-eo", "pid,args"], text=True)
            if "python -c import time; time.sleep(60)" in running:
                break
            assert process.poll() is None and time.monotonic() < expires
            time.sleep(0.1)
        process.kill()
        process.wait(timeout=10)
        before = sorted(p.name for p in path.iterdir())
        invoke(path, "--recover")
        attempt = validate_bundle(**read(path, "bundle.json"))["result"]["attempts"][0]
        assert (attempt["state"], attempt["verdict"], attempt["stop_reason"]) == (
            "interrupted", "ungraded", "interruption")
        assert attempt["verifier"]["status"] == "not_run"
        assert attempt["timing"]["setup"]["status"] == "known"
        assert attempt["timing"]["agent_work"]["status"] == "unknown"
        assert attempt["time_to_verified_completion"]["status"] == "unknown"
        cleanup = read(path, "cleanup.json")
        assert cleanup["removed"] and cleanup["remaining"] == []
        assert "receipt.json" not in before and not (path / "receipt.json").exists()
        original = (path / "bundle.json").read_bytes()
        invoke(path, "--recover")
        assert (path / "bundle.json").read_bytes() == original
        assert subprocess.check_output(
            ["docker", "ps", "-aq", "--filter", f"label=michael-proof={run_id}"],
            text=True).strip() == ""
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        if (path / "start.json").exists() and not (path / "bundle.json").exists():
            invoke(path, "--recover")
