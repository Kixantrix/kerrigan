"""MB-R3 AC-B2: public Harbor anchors converted to native curriculum packages.

Unit tests cover the converter's final-state contract bounding and the Harbor
verifier -> strict row adapter. Package tests check each converted anchor's
retained calibration (base fails, oracle passes, repeatable observations),
export, native policy and provenance; the fresh Docker re-grade runs only when
the anchor's verifier image is present (anchors_convert.py --build-only).
"""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from benchmarks.michael.curriculum import anchors_convert as convert
from benchmarks.michael.replay_grader import calibrate, harbor_adapter as adapter, specs
from benchmarks.michael.replay_grader.clauses import clause_passes
from benchmarks.michael.replay_trial import curriculum as native
from benchmarks.michael.tasks import curriculum, packages

HERE = Path(convert.HERE)
RECORD = json.loads((HERE / "anchors-native.json").read_text())
CONTRACTS = json.loads((HERE / "anchors-native-contracts.json").read_text())
ANCHORS = json.loads((HERE / "anchors.json").read_text())["anchors"]


# --- adapter: Harbor/pytest results -> strict rows ---------------------------------------

def _ctrf(*tests):
    return {"results": {"tool": {"name": "pytest"}, "tests": [{"name": n, "status": s} for n, s in tests]}}


def test_adapter_maps_pass_fail_error_skip_and_missing():
    assert [adapter.normalize(s) for s in ("passed", "failed", "skipped", "pending", "other", "weird", None)] == [
        "passed", "failed", "skipped", "skipped", "error", "error", "error"]
    table = adapter.rows(["test_a.py::ok", "test_a.py::bad", "test_b.py::skip", "test_b.py::err",
                          "test_b.py::lost"])
    probes = [row["probe"] for row in table]
    ctrf = _ctrf(("test_a.py::ok", "passed"), ("test_a.py::bad", "failed"), ("test_b.py::skip", "skipped"),
                 ("test_b.py::err", "other"), ("test_b.py::extra", "passed"))
    values = adapter.observe(ctrf, "0\n", probes)
    observed = {row["original_id"]: value for row, value in zip(table, values)}
    assert observed == {"tests/test_a.py::bad": "failed", "tests/test_a.py::ok": "passed",
                        "tests/test_b.py::err": "error", "tests/test_b.py::lost": "missing",
                        "tests/test_b.py::skip": "skipped", adapter.REWARD_ID: "0"}
    passed = {row["original_id"] for row, value in zip(table, values)
              if all(clause_passes(value, tuple(c)) for c in row["clauses"])}
    assert passed == {"tests/test_a.py::ok"}  # strict: skip, error, missing and reward 0 all fail
    assert adapter.denominators(table) == {"tests/test_a.py": 2, "tests/test_b.py": 3, adapter.REWARD_GROUP: 1}
    assert all(adapter.valid(row, value) for row, value in zip(table, values))
    assert not adapter.valid(table[0], "PASS") and not adapter.valid(table[-1], {"forged": True})


def test_adapter_fails_closed_on_missing_duplicate_or_malformed_reports():
    table = adapter.rows(["t.py::a"])
    probes = [row["probe"] for row in table]
    assert adapter.observe(None, None, probes) == ["missing", None]
    assert adapter.observe({"results": "x"}, " 1 \n", probes) == ["missing", "1"]
    assert adapter.observe(_ctrf(("t.py::a", "passed"), ("t.py::a", "passed")), "1", probes) == ["error", "1"]
    assert adapter.observe(_ctrf(("t.py::a", "passed")), "1", [{"kind": "discover"}]) == [[["t.py::a", "passed"]]]
    with pytest.raises(ValueError):
        adapter.rows(["t.py::a", "t.py::a"])
    with pytest.raises(ValueError):
        adapter.rows([])


# --- converter: bounded final-state contract ---------------------------------------------

def test_contract_paths_renames_and_reserved_names():
    renames = [["/app/site/.git/", "app/site-gitdir/"]]
    assert convert.agent_path("/app/site/.git/HEAD", renames) == "app/site-gitdir/HEAD"
    assert convert.agent_path("/etc/nginx/nginx.conf", renames) == "etc/nginx/nginx.conf"
    for bad in ("etc/x", "/etc/../x"):
        with pytest.raises(convert.ConversionError):
            convert.agent_path(bad, [])
    for path in ("/TASK.md", "/tests/x.py", "/anchor.json"):
        with pytest.raises(convert.ConversionError, match="reserved"):
            convert.artifact_contract({"artifacts": [{"path": path}]})
    with pytest.raises(convert.ConversionError, match="unique"):
        convert.artifact_contract({"artifacts": [{"path": "/a"}, {"path": "/a"}]})


