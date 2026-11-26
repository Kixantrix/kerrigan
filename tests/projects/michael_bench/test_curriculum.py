"""MB-008 curriculum: catalog coverage, package exports, Docker calibration, contracts.

Integration/cloud-linux (Docker). Candidate bytes are only ever graded inside the
independent no-network Docker grader; no test imports candidate code on the host.
"""

import json
import os
from pathlib import Path
import re
import shutil

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
    assert set(packaged) == {*packages.CASES, *curriculum.PACKAGES}
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
    assert set(policy) == set(VALIDATOR_POLICY)
    for key, value in VALIDATOR_POLICY.items():
        if key not in {"condition", "source", "scratch", "read", "write"}:
            assert policy[key] == value, key
    agent = curriculum.agent_files(name) if name in curriculum.PACKAGES else packages.agent_files(name)
    assert policy["source"] in agent and policy["source"] in policy["write"]
    assert set(policy["write"]) == {policy["source"], policy["scratch"]}
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
