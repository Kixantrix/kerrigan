from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_pr_doctor_has_help_and_sections() -> None:
    content = _read("tools/pr-doctor.ps1")
    for marker in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER", ".EXAMPLE"):
        assert marker in content

    for section in (
        "== PR state ==",
        "== Last 5 commits ==",
        "== Status checks (failures first) ==",
        "== action_required workflow runs ==",
        "== Review threads ==",
        "== Most recent review ==",
    ):
        assert section in content


def test_pr_resolve_threads_has_required_switches() -> None:
    content = _read("tools/pr-resolve-threads.ps1")
    assert ".SYNOPSIS" in content
    assert "[switch]$DryRun" in content
    assert "[switch]$Confirm" in content
    assert "resolveReviewThread" in content


def test_pr_rerun_pending_filters_by_status() -> None:
    content = _read("tools/pr-rerun-pending.ps1")
    assert ".SYNOPSIS" in content
    assert "action_required" in content
    assert "gh run rerun" in content


def test_pr_redispatch_posts_and_rearms() -> None:
    content = _read("tools/pr-redispatch.ps1")
    assert ".SYNOPSIS" in content
    assert "[string]$Body" in content
    assert "gh pr comment" in content
    assert "gh pr merge $PrNumber --auto --squash" in content


def test_gitignore_covers_pr_md() -> None:
    content = _read(".gitignore")
    assert "pr_*.md" in content


def test_playbook_present_and_links_helpers() -> None:
    path = REPO_ROOT / "playbooks" / "cloud-agent-pr-loop.md"
    content = path.read_text(encoding="utf-8")
    assert len(content.splitlines()) <= 120
    for name in (
        "pr-doctor.ps1",
        "pr-resolve-threads.ps1",
        "pr-rerun-pending.ps1",
        "pr-redispatch.ps1",
    ):
        assert name in content
    assert "action_required" in content
    assert "auto-merge" in content


def test_kerrigan_md_links_helpers() -> None:
    content = _read(".github/agents/kerrigan.md")
    assert "## PR loop helpers" in content
    for name in (
        "pr-doctor.ps1",
        "pr-resolve-threads.ps1",
        "pr-rerun-pending.ps1",
        "pr-redispatch.ps1",
    ):
        assert name in content
