"""MB-R3 AC-B2: public Harbor anchors converted to native curriculum packages.

Unit tests cover the converter's final-state contract bounding and the Harbor
verifier -> strict row adapter. Package tests check each converted anchor's
retained calibration (base fails, oracle passes, repeatable observations),
export, native policy and provenance; the fresh Docker re-grade runs only when
the anchor's verifier image is present (anchors_convert.py --build-only).
"""
import hashlib
import os
import re
import sys
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
DIFF = [n for n in curriculum.ANCHORS if curriculum.meta(n)["grader"].get("contract") == "git-diff"]
FILES = [n for n in curriculum.ANCHORS if n not in DIFF]
SKIP_CACHE = ("verified anchor cache absent; run `python -m benchmarks.michael.curriculum.anchors_convert "
              "--materialize` to fetch the upstream bytes")


def needs_cache(name):
    if not curriculum.available(name):
        pytest.skip(f"{name}: {SKIP_CACHE}")


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

@pytest.mark.parametrize("name", FILES)
def test_anchor_package_export_policy_and_provenance(name, tmp_path):
    info = curriculum.meta(name)
    assert name not in curriculum.PACKAGES  # separate registry; never pooled with tailored packages
    digest = curriculum.stage(name, tmp_path / "agent")  # also checks frozen manifest + native policy
    assert curriculum.check_export(name, tmp_path / "agent") == digest
    agent = curriculum.agent_files(name)
    assert "TASK.md" in agent and not any({".git", "hidden"} & set(Path(p).parts) for p in agent)
    assert all(len(data) <= 32768 for data in agent.values())
    export = json.loads((curriculum.package_dir(name) / "export.json").read_text())
    contract = json.loads(curriculum.verifier_files(name)["sandbox/anchor.json"])
    assert contract["artifacts"] == export["artifacts"] and contract["env"] == {"UV_OFFLINE": "1"}
    assert sorted(a["agent_path"] for a in contract["artifacts"]) == info["grader"]["candidates"]
    policy = json.loads((curriculum.package_dir(name) / "native-policy.json").read_text())
    assert policy == curriculum.native_policy(name) and policy["artifacts"] == info["grader"]["candidates"]
    _, closed, _ = native.material(name)
    assert set(closed["read"]) == {*agent, closed["scratch"]} and name in native.NAMES
    entry = {a["name"]: a for a in json.loads((HERE / "anchors-verification.json").read_text())["anchors"]}[
        info["anchor"]["name"]]
    assert entry["status"] == "verified" and info["anchor"]["tree_sha256"] == entry["tree_sha256"]
    assert info["anchor"]["license"] == "Apache-2.0" and "Apache-2.0" in (
        curriculum.package_dir(name) / "NOTICE").read_text()
    assert "## Original instruction" in agent["TASK.md"].decode()
    sandbox = {p: d for p, d in curriculum.verifier_files(name).items() if p.startswith("sandbox/tests/")}
    assert "sandbox/tests/test.sh" in sandbox and any(p.endswith(".py") for p in sandbox)
    assert curriculum.verifier_files(name)["reference"] not in b"".join(agent.values())
    size = curriculum.task_size(name)
    assert size["hidden_checks"] == sum(info["grader"]["denominators"].values()) and size["oracle_files_changed"]


