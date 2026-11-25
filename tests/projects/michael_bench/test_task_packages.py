"""Integration checks for trusted cloud-linux historical package staging."""

import json
import os
from pathlib import Path
import sys

import pytest

TASKS = Path(__file__).resolve().parents[3] / "benchmarks" / "michael" / "tasks"
sys.path.insert(0, str(TASKS))
from packages import (
    CASES, HERE, agent_files, bundle_digest, calibrate, check_export, descriptor, stage,
)


@pytest.mark.parametrize("name", CASES)
def test_frozen_export_and_contract(name, tmp_path):
    frozen = json.loads((HERE / name / "manifest.json").read_text())
    assert descriptor(name) == frozen
    destination = tmp_path / "agent"
    digest = stage(name, destination)
    assert len(digest) == 64
    assert check_export(name, destination) == digest
    assert {p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()} == set(agent_files(name))
    assert not (destination / ".git").exists()


@pytest.mark.parametrize("contamination", [".git/config", "hidden/tests.py", "solution.patch"])
def test_rejects_extra_files(tmp_path, contamination):
    destination = tmp_path / "agent"
    stage("validator", destination)
    extra = destination / contamination
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("contamination")
    with pytest.raises(ValueError, match="allowlist"):
        check_export("validator", destination)


def test_rejects_modified_source_and_symlink(tmp_path):
    destination = tmp_path / "agent"
    stage("validator", destination)
    source = destination / CASES["validator"]["source"]
    source.write_text(source.read_text() + "\n# solution\n")
    with pytest.raises(ValueError, match="allowlist"):
        check_export("validator", destination)
    source.unlink()
    source.symlink_to(HERE / "hidden" / "validator.py")
    with pytest.raises(ValueError, match="symlink"):
        check_export("validator", destination)


def test_rejects_empty_history_directory(tmp_path):
    destination = tmp_path / "agent"
    stage("validator", destination)
    (destination / ".git").mkdir()
    with pytest.raises(ValueError, match="directory allowlist"):
        check_export("validator", destination)


def test_rejects_special_file(tmp_path):
    destination = tmp_path / "agent"
    stage("validator", destination)
    os.mkfifo(destination / "pipe")
    with pytest.raises(ValueError, match="special file"):
        check_export("validator", destination)


@pytest.mark.parametrize("name", CASES)
def test_retained_calibration_denominators(name):
    receipt = json.loads((HERE / name / "calibration.json").read_text())
    assert receipt["source_sha256"]
    assert receipt["verifier_sha256"]
    assert receipt["export_sha256"] == bundle_digest(agent_files(name))
    preservation, regression, reference = receipt["phases"]
    assert preservation["counts"]["passed"] == preservation["counts"]["tests"] > 0
    assert regression["counts"]["failures"] > 0
    assert regression["returncode"] == 1
    assert reference["counts"]["passed"] == reference["counts"]["tests"]
    assert reference["counts"]["tests"] == preservation["counts"]["tests"] + regression["counts"]["tests"]
    for phase in receipt["phases"]:
        assert phase["counts"]["errors"] == phase["counts"]["skipped"] == 0
        assert phase["seconds"] > 0
        assert phase["command"]


@pytest.mark.parametrize("name", CASES)
def test_fresh_calibration_matches_retained_counts(name):
    fresh = calibrate(name)
    retained = json.loads((HERE / name / "calibration.json").read_text())
    assert fresh["export_sha256"] == retained["export_sha256"]
    assert fresh["verifier_sha256"] == retained["verifier_sha256"]
    assert [phase["counts"] for phase in fresh["phases"]] == [
        phase["counts"] for phase in retained["phases"]
    ]
