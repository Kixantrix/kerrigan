"""Actual native tests are opt-in on the authorized macOS executor."""
import json
import os
from pathlib import Path
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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
    inventory = json.loads((run / "receipt/inventory.json").read_bytes())
    description = inventory["metadata"]["tools"][0]["description"]
    assert policy["scratch"] in description
    assert "write your own self-tests" in description
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


@pytest.mark.parametrize("name", ["validator", "foal-meadow-regression-review-v2"])
def test_native_prompt_advertises_effective_package_limits(name):
    policy = native.round_three_policy(name)
    instruction = native.prompt(policy)
    for key, label in (("bytes", "bytes/file"), ("channel", "bytes/channel"),
                       ("payload", "bytes/action"), ("aggregate", "bytes aggregate input"),
                       ("outputAggregate", "bytes retained output")):
        assert f"{policy[key]} {label}" in instruction
    assert f"{policy['finalOutputReserve']} bytes reserved for final reads" in instruction
    assert f"{policy['runSeconds']}s timeout" in instruction
    assert "task-declared isolated grader runtime" in instruction
    if name == "foal-meadow-regression-review-v2":
        assert policy["finalOutputReserve"] == 393216
        assert "32KiB/file/channel" not in instruction


def test_scratch_metadata_scan_rejects_aliases_and_entry_overflow(tmp_path):
    from benchmarks.michael.local_transport.scratch_scan import scan
    root = tmp_path / ".scratch"
    root.mkdir()
    info = root.stat()
    identity = [info.st_dev, info.st_ino]
    (root / "nested").mkdir()
    (root / "nested/file").write_bytes(b"temp")
    assert scan(root, identity, 1048576, 128) == {"bytes": 4, "entries": 2}
    (root / "alias").symlink_to(tmp_path)
    with pytest.raises(ValueError, match="alias"):
        scan(root, identity, 1048576, 128)
    (root / "alias").unlink()
    os.link(root / "nested/file", root / "hardlink")
    with pytest.raises(ValueError, match="alias"):
        scan(root, identity, 1048576, 128)
    (root / "hardlink").unlink()
    with pytest.raises(ValueError, match="entry_budget"):
        scan(root, identity, 1048576, 1)
    with pytest.raises(ValueError, match="identity"):
        scan(root, [identity[0], identity[1] + 1], 1048576, 128)


@pytest.mark.parametrize("name", ["validator", "grouping"])
def test_round_three_tmpdir_write_run_cleanup_and_denial(owned, tmp_path, name):
    policy = native.round_three_policy(name, active_seconds=15)
    if name == "validator":
        source = (
            "import os,tempfile\n"
            "assert os.environ['TMPDIR'].endswith('/.scratch')\n"
            "with tempfile.NamedTemporaryFile(delete=False) as f: f.write(b'temp')\n"
            "assert open(f.name,'rb').read()==b'temp'\n"
            "try:\n open('../outside','w').write('bad')\n raise RuntimeError('write bypass')\n"
            "except PermissionError: pass\n"
            "try:\n os.fork()\n raise RuntimeError('fork bypass')\n"
            "except PermissionError: pass\n")
        scratch = ".scratch/nested/check.py"
    else:
        source = (
            "import fs from 'node:fs'; import os from 'node:os'; import cp from 'node:child_process';\n"
            "if(!os.tmpdir().endsWith('/.scratch'))throw Error('TMPDIR');\n"
            "fs.writeFileSync(os.tmpdir()+'/native-temp','temp');\n"
            "try{fs.writeFileSync('../outside','bad');throw Error('write bypass');}"
            "catch(e){if(!['EPERM','EACCES'].includes(e.code))throw e;}\n"
            "if(!cp.spawnSync('/usr/bin/true').error)throw Error('fork bypass');\n")
        scratch = ".scratch/nested/check.mjs"
    run = native.prepare(owned, tmp_path / "run", name, seconds=15, policy=policy,
        diagnostics=[{"op": "write", "path": scratch, "data": source},
                     {"op": "run", "path": scratch}])
    config = json.loads((run / "config.json").read_bytes())
    assert config["condition"] == "MB-R3"
    child = api.runner.launch(run)
    try:
        child.wait(timeout=32)
    finally:
        child.stdin.close()
    terminal = json.loads((run / "receipt/terminal.json").read_bytes())
    assert terminal["wholeProcessQuiescent"] and terminal["nativePrompts"] == 0
    inventory = json.loads((run / "receipt/inventory.json").read_bytes())
    assert policy["scratch"] in inventory["metadata"]["tools"][0]["description"]
    assert terminal["scratch"]["cleanup"] == {"discarded": True}
    assert not terminal["scratch"].get("error")
    assert not (run / "task/.scratch").exists()
    result = json.loads((run / "receipt/action-result-2.json").read_bytes())["result"]
    assert result["exitCode"] == 0
    assert native.collect(run) == specs.base(name)