@pytest.mark.parametrize("name", curriculum.ANCHORS)
def test_anchor_retained_calibration_base_fails_oracle_passes(name):
    needs_cache(name)
    receipt = json.loads(calibrate.path(name).read_text())
    agent, verifier, _, _ = specs.package(name)
    assert receipt["export_sha256"] == packages.bundle_digest(agent)
    assert receipt["verifier_sha256"] == packages.inventory(verifier)
    baseline, reference = receipt["phases"]
    assert baseline["verdict"] == "fail" and baseline["failed"] and adapter.REWARD_ID in baseline["failed"]
    assert reference["verdict"] == "pass" and not reference["failed"]
    rows = curriculum.rows(name)
    assert receipt["denominators"] == specs.spec(name)["denominators"] == adapter.denominators(rows)
    if name in DIFF:  # SWE-bench Pro: the base fails because FAIL_TO_PASS fails
        assert any(row.startswith("fail_to_pass::") for row in baseline["failed"])
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
    needs_cache(name)
    if not _image(name):
        pytest.skip("verifier image absent; build with anchors_convert.py --build-only")
    fresh = calibrate.receipt(name, tmp_path)
    retained = json.loads(calibrate.path(name).read_text())
    assert [(p["verdict"], p["counts"], p["failed"], p["observation_sha256"]) for p in fresh["phases"]] == [
        (p["verdict"], p["counts"], p["failed"], p["observation_sha256"]) for p in retained["phases"]]


# --- SWE-bench Pro: diff contract, subset resolution, F2P/P2P rows ----------------------

from benchmarks.michael.curriculum import anchors_subset  # noqa: E402
from benchmarks.michael.replay_grader import final_diff, swebenchpro_adapter as swe  # noqa: E402


def test_diff_contract_round_trips_and_is_git_apply_compatible(tmp_path):
    base = {"a.py": b"x\ny\nz\n", "b.txt": b"no newline", "c.txt": b"l1\r\nl2\r\n", "d": b"same\n", "e": b""}
    final = {"a.py": b"x\nY\nz\nw", "b.txt": b"no newline\nmore\n", "c.txt": b"l1\r\nL2\r\n", "d": b"same\n",
             "e": b"filled\n"}
    created = {"pkg/new.py": b"VALUE = 1\n", "pkg/empty.txt": b""}
    patch = final_diff.make(base, final, max_bytes=1 << 16, created=created)
    assert patch.startswith(final_diff.HEADER) and "d" not in final_diff.paths(patch)
    assert final_diff.apply(base, patch) == {**{p: final[p] for p in ("a.py", "b.txt", "c.txt", "e")}, **created}
    assert final_diff.make(base, dict(base), max_bytes=len(final_diff.HEADER)) == final_diff.HEADER  # base = empty
    for path, data in base.items():
        (tmp_path / path).write_bytes(data)
    (tmp_path / "final.patch").write_bytes(patch)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "apply", "--whitespace=nowarn", "final.patch"], cwd=tmp_path, check=True)
    assert all((tmp_path / p).read_bytes() == d for p, d in {**final, **created}.items())


def test_diff_contract_is_bounded_and_rejects_unsupported_states():
    base = {"a.py": b"x\n"}
    for kwargs, match in (({"final": {"a.py": b"y" * 200}, "max_bytes": 64}, "exceeds"),
                          ({"final": {"a.py": b"\xff"}, "max_bytes": 4096}, "UTF-8"),
                          ({"final": {"a.py": b"x\0"}, "max_bytes": 4096}, "NUL"),
                          ({"final": {"a.py": b"x\n", "b": b""}, "max_bytes": 4096}, "exactly"),
                          ({"final": {"a.py": b"x\n"}, "max_bytes": 4096, "created": {"a.py": b""}}, "new files"),
                          ({"final": {"a.py": b"x\n"}, "max_bytes": 4096, "created": {"../x": b""}}, "path")):
        with pytest.raises(final_diff.DiffError, match=match):
            final_diff.make(base, **kwargs)
    with pytest.raises(final_diff.DiffError, match="context"):
        final_diff.apply({"a.py": b"other\n"}, final_diff.make(base, {"a.py": b"y\n"}, max_bytes=4096))
    assert final_diff.new_files(b"{}\n", "app/") == {}
    assert final_diff.new_files(b'{"app/n.ts": "x"}', "app/") == {"app/n.ts": b"x"}
    for raw, match in ((b"[]", "map"), (b"{bad", "JSON"), (b'{"lib/x.py": ""}', "under"),
                       (b'{"app/a b": ""}', "path"),
                       (json.dumps({f"app/{i}": "" for i in range(65)}).encode(), "at most")):
        with pytest.raises(final_diff.DiffError, match=match):
            final_diff.new_files(raw, "app/")


