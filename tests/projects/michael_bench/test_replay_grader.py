"""MB-006j integration/cloud-linux: real Docker, no evaluated source on host."""

import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import types
import time
import unittest
import uuid

import pytest

GRADER = Path(__file__).resolve().parents[3] / "benchmarks" / "michael" / "replay_grader"
sys.path.insert(0, str(GRADER))
import api
from policy import cases

packages = api.packages


def test_owner_registration_preserves_linux_ticks_and_honest_macos_unknown(monkeypatch):
    import owner
    monkeypatch.setattr(owner.sys, "platform", "darwin")
    assert owner.identity() == {"process_start_ticks": None,
                                "process_identity_kind": "unknown-no-pid-signals", "platform": "darwin"}
    monkeypatch.setattr(owner.sys, "platform", "linux")
    monkeypatch.setattr(owner.Path, "read_text", lambda *_: "1 (name with spaces) " + " ".join(
        str(i) for i in range(25)))
    assert owner.identity()["process_start_ticks"] == "19"


def fault_grade(source, directory):
    """Direct trusted-worker failure injection; candidate still runs only in Docker."""
    directory.mkdir()
    api.persist(directory / "start.json", {"run_id": uuid.uuid4().hex})
    return api._grade(source, directory)


@pytest.fixture(scope="module")
def calibration(tmp_path_factory):
    root = tmp_path_factory.mktemp("replay")
    sources = {"base": packages.agent_files("validator")[packages.CASES["validator"]["source"]],
               "reference": packages.verifier_files("validator")["reference"]}
    return {name: api.grade(source, root / name) for name, source in sources.items()}


def test_exact_calibration_and_receipts(calibration):
    for name, expected in [("base", (15, 7)), ("reference", (15, 10))]:
        report = calibration[name]
        assert report["status"] == "graded", report
        assert report["verdict"] == ("fail" if name == "base" else "pass")
        assert report["counts"] == {"preservation": {"passed": expected[0], "total": 15},
                                     "regression": {"passed": expected[1], "total": 10}}
        assert len(report["assertions"]) == 25
        assert report["cleanup"]["proven"] and not api.owned(report["run_id"])
        assert all(value > 0 for value in report["timings"].values())
        assert report["bindings"]["package_sha256"] == packages.bundle_digest(packages.agent_files("validator"))
        assert report["bindings"]["verifier_policy_sha256"]
        assert report["candidate_archive_sha256"] and report["image_id"].startswith("sha256:")
        assert report["containment"]["NetworkMode"] == "none"
        assert not report["containment"]["Binds"]
        assert not report["candidate_state"]["Running"]


