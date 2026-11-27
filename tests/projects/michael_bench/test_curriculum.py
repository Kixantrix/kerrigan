"""MB-008 curriculum: catalog coverage, package exports, Docker calibration, contracts.

Integration/cloud-linux (Docker). Candidate bytes are only ever graded inside the
independent no-network Docker grader; no test imports candidate code on the host.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

import pytest

from benchmarks.michael.contracts.manifests import ManifestError, manifest_reference, validate_bundle
from benchmarks.michael.ledger_report.api import Ledger, compare
from benchmarks.michael.replay_grader import api, calibrate, specs
from benchmarks.michael.tasks import curriculum, packages

ROOT = Path(__file__).resolve().parents[3]
CATALOG = json.loads((ROOT / "benchmarks/michael/curriculum/catalog.json").read_text())
CANDIDATES = CATALOG["candidates"]
SHA = re.compile(r"[0-9a-f]{40}")
EVIDENCE = {"held_out_tests", "required_facts_checklist", "metric_within_tolerance",
            "service_health_probe", "defect_coverage", "constraint_validator", "integrated_outcome"}
REQUIRED_CALIBRATED = {"Experiment", "Review and repair", "Understand and plan", "Operate"}
VALIDATOR_POLICY = json.loads((ROOT / "benchmarks/michael/local_transport/validator-task-policy.json").read_text())


# --- AC-MB-008a: catalog schema and coverage -------------------------------------------

def test_catalog_candidate_schema():
    ids = [item["id"] for item in CANDIDATES]
    assert len(ids) == len(set(ids))
    for item in CANDIDATES:
        assert item["family"] in curriculum.FAMILIES, item["id"]
        assert item["privacy"] in curriculum.PRIVACY, item["id"]
        assert item["outcome_evidence"] in EVIDENCE, item["id"]
        assert SHA.fullmatch(item["base_ref"]) and SHA.fullmatch(item["reference_ref"]), item["id"]
        assert item["base_ref"] != item["reference_ref"]
        assert re.fullmatch(r"Kixantrix/[\w.-]+", item["repo"])
        assert item["history_status"] in {"merged", "unmerged-branch"}
        assert type(item["estimated_agent_minutes"]) is int and item["estimated_agent_minutes"] > 0
        assert item["long_horizon"] == (item["estimated_agent_minutes"] > 30)
        assert item["required_environment"] and item["toolchain"] and item["grader_image"]
        if not item["grader_container_ok"]:
            assert item["grader_image"].startswith("not-containerizable: requires ")
        if item["visibility"] == "private":
            assert item["privacy"] != "public", item["id"]


def test_catalog_covers_families_mix_and_breadth():
    by_family = {family: [c for c in CANDIDATES if c["family"] == family] for family in curriculum.FAMILIES}
    assert all(len(items) >= 2 for items in by_family.values()), {k: len(v) for k, v in by_family.items()}
    # The observed mix is dominated by Gridiron research and self-hosting: not token entries.
    assert len(by_family["Experiment"]) >= 5 and len(by_family["Operate"]) >= 5
    assert sum(c["long_horizon"] for c in CANDIDATES) >= 2
    repos = {c["repo"] for c in CANDIDATES}
    for name in ("personal-selfhost", "kerrigan", "alethiometer", "taste-engine", "your-voice",
                 "vhs-video-stack", "event-media-vault", "kirkland-prototype", "clinical-scribe",
                 "voxel-solar-wallpaper", "sunday-league", "foal-rescue-meadow"):
        assert f"Kixantrix/{name}" in repos, name
    stacks = {s for c in CANDIDATES for s in c["stack"]}
    assert {"python", "typescript", "kotlin", "gdscript", "html", "canvas", "cadquery"} <= stacks


def test_user_excluded_repositories_absent():
    text = json.dumps(CANDIDATES).lower()
    assert "hobl" not in text and "windowsdeveloperconfig" not in text
    assert set(CATALOG["excluded_repositories"]) == {"Kixantrix/HOBL", "Kixantrix/WindowsDeveloperConfig"}


def test_catalog_packages_match_their_sources():
    packaged = {c["package"]: c for c in CANDIDATES if c["package"]}
    retired = {name: c for c in CANDIDATES for name in c.get("retired_packages", [])}
    pending = {name for c in CANDIDATES for name in c.get("pending_reaudit_packages", [])}
    assert set(packaged) | set(retired) | pending == {*packages.CASES, *curriculum.PACKAGES}
    assert not pending & set(curriculum.retired())
    assert set(retired) == set(curriculum.retired()) and not set(packaged) & set(retired)
    for name, item in retired.items():
        assert curriculum.retired()[name]["superseded_by"] == item["package"]
    for name, item in packaged.items():
        if name in packages.CASES:
            case = packages.CASES[name]
            assert (item["base_ref"], item["reference_ref"]) == (case["base"], case["reference"])
            assert item["family"] == "Implement"
        else:
            source = curriculum.meta(name)["source"]
            assert (item["repo"], item["base_ref"], item["reference_ref"]) == (
                source["repo"], source["base_ref"], source["reference_ref"])
            assert item["family"] == curriculum.meta(name)["family"]
            assert item["history_status"] == source["history_status"]
    families = {curriculum.meta(name)["family"] for name in curriculum.PACKAGES}
    assert REQUIRED_CALIBRATED <= families
    assert sum(c["family"] == "Implement" and bool(c["package"]) for c in CANDIDATES) >= 3


# --- AC-MB-008b/d: exact export, leakage and contracts -----------------------------------

def test_package_trees_ignore_bytecode_and_untracked_noise(tmp_path):
    name = "sr-temporal-assay"
    before = curriculum.agent_files(name)
    cache = curriculum.HERE / name / "agent" / "assay" / "__pycache__"
    cache.mkdir(exist_ok=True)
    try:
        (cache / "temporal_mech.cpython-312.pyc").write_bytes(b"bytecode")
        (curriculum.HERE / name / "agent" / "assay" / "stray.pyc").write_bytes(b"bytecode")
        assert curriculum.agent_files(name) == before
        assert curriculum.descriptor(name) == json.loads((curriculum.HERE / name / "manifest.json").read_text())
    finally:
        shutil.rmtree(cache)
        (curriculum.HERE / name / "agent" / "assay" / "stray.pyc").unlink()


@pytest.mark.parametrize("name", curriculum.PACKAGES)
def test_frozen_export_without_leakage(name, tmp_path):
    info = curriculum.meta(name)
    assert curriculum.descriptor(name) == json.loads((curriculum.HERE / name / "manifest.json").read_text())
    digest = curriculum.stage(name, tmp_path / "agent")
    assert curriculum.check_export(name, tmp_path / "agent") == digest
    exported = {p.relative_to(tmp_path / "agent").as_posix() for p in (tmp_path / "agent").rglob("*") if p.is_file()}
    assert exported == set(curriculum.agent_files(name))
    assert "TASK.md" in exported and info["grader"]["candidate"] in exported
    assert not any(part in {".git", "hidden"} for path in exported for part in Path(path).parts)
    blob = b"".join(curriculum.agent_files(name).values())
    assert curriculum.verifier_files(name)["reference"] not in blob
    assert info["source"]["base_ref"].encode() not in blob and info["source"]["reference_ref"].encode() not in blob
    assert info["residual_rubric"], "residual judgment must be recorded, not model-judged"


@pytest.mark.parametrize("contamination", [".git/config", "hidden/rows.json", "solution.patch"])
def test_export_rejects_contamination(contamination, tmp_path):
    name = curriculum.PACKAGES[0]
    curriculum.stage(name, tmp_path / "agent")
    extra = tmp_path / "agent" / contamination
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("contamination")
    with pytest.raises(ValueError, match="allowlist"):
        curriculum.check_export(name, tmp_path / "agent")


@pytest.mark.parametrize("name", curriculum.PACKAGES)
def test_export_rejects_reference_substitution_and_symlink(name, tmp_path):
    curriculum.stage(name, tmp_path / "agent")
    candidate = tmp_path / "agent" / curriculum.meta(name)["grader"]["candidate"]
    candidate.write_bytes(curriculum.verifier_files(name)["reference"])
    with pytest.raises(ValueError, match="allowlist"):
        curriculum.check_export(name, tmp_path / "agent")
    candidate.unlink()
    candidate.symlink_to(curriculum.HERE / name / "hidden" / "reference")
    with pytest.raises(ValueError, match="symlink"):
        curriculum.check_export(name, tmp_path / "agent")


def test_hidden_expected_values_cannot_leak_into_export(tmp_path, monkeypatch):
    name = "plan-dashboard-waves"
    original = curriculum.agent_files

    def leaky(task):
        files = original(task)
        files["TASK.md"] += b"\nHint: implicit shared manifest conflict between M2.2 and M2.3 identified\n"
        return files

    curriculum.stage(name, tmp_path / "agent")
    monkeypatch.setattr(curriculum, "agent_files", leaky)
    (tmp_path / "agent/TASK.md").write_bytes(leaky(name)["TASK.md"])
    with pytest.raises(ValueError, match="leaks"):
        curriculum.check_export(name, tmp_path / "agent")


@pytest.mark.parametrize("name", [*curriculum.PACKAGES, "grouping", "status"])
def test_native_policy_matches_existing_trial_shape(name):
    directory = curriculum.HERE if name in curriculum.PACKAGES else packages.HERE
    policy = json.loads((directory / name / "native-policy.json").read_text())
    multi = name in curriculum.PACKAGES and len(curriculum.candidates(name)) > 1
    assert set(policy) == set(VALIDATOR_POLICY) | ({"artifacts"} if multi else set())
    for key, value in VALIDATOR_POLICY.items():
        if key not in {"condition", "source", "scratch", "read", "write"}:
            assert policy[key] == value, key
    agent = curriculum.agent_files(name) if name in curriculum.PACKAGES else packages.agent_files(name)
    assert policy["source"] in agent and policy["source"] in policy["write"]
    artifacts = policy.get("artifacts", [policy["source"]])
    assert set(policy["write"]) == {*artifacts, policy["scratch"]} and set(artifacts) <= set(agent)
    assert set(policy["read"]) == {*agent, policy["scratch"]}
    if name in curriculum.PACKAGES:
        assert policy == curriculum.native_policy(name)


def _bundle(name, label):
    task = (json.loads((curriculum.HERE / name / "manifest.json").read_text()) if name in curriculum.PACKAGES
            else json.loads((packages.HERE / name / "manifest.json").read_text()))
    unknown = {"status": "unknown", "reason": "fixture, not a model trial", "source": "MB-008 test"}
    base = {"schema_version": 1, "revision": "1", "provenance": {"source_id": "MB-008 contract test"}}
    target = {**base, "kind": "target", "id": f"synthetic-{label}", "requested_identity": "not invoked; calibration fixture",
              "observed_identity": unknown, "runtime": unknown}
    agent = {**base, "kind": "agent", "id": "mb008-fixture",
             "harness": {"id": "mb008", "revision": "1", "sha256": api.sha(b"mb008-fixture")},
             "configuration": unknown}
    condition = {**base, "kind": "condition", "id": f"mb008-{name}-{label}",
                 "task": manifest_reference(task), "target": manifest_reference(target),
                 "agent": manifest_reference(agent),
                 "hosts": {"agent": unknown, "inference": unknown,
                           "verifier": {"status": "known", "value": "cloud-linux-docker", "source": "MB-008"}},
                 "track": "practical_system", "retry_policy": "no_automatic_retries", "cache_policy": unknown,
                 "budgets": {"active_safety_seconds": {"status": "known", "value": 3600, "source": "native-policy.json"},
                             "attempt_limit": {"status": "known", "value": 1, "source": "MB-008"},
                             "response_tokens": unknown, "reasoning_tokens": unknown},
                 "capabilities": {}, "observability": {}, "required_semantics": []}
    return validate_bundle(task=task, target=target, agent=agent, condition=condition)


def _result(bundle, phase):
    status = {"pass": "passed", "fail": "failed"}[phase["verdict"]]
    unknown = {"status": "unknown", "reason": "fixture", "source": "MB-008"}
    attempt = {"id": "attempt-1", "verdict": status, "state": "completed",
               "stop_reason": "success" if status == "passed" else "agent_finished",
               "verifier": {"status": status, "independent": True, "source": "independent Docker grader"},
               "events": [], "timing": {}, "time_to_verified_completion": unknown,
               "usage": {key: unknown for key in ("tokens", "price", "credits", "power")}}
    result = {"schema_version": 1, "kind": "result", "id": f"{bundle['condition']['id']}-result", "revision": "1",
              "provenance": {"source_id": "MB-008 calibration receipt"},
              "condition": manifest_reference(bundle["condition"]), "attempts": [attempt]}
    return validate_bundle(**bundle, result=result)["result"]


@pytest.mark.parametrize("name", [*curriculum.PACKAGES, "grouping", "status"])
def test_calibration_receipts_flow_through_result_contract_and_ledger(name, tmp_path):
    receipt = json.loads(calibrate.path(name).read_text())
    ledger = Ledger(tmp_path / "ledger.jsonl")
    for phase in receipt["phases"]:
        bundle = _bundle(name, phase["phase"])
        ledger.start(phase["phase"], bundle, attempt_id="attempt-1", origin="synthetic")
        ledger.finalize(phase["phase"], _result(bundle, phase))
    report = compare(ledger, cohorts={"baseline": ["baseline"], "reference": ["reference"]},
                     suite=[manifest_reference(bundle["task"])])
    assert report["cohorts"]["reference"]["first_attempt_verified"] == 1
    assert report["cohorts"]["baseline"]["first_attempt_verified"] == 0
    with pytest.raises(ManifestError):
        bad = _bundle(name, "bad")
        bad_task = {**bad["task"], "verifier_material": bad["task"]["agent_material"]}
        validate_bundle(**{**bad, "task": bad_task})


# --- AC-MB-008b/c: Docker calibration ----------------------------------------------------

@pytest.mark.parametrize("name", [*curriculum.PACKAGES, "grouping", "status"])
def test_retained_calibration_baseline_fails_reference_passes(name):
    receipt = json.loads(calibrate.path(name).read_text())
    agent, verifier, _, _ = specs.package(name)
    assert receipt["export_sha256"] == packages.bundle_digest(agent)
    assert receipt["verifier_sha256"] == packages.inventory(verifier)
    baseline, reference = receipt["phases"]
    assert baseline["status"] == reference["status"] == "graded"
    assert baseline["verdict"] == "fail" and baseline["failed"]
    assert reference["verdict"] == "pass" and not reference["failed"]
    totals = {group: count["total"] for group, count in reference["counts"].items()}
    assert totals == receipt["denominators"] == specs.spec(name)["denominators"]
    assert all(count["passed"] == count["total"] for count in reference["counts"].values())
    for phase in receipt["phases"]:
        assert phase["cleanup_proven"] and phase["containment"]["NetworkMode"] == "none"
        assert not phase["containment"]["Binds"] and phase["containment"]["ReadonlyRootfs"]


@pytest.mark.parametrize("name", [*curriculum.PACKAGES, "grouping", "status"])
def test_fresh_docker_calibration_matches_retained(name, tmp_path):
    fresh = calibrate.receipt(name, tmp_path)
    retained = json.loads(calibrate.path(name).read_text())
    assert [(p["verdict"], p["counts"], p["failed"]) for p in fresh["phases"]] == [
        (p["verdict"], p["counts"], p["failed"]) for p in retained["phases"]]
    assert [p["observation_sha256"] for p in fresh["phases"]] == [
        p["observation_sha256"] for p in retained["phases"]]


@pytest.mark.parametrize("name", curriculum.PACKAGES)
def test_spoofed_and_hostile_candidates_cannot_pass(name, tmp_path):
    rows = specs.spec(name)["rows"]()
    forged = "".join(json.dumps({"id": i, "value": {"forged": True}}) + "\n" for i in range(len(rows)))
    attacks = {
        "print-pass": "print('PASS all checks')\n",
        "forged-frames": f"import sys\nsys.stdout.write({forged!r})\nsys.stdout.flush()\nimport os\nos._exit(0)\n",
        "network": "import socket\nsocket.create_connection(('192.0.2.1', 443), timeout=.2)\n",
        "loop": "while True: pass\n",
    }
    for label, attack in attacks.items():
        report = api.grade(attack.encode(), tmp_path / label, seconds=3, task=name)
        assert report["verdict"] != "pass", (label, report)
        assert report["cleanup"]["proven"] and not api.owned(report["run_id"])


def test_operate_grader_uses_trusted_supervisor_not_candidate(tmp_path):
    name = "selfhost-redeploy-state"
    archive = curriculum.sandbox_fixtures(name)
    agent = curriculum.agent_files(name)
    assert set(archive) == {"stack/api/server.py", "stack/supervisor.py"}
    assert all(archive[path] == agent[path] for path in archive)
    with pytest.raises(ValueError, match="candidate"):
        info = curriculum.meta(name)
        info["grader"]["agent_support"] = [info["grader"]["candidate"]]
        original = curriculum.meta
        try:
            curriculum.meta = lambda task: info
            curriculum.sandbox_fixtures(name)
        finally:
            curriculum.meta = original


# --- Public benchmark practice: Harbor layout, mining, admission, metrics, quality ------
import tomllib  # noqa: E402

from benchmarks.michael.curriculum import automation, harbor, metrics  # noqa: E402
from benchmarks.michael.curriculum.mining import mine  # noqa: E402

HARBOR_TASKS = [*packages.CASES, *curriculum.PACKAGES]


@pytest.mark.parametrize("name", HARBOR_TASKS)
def test_harbor_export_is_current_and_well_formed(name, tmp_path):
    digest = harbor.export(name, tmp_path / name)
    committed = harbor.EXPORT_ROOT / name
    assert digest == packages.bundle_digest({p.relative_to(committed).as_posix(): p.read_bytes()
                                             for p in curriculum._visible(committed)})
    assert not [p for p in committed.rglob("*") if "__pycache__" in p.parts or p.suffix == ".pyc"]
    for required in ("instruction.md", "task.toml", "environment/Dockerfile", "solution/solve.sh",
                     "tests/test.sh", "tests/Dockerfile"):
        assert (committed / required).is_file(), required
    config = tomllib.loads((committed / "task.toml").read_text())
    assert config["schema_version"] == "1.4"
    assert config["verifier"]["environment_mode"] == "separate"
    assert config["verifier"]["network_mode"] == config["agent"]["network_mode"] == "no-network"
    assert config["agent"]["user"] == "65534"
    assert config["artifacts"] == ["/app/" + path for path in specs.candidate_files(name)]
    for dockerfile in ("environment/Dockerfile", "tests/Dockerfile"):
        assert all("@sha256:" in line for line in (committed / dockerfile).read_text().splitlines()
                   if line.startswith(("FROM", "COPY --from")))
    # Agent-visible environment never carries hidden material.
    visible = b"".join(p.read_bytes() for p in (committed / "environment").rglob("*") if p.is_file())
    visible += (committed / "instruction.md").read_bytes()
    assert specs.reference(name) not in visible
    assert b"clauses" not in visible and not any(
        row["original_id"].encode() in visible for row in specs.spec(name)["rows"]()
        if "::" not in row["original_id"] and len(row["original_id"]) >= 16)
    assert "private/rows.json" not in [p.name for p in (committed / "environment").rglob("*")]


def test_harbor_loader_reads_public_task_shape(tmp_path):
    task = tmp_path / "public"
    (task / "tests").mkdir(parents=True)
    (task / "instruction.md").write_text("Do X")
    (task / "task.toml").write_text('schema_version = "1.4"\n[task]\nname = "org/x"\n[verifier]\ntimeout_sec = 9.0\n')
    loaded = harbor.load(task)
    assert loaded["verifier_mode"] == "shared" and not loaded["has_solution"]
    with pytest.raises(ValueError, match="separate"):
        harbor.verify(task, {})


def test_harbor_admission_matches_trusted_grader(tmp_path):
    name = "review-conflict-predictor"
    harbor.export(name, tmp_path / name)
    gates = harbor.admission(tmp_path / name)
    assert gates["base_fails"] and gates["oracle_passes"]
    receipt = json.loads(calibrate.path(name).read_text())
    for phase, result in zip(receipt["phases"], (gates["base"], gates["oracle"])):
        for group, count in phase["counts"].items():
            assert result["reward"][f"{group}_passed"] == count["passed"]
            assert result["reward"][f"{group}_total"] == count["total"]
    # A forged artifact that only prints "PASS" earns no reward in the Harbor verifier.
    forged = harbor.verify(tmp_path / name, {"/app/tools/conflict_predictor.py": b"print('PASS')\n"})
    assert forged["reward"]["reward"] == 0.0 and forged["reward"]["ungraded"] == 1.0


def test_retained_admission_records():
    records = json.loads((harbor.HERE / "admission.json").read_text())
    assert {r["task"] for r in records} == {f"kixantrix/michael-{n}" for n in HARBOR_TASKS}
    for record in records:
        assert record["deterministic"]["oracle_passes"] and record["deterministic"]["base_fails"]
        assert record["deterministic"]["verifier_network"] == "none"
        name = record["task"].removeprefix("kixantrix/michael-")
        assert record["decision"]["state"] == ("retired" if name in curriculum.retired() else "provisional")
        families = {a["family"] for a in record["model_gates"]["audits"]}
        assert len(families) >= 2
        assert record["model_gates"]["blind_reimplementation"]["family"] not in families


def test_mining_reproduces_fail_to_pass_for_pr_312():
    try:
        mine.require_image()
    except mine.MiningEnvironmentError as exc:
        pytest.skip(f"cloud_ok: preprovision required - {exc}")
    record = mine.instance("2071fffaf4cca41ec8d63ec06acd6963333236f3", pr=312)
    assert record["status"] == "admissible_candidate"
    assert record["FAIL_TO_PASS"] == sorted(
        f"tests/test_conflict_predictor.py::{name}" for name in (
            "TestParseTasks::test_task_prefix_and_milestone_id_preserved",
            "TestParseTasks::test_touch_bullet_parsed",
            "TestParseTasks::test_multiple_touch_bullets_are_unioned",
            "TestParseTasks::test_html_and_touch_bullet_both_accumulate",
            "TestRun::test_task_lines_without_touch_annotations_fail_loud",
            "TestRun::test_realistic_touch_bullets_parse_and_wave"))
    assert len(record["PASS_TO_PASS"]) == 50 and not set(record["FAIL_TO_PASS"]) & set(record["PASS_TO_PASS"])
    assert "tools/conflict_predictor.py" in record["source_files"]
    retained = {r["pr"]: r for r in json.loads((harbor.HERE / "mining/kerrigan-instances.json").read_text())}
    assert retained[312]["FAIL_TO_PASS"] == record["FAIL_TO_PASS"]
    assert sum(r["status"] == "admissible_candidate" for r in retained.values()) >= 10


def test_anchor_subset_is_small_fixed_and_pinned():
    anchors = json.loads((harbor.HERE / "anchors.json").read_text())["anchors"]
    assert len(anchors) == 10
    assert {a["dataset"] for a in anchors} == {"terminal-bench", "swebenchpro"}
    assert all(re.fullmatch(r"[0-9a-f]{40}", a["git_commit_id"]) and a["git_url"].startswith("https://") for a in anchors)


def test_metrics():
    assert metrics.wilson(0, 0) is None
    low, high = metrics.wilson(8, 10)
    assert 0.49 < low < 0.5 and 0.94 < high < 0.95
    assert metrics.pass_at_k(4, 1, 2) == 0.5 and metrics.pass_hat_k(4, 2, 2) == pytest.approx(1 / 6)
    trials = [{"task": "a", "resolved": True, "cost": 1.0, "wall_seconds": 10},
              {"task": "a", "resolved": True, "cost": 1.0, "wall_seconds": 20},
              {"task": "b", "resolved": False, "cost": 2.0, "wall_seconds": 30},
              {"task": "b", "resolved": True, "cost": None, "wall_seconds": 40},
              {"task": "c", "resolved": False, "wall_seconds": 5},
              {"task": "c", "resolved": False, "wall_seconds": 5}]
    summary = metrics.summarize(trials, k=2)
    assert summary["resolved"] == 3 and summary["pass^2"] == pytest.approx(1 / 3)
    assert summary["pass@2"] == pytest.approx(2 / 3)
    assert summary["cost_per_resolved"]["status"] == "unknown"
    assert summary["wall_seconds_per_resolved"]["value"] == pytest.approx(110 / 3)
    assert "time_horizon_50_minutes" not in summary and not hasattr(metrics, "time_horizon")
    assert summary["observed_difficulty"]["b"] == {"attempts": 2, "success_rate": 0.5, "median_agent_seconds": 35.0}
    assert summary["observed_difficulty"]["c"]["success_rate"] == 0.0


def test_model_requests_are_bound_and_family_constrained():
    req = automation.request("attribution", model="m", family="openai", payload={"run": "r1"})
    verdict = {"cause": "harness", "confidence": 0.9, "evidence": ["transport cap"]}
    assert automation.validate_verdict("attribution", {"request_sha256": req["request_sha256"],
                                                       "verdict": verdict}, req) == verdict
    with pytest.raises(ValueError, match="bound"):
        automation.validate_verdict("attribution", {"request_sha256": "0" * 64, "verdict": verdict}, req)
    with pytest.raises(ValueError, match="probability"):
        automation.validate_verdict("attribution", {"request_sha256": req["request_sha256"],
                                                    "verdict": {**verdict, "confidence": 3}}, req)
    with pytest.raises(ValueError, match="excluded"):
        automation.panel_requests(task="t", instruction="i", candidate_diff="c", oracle_diff="o",
                                  judges=[("a", "openai"), ("b", "anthropic")], model_under_test_family="openai")
    with pytest.raises(ValueError, match="two model families"):
        automation.panel_requests(task="t", instruction="i", candidate_diff="c", oracle_diff="o",
                                  judges=[("a", "google"), ("b", "google")], model_under_test_family="openai")


def test_admission_and_attribution_rules():
    clean = {"findings": [], "admit": True}
    leak = {"findings": [{"kind": "leakage", "citation": "TASK.md line 3"}], "admit": False}
    assert automation.admission(oracle_passes=False, base_fails=True, audits=None, blind=None)["state"] == "needs_fix"
    assert automation.admission(oracle_passes=True, base_fails=True, audits=None, blind=None)["state"] == "provisional"
    assert automation.admission(oracle_passes=True, base_fails=True, audits=[clean, leak],
                                blind=[{"passed": True}])["state"] == "needs_fix"
    wrongly_rejected = [{"passed": False, "adjudication": {"cause": "task", "citation": "x"}}]
    assert automation.admission(oracle_passes=True, base_fails=True, audits=[clean, clean],
                                blind=wrongly_rejected)["state"] == "needs_fix"
    assert automation.admission(oracle_passes=True, base_fails=True, audits=[clean, clean],
                                blind=[{"passed": True}])["state"] == "admitted"
    agree = [{"cause": "harness", "confidence": .9, "evidence": []}] * 2
    assert automation.route_failure(agree)["action"] == "fix_harness_and_rerun"
    split = [{"cause": "model", "confidence": .9, "evidence": []}, {"cause": "task", "confidence": .9, "evidence": []}]
    assert automation.route_failure(split) == {"cause": "unresolved", "action": "rerun_once_then_reattribute",
                                               "counts_as_model_failure": False}


def test_deterministic_quality_flags_seeded_degradations():
    name = "review-conflict-predictor"
    agent = curriculum.agent_files(name)
    path = "tools/conflict_predictor.py"
    oracle = {path: curriculum.verifier_files(name)["reference"]}
    good = automation.deterministic_quality(base={path: agent[path]}, candidate=oracle, oracle=oracle, writable=[path])
    assert good["diff_size_vs_oracle"] == 1.0 and good["debug_beyond_oracle"] == good["todo_beyond_oracle"] == 0
    variants = automation.degrade(oracle[path])
    debug = automation.deterministic_quality(base={path: agent[path]}, candidate={path: variants["debug_leftover"]},
                                             oracle=oracle, writable=[path])
    assert debug["debug_beyond_oracle"] == 1 and debug["todo_beyond_oracle"] == 1
    dead = automation.deterministic_quality(base={path: agent[path]}, candidate={path: variants["dead_code"]},
                                            oracle=oracle, writable=[path])
    assert dead["unreachable_statements"] >= 1
    outside = automation.deterministic_quality(base={path: agent[path], "x.py": b""},
                                               candidate={path: oracle[path], "x.py": b"y=1\n"},
                                               oracle=oracle, writable=[path])
    assert outside["files_outside_task"] == ["x.py"]
    assert automation.calibration_agreement([
        {"variant": v, "judge": j, "preferred_oracle": True} for v in variants for j in ("a", "b")])["admit_panel"]


def test_obscured_calibration_is_distinct_without_private_functions():
    source = b'def public():\n    descriptive_name = "descriptive_name"\n    return descriptive_name\n'
    variant = automation.degrade(source)["obscured_names"]
    assert variant != source
    assert b'"descriptive_name"' in variant and b"return _q0" in variant
    with pytest.raises(ValueError, match="distinct"):
        automation.degrade(b"def public():\n    return 1\n")


# --- MB-010c: harder, broader curriculum ------------------------------------------------

V2 = {"plan-dashboard-waves-v2": "plan-dashboard-waves", "review-conflict-predictor-v2": "review-conflict-predictor"}
CURRENT = {"orchestrate-voice-integration-v4": "orchestrate-voice-integration-v5",
           "kerrigan-plan-conflict-queue": "kerrigan-plan-conflict-queue-v3",
           "review-conflict-predictor-v3": "review-conflict-predictor-v4",
           "design-alethiometer-case-v2": "design-alethiometer-case-v3",
           "kerrigan-plan-conflict-queue-v2": "kerrigan-plan-conflict-queue-v3",
           "yv-relevance-instrument-v2": "yv-relevance-instrument-v3",
           "emv-thumbnails-gallery-v2": "emv-thumbnails-gallery-v3",
           "orchestrate-voice-integration-v3": "orchestrate-voice-integration-v5",
           "plan-dashboard-waves": "plan-dashboard-waves-v2", "review-conflict-predictor": "review-conflict-predictor-v4",
           "review-conflict-predictor-v2": "review-conflict-predictor-v4",
           "design-alethiometer-case": "design-alethiometer-case-v3",
           "yv-relevance-instrument": "yv-relevance-instrument-v3",
           "emv-thumbnails-gallery": "emv-thumbnails-gallery-v3",
           "orchestrate-voice-integration": "orchestrate-voice-integration-v5",
           "orchestrate-voice-integration-v2": "orchestrate-voice-integration-v5",
           "research-serverless-cost": "research-serverless-cost-v2"}
NON_PYTHON = {"typescript", "javascript"}
APP_OR_GAME_REPOS = {"Kixantrix/your-voice", "Kixantrix/event-media-vault", "Kixantrix/clinical-scribe",
                     "Kixantrix/sunday-league", "Kixantrix/foal-rescue-meadow", "Kixantrix/voxel-solar-wallpaper"}


def test_v1_retired_and_preserved_v2_corrections():
    retired = curriculum.retired()
    assert set(retired) == set(CURRENT)
    for old, new in CURRENT.items():
        assert retired[old]["superseded_by"] == new and retired[old]["reason"]
        if retired[old].get("evidence_pending"):  # native evidence not yet pushed; cited once it is
            assert "evidence" not in retired[old]
        elif old not in {"plan-dashboard-waves", "review-conflict-predictor"}:  # MB-009r retirements predate evidence files
            evidence = retired[old]["evidence"]
            assert (ROOT / evidence["path"]).is_file()
            assert hashlib.sha256((ROOT / evidence["path"]).read_bytes()).hexdigest() == evidence["sha256"]
    for v2, v1 in V2.items():
        assert curriculum.meta(v2)["supersedes"] == v1
        # v1 package bytes stay frozen and calibrated; v2 is a separate package.
        assert curriculum.descriptor(v1) == json.loads((curriculum.HERE / v1 / "manifest.json").read_text())
        assert curriculum.descriptor(v2)["id"] != curriculum.descriptor(v1)["id"]
    plan = json.loads(curriculum.verifier_files("plan-dashboard-waves-v2")["reference"])
    assert sorted("|".join(sorted(c["tasks"])) for c in plan["conflicts"]) == ["M2.2|M2.3", "M2.2|M2.4", "M2.3|M2.4"]
    review = curriculum.agent_files("review-conflict-predictor-v2")["TASK.md"].decode()
    assert "contains task lines" in review and "remains a clean zero-wave success" in review
    rows = {r["original_id"]: r for r in curriculum.rows("review-conflict-predictor-v2")}
    fail_loud = rows["tests/test_conflict_predictor.py::TestRun::test_task_lines_without_touch_annotations_fail_loud"]
    assert not any("/work/" in json.dumps(c) for c in fail_loud["clauses"])
    assert rows["tests/test_conflict_predictor.py::TestRun::test_missing_tasks_file_returns_1"]["clauses"] == [
        ("path_equal", [0, "rc"], 1)]


def test_every_family_has_a_calibrated_package():
    families = {curriculum.meta(name)["family"] for name in curriculum.PACKAGES if name not in curriculum.retired()}
    families |= {"Implement"}
    assert families == set(curriculum.FAMILIES)
    for family in ("Research", "Orchestrate", "Design", "Understand and plan"):
        packaged = [n for n in curriculum.PACKAGES if curriculum.meta(n)["family"] == family and n not in curriculum.retired()]
        assert packaged and all(curriculum.meta(n)["outcome_evidence"] != "model_judge" for n in packaged)


def test_long_horizon_set_spans_repos_languages_and_apps():
    long = [n for n in curriculum.PACKAGES if curriculum.meta(n).get("long_horizon")]
    assert len(long) >= 4
    for name in long:
        info = curriculum.meta(name)
        size = curriculum.task_size(name)
        assert size["oracle_files_changed"] >= 2 and size["oracle_lines_added"] + size["oracle_lines_removed"] >= 80
        assert size["hidden_checks"] >= 10
        assert len(curriculum.candidates(name)) >= 2, "long-horizon packages require multi-file changes"
    repos = {curriculum.meta(n)["source"]["repo"] for n in long}
    suffix = {".ts": "typescript", ".mjs": "javascript", ".js": "javascript", ".py": "python"}
    languages = {suffix.get(Path(p).suffix) for n in long for p in curriculum.candidates(n)}
    assert len(repos) >= 3 and len(languages & NON_PYTHON) >= 2
    assert repos & APP_OR_GAME_REPOS
    assert any(curriculum.meta(n)["source"]["history_status"] == "merged"
               and curriculum.meta(n)["privacy"] == "public" for n in long), "at least one exact merged public PR"


@pytest.mark.parametrize("name", [n for n in curriculum.PACKAGES if len(curriculum.candidates(n)) > 1])
def test_multi_artifact_bundles_are_exact(name, tmp_path):
    base = specs.base(name)
    files = specs.unbundle(name, base)
    assert sorted(files) == sorted(curriculum.candidates(name))
    with pytest.raises(ValueError, match="bundle"):
        specs.unbundle(name, specs.bundle({**files, "extra.txt": b"x"}))
    with pytest.raises(ValueError, match="bundle"):
        specs.unbundle(name, specs.bundle({k: v for k, v in list(files.items())[1:]}))
    report = api.grade(specs.bundle({**files, "extra.txt": b"x"}), tmp_path / "receipt", task=name)
    assert report["status"] == "ungraded" and report["cleanup"]["proven"]


def test_review_v3_counts_only_extracted_globs_and_is_overlap_only():
    assert curriculum.meta("review-conflict-predictor-v3")["supersedes"] == "review-conflict-predictor-v2"
    task = curriculum.agent_files("review-conflict-predictor-v3")["TASK.md"].decode()
    assert "file overlap only" in task and "must not affect wave assignment" in task
    oracle = curriculum.verifier_files("review-conflict-predictor-v3")["reference"].decode()
    assert oracle.count("touch_count += len(globs)") == 2 and "touch_count += 1" not in oracle
    rows = {r["original_id"]: r for r in curriculum.rows("review-conflict-predictor-v3")}
    assert "MB-010c::empty touch glob is not file-scope signal" in rows
    assert "MB-010c::dependencies do not affect overlap-only waves" in rows
    receipt = json.loads(calibrate.path("review-conflict-predictor-v3").read_text())
    assert [p["verdict"] for p in receipt["phases"]] == ["fail", "pass"]


def test_review_v3_rejects_the_v2_oracle_gap(tmp_path):
    report = api.grade(specs.reference("review-conflict-predictor-v2"), tmp_path / "r", task="review-conflict-predictor-v3")
    assert report["verdict"] == "fail"
    assert [a["original_id"] for a in report["assertions"] if not a["passed"]] == [
        "MB-010c::empty touch glob is not file-scope signal"]


def test_design_v2_documents_use_exact_rounding(tmp_path):
    info = curriculum.meta("design-alethiometer-case-v2")
    assert info["supersedes"] == "design-alethiometer-case"
    assert "rounded half-up" in curriculum.agent_files("design-alethiometer-case-v2")["TASK.md"].decode()
    rows = curriculum.rows("design-alethiometer-case-v2")
    docs = [c for r in rows if r["group"] == "docs" for c in r["clauses"]]
    assert docs and all(c[0] == "path_equal" for c in docs)
    assert all(c[3] < 0.01 for r in rows for c in r["clauses"] if c[0] == "path_within")
    oracle = json.loads(curriculum.verifier_files("design-alethiometer-case-v2")["reference"])["hardware/README.md"]
    assert "body is 36.9 mm tall" in oracle and "37.0" not in oracle
    v1 = api.grade(specs.reference("design-alethiometer-case"), tmp_path / "v1", task="design-alethiometer-case-v2")
    failed = [a["original_id"] for a in v1["assertions"] if not a["passed"]]
    assert v1["verdict"] == "fail" and failed == ["README size line matches the model", "README height table matches the model"]


def test_plan_queue_v2_states_at_least_once_semantics():
    task = curriculum.agent_files("kerrigan-plan-conflict-queue-v2")["TASK.md"].decode()
    assert "at-least-once" in task and "double-apply" not in task
    assert curriculum.verifier_files("kerrigan-plan-conflict-queue-v2")["reference"] == \
        curriculum.verifier_files("kerrigan-plan-conflict-queue")["reference"]
    assert curriculum.rows("kerrigan-plan-conflict-queue-v2") == curriculum.rows("kerrigan-plan-conflict-queue")
    cleanup = [r for r in curriculum.rows("kerrigan-plan-conflict-queue-v2") if r["probe"]["scenario"] == "replayCleanupFailure"]
    assert len(cleanup) == 1 and not any(c[1][:1] == ["second"] for c in cleanup[0]["clauses"])


@pytest.mark.parametrize("v2,v1,phrase", [
    ("yv-relevance-instrument-v2", "yv-relevance-instrument", "own enumerable"),
    ("emv-thumbnails-gallery-v2", "emv-thumbnails-gallery", "is not isolated"),
])
def test_instruction_only_v2_keeps_oracle_and_checks(v2, v1, phrase):
    assert curriculum.meta(v2)["supersedes"] == v1
    assert curriculum.verifier_files(v2) == curriculum.verifier_files(v1)
    assert curriculum.rows(v2) == curriculum.rows(v1)
    text = b"".join(data for path, data in curriculum.agent_files(v2).items() if path.endswith(".md")).decode()
    assert phrase in text
    changed = {p for p, d in curriculum.agent_files(v2).items() if curriculum.agent_files(v1).get(p) != d}
    assert changed <= {"TASK.md", "evals/relevance/SPEC.md", "policy.json"}


def test_emv_v2_states_real_height_and_exists_abort():
    task = curriculum.agent_files("emv-thumbnails-gallery-v2")["TASK.md"].decode()
    assert "sets `height` to\n`rowHeight`" in task and "whole run rejects" in task
    scenarios = curriculum.verifier_files("emv-thumbnails-gallery-v2")["sandbox/scenarios.mjs"].decode()
    assert "exists" not in scenarios.replace("thumbnail exists", "")


def test_research_v2_unknowns_check_is_set_based(tmp_path):
    name = "research-serverless-cost-v2"
    assert curriculum.meta(name)["supersedes"] == "research-serverless-cost"
    assert curriculum.agent_files(name) == curriculum.agent_files("research-serverless-cost")
    assert curriculum.verifier_files(name)["reference"] == curriculum.verifier_files("research-serverless-cost")["reference"]
    reference = json.loads(specs.reference(name))
    reordered = json.dumps({**reference, "unknowns": list(reversed(reference["unknowns"]))}).encode()
    duplicated = json.dumps({**reference, "unknowns": reference["unknowns"] + reference["unknowns"][:1]}).encode()
    v2 = api.grade(reordered, tmp_path / "v2", task=name)
    v1 = api.grade(reordered, tmp_path / "v1", task="research-serverless-cost")
    dup = api.grade(duplicated, tmp_path / "dup", task=name)
    assert v2["verdict"] == "pass"
    assert [a["original_id"] for a in v1["assertions"] if not a["passed"]] == ["unknowns list exactly the undeterminable keys"]
    assert [a["original_id"] for a in dup["assertions"] if not a["passed"]] == ["unknowns list exactly the undeterminable keys"]


def _orchestrate_variant(code_from, categories):
    files = specs.unbundle("orchestrate-voice-integration", specs.reference(code_from))
    ledger = json.loads(files["INTEGRATION.json"])
    ledger["defects"] = [{"category": c, "files": ["src/server.ts"]} for c in categories]
    files["INTEGRATION.json"] = (json.dumps(ledger, indent=2) + "\n").encode()
    return specs.bundle(files)


REQUIRED_DEFECTS = ["handshake-mismatch", "version-skew", "requirement-dropped", "content-in-telemetry", "unit-mismatch"]


@pytest.mark.parametrize("label,code_from,extra,failed", [
    ("sonnet-style: genuine leak listed and fixed", "orchestrate-voice-integration-v2", ["memory-leak"], []),
    ("five only, leak left unfixed", "orchestrate-voice-integration", [], []),
    ("mai-style: nonexistent auth-bypass", "orchestrate-voice-integration", ["auth-bypass"],
     ["no nonexistent or duplicate defects listed"]),
    ("leak claimed but not fixed", "orchestrate-voice-integration", ["memory-leak"],
     ["a listed extra defect is actually fixed"]),
    ("missing a required defect", "orchestrate-voice-integration-v2", ["memory-leak"], None),
])
def test_orchestrate_v2_ledger_rewards_real_work(label, code_from, extra, failed, tmp_path):
    categories = REQUIRED_DEFECTS + extra if failed is not None else REQUIRED_DEFECTS[1:] + extra
    report = api.grade(_orchestrate_variant(code_from, categories), tmp_path / "r", task="orchestrate-voice-integration-v2")
    observed = [a["original_id"] for a in report["assertions"] if not a["passed"]]
    assert observed == (failed if failed is not None else ["required integration defects recorded"]), label


def test_orchestrate_v2_audit_record():
    info = curriculum.meta("orchestrate-voice-integration-v2")
    audited = {d["category"] for d in info["audited_base_defects"]}
    assert audited == set(REQUIRED_DEFECTS) | {"memory-leak"}
    assert set(info["audited_absent"]) == {"auth-bypass", "race-condition"}
    base = curriculum.agent_files("orchestrate-voice-integration-v2")
    for defect in info["audited_base_defects"]:
        assert defect["line"] <= base[defect["file"]].decode().count("\n") + 1
    task = base["TASK.md"].decode()
    assert "Listing a defect that does not exist fails" in task


@pytest.mark.parametrize("label,code_from,extra,failed", [
    ("fixed race-condition", "orchestrate-voice-integration-v3", ["race-condition"], []),
    ("fixed race-condition and memory-leak", "orchestrate-voice-integration-v3", ["memory-leak", "race-condition"], []),
    ("unfixed race-condition", "orchestrate-voice-integration-v2", ["race-condition"], ["a listed race-condition is actually fixed"]),
    ("auth-bypass", "orchestrate-voice-integration-v3", ["auth-bypass"], ["no nonexistent or duplicate defects listed"]),
])
def test_orchestrate_v3_race_condition_ledger(label, code_from, extra, failed, tmp_path):
    report = api.grade(_orchestrate_variant(code_from, REQUIRED_DEFECTS + extra), tmp_path / "r",
                       task="orchestrate-voice-integration-v3")
    assert [a["original_id"] for a in report["assertions"] if not a["passed"]] == failed, label


def test_orchestrate_v3_audit_record():
    info = curriculum.meta("orchestrate-voice-integration-v3")
    assert {d["category"] for d in info["audited_base_defects"]} == set(REQUIRED_DEFECTS) | {"memory-leak", "race-condition"}
    assert set(info["audited_absent"]) == {"auth-bypass"}
    assert info["admission_evidence"]["sha256"].startswith("c049c7b4")


V4 = "orchestrate-voice-integration-v4"
V4_ID_LINE = "    const id = `s${this.count}`;\n"


def _orchestrate_v4(server_edits=(), drop=()):
    files = specs.unbundle(V4, specs.reference(V4))
    server = files["src/server.ts"].decode()
    for old, new in server_edits:
        assert server.count(old) == 1, old
        server = server.replace(old, new)
    files["src/server.ts"] = server.encode()
    ledger = json.loads(files["INTEGRATION.json"])
    ledger["defects"] = [d for d in ledger["defects"] if d["category"] not in drop]
    files["INTEGRATION.json"] = (json.dumps(ledger, indent=2) + "\n").encode()
    return specs.bundle(files)


@pytest.mark.parametrize("label,edits,failed", [
    ("randomUUID ids", [(V4_ID_LINE, "    const id = crypto.randomUUID();\n")], []),
    ("opaque prefixed ids", [(V4_ID_LINE, "    const id = `sess_${(this.count * 7919).toString(36)}`;\n")], []),
    ("id collides across sessions", [(V4_ID_LINE, "    const id = \"session\";\n")],
     ["R1 session ids opaque, stable, distinct and accepted"]),
    ("id changes mid-session", [
        (V4_ID_LINE, "    const id = crypto.randomUUID();\n"),
        ("        session.pending = message.correlationId;\n",
         "        session.id = crypto.randomUUID();\n        session.pending = message.correlationId;\n")],
     ["R1 session ids opaque, stable, distinct and accepted"]),
    ("empty id", [(V4_ID_LINE, "    const id = \"\";\n")], ["R1 session ids opaque, stable, distinct and accepted"]),
    ("renamed telemetry events", [
        ('name: "response"', 'name: "turn_answered"'), ('name: "cancelled"', 'name: "turn_cancelled"'),
        ('name: "audio"', 'name: "audio_chunk"')], []),
])
def test_orchestrate_v4_opaque_session_ids(label, edits, failed, tmp_path):
    report = api.grade(_orchestrate_v4(edits), tmp_path / "r", task=V4)
    assert report["status"] == "graded", label
    assert [a["original_id"] for a in report["assertions"] if not a["passed"]] == failed, label


def test_orchestrate_v4_retention_allows_constant_state(tmp_path):
    keep_tokens = [("    this.options = options;\n", "    this.options = options;\n    this.allowed = new Set(options.tokens);\n")]
    report = api.grade(_orchestrate_v4(keep_tokens), tmp_path / "r", task=V4)
    assert [a["original_id"] for a in report["assertions"] if not a["passed"]] == []


def test_orchestrate_v4_audit_record():
    info = curriculum.meta(V4)
    assert info["supersedes"] == "orchestrate-voice-integration-v3"
    assert info["admission_evidence"]["sha256"].startswith("1aa97a50")
    assert {d["category"] for d in info["audited_base_defects"]} == set(REQUIRED_DEFECTS) | {"memory-leak", "race-condition"}
    rows = json.loads((curriculum.HERE / V4 / "hidden" / "rows.json").read_text())
    literal = [c for r in rows for c in r["clauses"] if c[1][-1:] == ["sessionId"]]
    assert literal == []


def _edited_reference(task, path, old, new):
    files = specs.unbundle(task, specs.reference(task))
    text = files[path].decode()
    assert text.count(old) == 1, old
    files[path] = text.replace(old, new).encode()
    return files[path] if len(files) == 1 else specs.bundle(files)


def _failed(bundle, task, tmp_path):
    report = api.grade(bundle, Path(tempfile.mkdtemp(dir=tmp_path)) / task, task=task)
    assert report["status"] == "graded", report.get("error")
    return [a["original_id"] for a in report["assertions"] if not a["passed"]]


LITERAL_AUDIT_VARIANTS = [
    # (old version, new version, file, old text, new text, rows the old version wrongly failed)
    ("emv-thumbnails-gallery-v2", "emv-thumbnails-gallery-v3", "api/thumbnails.mjs",
     "for (const { name, metadata } of await store.list(prefix)) {",
     "for (const { name, metadata } of (await store.list(prefix)).reverse()) {",
     ["every new album image gets a planned thumbnail"]),
    ("emv-thumbnails-gallery-v2", "emv-thumbnails-gallery-v3", "web/gallery-layout.mjs",
     "      presized: sized,\n", "      presized: sized,\n      alt: item.name,\n",
     ["carousel containers are pre-sized from dimensions and use thumbnails"]),
    ("yv-relevance-instrument-v2", "yv-relevance-instrument-v3", "evals/relevance/score.ts",
     "    firedCount: shown.length,\n", "    firedCount: shown.length,\n    shownCount: shown.length,\n",
     ["precision, nDCG, misses and wrong reasons at k=5", "second arm scored at k=10",
      "unrated shown ids gain nothing", "zero ideal gain yields zero nDCG"]),
    ("kerrigan-plan-conflict-queue-v2", "kerrigan-plan-conflict-queue-v3",
     "apps/kerrigan-dashboard/src/lib/plan-queue.ts", "return `${safe}_${rand}`;", "return `${safe}+${rand}`;",
     ["enqueue writes one JSON entry holding the edit"]),
    ("design-alethiometer-case-v2", "design-alethiometer-case-v3", "hardware/stack.py",
     "GEAR_STANDOFF, HAND_STANDOFF = 8.0, 5.0", "GEAR_STANDOFF, HAND_STANDOFF = 8.0, 5",
     ["thinnest catalog hand-post standoff that keeps crystal clearance"]),
    ("review-conflict-predictor-v3", "review-conflict-predictor-v4", "tools/conflict_predictor.py",
     "            file=sys.stderr,\n        )\n        return 1\n", "            file=sys.stderr,\n        )\n        return 2\n",
     ["tests/test_conflict_predictor.py::TestRun::test_task_lines_without_touch_annotations_fail_loud",
      "MB-010c::CLI main propagates zero-signal failure", "MB-010c::empty touch glob is not file-scope signal"]),
]


@pytest.mark.parametrize("old,new,path,before,after,wrongly_failed", LITERAL_AUDIT_VARIANTS)
def test_literal_audit_accepts_valid_variants(old, new, path, before, after, wrongly_failed, tmp_path):
    variant = _edited_reference(new, path, before, after)
    assert _failed(variant, old, tmp_path) == wrongly_failed
    assert _failed(variant, new, tmp_path) == []


@pytest.mark.parametrize("new,path,before,after,still_failed", [
    ("kerrigan-plan-conflict-queue-v3", "apps/kerrigan-dashboard/src/lib/plan-queue.ts",
     "return `${safe}_${rand}`;", "return `${timestamp}/${rand}`;", "enqueue writes one JSON entry holding the edit"),
    ("review-conflict-predictor-v4", "tools/conflict_predictor.py",
     "            file=sys.stderr,\n        )\n        return 1\n", "            file=sys.stderr,\n        )\n        return 0\n",
     "MB-010c::CLI main propagates zero-signal failure"),
])
def test_literal_audit_keeps_real_failures(new, path, before, after, still_failed, tmp_path):
    assert still_failed in _failed(_edited_reference(new, path, before, after), new, tmp_path)


@pytest.mark.parametrize("new,old", [
    ("emv-thumbnails-gallery-v3", "emv-thumbnails-gallery-v2"), ("yv-relevance-instrument-v3", "yv-relevance-instrument-v2"),
    ("kerrigan-plan-conflict-queue-v3", "kerrigan-plan-conflict-queue-v2"),
    ("design-alethiometer-case-v3", "design-alethiometer-case-v2"), ("review-conflict-predictor-v4", "review-conflict-predictor-v3"),
])
def test_literal_audit_versions_keep_instruction_and_oracle(new, old):
    for rel in ["hidden/reference"] + sorted(str(p.relative_to(curriculum.HERE / old)) for p in (curriculum.HERE / old / "agent").rglob("*") if p.is_file()):
        assert (curriculum.HERE / new / rel).read_bytes() == (curriculum.HERE / old / rel).read_bytes(), rel
    info = curriculum.meta(new)
    assert info["supersedes"] == old
    evidence = info["admission_evidence"]
    assert evidence["path"].endswith("MB-010r-literal-audit.json")
    assert hashlib.sha256((ROOT / evidence["path"]).read_bytes()).hexdigest() == evidence["sha256"]


V5 = "orchestrate-voice-integration-v5"


def test_orchestrate_v5_guards_start_and_states_client_r7(tmp_path):
    # The v4 oracle's unguarded start() now fails exactly the out-of-order check; the v5 oracle passes.
    assert _failed(specs.reference("orchestrate-voice-integration-v4"), V5, tmp_path) == [
        "state machine ignores out-of-order controls"]
    restart = _edited_reference(V5, "src/session.ts", '    if (this.state !== "idle") return;\n    this.state = "joining";',
                                '    this.state = "joining";')
    assert _failed(restart, V5, tmp_path) == ["state machine ignores out-of-order controls"]
    info = curriculum.meta(V5)
    assert info["round"] == 3 and info["supersedes"] == "orchestrate-voice-integration-v4"
    agent = curriculum.HERE / V5 / "agent"
    assert "accounting" not in (agent / "briefs" / "L2-orchestration.md").read_text()
    assert "`start` unless idle" in (agent / "TASK.md").read_text()


def test_no_human_time_estimates_in_current_metadata():
    """User, 2026-11-26: difficulty is agent-native task size, never estimated human time."""
    retired = curriculum.retired()
    for name in curriculum.PACKAGES:
        assert not set(curriculum.HUMAN_TIME_FIELDS) & set(curriculum.meta(name))
        if name not in retired and curriculum.meta(name).get("round") == 3:
            raw = json.loads((curriculum.HERE / name / "task.json").read_text())
            assert not set(curriculum.HUMAN_TIME_FIELDS) & set(raw), name
    catalog = (ROOT / "benchmarks/michael/curriculum/catalog.json").read_text()
    assert "human_minutes" not in catalog and "human minutes" not in catalog.lower()
    for name in curriculum.PACKAGES:
        if name not in retired:
            toml = (ROOT / "benchmarks/michael/curriculum/harbor" / name / "task.toml").read_text()
            assert "human" not in toml and "task_size = " in toml
