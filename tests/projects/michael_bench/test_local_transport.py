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
from proof import LIMIT, ProofError, capture, environment, fixture, recover


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