def test_subset_resolves_transitive_local_python_imports():
    files = {"lib/pkg/__init__.py": b"", "lib/pkg/core.py": b"from . import util\nfrom .sub import deep\n",
             "lib/pkg/util.py": b"import json\nimport pkg.extra\n", "lib/pkg/extra.py": b"",
             "lib/pkg/sub/__init__.py": b"", "lib/pkg/sub/deep.py": b"from ..util import x\n",
             "lib/pkg/unused.py": b"", "test/units/__init__.py": b"", "test/units/compat.py": b"",
             "test/units/conftest.py": b"import pkg.gold_only\n", "lib/pkg/gold_only.py": b"",
             "test/units/test_core.py": b"old\n", "setup.cfg": b"", "docs/x.md": b"", "COPYING": b"",
             "lib/pkg/fixed.py": b""}
    tests = {"test/units/test_core.py": b"from pkg.core import thing\nfrom units.compat import mock\n"}
    result = anchors_subset.resolve(files, tests, language="python", python_roots=["lib", "test"],
                                    gold_paths=["lib/pkg/fixed.py"])
    assert set(result["paths"]) == {
        "lib/pkg/__init__.py", "lib/pkg/core.py", "lib/pkg/util.py", "lib/pkg/extra.py", "lib/pkg/sub/__init__.py",
        "lib/pkg/sub/deep.py", "test/units/__init__.py", "test/units/compat.py", "test/units/conftest.py",
        "lib/pkg/gold_only.py", "test/units/test_core.py", "setup.cfg", "COPYING", "lib/pkg/fixed.py"}
    assert result["reasons"]["lib/pkg/fixed.py"].startswith("gold patch") and result["files"] == 14


def test_subset_resolves_js_ts_relative_index_and_tsconfig_paths():
    files = {"tsconfig.json": b'{ // comment\n "compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]},},}',
             "src/a.ts": b'import { b } from "./b.js";\nexport * from "./dir";\nconst c = require("../lib/c");\n',
             "src/b.ts": b'import React from "react";\n', "src/dir/index.tsx": b'import "@/styles";\n',
             "src/styles.ts": b"", "lib/c.js": b"", "src/unused.ts": b"", "package.json": b"{}",
             "test/a-test.ts": b"old"}
    tests = {"test/a-test.ts": b'import { a } from "../src/a";\njest.mock("../src/b");\n'}
    result = anchors_subset.resolve(files, tests, language="js")
    assert set(result["paths"]) == {"tsconfig.json", "package.json", "src/a.ts", "src/b.ts", "src/dir/index.tsx",
                                    "src/styles.ts", "lib/c.js", "test/a-test.ts"}


def test_swebenchpro_rows_map_f2p_p2p_strictly():
    config = {"fail_to_pass": "['t.py::new']", "pass_to_pass": '["t.py::old", "u.py::keep"]'}
    table = swe.rows(config)
    assert swe.denominators(table) == {"fail_to_pass": 1, "pass_to_pass": 2, swe.REWARD_GROUP: 1}
    probes = [row["probe"] for row in table]
    output = {"tests": [{"name": "t.py::new", "status": "PASSED"}, {"name": "t.py::old", "status": "FAILED"},
                        {"name": "t.py::old", "status": "PASSED"}, {"name": "u.py::keep", "status": "SKIPPED"}]}
    assert swe.observe(output, "1\n", probes) == ["passed", "passed", "skipped", "1"]
    assert swe.observe({"tests": [{"name": "t.py::new", "status": "ERROR"}]}, "0", probes) == [
        "error", "missing", "missing", "0"]
    assert swe.observe(output, "1", probes, applied=False) == ["missing"] * 3 + [None]
    assert all(swe.valid(r, v) for r, v in zip(table, swe.observe(None, None, probes)))
    for bad in ({"fail_to_pass": "[]", "pass_to_pass": "[]"},
                {"fail_to_pass": '["a", "a"]', "pass_to_pass": "[]"},
                {"fail_to_pass": '["a"]', "pass_to_pass": '["a"]'}):
        with pytest.raises(ValueError):
            swe.rows(bad)


