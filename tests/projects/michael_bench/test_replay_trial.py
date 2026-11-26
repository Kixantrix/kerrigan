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
from replay_trial import validator, handoff


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


def test_mb006l_staging_and_absent_live_authority(tmp_path):
    run = validator.prepare(tmp_path, tmp_path / "offline")
    binding = json.loads((run / "trial-start.json").read_bytes())
    config = json.loads((run / "config.json").read_bytes())
    assert "fixtureSourceSha256" not in binding and config["validatorTask"]
    assert config["seconds"] == 3600 and "prompt" not in config
    assert sorted(p.relative_to(run / "task").as_posix() for p in (run / "task").rglob("*")
                  if p.is_file()) == sorted(validator.POLICY["read"])
    with pytest.raises((FileNotFoundError, validator.api.TrialError)):
        validator.prepare_live(tmp_path, tmp_path / "forbidden", "mai-code-2")
    assert not (tmp_path / validator.NAMESPACE).exists()


def mb006l_seal(tmp_path, monkeypatch):
    condition = validator.frozen(tmp_path)
    root = tmp_path / validator.NAMESPACE
    root.mkdir()
    trial.grader.persist(root / "approval.json", {"synthetic": True})
    trial.grader.persist(root / "safety.json", {"conditionSha256": validator.digest(condition),
        "passed": True, "attester": "authorized-local-executor", "nativePrompts": 0})
    seal = {"condition": "MB-006l", "conditionSha256": validator.digest(condition),
            "frozen": condition, "source": condition["source"],
            "authorizationSource": validator.AUTHORIZATION_SOURCE,
            "approvalSha256": trial.sha((root / "approval.json").read_bytes()),
            "safetySha256": trial.sha((root / "safety.json").read_bytes())}
    path = tmp_path / "synthetic-seal.json"
    trial.grader.persist(path, seal)
    monkeypatch.setattr(validator, "SEAL", path)
    return root, path, seal


@pytest.mark.parametrize("damage", ["source", "environment", "limits", "approval", "provenance", "condition"])
def test_mb006l_stale_authority_fails_before_allocation(tmp_path, monkeypatch, damage):
    root, path, seal = mb006l_seal(tmp_path, monkeypatch)
    if damage in ("source", "environment", "limits"):
        seal["frozen"][damage]["synthetic-mutation"] = True
    elif damage == "approval":
        (root / "approval.json").write_text("modified")
    elif damage == "provenance":
        seal["authorizationSource"] = "unbound coordinator suggestion"
    else:
        seal["condition"] = "MB-006h"
    trial.grader.persist(path, seal)
    with pytest.raises(trial.TrialError):
        validator.prepare_live(tmp_path, tmp_path / "denied", "mai-code-2")
    assert not (root / "slots").exists() and not (tmp_path / "denied").exists()


def test_mb006l_exclusive_temporary_slots_and_unreaped_sequence(tmp_path, monkeypatch):
    root, path, seal = mb006l_seal(tmp_path, monkeypatch)
    run = validator.prepare_live(tmp_path, tmp_path / "first", "mai-code-2")
    with pytest.raises(trial.TrialError, match="spent"):
        validator.prepare_live(tmp_path, tmp_path / "again", "mai-code-2")
    trial.grader.persist(run / "receipt/terminal.json", {"wholeProcessQuiescent": False})
    trial.grader.persist(run / "controller-terminal.json", {"ownerExited": False})
    with pytest.raises(trial.TrialError, match="cleanup"):
        validator.prepare_live(tmp_path, tmp_path / "second", "claude-sonnet-5.5")
    assert sorted(p.name for p in (root / "slots").iterdir()) == ["mai-code-2.json"]


def mb006l_wait(run):
    child = trial.runner.launch(run)
    try:
        child.wait(timeout=45)
    finally:
        child.stdin.close()
    return json.loads((run / "receipt/terminal.json").read_bytes())


