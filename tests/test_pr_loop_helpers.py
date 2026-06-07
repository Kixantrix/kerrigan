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


def test_pr_watch_guards_transient_failures() -> None:
    # Regression (2026-06-03): a transient `gh pr list` network failure is not a
    # terminating PowerShell error, so it yielded an empty map and the watcher
    # reported every watched PR as "left the open set" (merged/closed). The
    # signature function must check the gh exit code; the baseline must retry
    # transient failures; and an empty poll against a non-empty baseline must be
    # CONFIRMED with a re-poll rather than skipped forever (otherwise a genuine
    # single-PR merge would never wake the watcher).
    content = _read("tools/pr-watch.ps1")
    assert "$LASTEXITCODE -ne 0" in content
    assert "gh pr list failed" in content
    # Baseline retries transient failures instead of dying on a startup blip.
    assert "Get-PrSignatureMapWithRetry" in content
    # Empty-poll ambiguity is resolved by a confirm re-poll, and a confirmed
    # empty result is allowed to fall through to the delta (genuine mass-merge).
    assert "confirm re-poll" in content.lower()
    assert "$confirm = Get-PrSignatureMap" in content


def test_pr_watch_mine_mode_derives_author_set() -> None:
    # -Mine scopes the watch to my + Copilot-authored PRs, re-derived each poll
    # so new cloud PRs auto-join and merged ones drop without relaunching.
    content = _read("tools/pr-watch.ps1")
    assert "[switch]$Mine" in content
    assert "gh api user --jq" in content
    assert "'Copilot'" in content
    # The author filter is threaded through the per-cycle signature map.
    assert "-OnlyAuthors" in content
    # Regression (2026-06-08): the Copilot coding agent's author.login from
    # `gh pr list --json author` is 'app/copilot-swe-agent', not 'Copilot', so an
    # exact-string compare silently excluded every cloud PR. The filter must match
    # any copilot-ish login case-insensitively.
    assert "(?i)copilot" in content


def test_pr_watch_suppresses_wip_head_noise() -> None:
    # A head-only change while a PR is still draft+wip is the cloud agent
    # iterating mid-build (many commits/min) — non-actionable. The delta must
    # suppress it (still firing on wip->ready, merge, and review changes).
    content = _read("tools/pr-watch.ps1")
    assert "$onlyHeadChanged" in content
    assert "$stillDraftWip" in content
    # The signature fields it compares (state/draft/wip/reviewDecision unchanged,
    # head changed) and the draft+wip guard.
    assert "'draft'" in content and "'wip'" in content


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


def test_clean_build_uses_separator_aware_containment() -> None:
    # Safety regression: a bare StartsWith($repoRoot) check would treat a sibling
    # like `repo-backup` as inside `repo` (prefix collision), letting a deletion
    # tool escape the repo root. The containment must be separator-aware.
    content = _read("tools/clean-build.ps1")
    assert "DirectorySeparatorChar" in content
    assert "$rootWithSep" in content
    # Single-walk: must not run a recursive Get-ChildItem per pattern name.
    assert "-Filter $name" not in content


def test_new_pr_validates_inputs() -> None:
    # Regression: body file must be a real file (not a directory) and normalized
    # to an absolute path; a detached HEAD must be rejected rather than passing
    # the literal 'HEAD' to gh.
    content = _read("tools/new-pr.ps1")
    assert "-PathType Leaf" in content
    assert "$Head -eq 'HEAD'" in content