def test_round_three_scratch_overflow_stops_and_discards(owned, tmp_path):
    name = "validator"
    policy = native.round_three_policy(name, active_seconds=15)
    run = native.prepare(owned, tmp_path / "run", name, seconds=15, policy=policy,
        diagnostics=[{"op": "write", "path": ".scratch/fill.py",
            "data": "import os,time\nopen(os.environ['TMPDIR']+'/overflow','wb').write(b'x'*1048577)\ntime.sleep(3)\n"},
            {"op": "run", "path": ".scratch/fill.py"}])
    child = api.runner.launch(run)
    try:
        child.wait(timeout=32)
    finally:
        child.stdin.close()
    terminal = json.loads((run / "receipt/terminal.json").read_bytes())
    assert terminal["wholeProcessQuiescent"] and terminal["cleanupSeconds"] <= 15
    assert "scratch_byte_budget" in terminal["stopReason"]
    assert terminal["scratch"]["cleanup"] == {"discarded": True}
    assert not (run / "task/.scratch").exists()
    with pytest.raises(api.TrialError, match="proof failed"):
        native.collect(run)


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


def test_missing_path_probe_is_descriptor_bound_and_never_follows_aliases(tmp_path):
    from benchmarks.michael.local_transport.path_probe import missing
    root = tmp_path / "task"
    root.mkdir()
    identity = [root.stat().st_dev, root.stat().st_ino]
    (root / "existing").write_text("not read by the probe")
    (root / "alias").symlink_to(tmp_path, target_is_directory=True)
    assert missing(root, identity, "briefs/invented.md")
    assert not missing(root, identity, "existing")
    assert not missing(root, identity, "alias/missing")
    assert not missing(root, identity, "existing/missing")
    for path in ("../missing", "/missing", "a/../missing", "a//missing", ".", ""):
        assert not missing(root, identity, path)
    with pytest.raises(ValueError, match="identity"):
        missing(root, [identity[0], identity[1] + 1], "missing")


@pytest.mark.parametrize("op", ["read", "run"])
def test_native_nonexistent_task_path_is_charged_not_found_feedback(owned, tmp_path, op):
    run = native.prepare(owned, tmp_path / "run", "validator", seconds=15,
        policy=native.round_three_policy("validator", active_seconds=15),
        diagnostics=[{"op": op, "path": "briefs/invented.md"},
                     {"op": "read", "path": "TASK.md"}])
    child = api.runner.launch(run)
    try:
        child.wait(timeout=32)
    finally:
        child.stdin.close()
    terminal = json.loads((run / "receipt/terminal.json").read_bytes())
    feedback = json.loads((run / "receipt/action-result-1.json").read_bytes())
    assert feedback["rejected"] and feedback["result"]["exitCode"] == 2
    assert feedback["result"]["feedback"].startswith("not_found;")
    assert terminal["stopReason"] == "diagnostics_complete"
    assert terminal["wholeProcessQuiescent"] and terminal["nativePrompts"] == 0
    assert len(terminal["actions"]) == 3 and terminal["actionBytes"] > 0
    assert sum(row["kind"] == "task" for row in terminal["records"]) == 2
    assert native.collect(run) == specs.base("validator")


@pytest.mark.parametrize("path", ["hidden.txt", "alias/missing", "../missing", "/missing"])
def test_native_missing_path_feedback_never_widens_existing_or_outside_access(owned, tmp_path, path):
    run = native.prepare(owned, tmp_path / "run", "validator", seconds=15,
        diagnostics=[{"op": "read", "path": path}])
    (run / "task/hidden.txt").write_text("synthetic unlisted file")
    (run / "task/alias").symlink_to(tmp_path, target_is_directory=True)
    child = api.runner.launch(run)
    try:
        child.wait(timeout=32)
    finally:
        child.stdin.close()
    terminal = json.loads((run / "receipt/terminal.json").read_bytes())
    assert "action_denied" in terminal["stopReason"]
    assert terminal["wholeProcessQuiescent"] and terminal["nativePrompts"] == 0
    assert not terminal["actions"]
    assert all(row["kind"] == "cli" for row in terminal["records"])