def test_mb006l_native_unknown_repair_and_contracts(native_owned, tmp_path):
    ledger = handoff.Ledger(tmp_path / "synthetic-ledger.jsonl")
    for label, source, passes in (
        ("base", trial.packages.agent_files("validator")[trial.SOURCE] + b"\n# unknown final bytes\n", 22),
        ("reference", trial.packages.verifier_files("validator")["reference"], 25)):
        began = time.monotonic()
        run = validator.prepare(native_owned, tmp_path / label, diagnostics=[
            {"op": "read", "path": "TASK.md"},
            {"op": "write", "path": "self_test.py", "data": "assert False, 'public test failure'\n"},
            {"op": "run", "path": "self_test.py"},
            {"op": "write", "path": "self_test.py", "data": "import yaml; assert yaml.__version__=='6.0.2'\n"},
            {"op": "run", "path": "self_test.py"},
            {"op": "write", "path": trial.SOURCE, "data": source.decode()},
            {"op": "run", "path": trial.SOURCE}], seconds=20)
        frozen = handoff.bundle(native_owned, label + "-fixture", synthetic=True)
        ledger.start(label, frozen, attempt_id="attempt-1", origin="synthetic")
        setup_seconds = time.monotonic() - began
        native = mb006l_wait(run)
        assert native["wholeProcessQuiescent"] and native["nativePrompts"] == 0
        assert json.loads((run / "receipt/action-result-3.json").read_bytes())["result"]["exitCode"] == 1
        path = run / "task" / trial.SOURCE
        path.write_bytes(source + b"\n# trusted post-stop tamper\n")
        with pytest.raises(trial.TrialError, match="binding"):
            trial.collect(run)
        path.write_bytes(source)
        verification_began = time.monotonic()
        collected = trial.collect(run)
        assert collected == source
        graded = trial.grader.grade(collected, run / "independent-grader")
        assert graded["status"] == "graded" and sum(a["passed"] for a in graded["assertions"]) == passes
        timings = {"setup": setup_seconds, "agent_work": native["activeSeconds"],
                   "verification": time.monotonic() - verification_began,
                   "end_to_end": time.monotonic() - began}
        result = handoff.terminal(frozen, native, graded, timings, owner_exited=True,
                                  source_sha=trial.sha(collected), synthetic=True)
        ledger.finalize(label, result)
        trial.grader.persist(run / "synthetic-result.json", result)
        capped = handoff.terminal(frozen, {**native, "stopReason": "output_overflow:task"},
            graded, timings, owner_exited=True, source_sha=trial.sha(collected), synthetic=True)
        assert capped["attempts"][0]["verdict"] == "ungraded"
        assert capped["attempts"][0]["time_to_verified_completion"]["status"] == "unknown"
    report = handoff.compare(ledger, cohorts={"base-fixture": ["base"], "reference-fixture": ["reference"]},
                            suite=[handoff.ref(frozen["task"])])
    assert report["cohorts"]["reference-fixture"]["first_attempt_verified"] == 1
    assert report["both_success_complete_time_subset"]["paired_denominator"] == 0
    trial.grader.persist(tmp_path / "synthetic-comparison.json", report)


@pytest.mark.parametrize("mode", ["escape", "timeout", "kernel"])
def test_mb006l_native_boundaries(native_owned, tmp_path, mode):
    script = ("import os,socket\nfrom pathlib import Path\n"
              "for p in ['TASK.md','../config.json']:\n"
              " try: Path(p).write_text('denied')\n"
              " except PermissionError: pass\n else: raise RuntimeError('write escaped')\n"
              "try: os.fork()\nexcept PermissionError: pass\nelse: os._exit(9)\n"
              "try:\n s=socket.socket(); s.connect(('192.0.2.1',443))\nexcept PermissionError: pass\n"
              "else: raise RuntimeError('network allowed')\n")
    diagnostics = ([{"op": "read", "path": "../config.json"}] if mode == "escape" else [
        {"op": "write", "path": "self_test.py", "data": "while True: pass\n" if mode == "timeout" else script},
        {"op": "run", "path": "self_test.py"}])
    run = validator.prepare(native_owned, tmp_path / "run", diagnostics=diagnostics,
                            seconds=3 if mode == "timeout" else 20)
    native = mb006l_wait(run)
    assert native["wholeProcessQuiescent"] and native["cleanupSeconds"] < 15
    assert native["nativePrompts"] == 0
    if mode == "kernel":
        assert native["stopReason"] == "diagnostics_complete"
        assert json.loads((run / "receipt/action-result-2.json").read_bytes())["result"]["exitCode"] == 0
        trial.collect(run)
    elif mode == "timeout":
        assert native["partialBudgetExhausted"]
        trial.collect(run)
    else:
        with pytest.raises(trial.TrialError):
            trial.collect(run)


