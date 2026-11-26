"""Actual native tests are opt-in on the authorized macOS executor."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from benchmarks.michael.replay_trial import api, curriculum as native
from benchmarks.michael.replay_grader import specs


@pytest.fixture
def owned():
    path = os.environ.get("MB006K_OWNED")
    if not path:
        pytest.skip("local-attested-macos; requires authorized pinned native runtime")
    return Path(path)


@pytest.mark.parametrize("name", native.NAMES)
def test_native_package_calibration(owned, tmp_path, name):
    for label, data in (("base", specs.base(name)), ("reference", specs.reference(name))):
        report = native.offline(owned, tmp_path / label, name, data)
        assert report["status"] == "graded"
        assert all(row["passed"] == row["total"] for row in report["counts"].values()) if label == "reference" else report["verdict"] == "fail"
        assert report["cleanup"]["proven"]
        (tmp_path / label / "task" / specs.spec(name)["candidate"]).write_bytes(b"post-stop tamper")
        with pytest.raises(api.TrialError, match="mismatch"):
            native.collect(tmp_path / label)


@pytest.mark.parametrize("name", ["grouping", "validator"])
def test_native_no_fork_and_unlisted_files(owned, tmp_path, name):
    _, policy, _ = native.material(name)
    run = native.prepare(owned, tmp_path / "run", name, seconds=15)
    denied = run / "synthetic-nonsecret"
    denied.write_text("synthetic fixture; not credential state")
    if name == "grouping":
        source = (
            "import fs from 'node:fs'; import cp from 'node:child_process';\n"
            f"try {{fs.readFileSync({json.dumps(str(denied))});throw Error('read bypass');}} "
            "catch(e) {if(!['EPERM','EACCES'].includes(e.code))throw e;}\n"
            "const p=cp.spawnSync('/usr/bin/true');if(!p.error)throw Error('fork bypass');\n"
            "console.log('denied');\n")
    else:
        source = ("import os\ntry:\n os.fork()\n raise RuntimeError('fork bypass')\n"
                  "except PermissionError: pass\n"
                  f"try:\n open({str(denied)!r}).read()\n raise RuntimeError('read bypass')\n"
                  "except PermissionError: pass\nprint('denied')\n")
    config = json.loads((run / "config.json").read_bytes())
    config["diagnostics"] = [{"op": "write", "path": policy["scratch"], "data": source},
                            {"op": "run", "path": policy["scratch"]}]
    api.grader.persist(run / "config.json", config)
    binding = json.loads((run / "curriculum-start.json").read_bytes())
    from benchmarks.michael.replay_trial import validator
    binding["configSha256"] = validator.digest(config)
    api.grader.persist(run / "curriculum-start.json", binding)
    child = api.runner.launch(run)
    try:
        child.wait(timeout=32)
    finally:
        child.stdin.close()
    terminal = json.loads((run / "receipt/terminal.json").read_bytes())
    assert terminal["wholeProcessQuiescent"] and terminal["nativePrompts"] == 0
    result = json.loads((run / "receipt/action-result-2.json").read_bytes())["result"]
    assert result["exitCode"] == 0
    assert native.collect(run) == specs.base(name)


def test_package_policy_closure_and_node_pin():
    for name in native.NAMES:
        agent, policy, _ = native.material(name)
        assert set(policy["read"]) == set(agent) | {policy["scratch"]}
        artifacts = policy.get("artifacts", [policy["source"]])
        assert policy["source"] in artifacts and set(policy["write"]) == {*artifacts, policy["scratch"]}
        assert policy["finalOutputReserve"] == len(artifacts) * policy["bytes"]
        assert policy["runSeconds"] == 30 and policy["actions"] == 128
        assert policy["readonlySizes"] == {p: len(b) for p, b in agent.items() if p not in policy["write"]}
    assert native.NODE_VERSION.startswith("24.") and len(native.NODE_SHA256) == 64


def test_native_paged_read_and_final_collection(owned, tmp_path):
    agent, policy, _ = native.material("grouping")
    run = native.prepare(owned, tmp_path / "run", "grouping", seconds=15, diagnostics=[
        {"op": "read", "path": "package-lock.json", "offset": offset}
        for offset in range(0, len(agent["package-lock.json"]) + 4096, 4096)])
    child = api.runner.launch(run)
    try:
        child.wait(timeout=32)
    finally:
        child.stdin.close()
    import base64
    parts = []
    for index in range(1, 12):
        result = json.loads((run / f"receipt/action-result-{index}.json").read_bytes())["result"]
        parts.append(base64.b64decode(result["stdout"]))
        assert len(parts[-1]) <= 4096
    assert b"".join(parts) == agent["package-lock.json"]
    assert native.collect(run) == agent[policy["source"]]


def test_generalized_result_denominators_and_partial(tmp_path):
    from benchmarks.michael.replay_trial import handoff
    for count in (6, 8, 11, 21, 25, 40):
        graded = {"status": "graded", "verdict": "pass", "cleanup": {"proven": True},
                  "bindings": {"source_sha256": "a" * 64},
                  "assertions": [{"passed": True} for _ in range(count)]}
        bundle = handoff.bundle(tmp_path, "labeled-fixture", synthetic=True)
        result = handoff.terminal(bundle, {"wholeProcessQuiescent": True, "cleanupSeconds": 0,
            "stopReason": "diagnostics_complete", "nativePrompts": 0}, graded, {},
            owner_exited=True, source_sha="a" * 64, expected_assertions=count, synthetic=True)
        assert result["attempts"][0]["verdict"] == "passed"


def test_multifile_native_collection_denies_one_artifact_tamper(owned, tmp_path):
    name = "design-alethiometer-case"
    native.offline(owned, tmp_path / "run", name, specs.reference(name))
    path = tmp_path / "run/task/hardware/BOM.md"
    path.write_bytes(b"post-quiescence tamper")
    with pytest.raises(api.TrialError, match="mismatch"):
        native.collect(tmp_path / "run")


def test_audit_includes_effective_multifile_runtime_overlay():
    from benchmarks.michael.curriculum import live
    payload = live.audit_payload("orchestrate-voice-integration", active_seconds=10800)
    policy = payload["effectiveNativePolicy"]
    assert policy["scratch"] in policy["write"]
    assert policy["activeSeconds"] == 10800
    assert "Node24.11.1" in payload["effectiveNativeInstruction"]
    assert all(path in payload["effectiveNativeInstruction"] for path in policy["artifacts"])
    assert "replay_grader/harnesses/scenarios.mjs" in "\n".join(native.sources())


def test_role_request_echo_binding_is_explicit():
    from benchmarks.michael.curriculum import automation, live
    request = automation.request("audit", model="test-only", family="synthetic", payload={})
    _, _, prompt = live.request_material(request)
    assert f'"request_sha256":"{request["request_sha256"]}"' in prompt
    assert "copy it unchanged" in prompt


def test_native_bad_shape_is_charged_repair_feedback_not_execution(owned, tmp_path):
    run = native.prepare(owned, tmp_path / "run", "validator", seconds=15, diagnostics=[
        {"op": "write", "path": "self_test.py", "data": "print('repaired')\n"},
        {"op": "run", "path": "self_test.py", "offset": 0},
        {"op": "run", "path": "self_test.py"}])
    child = api.runner.launch(run)
    try:
        child.wait(timeout=32)
    finally:
        child.stdin.close()
    terminal = json.loads((run / "receipt/terminal.json").read_bytes())
    rejected = json.loads((run / "receipt/action-result-2.json").read_bytes())
    assert rejected["rejected"] and rejected["result"]["exitCode"] == 2
    assert "action_schema_invalid" in rejected["result"]["feedback"]
    assert len(terminal["actions"]) == 4
    assert sum(row["kind"] == "task" for row in terminal["records"]) == 3
    assert terminal["stopReason"] == "diagnostics_complete"
    assert terminal["taskOutputRetainedBytes"] >= len("repaired\n")
    assert native.collect(run) == specs.base("validator")
