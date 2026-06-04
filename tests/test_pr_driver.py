#!/usr/bin/env python3
"""Unit tests for tools/pr_driver_decide.py — pure decision function.

Covers every row of the state-machine table in the issue:
  WIP, Empty, Draft+real, Behind, CI gated, CI running, CI red,
  Threads (round 1), Threads (converged), Conflict, Clean, Merged, Stuck.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from pr_driver_decide import decide, _preflight_pass, _is_real_commit  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_open_state(**overrides):
    """Minimal valid open PR state that passes pre-flight."""
    state = {
        "title": "feat: add feature",
        "state": "OPEN",
        "files": 3,
        "commits": ["feat: implement feature"],
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "autoMergeArmed": True,
        "checkConclusions": ["success"],
        "checkNames": ["verify"],
        "checkStatuses": ["completed"],
        "actionRequiredRuns": 0,
        "unresolvedThreads": [],
        "latestReviewAt": None,
        "latestCommitAt": None,
        "latestReviewNewInlineComments": 0,
        "passCount": 0,
    }
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# Pre-flight / _is_real_commit
# ---------------------------------------------------------------------------

def test_is_real_commit_ordinary() -> None:
    assert _is_real_commit("feat: add stuff") is True


def test_is_real_commit_initial_plan() -> None:
    assert _is_real_commit("Initial plan") is False


def test_is_real_commit_initial_plan_case_insensitive() -> None:
    assert _is_real_commit("INITIAL PLAN") is False


def test_is_real_commit_merge_commit() -> None:
    assert _is_real_commit("Merge branch 'main' into feature") is False


def test_preflight_fails_no_files() -> None:
    assert _preflight_pass({"files": 0, "commits": ["feat: real work"]}) is False


def test_preflight_fails_only_placeholder_commits() -> None:
    assert _preflight_pass({"files": 2, "commits": ["Initial plan"]}) is False


def test_preflight_fails_only_merge_commits() -> None:
    assert _preflight_pass({"files": 2, "commits": ["Merge branch 'main'"]}) is False


def test_preflight_passes_with_real_commit() -> None:
    assert _preflight_pass({"files": 1, "commits": ["feat: real work"]}) is True


def test_preflight_passes_mixed_commits() -> None:
    assert _preflight_pass(
        {"files": 1, "commits": ["Initial plan", "feat: real work"]}
    ) is True


# ---------------------------------------------------------------------------
# State machine rows
# ---------------------------------------------------------------------------

# 1. MERGED
def test_merged_pr_returns_auto_done() -> None:
    result = decide({"state": "MERGED", "title": "done"})
    assert result["action"] == "AUTO_DONE"


def test_merged_pr_reason_mentions_merged() -> None:
    result = decide({"state": "MERGED", "title": "done"})
    assert "merged" in result["reason"].lower()


# 2. WIP
def test_wip_title_returns_skip() -> None:
    result = decide({"title": "[WIP] work in progress", "state": "OPEN"})
    assert result["action"] == "SKIP"


def test_wip_title_case_insensitive() -> None:
    result = decide({"title": "[wip] something", "state": "OPEN"})
    assert result["action"] == "SKIP"


def test_wip_mid_title() -> None:
    result = decide({"title": "feat: [WIP] half done", "state": "OPEN"})
    assert result["action"] == "SKIP"


# 3. Empty PR
def test_empty_pr_zero_files_escalates() -> None:
    result = decide({"title": "feat: thing", "state": "OPEN", "files": 0,
                     "commits": ["feat: real work"]})
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "empty-pr"


def test_empty_pr_only_placeholder_commits_escalates() -> None:
    result = decide({"title": "feat: thing", "state": "OPEN", "files": 3,
                     "commits": ["Initial plan"]})
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "empty-pr"


def test_empty_pr_never_auto_close_has_reason() -> None:
    result = decide({"title": "feat: thing", "state": "OPEN", "files": 0,
                     "commits": ["feat: real"]})
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "empty-pr"
    assert "human" in result["reason"].lower()


# 4. Draft + real work → promote
def test_draft_real_work_returns_auto_promote() -> None:
    result = decide(_base_open_state(isDraft=True))
    assert result["action"] == "AUTO_PROMOTE"


def test_draft_only_if_preflight_passes() -> None:
    # isDraft=True but empty PR → escalate, not promote
    result = decide({"title": "feat: thing", "state": "OPEN", "files": 0,
                     "commits": ["Initial plan"], "isDraft": True})
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "empty-pr"


# 5. Conflict
def test_conflicting_mergeable_escalates() -> None:
    result = decide(_base_open_state(mergeable="CONFLICTING"))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "conflict"


# 6. Behind
def test_behind_returns_auto_update_branch() -> None:
    result = decide(_base_open_state(mergeStateStatus="BEHIND"))
    assert result["action"] == "AUTO_UPDATE_BRANCH"


# 7. CI gated (action_required)
def test_action_required_runs_returns_auto_rerun_ci() -> None:
    result = decide(_base_open_state(actionRequiredRuns=2))
    assert result["action"] == "AUTO_RERUN_CI"


def test_action_required_run_count_in_reason() -> None:
    result = decide(_base_open_state(actionRequiredRuns=1))
    assert "1" in result["reason"]


# 8. CI running
def test_in_progress_checks_returns_auto_wait() -> None:
    result = decide(_base_open_state(checkStatuses=["in_progress"], checkConclusions=[]))
    assert result["action"] == "AUTO_WAIT"


def test_queued_checks_returns_auto_wait() -> None:
    result = decide(_base_open_state(checkStatuses=["queued"], checkConclusions=[]))
    assert result["action"] == "AUTO_WAIT"


# 9. CI red
def test_failed_check_escalates_ci_red() -> None:
    result = decide(_base_open_state(
        checkConclusions=["failure"],
        checkNames=["verify"],
        checkStatuses=["completed"],
    ))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "ci-red"


def test_cancelled_check_escalates_ci_red() -> None:
    result = decide(_base_open_state(
        checkConclusions=["cancelled"],
        checkNames=["verify"],
        checkStatuses=["completed"],
    ))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "ci-red"


def test_timed_out_check_escalates_ci_red() -> None:
    result = decide(_base_open_state(
        checkConclusions=["timed_out"],
        checkNames=["verify"],
        checkStatuses=["completed"],
    ))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "ci-red"


def test_startup_failure_check_escalates_ci_red() -> None:
    result = decide(_base_open_state(
        checkConclusions=["startup_failure"],
        checkNames=["verify"],
        checkStatuses=["completed"],
    ))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "ci-red"


def test_budget_telemetry_failure_is_ignored() -> None:
    """Budget Telemetry is the known non-required check; its failure must not escalate."""
    result = decide(_base_open_state(
        checkConclusions=["failure"],
        checkNames=["budget telemetry"],
        checkStatuses=["completed"],
        autoMergeArmed=True,
    ))
    # Should NOT escalate ci-red; should reach AUTO_WAIT (clean + armed)
    if result["action"] == "ESCALATE":
        assert result.get("escalate_type") != "ci-red"


def test_budget_telemetry_case_insensitive_ignored() -> None:
    result = decide(_base_open_state(
        checkConclusions=["failure"],
        checkNames=["Budget Telemetry"],
        checkStatuses=["completed"],
        autoMergeArmed=True,
    ))
    if result["action"] == "ESCALATE":
        assert result.get("escalate_type") != "ci-red"


# 10. Unresolved threads — round 1 (escalate review-classify)
def test_unresolved_threads_round1_escalates() -> None:
    threads = [
        {
            "id": "T1",
            "createdAt": "2026-05-01T10:00:00Z",
            "comments": [{"path": "src/foo.py", "line": 42, "body": "bad code",
                           "createdAt": "2026-05-01T10:00:00Z"}],
        }
    ]
    result = decide(_base_open_state(
        unresolvedThreads=threads,
        latestCommitAt=None,  # no post-fix commit
        latestReviewAt=None,
    ))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "review-classify"


def test_unresolved_threads_escalation_includes_thread_info() -> None:
    threads = [
        {
            "id": "T1",
            "createdAt": "2026-05-01T10:00:00Z",
            "comments": [{"path": "src/bar.py", "line": 7, "body": "nit",
                           "createdAt": "2026-05-01T10:00:00Z"}],
        }
    ]
    result = decide(_base_open_state(unresolvedThreads=threads))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "review-classify"
    assert "threads" in result
    assert result["threads"][0]["path"] == "src/bar.py"


# 11. Threads converged → auto-resolve
def test_threads_converged_returns_auto_resolve() -> None:
    """Threads predate last commit, and re-review after commit added 0 inline comments."""
    threads = [
        {
            "id": "T1",
            "createdAt": "2026-05-01T10:00:00Z",
            "comments": [{"path": "src/foo.py", "line": 1, "body": "old issue",
                           "createdAt": "2026-05-01T10:00:00Z"}],
        }
    ]
    result = decide(_base_open_state(
        unresolvedThreads=threads,
        latestCommitAt="2026-05-02T10:00:00Z",   # commit AFTER thread
        latestReviewAt="2026-05-03T10:00:00Z",   # review AFTER commit
        latestReviewNewInlineComments=0,
    ))
    assert result["action"] == "AUTO_RESOLVE_CONVERGED"


def test_threads_not_converged_if_review_before_commit() -> None:
    threads = [
        {
            "id": "T1",
            "createdAt": "2026-05-01T10:00:00Z",
            "comments": [{"createdAt": "2026-05-01T10:00:00Z",
                           "path": "x.py", "line": 1, "body": ""}],
        }
    ]
    result = decide(_base_open_state(
        unresolvedThreads=threads,
        latestCommitAt="2026-05-03T10:00:00Z",
        latestReviewAt="2026-05-02T10:00:00Z",   # review BEFORE commit → not converged
        latestReviewNewInlineComments=0,
    ))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "review-classify"


def test_threads_not_converged_if_new_inline_comments() -> None:
    threads = [
        {
            "id": "T1",
            "createdAt": "2026-05-01T10:00:00Z",
            "comments": [{"createdAt": "2026-05-01T10:00:00Z",
                           "path": "x.py", "line": 1, "body": ""}],
        }
    ]
    result = decide(_base_open_state(
        unresolvedThreads=threads,
        latestCommitAt="2026-05-02T10:00:00Z",
        latestReviewAt="2026-05-03T10:00:00Z",
        latestReviewNewInlineComments=1,   # new comments → NOT converged
    ))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "review-classify"


def test_threads_not_converged_if_thread_comment_postdates_commit() -> None:
    """A comment inside the thread that postdates the last commit means NOT converged."""
    threads = [
        {
            "id": "T1",
            "createdAt": "2026-05-01T10:00:00Z",
            "comments": [
                {"createdAt": "2026-05-04T12:00:00Z",  # AFTER the commit
                 "path": "x.py", "line": 1, "body": "new remark"},
            ],
        }
    ]
    result = decide(_base_open_state(
        unresolvedThreads=threads,
        latestCommitAt="2026-05-02T10:00:00Z",
        latestReviewAt="2026-05-05T10:00:00Z",
        latestReviewNewInlineComments=0,
    ))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "review-classify"


def test_converged_includes_thread_ids() -> None:
    threads = [
        {
            "id": "THREAD_NODE_1",
            "createdAt": "2026-05-01T10:00:00Z",
            "comments": [{"createdAt": "2026-05-01T10:00:00Z",
                           "path": "x.py", "line": 1, "body": ""}],
        }
    ]
    result = decide(_base_open_state(
        unresolvedThreads=threads,
        latestCommitAt="2026-05-02T10:00:00Z",
        latestReviewAt="2026-05-03T10:00:00Z",
        latestReviewNewInlineComments=0,
    ))
    assert result["action"] == "AUTO_RESOLVE_CONVERGED"
    assert "THREAD_NODE_1" in result["thread_ids"]


# 12. Clean (green + 0 unresolved + auto-merge armed)
def test_clean_state_returns_auto_wait() -> None:
    result = decide(_base_open_state(autoMergeArmed=True))
    assert result["action"] == "AUTO_WAIT"


# 13. Stuck
def test_stuck_escalates_after_threshold() -> None:
    result = decide(_base_open_state(passCount=3))
    assert result["action"] == "ESCALATE"
    assert result["escalate_type"] == "stuck"


def test_not_stuck_below_threshold() -> None:
    result = decide(_base_open_state(passCount=2, autoMergeArmed=True))
    # Should reach AUTO_WAIT (clean), not ESCALATE stuck
    assert result["action"] == "AUTO_WAIT"


# 14. Auto-promote to re-arm (green, no threads, auto-merge NOT armed)
def test_clean_no_auto_merge_triggers_promote() -> None:
    result = decide(_base_open_state(autoMergeArmed=False))
    assert result["action"] == "AUTO_PROMOTE"


# ---------------------------------------------------------------------------
# Priority ordering across rows
# ---------------------------------------------------------------------------

def test_wip_takes_priority_over_empty() -> None:
    """[WIP] title short-circuits even if pre-flight would fail."""
    result = decide({"title": "[WIP] nothing", "state": "OPEN", "files": 0,
                     "commits": ["Initial plan"]})
    assert result["action"] == "SKIP"


def test_merged_takes_priority_over_wip() -> None:
    result = decide({"title": "[WIP] still", "state": "MERGED"})
    assert result["action"] == "AUTO_DONE"


def test_conflict_does_not_preempt_draft() -> None:
    """Draft detection runs before conflict check."""
    result = decide(_base_open_state(isDraft=True, mergeable="CONFLICTING"))
    assert result["action"] == "AUTO_PROMOTE"


def test_action_required_preempts_ci_running() -> None:
    result = decide(_base_open_state(
        actionRequiredRuns=1,
        checkStatuses=["in_progress"],
    ))
    assert result["action"] == "AUTO_RERUN_CI"


def test_ci_running_preempts_ci_red() -> None:
    """If checks are still running, don't escalate red yet."""
    result = decide(_base_open_state(
        checkConclusions=["failure"],
        checkNames=["verify"],
        checkStatuses=["in_progress"],  # still running
    ))
    assert result["action"] == "AUTO_WAIT"


# ---------------------------------------------------------------------------
# Safety rails
# ---------------------------------------------------------------------------

def test_no_action_auto_close() -> None:
    """No action ever says AUTO_CLOSE."""
    cases = [
        {"title": "feat: x", "state": "OPEN", "files": 0, "commits": []},
        {"title": "feat: x", "state": "OPEN", "files": 0, "commits": ["Initial plan"]},
    ]
    for s in cases:
        result = decide(s)
        assert result["action"] != "AUTO_CLOSE"


def test_no_action_push_code() -> None:
    """No action is PUSH_CODE."""
    result = decide(_base_open_state())
    assert result["action"] != "PUSH_CODE"


def test_escalate_always_has_escalate_type() -> None:
    """Every ESCALATE result must carry an escalate_type."""
    test_states = [
        {"title": "feat: x", "state": "OPEN", "files": 0, "commits": []},
        _base_open_state(mergeable="CONFLICTING"),
        _base_open_state(checkConclusions=["failure"], checkNames=["ci"],
                         checkStatuses=["completed"]),
        _base_open_state(passCount=5),
    ]
    for s in test_states:
        r = decide(s)
        if r["action"] == "ESCALATE":
            assert "escalate_type" in r, f"Missing escalate_type for state {s}"