def test_swebenchpro_large_p2p_uses_aggregate_and_per_file_rows(monkeypatch):
    monkeypatch.setattr(swe, "P2P_PER_TEST_LIMIT", 2)
    config = {"fail_to_pass": ["a.ts | x"], "pass_to_pass": ["a.ts | y", "b.ts | z", "b.ts | w"]}
    table = swe.rows(config)
    assert swe.denominators(table) == {"fail_to_pass": 1, "pass_to_pass": 1, "pass_to_pass_files": 2,
                                       swe.REWARD_GROUP: 1}
    output = {"tests": [{"name": n, "status": "PASSED"} for n in ("a.ts | x", "a.ts | y", "b.ts | z")]}
    assert swe.observe(output, "0", [r["probe"] for r in table]) == ["passed", "missing", "passed", "missing", "0"]


@pytest.mark.parametrize("name", DIFF)
def test_swebenchpro_package_contract_policy_and_oracle(name, tmp_path):
    needs_cache(name)
    info, grader = curriculum.meta(name), curriculum.meta(name)["grader"]
    digest = curriculum.stage(name, tmp_path / "agent")  # frozen manifest, native policy, leak checks
    assert curriculum.check_export(name, tmp_path / "agent") == digest
    agent = curriculum.agent_files(name)
    repo_files = sorted(p for p in agent if p.startswith(grader["writable_prefix"]))
    assert {*agent} == {*repo_files, "TASK.md", "policy.json", grader["candidate"], grader["new_files"]}
    assert agent[grader["candidate"]] == final_diff.HEADER and agent[grader["new_files"]] == b"{}\n"
    subset = info["anchor"]["subset"]
    assert subset["exported_files"] == len(repo_files) <= subset["caps"]["files"] == 2000
    assert sum(len(agent[p]) for p in repo_files) == subset["exported_bytes"] <= subset["caps"]["bytes"]
    assert all(convert.is_text(agent[p]) and len(agent[p]) <= subset["caps"]["file_bytes"] for p in repo_files)
    policy = json.loads((curriculum.package_dir(name) / "native-policy.json").read_text())
    assert policy == curriculum.native_policy(name) and "artifacts" not in policy
    assert policy["write"] == [*repo_files, grader["new_files"], policy["scratch"]]
    assert policy["finalState"] == {"kind": "git-diff", "artifact": grader["candidate"], "maxBytes": 1048576,
                                    "newFiles": grader["new_files"], "prefix": grader["writable_prefix"]}
    assert max(len(agent[p]) for p in repo_files) <= policy["bytes"] and policy["finalOutputReserve"] == 0
    _, closed, _ = native.material(name)
    assert closed["run"] == [closed["scratch"]] and name in native.NAMES
    reference = curriculum.verifier_files(name)["reference"]
    changed = final_diff.apply({p: agent[p] for p in repo_files}, reference)
    prefix = grader["writable_prefix"]
    assert set(changed) == {prefix + p for p in [*info["anchor"]["gold_modified"], *info["anchor"]["gold_created"]]}
    config = json.loads(curriculum.verifier_files(name)["sandbox/tests/config.json"])
    assert curriculum.rows(name) == [{**r, "clauses": [tuple(c) for c in r["clauses"]]} for r in swe.rows(config)]
    assert info["anchor"]["gold_commit"].encode() not in b"".join(agent.values())
    record = {a.get("package"): a for a in RECORD["anchors"]}[name]
    assert record["calibration"]["fits_candidate_seconds"] and record["calibration"]["grading_seconds_max"] < \
        grader["candidate_seconds"]


