#!/usr/bin/env python3
"""Tests for pr-promote helper script and docs references."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_pr_promote_has_help_and_params() -> None:
    content = _read("tools/pr-promote.ps1")
    for token in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER", ".EXAMPLE"):
        assert token in content

    assert "[Parameter(Mandatory = $true, Position = 0)]" in content
    assert "[int]$PrNumber" in content
    assert "[switch]$DryRun" in content
    assert "[string]$MergeMethod = 'squash'" in content
    assert "[switch]$SkipReviewer" in content


def test_pr_promote_invokes_four_steps_in_order() -> None:
    content = _read("tools/pr-promote.ps1")
    for token in (
        "gh pr ready",
        "gh pr update-branch",
        "gh api --method POST",
        "requested_reviewers",
        "gh pr merge",
        "--auto",
    ):
        assert token in content

    assert content.index("gh pr ready") < content.index("gh pr merge")


def test_pr_promote_dry_run_branches_before_gh_calls() -> None:
    content = _read("tools/pr-promote.ps1")
    dry_run_idx = content.index("if ($DryRun)")
    for token in (
        "gh repo view --json nameWithOwner -q .nameWithOwner",
        "gh pr ready",
        "gh pr update-branch",
        "gh api --method POST",
        "gh pr merge",
    ):
        assert content.index(token) > dry_run_idx


def test_pr_promote_resolves_repo_name_with_owner() -> None:
    content = _read("tools/pr-promote.ps1")
    assert "nameWithOwner" in content


def test_playbook_lists_promote() -> None:
    content = _read("playbooks/cloud-agent-pr-loop.md")
    assert "pr-promote.ps1" in content


def test_kerrigan_md_lists_promote() -> None:
    content = _read(".github/agents/kerrigan.md")
    assert "pr-promote.ps1" in content
