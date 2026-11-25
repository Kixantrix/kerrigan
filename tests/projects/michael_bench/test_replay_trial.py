"""MB-006k integration/local-attested-macos; no inference or host candidate imports."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

MICHAEL = Path(__file__).resolve().parents[3] / "benchmarks" / "michael"
LOCAL = MICHAEL / "local_transport"
sys.path.insert(0, str(MICHAEL))
sys.path.insert(0, str(LOCAL))
from replay_trial import api as trial
import validator_worker as worker


def test_exact_export_closed_profile_and_support(tmp_path):
    source = trial.packages.agent_files("validator")[trial.SOURCE]
    run = trial.setup(tmp_path, tmp_path / "run", source)
    assert trial.packages.check_export("validator", run / "task")
    config = json.loads((run / "config.json").read_bytes())
    assert config["model"] is None and not config["approved"] and config["validatorReplay"]
    assert "prompt" not in config
    assert '(deny process-fork)' in config["taskProfile"]
    assert f'(subpath "{run / "task"}")' not in config["taskProfile"]
    assert f'(allow file-write* (literal "{run / "task" / trial.SOURCE}"))' in config["taskProfile"]
    assert not config["sandbox"]["userPolicy"]["network"]["allowOutbound"]
    assert not config["sandbox"]["allowBypass"]
    assert sorted(p.relative_to(run / "support").as_posix()
                  for p in (run / "support").rglob("*") if p.is_file()) == [
        "yaml/" + name for name in sorted(p.name for p in (run / "support/yaml").glob("*.py"))]
    assert not any((run / "task").rglob(".git"))
    assert not (tmp_path / "canary-slots").exists()
    (run / "receipt/terminal.json").write_text("{}")
    with pytest.raises(trial.TrialError, match="unproven"):
        trial.collect(run)


@pytest.mark.parametrize("attack", ["../TASK.md", "/TASK.md", "hidden/reference", "candidate.py"])
def test_worker_rejects_non_allowlisted_paths(tmp_path, attack):
    with pytest.raises(ValueError, match="path denied"):
        worker.read_source(tmp_path, attack)


@pytest.mark.parametrize("attack", ["leaf-link", "parent-link", "hardlink", "fifo", "oversize"])
def test_collector_rejects_aliases_special_files_and_oversize(tmp_path, attack):
    source = tmp_path / trial.SOURCE
    source.parent.mkdir(parents=True)
    secret = tmp_path / "not-agent-material"
    secret.write_bytes(b"synthetic-only")
    if attack == "leaf-link":
        source.symlink_to(secret)
    elif attack == "parent-link":
        source.parent.rmdir()
        source.parent.symlink_to(tmp_path)
    elif attack == "hardlink":
        os.link(secret, source)
    elif attack == "fifo":
        os.mkfifo(source)
    else:
        source.write_bytes(b"x" * (worker.POLICY["bytes"] + 1))
    with pytest.raises((OSError, ValueError)):
        worker.read_source(tmp_path, trial.SOURCE)


def test_collector_detects_in_read_mutation(tmp_path, monkeypatch):
    source = tmp_path / trial.SOURCE
    source.parent.mkdir(parents=True)
    source.write_bytes(b"before")
    original = worker.os.fstat
    calls = 0
    def raced(fd):
        nonlocal calls
        calls += 1
        if calls == 3:
            source.write_bytes(b"raced-content")
        return original(fd)
    monkeypatch.setattr(worker.os, "fstat", raced)
    with pytest.raises(ValueError, match="changed"):
        worker.read_source(tmp_path, trial.SOURCE)


def test_replay_broker_does_not_expand_canary_paths():
    script = """
import {validateAction} from './benchmarks/michael/local_transport/limits.mjs';
import assert from 'node:assert/strict';
const state=()=>({actions:new Set(),bytes:0}),p='tools/validators/agents_md.py';
assert.throws(()=>validateAction('old',{op:'read',path:p},state()),/denied/);
assert.throws(()=>validateAction('new',{op:'read',path:'candidate.py'},state(),true),/denied/);
for(const path of ['TASK.md','policy.json','requirements.txt','../secret'])
 assert.throws(()=>validateAction('write',{op:'write',path,data:'x'},state(),true),/denied/);
