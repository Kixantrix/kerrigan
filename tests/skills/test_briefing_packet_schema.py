#!/usr/bin/env python3
"""Tests for briefing-packet skill schema updates."""

from pathlib import Path
import re


def test_ac_line_has_level_and_environment():
    repo_root = Path(__file__).resolve().parents[2]
    skill_file = repo_root / ".github" / "skills" / "briefing-packet" / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")

    pattern = re.compile(r"AC-<id>.*level:.*environment:.*test:")
    assert pattern.search(content), "AC schema line should include level and environment fields"
    assert "Declare level and environment for every AC" in content
    assert "`manual-human` requires a scenario test referenced by path" in content