def test_workspace_selection_is_bounded_and_recorded():
    members = {"ok.md": b"text", "big.css": b"x" * 40, "font.woff": b"\0\1", "obj/ab/cd": b"\x78\x01\0",
               ".gitignore": b"*.log\n", "link": None, "skip/me.txt": b"t"}
    kept, dropped = convert.select(members, {"root": "/w", "exclude": ["skip/*"], "binary_ok": ["obj/*"],
                                             "max_file_bytes": 32}, [])
    assert kept == {"w/ok.md": b"text", "w/obj/ab/cd": b"\x78\x01\0"}
    reasons = {item["path"]: item["reason"] for item in dropped}
    assert reasons["/w/big.css"].startswith("larger than") and reasons["/w/font.woff"] == "binary"
    assert reasons["/w/link"] == "not a regular file" and reasons["/w/skip/me.txt"] == "excluded"
    assert reasons["/w/.gitignore"].startswith("git control file")
    assert all(item["sha256"] == hashlib.sha256(members[item["path"][3:]]).hexdigest()
               for item in dropped if item["bytes"] is not None)
    kept, _ = convert.select(members, {"root": "/w", "include": ["ok.md"]}, [])
    assert kept == {"w/ok.md": b"text"}


def test_final_state_collection_is_exact_text_and_bounded():
    contract = convert.artifact_contract({"artifacts": [{"path": "/etc/a.conf"},
                                                        {"path": "/var/b.html", "absent_if_empty": True}]})
    assert convert.bounded_artifacts(contract, {"etc/a.conf": b"x"}, 8) == {"etc/a.conf": b"x", "var/b.html": b""}
    for files, match in (({"etc/a.conf": b"x" * 9}, "exceeds"), ({"etc/a.conf": b"\xff"}, "UTF-8"),
                         ({"etc/a.conf": b""}, "absent_if_empty"), ({"etc/a.conf": b"x", "other": b""}, "undeclared")):
        with pytest.raises(convert.ConversionError, match=match):
            convert.bounded_artifacts(contract, files, 8)


def test_native_limits_are_sized_from_artifacts_and_never_lowered():
    assert convert.native_limits([100, 16384]) == {}
    assert convert.native_limits([40000]) == {"bytes": 131072, "channel": 131072, "finalOutputReserve": 131072,
                                              "payload": 524288}
    assert convert.memory("2G") == "2g" and convert.memory(4096) == "4096m"


def test_verifier_prepare_is_derived_from_test_sh():
    script = ("apt-get update\napt-get install -y curl\ncurl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh\n"
              "uvx \\\n  -p 3.13 \\\n  -w pytest==8.4.1 \\\n  -w pytest-json-ctrf==0.3.5 \\\n"
              "  pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA\n")
    assert convert.test_prepare(script) == [
        "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y curl",
        "uvx -p 3.13 -w pytest==8.4.1 -w pytest-json-ctrf==0.3.5 pytest --version"]
    with pytest.raises(convert.ConversionError, match="adapter"):
        convert.test_prepare("python -m unittest\n")


# --- record: every anchor converted or explicitly excluded/pending -----------------------

def test_every_anchor_is_converted_excluded_or_pending_with_reason():
    entries = {entry["name"]: entry for entry in RECORD["anchors"]}
    assert set(entries) == {anchor["name"] for anchor in ANCHORS} and len(entries) == len(RECORD["anchors"])
    assert RECORD["contracts_sha256"] == packages.sha((HERE / "anchors-native-contracts.json").read_bytes())
    for name, entry in entries.items():
        assert entry["status"] in {"converted", "excluded", "pending"}, (name, entry.get("error"))
        if entry["status"] == "converted":
            assert entry["package"] in curriculum.ANCHORS and CONTRACTS["conversions"][name]["package"] == entry["package"]
        else:
            assert len(entry["reason"]) > 80 and entry["kind"]
    assert {e["name"] for e in entries.values() if e["status"] == "converted"} == set(CONTRACTS["conversions"])


# --- converted packages ------------------------------------------------------------------

