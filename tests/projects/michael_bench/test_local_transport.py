"""AC-MB-002/003/004: integration; environment: local-attested-macos.

Trusted fake diagnostics only. Native CLI inventory and process trees remain gated.
"""
import base64
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "benchmarks/michael/local_transport"))
from proof import LIMIT, ProofError, capture, digest, environment, fixture, recover
from runner import HERE, SOURCES, prepare, recovery
import runner


def test_frozen_corrected_allowance_rejects_missing_stale_modified_reused_and_unreaped(tmp_path, monkeypatch):
    source = {name: digest(HERE / name) for name in SOURCES}
    approval = tmp_path / "mb006f/approval.json"
    approval.parent.mkdir()
    value = {"condition": "MB-006f", "attester": "authorized-local-executor",
             "evidenceClass": "local-agent-attested"}
    approval.write_text(json.dumps(value))
    frozen = tmp_path / "frozen.json"
    monkeypatch.setattr(runner, "FROZEN_APPROVAL", frozen)
    with pytest.raises(ProofError, match="required"):
        runner.corrected_allowance(tmp_path, "mai-code-2", approval, source)
    seal = {"condition": "MB-006f", "models": ["mai-code-2", "claude-sonnet-5.5"],
            "controllerPromptsPerModel": 1, "activeSeconds": 180, "cleanupSeconds": 15,
            "source": source, "approvalSha256": digest(approval)}
    frozen.write_text(json.dumps(seal))
    with pytest.raises(ProofError, match="stale"):
        runner.corrected_allowance(tmp_path, "mai-code-2", approval, {})
    approval.write_text(json.dumps({**value, "modified": True}))
    with pytest.raises(ProofError, match="modified"):
        runner.corrected_allowance(tmp_path, "mai-code-2", approval, source)
    approval.write_text(json.dumps(value))
    slots, _ = runner.corrected_allowance(tmp_path, "mai-code-2", approval, source)
    receipt = tmp_path / "first/receipt"
    receipt.mkdir(parents=True)
    from proof import persist
    persist(slots / "mai-code-2.json", {"receipt": str(receipt)})
    with pytest.raises(FileExistsError):
        persist(slots / "mai-code-2.json", {"receipt": str(receipt)})
    (receipt / "terminal.json").write_text(json.dumps({"wholeProcessQuiescent": False}))
    with pytest.raises(ProofError, match="cleanup"):
        runner.corrected_allowance(tmp_path, "claude-sonnet-5.5", approval, source)
    (receipt / "terminal.json").write_text(json.dumps({
        "wholeProcessQuiescent": True, "cleanupSeconds": 0.1}))
    runner.corrected_allowance(tmp_path, "claude-sonnet-5.5", approval, source)
    assert not (tmp_path / "canary-slots").exists()


def test_native_cannot_launch_before_inventory_and_tree_proof(tmp_path):
    with pytest.raises(ProofError, match="gated"):
        capture(["not-executed"], tmp_path, tmp_path / "evidence", native=True)
    assert not (tmp_path / "evidence").exists()


@pytest.mark.parametrize("channel", [1, 2])
def test_stream_overflow_is_bounded_and_cleanup_not_overclaimed(tmp_path, channel):
    receipt = capture([sys.executable, "-c",
                       f"import os\nwhile True: os.write({channel},b'x'*8192)"],
                      tmp_path, tmp_path / "receipt", seconds=3)
    name = "stdout" if channel == 1 else "stderr"
    assert receipt["stop_reason"] == f"output_overflow:{name}"
    output = json.loads((tmp_path / "receipt/capture.json").read_text())["channels"][name]
    assert len(base64.b64decode(output["base64_prefix"])) == LIMIT
    assert output["observed_bytes_lower_bound"] > LIMIT
    assert receipt["cleanup"]["direct_child_reaped"]
    assert receipt["cleanup"]["whole_process_tree"] == "unproven"


def test_timeout_has_durable_start_and_nonreplaying_recovery(tmp_path):
    receipt = capture([sys.executable, "-c", "import time; time.sleep(60)"],
                      tmp_path, tmp_path / "receipt", seconds=0.3)
    assert receipt["stop_reason"] == "timeout"
    assert receipt["active_seconds"] < 2
    assert receipt["cleanup_seconds"] < 15
    assert receipt["cleanup"]["direct_child_reaped"]
    with pytest.raises(ProofError, match="quiescence"):
        recover(tmp_path / "receipt")
    before = (tmp_path / "receipt/recovery.json").read_bytes()
    with pytest.raises(ProofError):
        recover(tmp_path / "receipt")
    assert (tmp_path / "receipt/recovery.json").read_bytes() == before
    assert json.loads(before)["signals_sent"] == 0