def test_mb006l_native_owner_survives_controller_loss(native_owned, tmp_path):
    run = tmp_path / "run"
    code = ("from benchmarks.michael.replay_trial import validator,api\n"
            f"r=validator.prepare({str(native_owned)!r},{str(run)!r},"
            "diagnostics=[{'op':'read','path':'TASK.md'}],seconds=8,hold=True)\n"
            "api.runner.launch(r).wait(timeout=30)\n")
    controller = subprocess.Popen([sys.executable, "-c", code], cwd=trial.packages.ROOT)
    try:
        until = time.monotonic() + 15
        while not (run / "receipt/action-result-1.json").exists():
            assert time.monotonic() < until
            time.sleep(.025)
        controller.kill()
        controller.wait(timeout=5)
        until = time.monotonic() + 20
        while not (run / "receipt/terminal.json").exists():
            assert time.monotonic() < until
            time.sleep(.025)
        native = json.loads((run / "receipt/terminal.json").read_bytes())
        assert native["wholeProcessQuiescent"] and native["stopReason"] == "controller_lost"
    finally:
        if controller.poll() is None:
            controller.kill()
        controller.wait(timeout=5)


@pytest.mark.parametrize("failure", [False, True])
def test_mb006l_synthetic_owner_tool_loop(tmp_path, failure):
    run = validator.prepare(tmp_path, tmp_path / "run", diagnostics=[
        {"op": "write", "path": "self_test.py", "data": "synthetic-only"},
        {"op": "run", "path": "self_test.py"},
        {"op": "read", "path": trial.SOURCE}])
    for name in ("synthetic_sdk.mjs", "protocol.mjs", "budgets.json"):
        (run / "trusted" / name).write_bytes((trial.runner.HERE / name).read_bytes())
    trial.grader.persist(run / "trusted/fixture.json", {"failure": failure, "modelLoop": True, "fragment": 11})
    config = json.loads((run / "config.json").read_bytes())
    config["sdk"] = str(run / "trusted/synthetic_sdk.mjs")
    trial.grader.persist(run / "config.json", config)
    native = mb006l_wait(run)
    assert native["wholeProcessQuiescent"] and native["nativePrompts"] == 0
    assert len(native["nativeStarts"]) == 1 and native["usage"] != "unknown"
    assert native["stopReason"] == ("native_model_failure:model.call_failure" if failure else "diagnostics_complete")
    assert len(native["actions"]) == (0 if failure else 4)


def test_mb006l_javascript_admission_synthetic_files_only(tmp_path):
    module = tmp_path / "synthetic/local_transport"
    module.mkdir(parents=True)
    for name in ("validator_admission.mjs", "curriculum_admission.mjs", "limits.mjs", "validator-policy.json", "validator-task-policy.json"):
        (module / name).write_bytes((trial.runner.HERE / name).read_bytes())
    authority = module.parent / "replay_trial"
    authority.mkdir()
    root = tmp_path / "synthetic-mb006l-slots"
    (root / "slots").mkdir(parents=True)
    for name in ("approval.json", "safety.json", "copilot", "sdk/dist/v1/index.js", "sdk/bin/arm64/mxc-exec-mac", "ca"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic public bytes; never executed")
    node = subprocess.check_output(["node", "-p", "process.execPath"], text=True).strip()
    runtime = {"cli": root / "copilot", "sdk": root / "sdk/dist/v1/index.js",
               "executor": root / "sdk/bin/arm64/mxc-exec-mac", "node": Path(node), "taskPython": Path(sys.executable)}
    frozen = {"namespace": root.name, "models": ["mai-code-2"], "source": {},
              "runtime": {name: trial.sha(path.read_bytes()) for name, path in runtime.items()},
              "caSha256": trial.sha((root / "ca").read_bytes())}
    seal = {"frozen": frozen, "conditionSha256": validator.digest(frozen), "source": {},
            "authorizationSource": validator.AUTHORIZATION_SOURCE,
            "approvalSha256": trial.sha((root / "approval.json").read_bytes()),
            "safetySha256": trial.sha((root / "safety.json").read_bytes())}
    trial.grader.persist(authority / "mb006l-response-v2-authorization.json", seal)
    config = {"validatorTask": True, "validatorReplay": False, "condition": "MB-006l", "seconds": 3600,
              "model": "mai-code-2", "approved": True, "slot": str(root / "slots/mai-code-2.json"),
              "receipt": str(root), "conditionSha256": seal["conditionSha256"], "sdk": str(runtime["sdk"]),
              "command": str(runtime["cli"]), "python": str(runtime["taskPython"]),
              "environment": {"SSL_CERT_FILE": str(root / "ca")}}
    trial.grader.persist(Path(config["slot"]), {"model": config["model"],
        "configSha256": validator.digest(config), "sealSha256": validator.digest(seal)})
    script = f"import {{admission}} from {json.dumps((module/'validator_admission.mjs').as_uri())}; admission({json.dumps(config)});"
    def invoke():
        return subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, timeout=5)
    assert invoke().returncode == 0
    assert b"EEXIST" in invoke().stderr
    (root / "approval.json").write_text("trusted synthetic mutation")
    assert b"validator_approval_stale" in invoke().stderr