@pytest.mark.parametrize("name", DIFF)
def test_native_diff_collector_computes_bounded_patch(name, tmp_path):
    needs_cache(name)
    """The trusted collector (host-side byte reads, no execution) turns edits into the canonical patch."""
    _, policy, _ = native.material(name)
    agent = curriculum.agent_files(name)
    task = tmp_path / "task"
    for path, data in agent.items():
        (task / path).parent.mkdir(parents=True, exist_ok=True)
        (task / path).write_bytes(data)
    binding = {"agentFiles": packages.inventory(agent)}
    config = {"curriculumTask": name}
    assert native.diff_final_state(tmp_path, binding, policy, config) == final_diff.HEADER  # base = empty diff
    target = next(p for p in policy["write"] if p.startswith("app/") and agent[p].endswith(b"\n"))
    (task / target).write_bytes(agent[target] + b"# edit\n")
    (task / policy["finalState"]["newFiles"]).write_text('{"app/mb_new_file.txt": "hello\\n"}')
    patch = native.diff_final_state(tmp_path, binding, policy, config)
    assert final_diff.paths(patch) == sorted([target, "app/mb_new_file.txt"])
    (task / policy["finalState"]["newFiles"]).write_text('{"elsewhere/x": ""}')
    with pytest.raises(native.api.TrialError, match="rejected"):
        native.diff_final_state(tmp_path, binding, policy, config)


# --- materialized anchors: no upstream bytes in git, verified cache, fail closed --------

from benchmarks.michael.curriculum import anchors_materialize, live  # noqa: E402

COMMITTED = {"task.json", "NOTICE", "manifest.json", "native-policy.json", "calibration.json", "export.json",
             "materialize.json"}


@pytest.mark.parametrize("name", DIFF)
def test_materialized_package_commits_only_authored_metadata(name):
    root = curriculum.package_dir(name)
    assert curriculum.materialized(name) and root == curriculum.ANCHOR_ROOT / name
    assert {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} == COMMITTED
    manifest = json.loads((root / "materialize.json").read_text())
    assert set(manifest["sources"]) == {"upstream", "task_image", "harbor_datasets"}
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["sources"]["upstream"]["commit"])
    assert manifest["sources"]["task_image"].split("@sha256:")[1] and len(manifest["gold_patch_sha256"]) == 64
    assert all(re.fullmatch(r"[0-9a-f]{64}", d) for d in manifest["files"].values())
    assert {f"hidden/sandbox/tests/{p}" for p in manifest["hidden_tests_sha256"]} <= set(manifest["files"])
    descriptor = json.loads((root / "manifest.json").read_text())
    assert descriptor["provenance"]["materialized_manifest_sha256"] == packages.sha((root / "materialize.json").read_bytes())
    ignored = subprocess.run(["git", "check-ignore", "-q", str(curriculum.CACHE_ROOT / name / "agent/TASK.md")],
                             cwd=packages.ROOT)
    assert ignored.returncode == 0  # the cache is gitignored


def _copy_cache(name, tmp_path, monkeypatch):
    needs_cache(name)
    import shutil
    shutil.copytree(curriculum.CACHE_ROOT / name, tmp_path / name)
    monkeypatch.setattr(curriculum, "CACHE_ROOT", tmp_path)
    curriculum._VERIFIED.pop(name, None)
    return tmp_path / name


@pytest.mark.parametrize("name", DIFF[:1])
def test_tampered_cache_fails_closed_for_loading_and_calibration(name, tmp_path, monkeypatch):
    cache = _copy_cache(name, tmp_path, monkeypatch)
    assert curriculum.agent_files(name)  # the verified copy loads
    target = next(p for p in sorted((cache / "agent/app").rglob("*")) if p.is_file())
    target.write_bytes(target.read_bytes() + b"# tampered\n")
    for load in (curriculum.agent_files, curriculum.verifier_files, specs.package, native.material,
                 lambda n: calibrate.receipt(n, tmp_path / "grade")):
        with pytest.raises(curriculum.AnchorCacheError, match="fails its pinned sha256.*--materialize"):
            load(name)
    target.unlink()
    with pytest.raises(curriculum.AnchorCacheError, match="file set differs"):
        curriculum.agent_files(name)
    assert not curriculum.available(name)