def test_success_is_ungraded_and_does_not_prove_subtree(tmp_path):
    receipt = capture([sys.executable, "-c", "print('synthetic')"],
                      tmp_path, tmp_path / "receipt")
    assert receipt["stop_reason"] == "completed"
    assert receipt["verdict"] == "ungraded"
    assert receipt["cleanup"]["recoverable"]
    assert (tmp_path / "receipt/start.json").exists()
    with pytest.raises(FileExistsError):
        capture(["not-executed"], tmp_path, tmp_path / "receipt")


def test_cross_process_clock_epoch_after_parent_uptime(tmp_path):
    time.sleep(0.1)
    for index in range(2):
        receipt = capture([sys.executable, "-c", "print('synthetic')"],
                          tmp_path, tmp_path / f"receipt-{index}")
        assert 0 <= receipt["active_seconds"] < 2
        assert 0 <= receipt["cleanup_seconds"] < 15


def test_external_watchdog_stops_direct_child_when_controller_dies(tmp_path):
    script = (
        f"import sys;sys.path.insert(0,{str(ROOT / 'benchmarks/michael/local_transport')!r})\n"
        "from proof import capture\n"
        f"capture([sys.executable,'-c','import time;time.sleep(60)'],"
        f"{str(tmp_path)!r},{str(tmp_path / 'receipt')!r},seconds=5)\n"
    )
    controller = subprocess.Popen([sys.executable, "-c", script])
    try:
        until = time.monotonic() + 3
        while not (tmp_path / "receipt/process.json").exists():
            assert time.monotonic() < until
            time.sleep(0.01)
        controller.kill()
        controller.wait(timeout=2)
        while not (tmp_path / "receipt/terminal.json").exists():
            assert time.monotonic() < until
            time.sleep(0.01)
        receipt = json.loads((tmp_path / "receipt/terminal.json").read_text())
        assert receipt["stop_reason"] == "controller_lost"
        assert receipt["cleanup"]["direct_child_reaped"]
        assert receipt["cleanup"]["whole_process_tree"] == "unproven"
    finally:
        if controller.poll() is None:
            controller.kill()
        controller.wait(timeout=2)


def test_detached_child_is_not_misreported_as_whole_process_cleanup(tmp_path):
    marker = tmp_path / "descendant-finished"
    descendant = (
        "import time;from pathlib import Path;time.sleep(0.6);"
        f"Path({str(marker)!r}).write_text('synthetic')"
    )
    program = (
        "import subprocess,sys\n"
        f"subprocess.Popen([sys.executable,'-c',{descendant!r}],start_new_session=True)\n"
    )
    receipt = capture([sys.executable, "-c", program],
                      tmp_path, tmp_path / "receipt", seconds=0.2)
    assert receipt["stop_reason"] == "timeout"
    assert receipt["cleanup"]["direct_child_reaped"]
    assert receipt["cleanup"]["whole_process_tree"] == "unproven"
    until = time.monotonic() + 3
    while not marker.exists():
        assert time.monotonic() < until
        time.sleep(0.01)
    with pytest.raises(ProofError, match="quiescence"):
        recover(tmp_path / "receipt")


@pytest.mark.parametrize("seconds", [0, -1, 181, float("nan"), float("inf")])
def test_invalid_budget_never_launches(tmp_path, seconds):
    with pytest.raises(ValueError):
        capture(["not-executed"], tmp_path, tmp_path / "receipt", seconds=seconds)
    assert not (tmp_path / "receipt").exists()


def test_input_and_repository_rejected_before_launch(tmp_path):
    with pytest.raises(ProofError, match="input_overflow"):
        capture(["not-executed"], tmp_path, tmp_path / "receipt", input_bytes=b"x" * 8193)
    with pytest.raises(ProofError, match="repository/history"):
        fixture(ROOT / "benchmarks/michael/local_transport/never-created")


def test_fixture_has_no_shared_environment_or_bypass(tmp_path):
    state = fixture(tmp_path / "fixture")
    env = environment(state)
    assert not any("TOKEN" in key or "SECRET" in key for key in env)
    assert env["COPILOT_HOME"] == str(state / "cli")
    settings = json.loads((state / "cli/settings.json").read_text())
    assert settings["sandbox"]["allowBypass"] is False
    assert settings["sandbox"]["auth"] == {"git": False, "gh": False}
    assert settings["sandbox"]["userPolicy"]["network"] == {
        "allowOutbound": False, "allowLocalNetwork": False}


