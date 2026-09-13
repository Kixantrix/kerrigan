#!/usr/bin/env python3
"""Tests for test-strategy skill files."""

from pathlib import Path

import pytest


SKILLS = [
    "test-ladder",
    "test-environment",
    "e2e-test",
    "scenario-test",
]
REQUIRED_SECTIONS = [
    "**When:**",
    "**Output:**",
    "**Why:**",
    "## Contract",
    "## Shape",
    "## What to test",
    "## What not to test",
]


def test_each_skill_has_required_sections():
    repo_root = Path(__file__).resolve().parents[2]
    for skill_name in SKILLS:
        skill_file = repo_root / ".github" / "skills" / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Missing skill file: {skill_file}"
        content = skill_file.read_text(encoding="utf-8")
        assert len(content.splitlines()) <= 120, f"{skill_name} skill is too long"
        for section in REQUIRED_SECTIONS:
            assert section in content, f"{skill_name} missing section: {section}"


@pytest.mark.parametrize("skill_name", SKILLS)
def test_skills_link_canonical_risk_and_evidence_contract(skill_name):
    root = Path(__file__).resolve().parents[2]
    skill = root / ".github" / "skills" / skill_name / "SKILL.md"
    target = "../../../docs/test-strategy.md"
    anchor = "risk-trigger-and-evidence-matrix"
    content = skill.read_text(encoding="utf-8")
    assert f"]({target}#{anchor})" in content
    doc = (skill.parent / target).resolve()
    assert doc == root / "docs" / "test-strategy.md"
    assert "## Risk, trigger and evidence matrix" in doc.read_text(encoding="utf-8")
    assert "evidence" in content.lower()
    assert "logs" in content or "retained-log" in content


@pytest.mark.parametrize(("skill_name", "required"), [
    ("test-ladder", ["unknown selection means broader tests", "shadow selection",
                     "checksum-pinned", "Real model/device checks"]),
    ("test-environment", ["full tested SHA", "input digests", "runtime/device",
                          "retained logs", "combined merge candidates"]),
    ("e2e-test", ["transitive consumers", "broader tests", "Shadow selection",
                  "full tested SHA"]),
    ("scenario-test", ["full tested SHA", "clean/patch state", "model/input",
                       "pending-attestation:", "retained logs", "warmup, sample count"]),
])
def test_skills_preserve_selection_and_handoff_safeguards(skill_name, required):
    root = Path(__file__).resolve().parents[2]
    content = " ".join((root / ".github" / "skills" / skill_name / "SKILL.md")
                       .read_text(encoding="utf-8").split())
    for phrase in required:
        assert phrase in content, f"{skill_name} must retain: {phrase}"


def test_scenario_contract_preserves_manual_human_completion_without_attestation():
    root = Path(__file__).resolve().parents[2]
    content = (root / ".github" / "skills" / "scenario-test" / "SKILL.md").read_text(encoding="utf-8")
    contract = content.split("## Contract\n", 1)[1].split("\n## ", 1)[0]
    bullets = [" ".join(bullet.split()) for bullet in contract.split("\n- ")]
    attestation = [bullet for bullet in bullets if "pending-attestation:" in bullet]
    assert len(attestation) == 1
    assert attestation[0].startswith("For `local-attested-*` only,")
    manual = next(bullet for bullet in bullets if bullet.startswith("For `manual-human`,"))
    assert "close the AC when a qualified reviewer accepts all named rubric criteria" in manual
    assert "retains the decision with matching evidence" in manual
    assert "no local-attestation marker is required" in manual
