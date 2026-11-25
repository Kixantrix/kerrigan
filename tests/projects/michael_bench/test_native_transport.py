"""AC-MB-002/003/004: integration, cloud-linux; real Docker, fake transport only."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import pytest

TRANSPORT = Path(__file__).resolve().parents[3] / "benchmarks" / "michael" / "native_transport"
sys.path.insert(0, str(TRANSPORT))
from broker import BoundaryError, IMAGE, LIMIT, action, capture, create, docker, remove
from native import MODELS, fixture
from supervisor import recover, run


@pytest.fixture
def sandbox(tmp_path):
    run_id = uuid.uuid4().hex
    until = time.monotonic() + 90
    info = create(run_id, until)
    (tmp_path / "isolation.json").write_text(json.dumps(info, indent=2))
    try:
        yield run_id, tmp_path, until
    finally:
        (tmp_path / "cleanup.json").write_text(json.dumps(remove(run_id, time.monotonic() + 15)))


def call(sandbox, identity, op, **args):
    run_id, directory, until = sandbox
    return action(run_id, directory, {"action_id": identity, "op": op, **args}, until)


def test_actual_sandbox_is_answer_free_network_denied_and_resource_bounded(sandbox):
    run_id, directory, until = sandbox
    info = json.loads((directory / "isolation.json").read_text())["inspect"]
    assert info["Config"]["Image"] == IMAGE
    assert info["Mounts"] == []
    config = info["HostConfig"]
    assert config["NetworkMode"] == "none" and config["ReadonlyRootfs"]
    assert config["MemorySwap"] == config["Memory"] == 256 * 1024 * 1024
    assert config["PidsLimit"] == 64 and config["NanoCpus"] == 1000000000
    assert call(sandbox, "base", "read", path="solution.py")["stdout"].endswith("NotImplementedError\n")
    program = (
        "import os,socket\nfrom pathlib import Path\n"
        "assert os.getuid()==65534\n"
        "assert sorted(p.name for p in Path('/work').iterdir())==['REQUIREMENT.txt','solution.py']\n"
        "assert not Path('/var/run/docker.sock').exists()\n"
        "try:\n Path('/root/.copilot/settings.json').read_text()\n"
        "except (PermissionError,FileNotFoundError):\n print('home-denied')\n"
        "else:\n raise AssertionError('home escaped')\n"
        "assert not any('TOKEN' in k or 'SECRET' in k for k in os.environ)\n"
        "try:\n Path('/work/extra.py').write_text('escape')\n"
        "except PermissionError:\n print('write-denied')\n"
        "else:\n raise AssertionError('write escaped')\n"
        "s=socket.socket();s.settimeout(1)\n"
        "try:\n s.connect(('192.0.2.1',443))\n"
        "except OSError as e:\n print('network-denied',e.errno)\n"
        "else:\n raise AssertionError('network escaped')\n"
    )
    call(sandbox, "write", "write", path="solution.py", content=program)
    result = call(sandbox, "probe", "run")
    assert "write-denied" in result["stdout"] and "network-denied" in result["stdout"]
    assert "home-denied" in result["stdout"]


@pytest.mark.parametrize("op,args,error", [
    ("read", {"path": "/etc/passwd"}, "path denied"),
    ("read", {"path": "../solution.py"}, "path denied"),
    ("write", {"path": "REQUIREMENT.txt", "content": "tamper"}, "write denied"),
    ("network", {"url": "https://example.com"}, "invalid action schema"),
    ("write", {"path": "solution.py", "content": "x" * 8193}, "input_overflow"),
])
def test_actual_broker_rejects_nonallowlisted_actions(sandbox, op, args, error):
    with pytest.raises(BoundaryError, match=error):
        call(sandbox, "denied", op, **args)
    with pytest.raises(BoundaryError, match="duplicate"):
        call(sandbox, "denied", "read", path="solution.py")


def test_recovered_started_action_is_not_replayed(sandbox):
    run_id, directory, until = sandbox
    journal = directory / "actions.jsonl"
    journal.write_text('{"action_id":"started","state":"started"}\n')
    before = journal.read_bytes()
    with pytest.raises(BoundaryError, match="no replay"):
        call(sandbox, "started", "write", path="solution.py", content="not executed")
    assert journal.read_bytes() == before


@pytest.mark.parametrize("channel", [1, 2])
def test_actual_broker_overflow_stops_sandbox(sandbox, channel):
    call(sandbox, "write", "write", path="solution.py",
         content=f"import os\nwhile True:\n os.write({channel},b'x'*8192)\n")
    with pytest.raises(BoundaryError, match="output_overflow"):
        call(sandbox, "overflow", "run")
    run_id, directory, until = sandbox
    rejected = json.loads((directory / "actions.jsonl").read_text().splitlines()[-1])
    assert max(rejected["capture"]["retained_bytes"].values()) == LIMIT
    info = json.loads(docker("inspect", f"mb-native-{run_id}", until=until))[0]
    assert not info["State"]["Running"]


def test_stdio_mcp_exact_inventory_and_actual_broker_execution(sandbox):
    run_id, directory, until = sandbox
    requests = [
        {"id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}},
        {"id": 2, "method": "tools/list"},
        {"id": 3, "method": "tools/call", "params": {"name": "action", "arguments": {
            "action_id": "read", "op": "read", "path": "solution.py"}}},
        {"id": 4, "method": "tools/call", "params": {"name": "read_file", "arguments": {}}},
    ]
    data = "".join(json.dumps({"jsonrpc": "2.0", **r}) + "\n" for r in requests).encode()
    result = capture([sys.executable, str(TRANSPORT / "broker.py"), run_id, str(directory),
                      str(until)], until, data)
    responses = [json.loads(line) for line in result["stdout"].splitlines()]
    assert [t["name"] for t in responses[1]["result"]["tools"]] == ["action"]
    assert "NotImplementedError" in responses[2]["result"]["content"][0]["text"]
    assert "denied" in responses[3]["error"]["message"]
    (directory / "mcp-receipt.json").write_text(json.dumps(responses, indent=2))


@pytest.mark.parametrize("mode,reason", [
    ("success", "completed"), ("timeout", "timeout"),
    ("overflow", "output_overflow:stdout"), ("failure", "runtime_error"),
])
def test_external_supervisor_limits_and_durable_start(tmp_path, mode, reason):
    driver = tmp_path / "driver.py"
    driver.write_text(
        "import json,os,sys,time\nfrom pathlib import Path\n"
        "d=Path(sys.argv[1]);assert (d/'start.json').exists()\n"
        "assert (d/'sandbox.json').exists()\n"
        + {"success": (
            "import subprocess\n"
            "requests=[{'id':1,'method':'tools/list'},"
            "{'id':2,'method':'tools/call','params':{'name':'action','arguments':"
            "{'action_id':'read','op':'read','path':'solution.py'}}},"
            "{'id':3,'method':'tools/call','params':{'name':'action','arguments':"
            "{'action_id':'write','op':'write','path':'solution.py',"
            "'content':'def double(n):\\n return n*2\\nprint(double(13))\\n'}}},"
            "{'id':4,'method':'tools/call','params':{'name':'action','arguments':"
            "{'action_id':'run','op':'run'}}}]\n"
            f"p=subprocess.run([sys.executable,{str(TRANSPORT / 'broker.py')!r},"
            "sys.argv[2],str(d),sys.argv[3]],input=''.join(json.dumps(r)+'\\n' for r in requests),"
            "text=True,capture_output=True,timeout=10)\n"
            "assert p.returncode==0,p.stderr\n"
            "responses=[json.loads(line) for line in p.stdout.splitlines()]\n"
            "assert [t['name'] for t in responses[0]['result']['tools']]==['action']\n"
            "assert json.loads(responses[-1]['result']['content'][0]['text'])['stdout']=='26\\n'\n"
            "(d/'fake-mcp.json').write_text(json.dumps(responses))\nprint(p.stdout)\n"
        ), "timeout": "time.sleep(60)\n",
           "overflow": "while True:\n os.write(1,b'x'*8192)\n",
           "failure": "raise RuntimeError('synthetic transport failure')\n"}[mode])
    directory = tmp_path / "evidence"
    receipt = run([sys.executable, str(driver), "{directory}", "{run_id}", "{deadline}"],
                  tmp_path, directory, seconds=2)
    assert receipt["stop_reason"] == reason and receipt["verdict"] == "ungraded"
    assert receipt["cleanup"]["sandbox"]["remaining"] == []
    assert receipt["cleanup"]["processes"]["remaining"] == {}
    assert receipt["cleanup_seconds"] <= 15
    assert len(json.loads((directory / "output.json").read_text())["stdout"].encode()) <= LIMIT
    assert recover(directory) == receipt


def wait_file(path, seconds=15):
    until = time.monotonic() + seconds
    while not path.exists():
        if time.monotonic() >= until:
            raise AssertionError(f"timed out waiting for {path.name}")
        time.sleep(0.02)


@pytest.mark.parametrize("signal_number,reason", [
    (signal.SIGTERM, "cancelled"), (signal.SIGKILL, "controller_lost"),
])
def test_cancellation_controller_loss_kills_detached_descendant_without_replay(
        tmp_path, signal_number, reason):
    driver = tmp_path / "driver.py"
    driver.write_text(
        "import subprocess,sys,time\nfrom pathlib import Path\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)\n"
        "Path(sys.argv[1],'child.pid').write_text(str(p.pid))\ntime.sleep(60)\n")
    directory = tmp_path / "evidence"
    controller = tmp_path / "controller.py"
    controller.write_text(
        f"import sys\nsys.path.insert(0,{str(TRANSPORT)!r})\nfrom supervisor import run\n"
        f"run([sys.executable,{str(driver)!r},'{{directory}}'],{str(tmp_path)!r},"
        f"{str(directory)!r},seconds=30)\n")
    process = subprocess.Popen([sys.executable, str(controller)], start_new_session=True)
    try:
        wait_file(directory / "child.pid")
        if signal_number == signal.SIGTERM:
            pid = json.loads((directory / "progress.json").read_text())["supervisor_pid"]
            os.kill(pid, signal_number)
        else:
            process.kill()
        wait_file(directory / "terminal.json")
        receipt = recover(directory)
        assert receipt["stop_reason"] == reason
        assert receipt["cleanup"]["sandbox"]["remaining"] == []
        child = directory.joinpath("child.pid").read_text()
        stat = Path(f"/proc/{child}/stat")
        assert not stat.exists() or stat.read_text().rsplit(")", 1)[1].split()[0] == "Z"
        assert recover(directory) == receipt
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)


@pytest.mark.parametrize("model", MODELS)
def test_model_pinned_fixture_is_session_owned_and_native_launch_is_gated(tmp_path, model):
    config = fixture(tmp_path / "fixture", model, uuid.uuid4().hex, tmp_path, time.monotonic() + 180)
    assert config["argv"][config["argv"].index("--model") + 1] == model
    profile = tmp_path / "fixture" / ".github" / "agents" / "mb-canary.agent.md"
    assert "model-policy: required" in profile.read_text() and "strict-tools-list: true" in profile.read_text()
    assert len(config["hashes"]) == 2 and config["effective_inventory"] == "unknown"
    with pytest.raises(BoundaryError, match="native launch gated"):
        run(config["argv"], tmp_path, tmp_path / "never-started", native=True)
    assert not (tmp_path / "never-started").exists()
    with pytest.raises(ValueError, match="unapproved"):
        fixture(tmp_path / "other", "fallback", uuid.uuid4().hex, tmp_path, 0)


def test_transport_rejects_checkout_and_unproven_recovery(tmp_path):
    with pytest.raises(BoundaryError, match="outside repository"):
        run([sys.executable, "-c", "raise AssertionError('must not execute')"],
            TRANSPORT, tmp_path / "forbidden")
    assert not (tmp_path / "forbidden").exists()
    pending = tmp_path / "pending"
    pending.mkdir()
    (pending / "start.json").write_text(json.dumps({"run_id": uuid.uuid4().hex}))
    with pytest.raises(BoundaryError, match="quiescence is unproven"):
        recover(pending)
    (pending / "terminal.json").write_text(json.dumps({"cleanup": {"remaining": []}}))
    with pytest.raises(BoundaryError, match="quiescence is unproven"):
        recover(pending)


def test_supervisor_loss_retains_start_when_detached_client_quiescence_is_unproven(tmp_path):
    driver = tmp_path / "driver.py"
    driver.write_text(
        "import json,os,subprocess,sys,time\nfrom pathlib import Path\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],"
        "start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
        "d=Path(sys.argv[1]);(d/'launches.txt').open('a').write('one-launch\\n')\n"
        "(d/'owned.json').write_text(json.dumps({'driver':os.getpid(),'child':p.pid}))\n"
        "time.sleep(60)\n")
    directory = tmp_path / "evidence"
    controller = tmp_path / "controller.py"
    controller.write_text(
        f"import ctypes,os,sys,time\nfrom pathlib import Path\nsys.path.insert(0,{str(TRANSPORT)!r})\n"
        "from supervisor import BoundaryError,run,terminate\n"
        "assert ctypes.CDLL(None).prctl(36,1,0,0,0)==0\n"
        "try:\n"
        f" try:\n  run([sys.executable,{str(driver)!r},'{{directory}}'],"
        f"{str(tmp_path)!r},{str(directory)!r},seconds=30)\n"
        " except BoundaryError as exc:\n"
        f"  Path({str(tmp_path / 'controller-error.json')!r}).write_text(str(exc))\n"
        " until=time.monotonic()+15\n"
        f" while not Path({str(tmp_path / 'release-cleanup')!r}).exists():\n"
        "  assert time.monotonic()<until\n  time.sleep(0.02)\n"
        "finally:\n terminate(time.monotonic()+5)\n"
        " while True:\n"
        "  try:\n"
        "   if os.waitpid(-1,os.WNOHANG)[0]==0:\n    break\n"
        "  except ChildProcessError:\n   break\n")
    process = subprocess.Popen([sys.executable, str(controller)], start_new_session=True)
    handles = []
    try:
        wait_file(directory / "owned.json")
        owned = json.loads((directory / "owned.json").read_text())
        watcher = json.loads((directory / "progress.json").read_text())["supervisor_pid"]
        for pid, parent in ((watcher, process.pid), (owned["driver"], watcher),
                            (owned["child"], owned["driver"])):
            path = Path(f"/proc/{pid}/stat")
            original = path.read_text().rsplit(")", 1)[1].split()
            assert int(original[1]) == parent
            fd = os.pidfd_open(pid)
            handles.append(fd)
            assert path.read_text().rsplit(")", 1)[1].split()[19] == original[19]
        signal.pidfd_send_signal(handles[0], signal.SIGKILL)
        wait_file(tmp_path / "controller-error.json")
        signal.pidfd_send_signal(handles[2], 0)
        start = (directory / "start.json").read_bytes()
        for _ in range(2):
            with pytest.raises(BoundaryError, match="quiescence is unproven"):
                recover(directory)
            assert not (directory / "terminal.json").exists()
            assert (directory / "start.json").read_bytes() == start
            assert (directory / "launches.txt").read_text() == "one-launch\n"
        receipt = json.loads((directory / "recovery.json").read_text())
        assert receipt["state"] == "quiescence_unproven"
        assert receipt["sandbox_cleanup"]["remaining"] == []
        signal.pidfd_send_signal(handles[2], 0)
    finally:
        (tmp_path / "release-cleanup").touch()
        try:
            process.wait(timeout=10)
        finally:
            for fd in handles:
                try:
                    signal.pidfd_send_signal(fd, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                os.close(fd)
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            if (directory / "start.json").exists():
                run_id = json.loads((directory / "start.json").read_text())["run_id"]
                remove(run_id, time.monotonic() + 15)