@pytest.mark.parametrize("mode", ["hang", "overflow", "deadline", "actions", "runaway", "retained"])
def test_mb006l_review_native_feedback_and_partial(native_owned, tmp_path, mode):
    source = "while True: pass\n" if mode in ("hang", "deadline") else "print('x'*40000)\n"
    if mode == "runaway":
        source = "while True: print('x'*8192)\n"
    diagnostics = [{"op": "write", "path": "self_test.py", "data": source},
        {"op": "run", "path": "self_test.py"},
        {"op": "write", "path": "self_test.py", "data": "assert True\n"},
        {"op": "run", "path": "self_test.py"}]
    if mode == "actions":
        diagnostics = [{"op": "read", "path": "requirements.txt"}] * 128
    if mode == "retained":
        diagnostics = [{"op": "write", "path": "self_test.py", "data": "print('x'*32767)\n"}] + [
            {"op": "run", "path": "self_test.py"}] * 32
    run = validator.prepare(native_owned, tmp_path / "run", diagnostics=diagnostics,
                            seconds=3 if mode == "deadline" else 45)
    native = mb006l_wait(run)
    assert native["wholeProcessQuiescent"] and native["cleanupSeconds"] < 15
    assert native["nativePrompts"] == 0
    assert native["taskOutputRetainedBytes"] <= 1048576
    if mode in ("hang", "overflow", "runaway"):
        result = json.loads((run / "receipt/action-result-2.json").read_bytes())["result"]
        assert result["timedOut"] if mode in ("hang", "runaway") else result["feedback"]["stdout"]["truncated"]
        if mode == "overflow":
            assert result["feedback"]["stdout"] == {"emitted": 40001, "retained": 32768, "truncated": True}
        if mode == "runaway":
            assert result["feedback"]["stdout"]["emitted"] > 1048576
            assert result["feedback"]["stdout"]["retained"] == 32768
            assert (run / "receipt/task-2-stdout.bin").stat().st_size == 32768
            assert native["taskOutputRetainedBytes"] < 65536
        assert json.loads((run / "receipt/action-result-4.json").read_bytes())["result"]["exitCode"] == 0
    else:
        assert native["partialBudgetExhausted"]
        if mode == "retained":
            assert native["stopReason"] == "broker:task_output_budget"
    final = json.loads((run / f"receipt/owned-start-{len(native['records'])-1}.json").read_bytes())
    assert final["startedMs"] >= native["records"][0]["finishedMs"]
    collected = trial.collect(run)
    graded = trial.grader.grade(collected, run / "independent-grader")
    assert graded["status"] == "graded" and len(graded["assertions"]) == 25
    if mode in ("deadline", "actions", "retained"):
        frozen = handoff.bundle(native_owned, mode + "-fixture", synthetic=True)
        ledger = handoff.Ledger(tmp_path / "synthetic-partial.jsonl")
        ledger.start(mode, frozen, attempt_id="attempt-1", origin="synthetic")
        result = handoff.terminal(frozen, native, graded, {"end_to_end": native["activeSeconds"]},
                                  owner_exited=True, source_sha=trial.sha(collected), synthetic=True)
        assert result["attempts"][0]["verdict"] == "ungraded"
        assert result["attempts"][0]["time_to_verified_completion"]["status"] == "unknown"
        assert result["attempts"][0]["events"][0]["code"] == "not-completed-within-budget"
        path = run / "independent-grader/report.json"
        ledger.finalize(mode, result, partial={"result": handoff.ref(result), "attempt_id": "attempt-1",
            "passed": sum(a["passed"] for a in graded["assertions"]), "total": 25,
            "source": "not completed within budget; independent partial diagnostics",
            "artifacts": [{"uri": str(path), "sha256": trial.sha(path.read_bytes())}]})
        trial.grader.persist(run / "synthetic-result.json", result)
