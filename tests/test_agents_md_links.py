#!/usr/bin/env python3
"""Tests for AGENTS.md testing section links."""

from pathlib import Path
import re


def test_testing_section_present_and_links_resolve():
    repo_root = Path(__file__).resolve().parent.parent
    agents_md = repo_root / "AGENTS.md"
    content = agents_md.read_text(encoding="utf-8")

    assert "## Testing" in content
    assert "docs/test-strategy.md" in content

    link_matches = re.findall(r"\((\./[^)]+)\)", content)
    for link in link_matches:
        path = (repo_root / link[2:]).resolve()
        assert path.exists(), f"Broken relative link in AGENTS.md: {link}"
