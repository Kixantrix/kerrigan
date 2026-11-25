"""AC-MB-002/003/004/005/008: real Docker integration/e2e, cloud-linux, no inference."""

import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("mb005_controller", ROOT / "benchmarks/michael/cli/__main__.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def invoke(path, *args, expected=0):
    result = subprocess.run([sys.executable, "-m", "benchmarks.michael.cli", *args[:1],
                             str(path), *args[1:]], cwd=ROOT, capture_output=True, text=True, timeout=110)
    assert result.returncode == expected, result.stdout + result.stderr
    return result


def read(path, name):
    return json.loads((path / name).read_text())


def assert_clean(path):
    safety = read(path, "cleanup.json")
    assert not safety["errors"]
    for kind in ("processes", "containers", "volumes"):
        assert safety[f"remaining_{kind}"] == []


def test_public_comparison_binds_real_artifacts_and_preserves_synthetic_coverage(tmp_path):
    path = tmp_path / "comparison"
    invoke(path, "compare")
    report = read(path, "report.json")
    assert report["both_success_complete_time_subset"]["paired_denominator"] == 1
    for cohort in report["cohorts"].values():
        assert cohort["completion_coverage"] == 1
        assert cohort["started_attempts"] == 1
        assert cohort["usage"]["credits"]["total"] is None
        assert cohort["usage"]["synthetic_total_tokens"]["total"] is None
    terminals = [read(path / arm, "terminal.json") for arm in ("A", "B")]
    assert terminals[0]["bundle"]["task"] == terminals[1]["bundle"]["task"]
    for arm, terminal in zip(("A", "B"), terminals):
        owned = path / arm
        assert_clean(owned)
        assert terminal["origin"] == "synthetic"
        receipt = read(owned, "receipt.json")
        assert receipt["lifecycle"].index("agent_container_stopped") < receipt["lifecycle"].index("fresh_verifier_start")
        assert not receipt["agent_stopped_state"]["Running"]
        assert receipt["agent_id"] != receipt["verifier_id"]
        assert receipt["verifier_inspect"]["Mounts"] == []
        assert receipt["verifier_inspect"]["HostConfig"]["NetworkMode"] == "none"
        for artifact in read(owned, "evidence.json")["artifacts"]:
            assert hashlib.sha256((owned / artifact["uri"]).read_bytes()).hexdigest() == artifact["sha256"]
        attempt = terminal["attempts"][0]
        assert attempt["time_to_verified_completion"] == attempt["timing"]["end_to_end"]


@pytest.mark.parametrize("mode", ["negative", "runtime_error", "background", "symlink",
                                  "special", "extra_output", "outside", "evaluator_error"])
def test_adversarial_and_failed_cli_trials_are_not_fast_success(tmp_path, mode):
    path = tmp_path / mode
    invoke(path, "compare" if mode == "negative" else "run", "--mode", mode, expected=2)
    if mode == "negative":
        assert all(c["completion_coverage"] == 0 for c in read(path, "report.json")["cohorts"].values())
        path = path / "A"
    assert_clean(path)
    attempt = read(path, "terminal.json")["attempts"][0]
    assert attempt["verdict"] != "passed"
    assert attempt["time_to_verified_completion"]["status"] == "unknown"
    if mode == "background":
        progress = read(path, "progress.json")
        assert not progress["agent_stopped_state"]["Running"]
        assert "fresh_verifier_start" not in progress["lifecycle"]
        assert len(progress["agent_processes_before_stop"].strip().splitlines()) > 2
    if mode in ("symlink", "special", "extra_output"):
        assert "fresh_verifier_start" not in read(path, "progress.json")["lifecycle"]


def sleeping_trial(path):
    process = subprocess.Popen([sys.executable, "-m", "benchmarks.michael.cli", "run",
                                str(path), "--mode", "timeout", "--seconds", "12"],
                               cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    until = time.monotonic() + 10
    while time.monotonic() < until:
        if (path / "progress.json").exists():
            progress = read(path, "progress.json")
            top = subprocess.run(["docker", "top", progress["agent_id"], "-eo", "pid,args"],
                                 capture_output=True, text=True, timeout=2)
            if "time.sleep(60)" in top.stdout:
                return process
        if process.poll() is not None:
            break
        time.sleep(0.05)
    process.terminate()
    process.wait(timeout=20)
    pytest.fail("did not observe actual sleeping sandbox worker")


def test_whole_trial_cutoff_precedes_30_second_tool_deadline(tmp_path):
    path = tmp_path / "cutoff"
    begin = time.monotonic()
    process = sleeping_trial(path)
    assert process.wait(timeout=25) == 3
    assert time.monotonic() - begin < 27
    assert_clean(path)
    assert read(path, "evidence.json")["safety"]["cutoff"]
    attempt = read(path, "terminal.json")["attempts"][0]
    assert attempt["stop_reason"] == "timeout"
    assert attempt["verifier"]["status"] == "not_run"
    assert attempt["time_to_verified_completion"]["status"] == "unknown"
    assert read(path, "cleanup.json")["killed_pids"]
    assert attempt["usage"]["synthetic_total_tokens"]["status"] == "unknown"


def test_killed_controller_recovery_never_replays_tools(tmp_path):
    path = tmp_path / "interrupted"
    process = sleeping_trial(path)
    os.kill(process.pid, signal.SIGKILL)
    process.wait(timeout=5)
    invoke(path, "recover", expected=3)
    assert_clean(path)
    terminal = read(path, "terminal.json")
    assert len(terminal["starts"]) == 1
    assert terminal["attempts"][0]["state"] == "interrupted"
    assert terminal["attempts"][0]["verifier"]["status"] == "not_run"
    before = (path / "ledger.jsonl").read_bytes()
    invoke(path, "recover", expected=3)
    assert (path / "ledger.jsonl").read_bytes() == before


def test_unsafe_archive_and_cleanup_errors_are_explicit(monkeypatch):
    for name, kind in (("../answer.py", tarfile.REGTYPE), ("./answer.py", tarfile.SYMTYPE)):
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as tar:
            member = tarfile.TarInfo(name)
            member.type = kind
            tar.addfile(member)
        with pytest.raises(ValueError, match="non-allowlisted"):
            sys.modules["benchmarks.michael.cli.worker"].safe_output(archive.getvalue())
    def fail(*args, **kwargs):
        raise RuntimeError("injected Docker cleanup failure")
    monkeypatch.setattr(cli, "command", fail)
    assert cli.cleanup("0" * 32)["errors"] == ["injected Docker cleanup failure"]


@pytest.mark.parametrize("seconds", ["nan", "0", "91"])
def test_malformed_cli_never_emits_success(tmp_path, seconds):
    result = invoke(tmp_path / "invalid", "run", "--seconds", seconds, expected=4)
    assert not result.stdout
    assert not (tmp_path / "invalid").exists()
