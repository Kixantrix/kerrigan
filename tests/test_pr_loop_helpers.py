#!/usr/bin/env python3
"""Tests for PR loop helper scripts and docs."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_pr_doctor_has_help_and_sections() -> None:
    content = _read("tools/pr-doctor.ps1")
    for token in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER", ".EXAMPLE"):
        assert token in content

    for section in (
        "== PR STATE ==",
        "== LAST 5 COMMITS ==",
        "== STATUS CHECKS ==",
        "== ACTION_REQUIRED WORKFLOW RUNS ==",
        "== REVIEW THREAD COUNTS ==",
        "== MOST RECENT REVIEW ==",
    ):
        assert section in content


def test_pr_resolve_threads_has_required_switches() -> None:
    content = _read("tools/pr-resolve-threads.ps1")
    for token in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER", ".EXAMPLE"):
        assert token in content

    assert "[switch]$DryRun" in content
    assert "[switch]$Confirm" in content
    assert "resolveReviewThread" in content


def test_pr_resolve_threads_binds_thread_id_to_local() -> None:
    # Regression: `-f threadId=$thread.id` makes PowerShell stringify $thread
    # (its type name) and append literal ".id", sending a garbage thread id so
    # the resolve silently no-ops. The property must be bound to a local first.
    content = _read("tools/pr-resolve-threads.ps1")
    assert "threadId=$thread.id" not in content
    assert "$threadId = $thread.id" in content
    assert "threadId=$threadId" in content


def test_pr_rerun_pending_filters_by_status() -> None:
    content = _read("tools/pr-rerun-pending.ps1")
    for token in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER", ".EXAMPLE"):
        assert token in content

    assert "action_required" in content
    assert "gh run rerun" in content


def test_pr_redispatch_posts_and_rearms() -> None:
    content = _read("tools/pr-redispatch.ps1")
    for token in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER", ".EXAMPLE"):
        assert token in content

    assert "[string]$Body" in content
    assert "gh pr comment" in content
    assert "gh pr merge" in content
    assert "--auto --squash" in content


def test_gitignore_covers_pr_md() -> None:
    content = _read(".gitignore")
    assert "pr_*.md" in content


def test_playbook_present_and_links_helpers() -> None:
    playbook = REPO_ROOT / "playbooks" / "cloud-agent-pr-loop.md"
    assert playbook.exists()

    content = playbook.read_text(encoding="utf-8")
    assert len(content.splitlines()) <= 120
    for script in (
        "pr-doctor.ps1",
        "pr-resolve-threads.ps1",
        "pr-rerun-pending.ps1",
        "pr-redispatch.ps1",
    ):
        assert script in content

    assert "action_required" in content
    assert "auto-merge" in content


def test_kerrigan_md_links_helpers() -> None:
    content = _read(".github/agents/kerrigan.md")
    assert "## PR loop helpers" in content
    for script in (
        "pr-doctor.ps1",
        "pr-resolve-threads.ps1",
        "pr-rerun-pending.ps1",
        "pr-redispatch.ps1",
    ):
        assert script in content