def test_canary_cannot_start_without_exact_current_safety_source(tmp_path):
    with pytest.raises(ProofError, match="approval required"):
        prepare(tmp_path, tmp_path / "run", model="mai-code-2")
    assert not (tmp_path / "canary-slots").exists()
    receipt = recovery(tmp_path / "run")
    assert receipt == {"wholeProcessQuiescent": False, "signalsSent": 0,
                       "replayedActions": 0, "status": "unknown; no relaunch"}


def test_broker_rejects_traversal_duplicates_and_all_budgets():
    script = """
import {validateAction,nativeFailure} from './benchmarks/michael/local_transport/limits.mjs';
import assert from 'node:assert/strict';
const state=()=>({actions:new Set(),bytes:0});
const good={op:'read',path:'candidate.py'};
for(const bad of [{...good,path:'../candidate.py'},{...good,extra:true},
                  {...good,op:'shell'},{op:'run',path:'result.txt'},
                  {op:'write',path:'candidate.py',data:5}])
    assert.throws(()=>validateAction('a',bad,state()),/denied/);
const s=state();validateAction('a',good,s);
assert.throws(()=>validateAction('a',good,s),/duplicate/);
assert.throws(()=>validateAction('b',{op:'write',path:'candidate.py',data:'x'.repeat(8192)},s),/budget/);
const count=state();
for(let i=0;i<8;i++) validateAction('a'+i,good,count);
assert.throws(()=>validateAction('overflow',good,count),/budget/);
const bytes=state();
for(let i=0;i<4;i++)validateAction('b'+i,{op:'write',path:'candidate.py',data:'x'.repeat(7000)},bytes);
assert.throws(()=>validateAction('aggregate',{op:'write',path:'candidate.py',data:'x'.repeat(7000)},bytes),/budget/);
for(const type of ['model.call_failure','model.model_call_failure','model.turn_retry','assistant.turn_retry'])
    assert.match(nativeFailure({type},'mai-code-2'),/native_model_failure/);
assert.equal(nativeFailure({type:'model.model_call_started',data:{model:'other'}},'mai-code-2'),
             'native_model_identity_mismatch');
assert.equal(nativeFailure({type:'model.model_call_started',data:{model:'mai-code-2'}},'mai-code-2'),null);
"""
    subprocess.run(["node", "--input-type=module", "-e", script],
                   cwd=ROOT, check=True, timeout=5)