@pytest.mark.parametrize("name", ["base", "reference"])
def test_original_assertions_against_observations(name, calibration, tmp_path, monkeypatch):
    """Run *trusted original tests* against an RPC-result proxy, not candidate code.

    This checks every translated clause and fixture against the hash-bound tests.
    No original assertion code ever goes into a candidate container.
    """
    report = calibration[name]
    assert report["status"] == "graded", report
    rows = cases()
    observed = [a["observed"] for a in report["assertions"]]
    proxy = types.ModuleType("agents_md")
    proxy.REPO_ROOT = tmp_path
    proxy.AGENTS_MD = tmp_path / "AGENTS.md"
    proxy.AGENTS_MD.write_text(".github/agents/\n")

    def lookup(op, text, path=""):
        matches = [i for i, row in enumerate(rows)
                   if row["probe"] == {"op": op, "text": text, "path": path}]
        assert len(matches) == 1, (op, text, path)
        return copy.deepcopy(observed[matches[0]])

    proxy.parse_frontmatter = lambda text: lookup("parse", text)
    proxy.check_agent_profile = lambda path, errors: errors.extend(lookup("profile", path.read_text(), path.name))
    proxy.check_skill = lambda path, errors: errors.extend(
        lookup("skill", path.read_text(), f"{path.parent.name}/{path.name}"))
    proxy.check_agents_md = lambda errors: errors.extend(lookup(
        "agents", proxy.AGENTS_MD.read_text() if proxy.AGENTS_MD.exists() else None, "AGENTS.md"))
    monkeypatch.setitem(sys.modules, "agents_md", proxy)
    hidden = packages.verifier_files("validator")
    namespace = {"__file__": str(tmp_path / "tests/validators/test_agents_md.py")}
    saved_path = sys.path[:]
    try:
        exec(compile(hidden["preservation"], "original-preservation", "exec"), namespace)
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(value)
                                   for value in namespace.values()
                                   if isinstance(value, type) and issubclass(value, unittest.TestCase))
        original_ids = {f"{packages.CASES['validator']['preservation']}::{test.__class__.__name__}::{test._testMethodName}"
                        for group in suite for test in group}
        assert original_ids == {row["original_id"] for row in rows[:15]}
        result = unittest.TestResult()
        suite.run(result)
        assert result.testsRun == 15 and not result.errors and not result.failures
        namespace = {"__file__": str(tmp_path / "tests/validators/test_regression.py")}
        exec(compile(hidden["regression"], "original-regression", "exec"), namespace)
        ids, passed = [], []
        for node in ast.parse(hidden["regression"]).body:
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            parameters = [None]
            if node.decorator_list:
                parameters = ast.literal_eval(node.decorator_list[0].args[1])
            for index, parameter in enumerate(parameters):
                work = tmp_path / f"{node.name}-{index}"
                work.mkdir()
                kwargs = {}
                if node.args.args:
                    kwargs = {"tmp_path": work, "monkeypatch": monkeypatch}
                if parameter is not None:
                    kwargs["extra"] = parameter
                suffix = "[" + parameter.replace("\n", "\\n") + "]" if parameter is not None else ""
                ids.append(f"tests/validators/test_regression.py::{node.name}{suffix}")
                try:
                    namespace[node.name](**kwargs)
                except AssertionError:
                    passed.append(False)
                else:
                    passed.append(True)
        regression = report["assertions"][15:]
        assert ids == [row["original_id"] for row in regression]
        assert passed == [row["passed"] for row in regression]
    finally:
        sys.path[:] = saved_path


@pytest.mark.parametrize("attack,error", [
    ("print('PASS 25/25'); raise SystemExit(0)", "missing_or_extra"),
    ("import os; os._exit(0)", "truncated"),
    ("import os; os.write(1,b'x'*200000)", "output_overflow"),
    ("import sys; sys.stderr.write('x'*200000)", "output_overflow"),
    ("while True: pass", "timeout"),
    ("import os,time\nif os.fork() == 0: time.sleep(60)\ntime.sleep(60)", "timeout"),
    ("x=bytearray(300_000_000)", "candidate_oom"),
    ("from pathlib import Path\nPath('/app/verdict.json').write_text('PASS')", "candidate_exit"),
    ("from pathlib import Path\nPath('/var/run/docker.sock').read_bytes()", "candidate_exit"),
    ("from pathlib import Path\nPath('/work/forged-summary.json').write_text('{\"passed\":25}')\n"
     "print('{\"id\":0,\"value\":[]}'); raise SystemExit(0)", "missing_or_extra"),
])
def test_hostile_candidates_ungraded_and_clean(attack, error, tmp_path):
    report = api.grade(attack.encode(), tmp_path / "receipt", seconds=2)
    assert report["status"] == "ungraded" and report["verdict"] is None, report
    assert error in report["error"], report
    assert report["counts"] is None
    assert report["cleanup"]["proven"] and len(report["cleanup"]["removed"]) == 1
    assert not api.owned(report["run_id"])
    assert api.recover(tmp_path / "receipt") == {"removed": [], "remaining": [], "proven": True}


def test_all_empty_errors_cannot_fabricate_success(tmp_path):
    attack = ("import json\n"
              "for i in range(25): print(json.dumps({'id':i,'value':None if i<4 or i==24 else []}))\n"
              "raise SystemExit(0)\n")
    report = api.grade(attack.encode(), tmp_path / "receipt")
    assert report["status"] == "graded" and report["verdict"] == "fail"
    assert sum(v["passed"] for v in report["counts"].values()) < 25


