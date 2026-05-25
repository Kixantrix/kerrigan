#!/usr/bin/env python3
"""Tests for pr-promote helper script and docs references."""

import os
import shutil
import stat
import subprocess
import textwrap
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
        "gh repo view --json nameWithOwner --jq",
        "gh pr ready",
        "gh pr update-branch",
        "gh api --method POST",
        "gh pr merge",
    ):
        assert content.index(token) > dry_run_idx


def test_pr_promote_resolves_repo_name_with_owner() -> None:
    content = _read("tools/pr-promote.ps1")
    assert "nameWithOwner" in content
    assert "--jq '.nameWithOwner'" in content


def test_pr_promote_aborts_when_update_branch_fails(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        raise AssertionError("pwsh is required for this test")

    call_log = tmp_path / "gh-calls.log"
    gh = tmp_path / "gh"
    gh.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            echo "$*" >> "$GH_CALL_LOG"
            if [[ "$1" == "repo" && "$2" == "view" ]]; then
              echo "Kixantrix/kerrigan"
              exit 0
            fi
            if [[ "$1" == "pr" && "$2" == "ready" ]]; then
              exit 0
            fi
            if [[ "$1" == "pr" && "$2" == "update-branch" ]]; then
              echo "update branch failed" >&2
              exit 42
            fi
            if [[ "$1" == "api" ]]; then
              exit 0
            fi
            if [[ "$1" == "pr" && "$2" == "merge" ]]; then
              exit 0
            fi
            exit 0
            """
        ),
        encoding="utf-8",
    )
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["GH_CALL_LOG"] = str(call_log)
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    result = subprocess.run(
        [pwsh, "-NoProfile", "-File", str(REPO_ROOT / "tools/pr-promote.ps1"), "123"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    calls = call_log.read_text(encoding="utf-8")
    assert "pr update-branch 123" in calls
    assert "requested_reviewers" not in calls
    assert "pr merge 123" not in calls


def test_playbook_lists_promote() -> None:
    content = _read("playbooks/cloud-agent-pr-loop.md")
    assert "pr-promote.ps1" in content


def test_kerrigan_md_lists_promote() -> None:
    content = _read(".github/agents/kerrigan.md")
    assert "pr-promote.ps1" in content
