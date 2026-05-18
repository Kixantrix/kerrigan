#!/usr/bin/env python3
"""Tests for test-strategy skill files."""

from pathlib import Path


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