@pytest.mark.parametrize("mode", ["complete", "deadline", "output-cap", "schema-feedback", "external-stop"])
def test_synthetic_local_http_uses_actual_native_gate_actions_and_collection(owned, tmp_path, mode):
    cutoff = mode == "deadline"
    seen = []
    actions = [{"op": "read", "path": "TASK.md"},
               {"op": "write", "path": "self_test.py", "data": "print('local-native-proof')\n"},
               {"op": "run", "path": "self_test.py"}]
    if mode == "schema-feedback":
        actions.insert(0, {"op": "read", "path": "TASK.md", "limit": 100})
    if cutoff:
        actions = [{"op": "write", "path": "self_test.py", "data": "import time\ntime.sleep(30)\n"},
                   {"op": "run", "path": "self_test.py"}]
    if mode == "external-stop":
        actions = [{"op": "write", "path": "self_test.py", "data":
                    "import os,time\nfrom pathlib import Path\n"
                    "Path(os.environ['TMPDIR'], 'running').write_text('running')\ntime.sleep(30)\n"},
                   {"op": "run", "path": "self_test.py"}]

    class Stub(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, value):
            data = json.dumps(value).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.reply({"ok": True, "active_requests": 0} if self.path == "/health"
                       else {"data": [{"id": "synthetic-only"}]})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(body)
            index = len(seen) - 1
            message = {"role": "assistant", "content": "done"}
            if index < len(actions):
                message = {"role": "assistant", "content": None, "tool_calls": [{
                    "type": "function", "id": f"local-{index}",
                    "function": {"name": "mb_action", "arguments": json.dumps(actions[index])}}]}
            self.reply({"id": self.headers["x-mtplx-request-id"], "model": "synthetic-only",
                        "choices": [{"message": message,
                                     "finish_reason": "length" if mode == "output-cap" else
                                     "tool_calls" if index < len(actions) else "stop"}],
                        "usage": {"prompt_tokens": 30, "completion_tokens": 4, "total_tokens": 34}})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        import time
        from benchmarks.michael.local_transport import local_trial
        from benchmarks.michael.replay_trial import validator
        root = tmp_path / "slot"
        policy = native.round_three_policy("validator", active_seconds=30)
        frozen = native.freeze(owned, "validator", native.material("validator")[0], policy,
                               ["synthetic-only"], "Synthetic containment test; not a model trial.")
        run = native.prepare(owned, root / "synthetic-only", "validator", seconds=30, policy=policy)
        config = json.loads((run / "config.json").read_bytes())
        config.update(localPrompt="Synthetic containment test; not a model trial.",
                      localInference={"endpoint": f"http://127.0.0.1:{server.server_port}/v1",
                                      "synthetic": True, "model": "synthetic-only", "allowWarning": True,
                                      "owningSession": "synthetic-owner", "requestNamespace": "synthetic-proof",
                                      "limits": {"inputTokens": 229376, "contextTokens": 262144,
                                                 "outputTokens": 16384},
                                      "requestSeconds": 5, "windowStartMs": time.time() * 1000 - 1000,
                                      "windowEndMs": time.time() * 1000 + (22000 if cutoff else 60000),
                                      "concurrency": 1, "grading": "after-window-release"})
        api.grader.persist(run / "config.json", config)
        binding = json.loads((run / "curriculum-start.json").read_bytes())
        binding["configSha256"] = validator.digest(config)
        api.grader.persist(run / "curriculum-start.json", binding)
        frozen.update(condition="MB-R3/local-laptop", localInference=config["localInference"],
                      localTrialSha256=api.sha(Path(local_trial.__file__).read_bytes()))
        api.grader.persist(root / "seal.json", {
            "frozen": frozen, "conditionSha256": validator.digest(frozen)})
        stop_requested = (lambda: "synthetic-owned-external-stop"
                          if (run / "task/.scratch/running").is_file() else None)
        collected = local_trial.execute(root, stop_requested=stop_requested if mode == "external-stop" else None)
        assert collected["status"] == "awaiting-post-window-verification"
        assert collected["sourceSha256"] == api.sha(specs.base("validator"))
        assert not (run / "independent-grader").exists()
        terminal = json.loads((run / "receipt/terminal.json").read_bytes())
        assert terminal["wholeProcessQuiescent"] and terminal["nativePrompts"] == 0
        assert terminal["localInference"]["release"]["ownedRequestsDrained"]
        assert terminal["scratch"]["cleanup"] == {"discarded": True}
        assert terminal["cleanupSeconds"] <= 15
        assert all(record["reaped"] and not record["warnings"] for record in terminal["records"])
        assert [tool["function"]["name"] for tool in seen[0]["tools"]] == ["mb_action"]
        finalized = local_trial.finalize(root, {
            "released": True, "ownedRequestsDrained": True, "releasedAtMs": time.time() * 1000,
            "owningSession": "synthetic-owner", "requestNamespace": "synthetic-proof"})
        assert finalized["status"] == "ungraded"
        assert finalized["completionSeconds"] is None
        if mode == "external-stop":
            assert terminal["stopReason"] == "external_cancel"
            assert collected["externalStopReason"] == "synthetic-owned-external-stop"
            assert not terminal["partialBudgetExhausted"]
            assert terminal["activeSeconds"] < 15
            assert len(seen) == terminal["localInference"]["attempts"] == 2
            assert any(record["kind"] == "task" for record in terminal["records"])
            with pytest.raises(api.TrialError, match="completion proof failed"):
                native.collect(run)
            return
        if mode == "output-cap":
            assert terminal["stopReason"] == "local_output_cap"
            assert terminal["partialBudgetExhausted"]
            assert len(seen) == terminal["localInference"]["attempts"] == 1
            assert terminal["actions"] == ["controller-final-source"]
            return
        if cutoff:
            assert terminal["stopReason"] == "timeout", terminal["stopReason"]
            assert terminal["activeSeconds"] <= 7.5
            assert len(seen) == terminal["localInference"]["attempts"] == 2
            assert any(record["kind"] == "task" for record in terminal["records"])
            with pytest.raises(api.TrialError, match="completion proof failed"):
                native.collect(run)
            return
        assert terminal["stopReason"] == "session_idle", terminal["stopReason"]
        assert len(seen) == terminal["localInference"]["attempts"] == len(actions) + 1
        if mode == "schema-feedback":
            assert "action_schema_invalid" in json.dumps(seen[1]["messages"])
        assert "local-native-proof" in json.dumps(seen[-1]["messages"])
        assert (run / "collected-source.bin").read_bytes() == specs.base("validator")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