assert.ok(validateAction('ok',{op:'write',path:p,data:'trusted fixture'},state(),true));
"""
    subprocess.run(["node", "--input-type=module", "-e", script],
                   cwd=trial.packages.ROOT, check=True, timeout=5)


@pytest.mark.parametrize("forbidden", [{"model": "mai-code-2"}, {"prompt": "not authorized"}])
def test_native_replay_rejects_inference_before_loading_sdk(tmp_path, forbidden):
    config = {"validatorReplay": True, "model": None, "approved": False,
              "transportProbe": False, "condition": "MB-006k-offline",
              "sdk": str(tmp_path / "must-not-load.mjs"), **forbidden}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    result = subprocess.run(["node", str(trial.runner.HERE / "owner.mjs"), str(path)],
                            capture_output=True, timeout=5)
    assert result.returncode and b"validator_replay_forbids_inference" in result.stderr


@pytest.fixture(scope="module")
def native_owned():
    path = os.environ.get("MB006K_OWNED")
    if not path:
        pytest.skip("local_required: explicitly supply isolated macOS MXC state for native scenario")
    return Path(path)


@pytest.mark.parametrize("name,counts", [("base", (15, 7)), ("reference", (15, 10))])
def test_real_native_fixture_to_independent_grader(native_owned, tmp_path, name, counts):
    source = (trial.packages.agent_files("validator")[trial.SOURCE] if name == "base"
              else trial.packages.verifier_files("validator")["reference"])
    report = trial.execute(native_owned, tmp_path / "native", source, label=f"trusted-{name}")
    assert report["status"] == "graded", report
    assert report["nativeQuiescent"] and not report["scoredTrial"] and report["modelPrompts"] == 0
    assert report["counts"] == {"preservation": {"passed": counts[0], "total": 15},
                                 "regression": {"passed": counts[1], "total": 10}}
    assert len(report["assertions"]) == 25
    assert report["verifier"]["cleanup"]["proven"]
    assert report["sourceSha256"] == report["verifier"]["bindings"]["source_sha256"]
    assert all(value > 0 for value in report["timings"].values())


def test_grade_requires_real_owned_cleanup(tmp_path, monkeypatch):
    source = trial.packages.agent_files("validator")[trial.SOURCE]
    run = trial.setup(tmp_path, tmp_path / "run", source)
    (run / "receipt/terminal.json").write_text(json.dumps({
        "wholeProcessQuiescent": False, "stopReason": "diagnostics_complete", "nativePrompts": 0}))
    monkeypatch.setattr(trial.grader, "grade", lambda *_: pytest.fail("grader called before native stop"))
    with pytest.raises(trial.TrialError, match="unproven"):
        trial.grade_stopped(run)


@pytest.mark.parametrize("attack", ["source", "readonly", "dependency", "cleanup"])
def test_native_stopped_artifact_tamper_never_reaches_grader(native_owned, tmp_path, monkeypatch, attack):
    source = trial.packages.agent_files("validator")[trial.SOURCE]
    run = trial.setup(native_owned, tmp_path / "run", source)
    child = trial.runner.launch(run)
    try:
        child.wait(timeout=40)
    finally:
        child.stdin.close()
    if attack == "cleanup":
        path = run / "receipt/terminal.json"
        value = json.loads(path.read_bytes())
        value["wholeProcessQuiescent"] = False
        path.write_text(json.dumps(value))
    else:
        path = {"source": run / "task" / trial.SOURCE, "readonly": run / "task/TASK.md",
                "dependency": run / "support/yaml/__init__.py"}[attack]
        path.write_bytes(path.read_bytes() + b"\n# trusted tamper fixture\n")
    monkeypatch.setattr(trial.grader, "grade", lambda *_: pytest.fail("tampered artifact graded"))
    with pytest.raises((trial.TrialError, OSError, ValueError)):
        trial.grade_stopped(run)


@pytest.mark.parametrize("name,source", [
    ("false-success", b"print('PASS 25/25'); raise SystemExit(0)\n"),
    ("malformed", b"def invalid(\n"),
    ("timeout", b"while True: pass\n"),
])
def test_native_negative_outcomes_not_model_results(native_owned, tmp_path, name, source):
    report = trial.execute(native_owned, tmp_path / "run", source,
                           label=f"trusted-{name}", seconds=3 if name == "timeout" else 20)
    assert report["status"] == "ungraded" and report["verdict"] is None and report["counts"] is None
    assert report["nativeQuiescent"], report
    assert report["modelPrompts"] == 0 and not report["scoredTrial"]
    if name == "false-success":
        assert report["verifier"]["cleanup"]["proven"]
        assert "missing_or_extra" in report["verifier"]["error"]
    else:
        assert report["nativeStopReason"] != "diagnostics_complete"


@pytest.mark.parametrize("loss", ["controller-loss", "deadline"])
def test_native_independent_owner_survives_controller_loss(native_owned, tmp_path, loss):
    import signal
    source = trial.packages.agent_files("validator")[trial.SOURCE]
    directory = tmp_path / "run"
    code = (
        "from benchmarks.michael.replay_trial import api\n"
        f"run=api.setup({str(native_owned)!r},{str(directory)!r},{source!r},seconds=6,hold=True)\n"
        "child=api.runner.launch(run)\nchild.wait(timeout=30)\n")
    controller = subprocess.Popen([sys.executable, "-c", code], cwd=trial.packages.ROOT)
    try:
        until = time.monotonic() + 15
        while not (directory / "receipt/action-result-4.json").exists():
            assert time.monotonic() < until
            time.sleep(.025)
        if loss == "deadline":
            controller.send_signal(signal.SIGSTOP)
        else:
            controller.kill()
            controller.wait(timeout=5)
        until = time.monotonic() + 20
        while not (directory / "receipt/terminal.json").exists():
            assert time.monotonic() < until
            time.sleep(.025)
        terminal = json.loads((directory / "receipt/terminal.json").read_bytes())
        assert terminal["wholeProcessQuiescent"] and terminal["cleanupSeconds"] < 15
        assert terminal["stopReason"] == ("timeout" if loss == "deadline" else "controller_lost")
        with pytest.raises(trial.TrialError):
            trial.grade_stopped(directory)
    finally:
        if controller.poll() is None:
            controller.kill()
        controller.wait(timeout=5)


def test_real_task_kernel_denies_outside_reads_support_writes_fork_and_network(native_owned, tmp_path):
    marker = tmp_path / "not-agent-material"
    marker.write_text("synthetic-nonsecret")
    source = (
        "import os,errno,socket,yaml\nfrom pathlib import Path\n"
        f"try: Path({str(marker)!r}).read_bytes()\n"
        "except PermissionError: pass\nelse: raise RuntimeError('outside readable')\n"
        "for p in ['TASK.md',yaml.__file__]:\n"
        " try: Path(p).write_text('should be denied')\n"
        " except PermissionError: pass\n else: raise RuntimeError('readonly writable')\n"
        "try: pid=os.fork()\nexcept PermissionError: pass\nelse:\n"
        " if pid==0: os._exit(7)\n"
        " os.waitpid(pid,0)\n raise RuntimeError('fork allowed')\n"
        "try:\n s=socket.socket()\n s.settimeout(.1)\n"
        " try: s.connect(('192.0.2.1',443))\n finally: s.close()\n"
        "except OSError as e: assert e.errno in (errno.EPERM,errno.EACCES)\n"
        "else: raise RuntimeError('network allowed')\n"
        "def parse_frontmatter(text): return None\n"
    ).encode()
    run = trial.setup(native_owned, tmp_path / "run", source)
    child = trial.runner.launch(run)
    try:
        child.wait(timeout=40)
    finally:
        child.stdin.close()
    assert trial.collect(run) == source
    assert marker.read_text() == "synthetic-nonsecret"


def test_real_native_tool_path_escape_stops_before_worker(native_owned, tmp_path):
    source = trial.packages.agent_files("validator")[trial.SOURCE]
    run = trial.setup(native_owned, tmp_path / "run", source)
    config = json.loads((run / "config.json").read_bytes())
    config["diagnostics"] = [{"op": "read", "path": "../not-agent-material"}]
    (run / "config.json").write_text(json.dumps(config))
    child = trial.runner.launch(run)
    try:
        child.wait(timeout=40)
    finally:
        child.stdin.close()
    terminal = json.loads((run / "receipt/terminal.json").read_bytes())
    assert terminal["wholeProcessQuiescent"] and terminal["nativePrompts"] == 0
    assert terminal["stopReason"] != "diagnostics_complete" and not terminal["actions"]
