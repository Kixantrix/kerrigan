#!/usr/bin/env python3
"""Tests for delegation-rubric updates."""

from pathlib import Path


def test_local_attested_rule_present():
    repo_root = Path(__file__).resolve().parents[2]
    rubric_file = repo_root / ".github" / "skills" / "delegation-rubric" / "SKILL.md"
    content = rubric_file.read_text(encoding="utf-8")

    assert "R-local-attested.platform-specific" in content
    assert "Windows NPU" in content
    assert "iOS" in content
    assert ".github/skills/e2e-test/SKILL.md" in content