PARITY_CASES = [
    ("directory", {"op": "read", "path": "briefs"}, "action_directory_feedback"),
    ("directory-slash", {"op": "read", "path": "briefs/"}, "action_directory_feedback"),
    ("directory-case", {"op": "read", "path": "BRIEFS"}, "action_directory_feedback"),
    ("root", {"op": "read", "path": "."}, "action_directory_feedback"),
    ("root-prefix", {"op": "read", "path": "./"}, "action_directory_feedback"),
    ("offset", {"op": "read", "path": "TASK.md", "offset": 1}, "execute"),
    ("limit", {"op": "read", "path": "TASK.md", "limit": 100}, "action_schema_invalid"),
    ("offset-limit", {"op": "read", "path": "TASK.md", "offset": 0, "limit": 100}, "action_schema_invalid"),
    ("negative-offset", {"op": "read", "path": "TASK.md", "offset": -1}, "action_schema_invalid"),
    ("string-offset", {"op": "read", "path": "TASK.md", "offset": "0"}, "action_schema_invalid"),
    ("large-offset", {"op": "read", "path": "TASK.md", "offset": 4194305}, "action_schema_invalid"),
    ("eof-offset", {"op": "read", "path": "TASK.md", "offset": 4194304}, "execute"),
    ("invented-brief", {"op": "read", "path": "briefs/T012-L2-session.md"}, "not_found"),
    ("tooltip-self-test", {"op": "run", "path": "self_test.py"}, "not_found"),
    ("missing-leaf", {"op": "read", "path": "briefs/missing.md"}, "not_found"),
    ("missing-parent", {"op": "run", "path": "missing/check.mjs"}, "not_found"),
    ("trailing-slash-file", {"op": "read", "path": "TASK.md/"}, "action_path_feedback"),
    ("dot-prefix", {"op": "read", "path": "./TASK.md"}, "action_path_feedback"),
    ("redundant-separators", {"op": "read", "path": "src//session.ts"}, "action_path_feedback"),
    ("case", {"op": "read", "path": "task.md"}, "action_path_feedback"),
    ("absolute-in-root", {"op": "read", "path": "$ROOT/TASK.md"}, "action_path_feedback"),
    ("run-args", {"op": "run", "path": "self_test.mjs", "args": ["--check"]}, "action_schema_invalid"),
    ("run-extra-data", {"op": "run", "path": "self_test.mjs", "data": ""}, "action_schema_invalid"),
    ("run-readonly", {"op": "run", "path": "TASK.md"}, "action_operation_feedback"),
    ("write-new-allowed", {"op": "write", "path": "self_test.mjs", "data": "console.log('safe');"}, "execute"),
    ("write-new-artifact", {"op": "write", "path": "src/session.ts", "data": "$BASE"}, "execute"),
    ("write-new-undeclared", {"op": "write", "path": "new.txt", "data": "not written"}, "not_found"),
    ("write-readonly", {"op": "write", "path": "TASK.md", "data": "not written"}, "action_operation_feedback"),
    ("write-directory", {"op": "write", "path": "briefs", "data": "not written"}, "action_directory_feedback"),
    ("file-as-directory", {"op": "read", "path": "TASK.md/missing"}, "action_path_feedback"),
    ("missing-space", {"op": "read", "path": "missing name.md"}, "not_found"),
    ("missing-unicode", {"op": "read", "path": "missing-\u03b1.md"}, "not_found"),
    ("empty-path", {"op": "read", "path": ""}, "action_schema_invalid"),
    ("nul-path", {"op": "read", "path": "missing\0file"}, "action_schema_invalid"),
    ("long-component", {"op": "read", "path": "x" * 256}, "action_schema_invalid"),
    ("extra-operation", {"op": "list", "path": "TASK.md"}, "action_operation_feedback"),
    ("existing-undeclared", {"op": "read", "path": "briefs/HIDDEN.md"}, "cutoff"),
    ("run-existing-undeclared", {"op": "run", "path": "hidden.txt"}, "cutoff"),
    ("write-existing-undeclared", {"op": "write", "path": "hidden.txt", "data": "not written"}, "cutoff"),
    ("undeclared-directory", {"op": "read", "path": "hidden-dir"}, "cutoff"),
    ("outside-root", {"op": "read", "path": "/missing"}, "cutoff"),
    ("parent-traversal", {"op": "read", "path": "../missing"}, "cutoff"),
    ("internal-traversal", {"op": "read", "path": "briefs/../TASK.md"}, "cutoff"),
    ("symlink-file", {"op": "read", "path": "alias-file"}, "cutoff"),
    ("symlink-directory", {"op": "read", "path": "alias-dir/missing"}, "cutoff"),
    ("hardlink", {"op": "read", "path": "hardlink"}, "cutoff"),
    ("special-file", {"op": "read", "path": "fifo"}, "cutoff"),
]