def test_tls_proof_and_exclusive_canary_slot_are_required(tmp_path):
    approval = tmp_path / "approval.json"
    value = {"source": {name: digest(HERE / name) for name in SOURCES},
             "passed": True, "transportReady": False}
    approval.write_text(json.dumps(value))
    with pytest.raises(ProofError, match="TLS transport unproven"):
        prepare(tmp_path, tmp_path / "denied", model="mai-code-2", approval=approval)
    assert not (tmp_path / "canary-slots").exists()
    value["transportReady"] = True
    approval.write_text(json.dumps(value))
    with pytest.raises(ProofError, match="TLS transport unproven"):
        prepare(tmp_path, tmp_path / "unbound", model="mai-code-2", approval=approval)
    probe = prepare(tmp_path, tmp_path / "probe", transport_probe=True)
    config = json.loads((probe / "config.json").read_text())
    pins = json.loads((HERE / "runtime.json").read_text())
    import hashlib
    value["transport"] = {
        "transportReady": True, "nativePrompts": 0, "source": value["source"], "config": config,
        "configSha256": hashlib.sha256(json.dumps(
            config, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(),
        "publicCaSha256": pins["public_transport_ca"]["sha256"],
        "runtime": {"cliSha256": pins["copilot"]["executable_sha256"],
                    "mxcSha256": pins["mxc_executor"]["executable_sha256"],
                    "mxcVersion": "1.1.0", "nodeVersion": "fixture", "nodeSha256": "0" * 64},
        "request": {"method": "HEAD", "url": "https://api.github.com/meta", "headers": [],
                    "timeoutMs": 5000, "bodyLimitBytes": 8192,
                    "retryOptions": {"maxRetries": 0, "enableCircuitBreaker": False}},
        "response": {"verified": True, "kind": "response", "status": 200,
                     "url": "https://api.github.com/meta", "headersCount": 0, "bodyBytes": 0,
                     "responseKeys": ["bodyBase64", "headers", "kind", "status", "statusText", "url"]},
    }
    original = value["transport"]["configSha256"]
    value["transport"]["configSha256"] = "0" * 64
    approval.write_text(json.dumps(value))
    with pytest.raises(ProofError, match="TLS transport unproven"):
        prepare(tmp_path, tmp_path / "modified", model="mai-code-2", approval=approval)
    value["transport"]["configSha256"] = original
    approval.write_text(json.dumps(value))
    prepare(tmp_path, tmp_path / "reserved", model="mai-code-2", approval=approval)
    with pytest.raises(FileExistsError):
        prepare(tmp_path, tmp_path / "retry", model="mai-code-2", approval=approval)


def test_native_https_union_fails_closed():
    script = """
import {verifiedPublicHttps} from './benchmarks/michael/local_transport/limits.mjs';
import assert from 'node:assert/strict';
const good={kind:'response',status:200,statusText:'OK',url:'https://api.github.com/meta',
            headers:[{name:'content-type',value:'application/json'}],bodyBase64:''};
assert.equal(verifiedPublicHttps(good),true);
for(const bad of [null,'ok',{}, {kind:'failed'},{kind:'proxy-response',status:200},
    {kind:'circuit-breaker'}, {kind:'response',status:200},
    {...good,status:'200'}, {...good,status:302}, {...good,url:'http://api.github.com/meta'},
    {...good,bodyBase64:'AA=='}, {...good,headers:[{name:'x',value:3}]},
    {...good,httpError:{}}, {...good,unexpected:true}])
    assert.equal(verifiedPublicHttps(bad),false);
"""
    subprocess.run(["node", "--input-type=module", "-e", script],
                   cwd=ROOT, check=True, timeout=5)


def test_first_failure_cutoff_replays_retained_native_canary_events():
    import tarfile
    types = {"model.call_failure", "model.model_call_failure", "model.turn_retry", "assistant.turn_retry"}

    def walk(value):
        if isinstance(value, dict):
            if value.get("type") in types:
                yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)

    fixtures = []
    with tarfile.open(HERE / "integrated-evidence.tar.gz") as archive:
        for member in archive.getmembers():
            if not member.name.endswith("terminal-safe.json"):
                continue
            retained = json.load(archive.extractfile(member))
            if retained.get("requestedModel") in ("mai-code-2", "claude-sonnet-5.5"):
                events = list(walk(retained))
                assert events and any(event["type"] == "model.call_failure" for event in events)
                fixtures.append({"model": retained["requestedModel"], "events": events})
    assert len(fixtures) == 2
    script = """
import {nativeFailure} from './benchmarks/michael/local_transport/limits.mjs';
import assert from 'node:assert/strict';
for(const fixture of JSON.parse(process.argv[1])) {
    let calls=0, stopped=false;
    for(const event of fixture.events) {
        if(stopped) continue;
        calls++;
        stopped=Boolean(nativeFailure(event,fixture.model));
    }
    assert.equal(stopped,true); assert.equal(calls,1);
}
"""
    subprocess.run(["node", "--input-type=module", "-e", script, json.dumps(fixtures)],
                   cwd=ROOT, check=True, timeout=5)


def test_protocol_fragmentation_limits_and_first_failure():
    script = """
import {Protocol,PROTOCOL} from './benchmarks/michael/local_transport/protocol.mjs';
import {nativeFailure} from './benchmarks/michael/local_transport/limits.mjs';
import assert from 'node:assert/strict';
const frame=m=>{const b=Buffer.from(JSON.stringify(m));return Buffer.concat([
    Buffer.from(`Content-Length: ${b.length}\\r\\n\\r\\n`),b]);};
const frames=[{jsonrpc:'2.0',method:'one',text:'é'},
              {jsonrpc:'2.0',method:'two',text:'x'.repeat(90000)}].map(frame);
const all=Buffer.concat(frames);
for(const size of [1,2,7,31,65536,all.length]) {
    const got=[], p=new Protocol(m=>got.push(m));
    for(let i=0;i<all.length;i+=size)p.feed(all.subarray(i,i+size));
    p.finish();assert.equal(got.length,2);assert.equal(p.total,all.length);
}
const message={jsonrpc:'2.0',method:'ok'}, f=frame(message), n=JSON.stringify(message).length;
const exact={...PROTOCOL,frame:n,total:f.length,events:1};
const p=new Protocol(()=>{},exact);p.feed(f);p.finish();
assert.throws(()=>p.feed(Buffer.from('x')),/total_overflow/);
assert.throws(()=>new Protocol(()=>{},{...PROTOCOL,frame:n-1}).feed(f),/frame_denied/);
assert.throws(()=>new Protocol(()=>{},{...PROTOCOL,events:1}).feed(Buffer.concat([f,f])),/event_overflow/);
const full=frame({...message,text:'x'.repeat(PROTOCOL.frame-JSON.stringify({...message,text:''}).length)});
const max=new Protocol(()=>{});max.feed(full);max.finish();
assert.throws(()=>new Protocol(()=>{}).feed(frame({...message,text:'x'.repeat(PROTOCOL.frame)})),/frame_denied/);
const many=new Protocol(()=>{});many.feed(Buffer.concat(Array(PROTOCOL.events).fill(f)));many.finish();
assert.throws(()=>many.feed(f),/event_overflow/);
const header=new Protocol(()=>{});
header.feed(Buffer.alloc(PROTOCOL.header,120));
assert.throws(()=>header.feed(Buffer.from('x')),/header_overflow/);
assert.throws(()=>new Protocol(()=>{}).feed(Buffer.from([0xc3,0x6f,0x6e,0x74,13,10,13,10])),/frame_denied/);
for(const value of ['x'.repeat(PROTOCOL.header+1),'Content-Length: 0\\r\\n\\r\\n',
    'Content-Length: 99999999999999999999\\r\\n\\r\\n','Content-Length: -1\\r\\n\\r\\n',
    'Content-Length: 2\\r\\n\\r\\n[]','Content-Length: 2\\r\\n\\r\\n{}',
    'Content-Length: 2\\r\\n\\r\\nxx'])assert.throws(()=>new Protocol(()=>{}).feed(Buffer.from(value)));
for(const value of ['Content-L','Content-Length: 99\\r\\n\\r\\n{}']) {
    const q=new Protocol(()=>{});q.feed(Buffer.from(value));assert.throws(()=>q.finish(),/truncated/);
}
const seen=[], q=new Protocol(m=>{seen.push(m.type);return !nativeFailure(m,'synthetic');});
q.feed(Buffer.concat(['model.call_failure','model.turn_retry'].map(type=>frame({jsonrpc:'2.0',type}))));
assert.deepEqual(seen,['model.call_failure']);assert.equal(q.halted,true);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT, check=True, timeout=10)


@pytest.mark.parametrize("variant,expected", [
    ({}, "diagnostics_complete"), ({"fragment": 7}, "diagnostics_complete"),
    ({"failure": True}, "native_model_failure:model.call_failure"),
    ({"duplicate": True}, "broker:duplicate_or_invalid_action"),
    ({"sideChannel": True}, 'runtime:diagnostic_failed:{"resultType":"side_channel_denied"}'),
    ({"taskOverflow": True}, "output_overflow:task-2-stdout"),
])
def test_actual_owner_broker_with_labeled_synthetic_sdk(tmp_path, variant, expected):
    import shutil
    run = prepare(tmp_path, tmp_path / "run", seconds=3, diagnostics=(
        {"op": "write", "path": "candidate.py", "data": "print(2+3)"},
        {"op": "run", "path": "candidate.py"}))
    for name in ("synthetic_sdk.mjs", "protocol.mjs"):
        shutil.copyfile(HERE / name, tmp_path / name)
    (tmp_path / "fixture.json").write_text(json.dumps(variant))
    config = json.loads((run / "config.json").read_text())
    config["sdk"] = str(tmp_path / "synthetic_sdk.mjs")
    (run / "config.json").write_text(json.dumps(config))
    child = runner.launch(run)
    try:
        child.wait(timeout=10)
    finally:
        child.stdin.close()
    terminal = json.loads((run / "receipt/terminal.json").read_text())
    assert terminal["stopReason"] == expected
    assert terminal["nativePrompts"] == 0 and terminal["wholeProcessQuiescent"] is True
    assert terminal["protocolBytes"] > 65536
    assert terminal["protocolCondition"]["condition"] == "MB-006g-offline"
    if expected == "diagnostics_complete":
        assert terminal["actions"] == ["synthetic-1", "synthetic-2"]
        result = json.loads((run / "receipt/action-result-2.json").read_text())["result"]
        assert base64.b64decode(result["stdout"]) == b"5\n"
        assert any(item["message"].get("params", {}).get("event", {}).get("type") == "session.idle"
                   for item in terminal["messages"])
    assert not (tmp_path / "mb006f").exists()