@pytest.mark.parametrize("name", DIFF[:1])
def test_absent_cache_refuses_to_load_with_materialize_command(name, tmp_path, monkeypatch):
    monkeypatch.setattr(curriculum, "CACHE_ROOT", tmp_path)
    curriculum._VERIFIED.pop(name, None)
    with pytest.raises(curriculum.AnchorCacheError, match="absent; run `python -m benchmarks.michael."
                                                          "curriculum.anchors_convert --materialize"):
        curriculum.agent_files(name)
    assert not curriculum.available(name) and curriculum.meta(name)["grader"]["contract"] == "git-diff"


@pytest.mark.parametrize("name", DIFF[:1])
def test_materialize_verifies_every_file_and_accepts_nothing_on_mismatch(name, tmp_path, monkeypatch):
    cache = _copy_cache(name, tmp_path, monkeypatch)
    monkeypatch.setattr(anchors_materialize, "CACHE", tmp_path)
    good = {p.relative_to(cache).as_posix(): p.read_bytes() for p in cache.rglob("*") if p.is_file()}
    before = {p: packages.sha(d) for p, d in good.items()}
    bad = {**good, "hidden/reference": good["hidden/reference"] + b"\n"}
    monkeypatch.setattr(anchors_materialize, "build", lambda n, work: bad)
    with pytest.raises(anchors_materialize.MaterializeError, match="fail their pinned sha256"):
        anchors_materialize.materialize(name, tmp_path / "work")
    monkeypatch.setattr(anchors_materialize, "build", lambda n, work: {**good, "agent/extra.txt": b""})
    with pytest.raises(anchors_materialize.MaterializeError, match="file set differs"):
        anchors_materialize.materialize(name, tmp_path / "work")
    assert {p.relative_to(cache).as_posix(): packages.sha(p.read_bytes()) for p in cache.rglob("*")
            if p.is_file()} == before  # the previously verified cache is untouched
    assert not list(tmp_path.glob(".*staging"))
    monkeypatch.setattr(anchors_materialize, "build", lambda n, work: good)
    assert anchors_materialize.materialize(name, tmp_path / "work") == cache and curriculum.agent_files(name)


def test_materialize_cli_fails_closed_with_nonzero_exit():
    result = subprocess.run([sys.executable, "-m", "benchmarks.michael.curriculum.anchors_convert", "--materialize",
                             "no-such-anchor"], cwd=packages.ROOT, capture_output=True, text=True,
                            env={**os.environ, "PYTHONPATH": str(packages.ROOT), "PYTHONDONTWRITEBYTECODE": "1"})
    assert result.returncode == 1 and "nothing accepted" in result.stderr


# --- one package resolver; binary-safe audit payloads ------------------------------------

def test_every_package_resolves_through_package_dir():
    names = [*packages.CASES, *curriculum.PACKAGES, *curriculum.ANCHORS]
    for name in names:
        root = curriculum.package_dir(name)
        assert (root / "manifest.json").is_file(), name
        expected = curriculum.ANCHOR_ROOT / name if name in curriculum.ANCHORS else curriculum.HERE / name
        assert root == expected
    for name in curriculum.ANCHORS:
        assert curriculum.package_dir(name).parent == curriculum.ANCHOR_ROOT and calibrate.path(name).parent == \
            curriculum.package_dir(name)
    from benchmarks.michael.replay_trial import handoff
    frozen = {"source": {}, "activeSeconds": 60}
    for name in [*FILES, *[n for n in DIFF if curriculum.available(n)]]:
        bundle = handoff.bundle(None, "fixture-model", synthetic=True, task_name=name, configuration=frozen)
        assert bundle["task"] == json.loads((curriculum.package_dir(name) / "manifest.json").read_text())
    with pytest.raises(ValueError, match="unknown"):
        curriculum.package_dir("no-such-package")