@pytest.mark.parametrize("case,args,expected", PARITY_CASES, ids=[row[0] for row in PARITY_CASES])
def test_native_cli_parity_sweep(owned, tmp_path, case, args, expected):
    name = "orchestrate-voice-integration-v5"
    policy = native.round_three_policy(name, active_seconds=15)
    run = native.prepare(owned, tmp_path / "run", name, seconds=15, policy=policy)
    task = run / "task"
    (task / "hidden.txt").write_text("synthetic undeclared fixture")
    (task / "briefs/HIDDEN.md").write_text("not in the declared manifest")
    (task / "hidden-dir").mkdir()
    (task / "alias-file").symlink_to(task / "TASK.md")
    (task / "alias-dir").symlink_to(task / "briefs", target_is_directory=True)
    os.link(task / "hidden.txt", task / "hardlink")
    os.mkfifo(task / "fifo")
    if case == "write-new-allowed":
        (task / policy["scratch"]).unlink()
    if case == "write-new-artifact":
        (task / "src/session.ts").unlink()
    args = {**args, "path": args["path"].replace("$ROOT", str(task))}
    if args.get("data") == "$BASE":
        args["data"] = specs.package(name)[0]["src/session.ts"].decode()
    config = json.loads((run / "config.json").read_bytes())
    config["diagnostics"] = [args, {"op": "read", "path": "TASK.md"}]
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
    assert terminal["wholeProcessQuiescent"] and terminal["cleanupSeconds"] <= 15
    assert terminal["nativePrompts"] == 0 and not terminal["nativeStarts"]
    if expected == "cutoff":
        assert "action_denied" in terminal["stopReason"]
        assert not terminal["actions"]
    else:
        assert terminal["stopReason"] == "diagnostics_complete", terminal["stopReason"]
        assert len(terminal["actions"]) == 2 + len(policy["artifacts"])
        first = json.loads((run / "receipt/action-result-1.json").read_bytes())
        if expected != "execute":
            assert first["rejected"] and first["result"]["feedback"].startswith(expected + ";")
        else:
            assert first["result"]["exitCode"] == 0
        if expected == "action_directory_feedback" and args["op"] == "read":
            import base64
            listing = base64.b64decode(first["result"]["stdout"]).decode()
            assert "HIDDEN" not in listing and "hidden" not in listing
        assert native.collect(run) == specs.base(name)
    assert (task / "hidden.txt").read_text() == "synthetic undeclared fixture"
    assert not (task / "new.txt").exists()