def test_candidate_cannot_read_or_tamper_with_verifier(tmp_path, monkeypatch):
    monkeypatch.setenv("MB_GRADER_SYNTHETIC_SECRET", "synthetic-only")
    protected = tmp_path / "trusted-verdict.json"
    protected.write_text("unchanged")
    source = (
        "import os,socket\nfrom pathlib import Path\n"
        f"for p in ({str(protected)!r},{str(api.HERE)!r},"
        "'/root/.ssh','/root/.aws','/var/run/docker.sock','/work/.git'):\n"
        " try: assert not Path(p).exists()\n"
        " except PermissionError: pass\n"
        "assert 'MB_GRADER_SYNTHETIC_SECRET' not in os.environ\n"
        "try: socket.create_connection(('192.0.2.1',443),timeout=.1)\n"
        "except OSError: pass\nelse: raise RuntimeError('network available')\n"
        f"try: Path({str(protected)!r}).write_text('PASS')\n"
        "except (FileNotFoundError,PermissionError): pass\n"
        "else: raise RuntimeError('trusted file writable')\n")
    source += f"exec({packages.verifier_files('validator')['reference']!r})\n"
    report = api.grade(source.encode(), tmp_path / "receipt")
    assert report["verdict"] == "pass" and report["cleanup"]["proven"], report
    assert protected.read_text() == "unchanged"


@pytest.mark.parametrize("mutate,error", [
    (lambda lines: lines[:-1], "missing_or_extra"),
    (lambda lines: lines + lines[:1], "missing_or_extra"),
    (lambda lines: [lines[0]] * 25, "duplicate_observation_id"),
    (lambda lines: [b'{"id":0,"id":0,"value":null}'] + lines[1:], "duplicate observation key"),
    (lambda lines: [b"PASS"] + lines[1:], "malformed"),
    (lambda lines: [b'{"id":true,"value":null}'] + lines[1:], "invalid_or_duplicate"),
    (lambda lines: [b'{"id":0,"value":NaN}'] + lines[1:], "invalid_observation_value"),
    (lambda lines: [b" " * 9000] + lines[1:], "frame_overflow"),
])
def test_framing_rejects_spoofs(mutate, error):
    lines = [api.encoded({"id": i, "value": None}).rstrip() for i in range(25)]
    with pytest.raises(api.GraderError, match=error):
        api.observations(b"\n".join(mutate(lines)) + b"\n", cases())


