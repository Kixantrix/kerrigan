#!/usr/bin/env python3
"""Tests for the new-issue.ps1 dispatch helper."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_new_issue_has_help_sections() -> None:
    content = _read("tools/new-issue.ps1")
    for token in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER", ".EXAMPLE"):
        assert token in content


def test_new_issue_normalizes_copilot_assignee() -> None:
    # The Copilot coding agent is a Bot actor: gh only accepts the '@copilot'
    # handle for it. Bare 'copilot' fails with "'copilot' not found". The helper
    # must normalize the known aliases to '@copilot' so `-Assignee copilot` works
    # without any GraphQL fallback.
    content = _read("tools/new-issue.ps1")
    assert "'copilot', '@copilot', 'copilot-swe-agent'" in content
    assert "$Assignee = '@copilot'" in content
    assert "$Assignee.ToLowerInvariant()" in content


def test_new_issue_uses_body_file_single_invocation() -> None:
    # Guards the heredoc double-fire footgun: the body must come from --body-file
    # and gh must be invoked exactly once via the splatted arg array.
    content = _read("tools/new-issue.ps1")
    assert "--body-file" in content
    assert content.count("& gh @args") == 1