@pytest.mark.parametrize("name", curriculum.ANCHORS)
def test_anchor_package_export_policy_and_provenance(name, tmp_path):
    info = curriculum.meta(name)
    assert name not in curriculum.PACKAGES  # separate registry; never pooled with tailored packages
    digest = curriculum.stage(name, tmp_path / "agent")  # also checks frozen manifest + native policy
    assert curriculum.check_export(name, tmp_path / "agent") == digest
    agent = curriculum.agent_files(name)
    assert "TASK.md" in agent and not any({".git", "hidden"} & set(Path(p).parts) for p in agent)
    assert all(len(data) <= 32768 for data in agent.values())
    export = json.loads((curriculum.directory(name) / "export.json").read_text())
    contract = json.loads(curriculum.verifier_files(name)["sandbox/anchor.json"])
    assert contract["artifacts"] == export["artifacts"] and contract["env"] == {"UV_OFFLINE": "1"}
    assert sorted(a["agent_path"] for a in contract["artifacts"]) == info["grader"]["candidates"]
    policy = json.loads((curriculum.directory(name) / "native-policy.json").read_text())
    assert policy == curriculum.native_policy(name) and policy["artifacts"] == info["grader"]["candidates"]
    _, closed, _ = native.material(name)
    assert set(closed["read"]) == {*agent, closed["scratch"]} and name in native.NAMES
    entry = {a["name"]: a for a in json.loads((HERE / "anchors-verification.json").read_text())["anchors"]}[
        info["anchor"]["name"]]
    assert entry["status"] == "verified" and info["anchor"]["tree_sha256"] == entry["tree_sha256"]
    assert info["anchor"]["license"] == "Apache-2.0" and "Apache-2.0" in (
        curriculum.directory(name) / "NOTICE").read_text()
    assert "## Original instruction" in agent["TASK.md"].decode()
    sandbox = {p: d for p, d in curriculum.verifier_files(name).items() if p.startswith("sandbox/tests/")}
    assert "sandbox/tests/test.sh" in sandbox and any(p.endswith(".py") for p in sandbox)
    assert curriculum.verifier_files(name)["reference"] not in b"".join(agent.values())
    size = curriculum.task_size(name)
    assert size["hidden_checks"] == sum(info["grader"]["denominators"].values()) and size["oracle_files_changed"]


@pytest.mark.parametrize("name", curriculum.ANCHORS)
def test_anchor_retained_calibration_base_fails_oracle_passes(name):
    receipt = json.loads(calibrate.path(name).read_text())
    agent, verifier, _, _ = specs.package(name)
    assert receipt["export_sha256"] == packages.bundle_digest(agent)
    assert receipt["verifier_sha256"] == packages.inventory(verifier)
    baseline, reference = receipt["phases"]
    assert baseline["verdict"] == "fail" and baseline["failed"] and adapter.REWARD_ID in baseline["failed"]
    assert reference["verdict"] == "pass" and not reference["failed"]
    rows = curriculum.rows(name)
    assert receipt["denominators"] == specs.spec(name)["denominators"] == adapter.denominators(rows)
    assert {g: c["total"] for g, c in reference["counts"].items()} == receipt["denominators"]
    for phase in receipt["phases"]:
        assert phase["status"] == "graded" and phase["cleanup_proven"]
        assert phase["containment"]["NetworkMode"] == "none" and not phase["containment"]["Binds"]
        assert phase["containment"]["CapDrop"] == ["ALL"] and "no-new-privileges:true" in phase["containment"]["SecurityOpt"]
    record = {a.get("package"): a for a in RECORD["anchors"]}[name]["calibration"]
    assert record["repeatable"] and record["base_fails"] and record["oracle_passes"]
    for label, phase in (("baseline", baseline), ("reference", reference)):
        assert record["phases"][label]["observation_sha256"] == [phase["observation_sha256"]] * 2


def _image(name):
    return subprocess.run(["docker", "image", "inspect", specs.spec(name)["image"]], capture_output=True).returncode == 0


@pytest.mark.parametrize("name", curriculum.ANCHORS)
def test_anchor_fresh_docker_calibration_matches_retained(name, tmp_path):
    if not _image(name):
        pytest.skip("verifier image absent; build with anchors_convert.py --build-only")
    fresh = calibrate.receipt(name, tmp_path)
    retained = json.loads(calibrate.path(name).read_text())
    assert [(p["verdict"], p["counts"], p["failed"], p["observation_sha256"]) for p in fresh["phases"]] == [
        (p["verdict"], p["counts"], p["failed"], p["observation_sha256"]) for p in retained["phases"]]