def test_audit_payload_lists_binary_files_without_content():
    assert live.payload_file("a.txt", "é\n".encode()) == "é\n"
    blob = b"\x78\x01\xff\x00"
    assert live.payload_file("o/ab", blob) == {"path": "o/ab", "sha256": packages.sha(blob), "bytes": 4, "binary": True}
    payload = live.audit_payload("anchor-tb-fix-git")
    agent = curriculum.agent_files("anchor-tb-fix-git")
    binary = {p: v for p, v in payload["visible"].items() if isinstance(v, dict)}
    assert len(binary) == 6 and all(v["sha256"] == packages.sha(agent[p]) and "content" not in v for p, v in binary.items())
    assert all(payload["visible"][p] == d.decode() for p, d in agent.items() if p not in binary)
    assert payload["binaryContentOmitted"] == live.BINARY_NOTE and live.BINARY_NOTE in payload["contextPrecedence"]
    json.dumps(payload)
    text_only = live.audit_payload("anchor-tb-nginx-request-logging")
    assert "binaryContentOmitted" not in text_only and all(isinstance(v, str) for v in text_only["visible"].values())


# --- verifier build trust: explicit, hash-bound, never empty ---------------------------

_PEM = b"-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n"


def test_ca_bundle_refuses_empty_or_missing_bundle(tmp_path):
    empty = tmp_path / "empty.pem"
    empty.write_bytes(b"")
    with pytest.raises(convert.ConversionError, match="empty"):
        convert.ca_bundle(empty, hashlib.sha256(b"").hexdigest())
    with pytest.raises(convert.ConversionError, match="empty"):
        convert.ca_bundle(default=empty)
    with pytest.raises(convert.ConversionError, match="--ca-bundle PATH"):
        convert.ca_bundle(default=tmp_path / "absent.pem")
    with pytest.raises(convert.ConversionError, match="--ca-bundle-sha256"):
        convert.ca_bundle(empty)
    with pytest.raises(convert.ConversionError, match="empty"):
        convert.build_verifier("img", [], "/", "tag", tmp_path, tmp_path, "n", "img", b"")


def test_ca_bundle_rejects_hash_mismatch_and_accepts_pinned_bundle(tmp_path):
    bundle = tmp_path / "cacert.pem"
    bundle.write_bytes(_PEM)
    with pytest.raises(convert.ConversionError, match="sha256"):
        convert.ca_bundle(bundle, "0" * 64)
    assert convert.ca_bundle(bundle, hashlib.sha256(_PEM).hexdigest().upper()) == _PEM


def test_ca_bundle_defaults_to_linux_system_bundle(tmp_path, monkeypatch):
    assert convert.LINUX_CA_BUNDLE == Path("/etc/ssl/certs/ca-certificates.crt")
    system = tmp_path / "ca-certificates.crt"
    system.write_bytes(_PEM)
    monkeypatch.setattr(convert.ca_bundle, "__defaults__", (None, None, system))
    args = convert.argparse.Namespace()
    assert convert.build_ca(args) == _PEM and args.ca_pem == _PEM


def test_ca_cli_fails_closed_before_building(tmp_path):
    empty = tmp_path / "empty.pem"
    empty.write_bytes(b"")
    result = subprocess.run([sys.executable, "-m", "benchmarks.michael.curriculum.anchors_convert", "--build-only",
                             "fix-git", "--ca-bundle", str(empty), "--ca-bundle-sha256",
                             hashlib.sha256(b"").hexdigest(), "--work-dir", str(tmp_path)],
                            capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 2 and "CA bundle refused (nothing built)" in result.stderr