def test_evaluator_failure_and_budget_limits(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        api.grade(b"x" * (api.SOURCE_LIMIT + 1), tmp_path / "too-big")
    for seconds in (float("nan"), float("inf"), 0, 31):
        with pytest.raises(ValueError):
            api.grade(b"pass", tmp_path / "bad-time", seconds=seconds)
    with pytest.raises(ValueError):
        api.cleanup("not-an-owned-uuid")
    monkeypatch.setattr(api, "clause_passes", lambda *_: (_ for _ in ()).throw(ValueError("evaluator fault")))
    report = fault_grade(packages.verifier_files("validator")["reference"], tmp_path / "evaluator")
    assert report["status"] == "ungraded" and report["verdict"] is None
    assert "evaluator fault" in report["error"] and report["cleanup"]["proven"]
    assert json.loads((tmp_path / "evaluator/report.json").read_bytes()) == report


def test_recovery_removes_only_persisted_owner(tmp_path):
    first, other = uuid.uuid4().hex, uuid.uuid4().hex
    (tmp_path / "start.json").write_bytes(api.encoded({"run_id": first}))
    try:
        for owner in (first, other):
            api.docker("create", "--label", f"{api.LABEL}={owner}", "--network", "none",
                       "--read-only", api.IMAGE, "python", "-c", "raise RuntimeError('never start')")
        assert len(api.recover(tmp_path)["removed"]) == 1
        assert not api.owned(first) and len(api.owned(other)) == 1
        assert api.recover(tmp_path)["removed"] == []
    finally:
        api.cleanup(first)
        api.cleanup(other)


def test_unproven_cleanup_cannot_authorize_success(tmp_path, monkeypatch):
    real_cleanup = api.cleanup

    def failed_proof(owner):
        real_cleanup(owner)
        raise api.GraderError("synthetic cleanup proof failure")

    monkeypatch.setattr(api, "cleanup", failed_proof)
    report = fault_grade(packages.verifier_files("validator")["reference"], tmp_path / "receipt")
    assert report["status"] == "ungraded" and report["verdict"] is None
    assert not report["cleanup"]["proven"] and not api.owned(report["run_id"])


def test_corrupt_owner_terminal_cannot_prove_recovery(tmp_path):
    directory = tmp_path / "receipt"
    report = api.grade(packages.verifier_files("validator")["reference"], directory)
    assert report["verdict"] == "pass"
    api.persist(directory / "terminal.json", {})
    with pytest.raises(api.GraderError, match="unproven"):
        api.recover(directory)


def wait_for(predicate, seconds=10):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        time.sleep(.025)
    raise AssertionError("bounded fixture wait expired")


@pytest.mark.parametrize("stage", ["create", "running", "deadline", "owner-loss"])
def test_independent_owner_survives_controller_loss(stage, tmp_path):
    import signal

    directory = tmp_path / "receipt"
    source = b"import os\nos.fork()\nwhile True: pass\n"
    code = (
        "from pathlib import Path\n"
        "from benchmarks.michael.replay_grader import api\n"
        f"api.grade({source!r},Path({str(directory)!r}),seconds=3)\n")
    other = uuid.uuid4().hex
    api.docker("create", "--label", f"{api.LABEL}={other}", "--network", "none",
               api.IMAGE, "python", "--version")
    environment = os.environ.copy()
    if stage == "create":
        wrapper = tmp_path / "docker"
        wrapper.write_text(
            f"#!{sys.executable}\nimport subprocess,sys,time\nfrom pathlib import Path\n"
            f"code=subprocess.call([{shutil.which('docker')!r},*sys.argv[1:]])\n"
            f"if sys.argv[1]=='create':\n Path({str(tmp_path / 'created')!r}).touch()\n time.sleep(.5)\n"
            "raise SystemExit(code)\n")
        wrapper.chmod(0o700)
        environment["PATH"] = str(tmp_path) + os.pathsep + environment["PATH"]
    controller = subprocess.Popen([sys.executable, "-c", code], env=environment,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run_id = None
    try:
        wait_for(lambda: (directory / "owner.json").exists())
        run_id = json.loads((directory / "start.json").read_bytes())["run_id"]
        owner = json.loads((directory / "owner.json").read_bytes())
        assert owner["state"] == "registered_before_create"
        if stage == "create":
            wait_for(lambda: (tmp_path / "created").exists())
        cid = wait_for(lambda: api.owned(run_id))
        if stage != "create":
            wait_for(lambda: json.loads(api.docker("inspect", cid[0]))[0]["State"]["Running"])
            wait_for(lambda: len(api.docker("top", cid[0], "-eo", "pid").splitlines()) >= 3)
        if stage == "owner-loss":
            # pidfd binds this recorded live process, never a guessed/reused PID.
            fd = os.pidfd_open(owner["pid"])
            try:
                assert Path(f"/proc/{owner['pid']}/stat").read_text().rsplit(")", 1)[1].split()[19] == owner["process_start_ticks"]
                signal.pidfd_send_signal(fd, signal.SIGKILL)
            finally:
                os.close(fd)
            controller.wait(timeout=10)
            report = json.loads((directory / "report.json").read_bytes())
            assert report["verdict"] is None and not report["cleanup"]["proven"]
            with pytest.raises(api.GraderError, match="unproven"):
                api.recover(directory)
        else:
            began = time.monotonic()
            if stage == "deadline":
                controller.send_signal(signal.SIGSTOP)
            else:
                controller.kill()
                controller.wait(timeout=5)
            wait_for(lambda: (directory / "terminal.json").exists())
            assert time.monotonic() - began < 5
            report = json.loads((directory / "report.json").read_bytes())
            assert report["verdict"] is None and report["cleanup"]["proven"], report
            assert ("timeout" if stage == "deadline" else "controller_lost") in report["error"], report
            # No recover() call has occurred: the independent owner removed it.
            assert not api.owned(run_id)
        assert len(api.owned(other)) == 1
        api.persist(directory / "controller-loss-proof.json", {
            "fixture": stage, "controller_pid": controller.pid,
            "controller_returncode": controller.poll(), "owner": owner,
            "candidate_run_id": run_id, "candidate_remaining": api.owned(run_id),
            "independent_stop_seconds": time.monotonic() - began if stage != "owner-loss" else None,
            "termination_required_recover": stage == "owner-loss",
            "unrelated_owner_preserved": len(api.owned(other)) == 1})
    finally:
        if controller.poll() is None:
            controller.kill()
            controller.wait()
        if run_id:
            api.cleanup(run_id)
        api.cleanup(other)


# --- MB-008: TypeScript replays (grouping, status) in the Node 24 sandbox ---------------
import specs  # noqa: E402


@pytest.mark.parametrize("task,base,total", [
    ("grouping", {"preservation": 4, "regression": 0}, {"preservation": 4, "regression": 2}),
    ("status", {"preservation": 32, "regression": 0}, {"preservation": 32, "regression": 8}),
])
def test_typescript_replays_match_original_vitest_calibration(task, base, total, tmp_path):
    retained = json.loads((packages.HERE / task / "calibration.json").read_text())
    vitest_failures = {f["name"] for f in retained["phases"][1]["failures"]}
    for label, source in (("base", specs.base(task)), ("reference", specs.reference(task))):
        report = api.grade(source, tmp_path / label, task=task)
        assert report["status"] == "graded", report
        expected = base if label == "base" else {g: n for g, n in total.items()}
        assert {g: c["passed"] for g, c in report["counts"].items()} == expected
        assert {g: c["total"] for g, c in report["counts"].items()} == total
        assert report["containment"]["NetworkMode"] == "none" and not report["containment"]["Binds"]
        assert report["cleanup"]["proven"] and not api.owned(report["run_id"])
        failed = {a["original_id"] for a in report["assertions"] if not a["passed"]}
        # Same failing set as the original vitest run on the trusted host baseline.
        assert failed == (vitest_failures if label == "base" else set())


@pytest.mark.parametrize("attack,error", [
    ("export const x = 1; process.stdout.write('PASS\\n');", "missing_or_extra"),
    ("while (true) {}", "timeout"),
    ("const n = await import('node:net'); await new Promise((ok, no) => "
     "n.connect(443, '192.0.2.1').on('error', no).on('connect', ok)); export {};", "candidate_exit"),
    ("import {readFileSync} from 'node:fs'; readFileSync('/var/run/docker.sock'); export {};", "candidate_exit"),
])
def test_typescript_hostile_candidates_ungraded_and_clean(attack, error, tmp_path):
    report = api.grade(attack.encode(), tmp_path / "receipt", seconds=3, task="grouping")
    assert report["status"] == "ungraded" and report["verdict"] is None, report
    assert error in report["error"], report
    assert report["cleanup"]["proven"] and not api.owned(report["run_id"])


def test_typescript_archive_carries_no_assertions(monkeypatch, tmp_path):
    captured = {}
    real = api.command

    def spy(args, **kwargs):
        if args[:3] == ["docker", "start", "-ai"]:
            captured["payload"] = kwargs["payload"]
        return real(args, **kwargs)

    monkeypatch.setattr(api, "command", spy)
    directory = tmp_path / "receipt"
    directory.mkdir()
    api.persist(directory / "start.json", {"run_id": uuid.uuid4().hex, "task": "status"})
    report = api._grade(specs.reference("status"), directory)
    assert report["verdict"] == "pass"
    payload = captured["payload"]
    for row in specs.spec("status")["rows"]():
        assert row["original_id"].encode() not in payload
    assert b"path_equal" not in payload and b"clauses" not in payload
