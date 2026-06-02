#!/usr/bin/env python3
"""Pure decision function for the PR driver loop.

Given a state dictionary describing a PR's current condition, returns the
next action the driver should take.  No network calls or side-effects — safe
to unit-test without GitHub access.

State dict keys (all optional; absent keys are treated as falsy/empty):
  title          (str)   PR title
  files          (int)   number of changed files
  commits        (list)  list of commit headline strings
  isDraft        (bool)
  state          (str)   PR state: "OPEN", "CLOSED", "MERGED"
  mergeable      (str)   "MERGEABLE", "CONFLICTING", "UNKNOWN"
  mergeStateStatus (str) "BEHIND", "BLOCKED", "CLEAN", "DIRTY", "DRAFT",
                         "HAS_HOOKS", "UNKNOWN", "UNSTABLE"
  autoMergeArmed (bool)  True when auto-merge is armed
  checkConclusions (list) list of conclusion strings for finished check-runs
  checkStatuses   (list) list of status strings for in-flight check-runs
  actionRequiredRuns (int) count of action_required workflow runs
  unresolvedThreads (list) list of thread dicts:
      { "id": str, "createdAt": str, "comments": [{"createdAt": str}] }
  latestReviewAt  (str|None) ISO-8601 timestamp of the most-recent review
  latestCommitAt  (str|None) ISO-8601 timestamp of the most-recent commit
  latestReviewNewInlineComments (int)  new inline comments added by the latest
                                        review (0 = converged)
  passCount       (int)   number of consecutive passes with no state change
                          (for stuck detection)

Returned action dict always has:
  { "action": str, "reason": str, ...extra keys }

Possible action values (mirrors the issue state machine):
  SKIP            WIP – agent still working
  ESCALATE        human decision needed; "escalate_type" sub-key gives the
                  category (empty-pr, ci-red, review-classify, conflict, stuck)
  AUTO_PROMOTE    call pr-promote.ps1
  AUTO_UPDATE_BRANCH  call pr-promote.ps1 (update-branch step) + re-arm
  AUTO_RERUN_CI   call pr-rerun-pending.ps1
  AUTO_WAIT       nothing to do right now; CI or merge in flight
  AUTO_RESOLVE_CONVERGED  resolve pre-fix threads (guarded by -AutoResolveConverged)
  AUTO_DONE       PR merged; emit dependent-unblocked note
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Check-run conclusions that indicate a broken CI state.
_CI_FAIL_CONCLUSIONS = frozenset(
    {"failure", "cancelled", "timed_out", "startup_failure"}
)

# Commit headlines that indicate an empty/stalled PR.
_EMPTY_HEADLINES = frozenset({"initial plan"})

# Known non-required check that should not gate CI-red escalation.
_IGNORED_CHECK_NAMES = frozenset({"budget telemetry"})

# After this many consecutive unchanged passes, escalate as stuck.
_STUCK_THRESHOLD = 3


def _is_wip(title: str) -> bool:
    return "[wip]" in title.lower()


def _is_real_commit(headline: str) -> bool:
    """Return True if the commit headline represents real work (not a placeholder)."""
    h = headline.strip().lower()
    if h in _EMPTY_HEADLINES:
        return False
    if h.startswith("merge "):
        return False
    return True


def _preflight_pass(state: dict[str, Any]) -> bool:
    """Return True when the PR passes the mandatory pre-flight gate.

    Requires: files > 0 AND at least one commit whose headline is not
    'Initial plan' and is not a merge commit.
    """
    files = int(state.get("files", 0))
    if files == 0:
        return False
    commits: list[str] = state.get("commits", [])
    return any(_is_real_commit(c) for c in commits)


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    ts = ts.rstrip("Z")
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _threads_all_predate_commit(
    threads: list[dict[str, Any]], last_commit_at: datetime | None
) -> bool:
    """Return True if every unresolved thread was created before the last commit."""
    if last_commit_at is None:
        return False
    for t in threads:
        created = _parse_iso(t.get("createdAt"))
        if created is None:
            return False
        # Also check individual comments within the thread
        for c in t.get("comments", []):
            c_created = _parse_iso(c.get("createdAt"))
            if c_created and c_created >= last_commit_at:
                return False
        if created >= last_commit_at:
            return False
    return True


def decide(state: dict[str, Any]) -> dict[str, Any]:
    """Return the next action for the given PR state.

    This function is pure: no I/O, no random, deterministic given state.
    """
    title: str = state.get("title", "")
    pr_state: str = (state.get("state") or "OPEN").upper()
    mergeable: str = (state.get("mergeable") or "").upper()
    merge_status: str = (state.get("mergeStateStatus") or "").upper()
    is_draft: bool = bool(state.get("isDraft", False))
    auto_merge_armed: bool = bool(state.get("autoMergeArmed", False))

    check_conclusions: list[str] = [
        (c or "").lower() for c in state.get("checkConclusions", [])
    ]
    check_names: list[str] = [
        (n or "").lower() for n in state.get("checkNames", [])
    ]
    check_statuses: list[str] = [
        (s or "").lower() for s in state.get("checkStatuses", [])
    ]
    action_required_runs: int = int(state.get("actionRequiredRuns", 0))
    unresolved_threads: list[dict[str, Any]] = state.get("unresolvedThreads", [])
    latest_review_at: str | None = state.get("latestReviewAt")
    latest_commit_at: str | None = state.get("latestCommitAt")
    new_inline_from_latest_review: int = int(
        state.get("latestReviewNewInlineComments", 0)
    )
    pass_count: int = int(state.get("passCount", 0))

    # ── 1. MERGED ────────────────────────────────────────────────────────────
    if pr_state == "MERGED":
        return {
            "action": "AUTO_DONE",
            "reason": "PR is merged.",
        }

    # ── 2. WIP ───────────────────────────────────────────────────────────────
    if _is_wip(title):
        return {
            "action": "SKIP",
            "reason": "[WIP] found in title — agent still working.",
        }

    # ── 3. Pre-flight (empty-PR) ──────────────────────────────────────────────
    if not _preflight_pass(state):
        return {
            "action": "ESCALATE",
            "escalate_type": "empty-pr",
            "reason": (
                "Pre-flight failed: files==0 or all commits are placeholders/merges. "
                "Never auto-close — human must decide."
            ),
        }

    # ── 4. Draft + real work → promote ───────────────────────────────────────
    if is_draft:
        return {
            "action": "AUTO_PROMOTE",
            "reason": "PR has real work and is still a draft — promote.",
        }

    # ── 5. Conflict ───────────────────────────────────────────────────────────
    if mergeable == "CONFLICTING":
        return {
            "action": "ESCALATE",
            "escalate_type": "conflict",
            "reason": "mergeable==CONFLICTING — human must resolve conflicts.",
        }

    # ── 6. Behind base branch ─────────────────────────────────────────────────
    if merge_status == "BEHIND":
        return {
            "action": "AUTO_UPDATE_BRANCH",
            "reason": "mergeStateStatus==BEHIND — update branch and re-arm auto-merge.",
        }

    # ── 7. CI gated (action_required) ────────────────────────────────────────
    if action_required_runs > 0:
        return {
            "action": "AUTO_RERUN_CI",
            "reason": f"{action_required_runs} action_required run(s) — rerun CI.",
        }

    # ── 8. CI running (in_progress / queued) ─────────────────────────────────
    if any(s in ("in_progress", "queued") for s in check_statuses):
        return {
            "action": "AUTO_WAIT",
            "reason": "Checks in_progress or queued — waiting for CI.",
        }

    # ── 9. CI red ─────────────────────────────────────────────────────────────
    # A check is "red" if its conclusion is in _CI_FAIL_CONCLUSIONS and its name
    # is not in the known-non-required ignore list.
    for idx, conclusion in enumerate(check_conclusions):
        if conclusion in _CI_FAIL_CONCLUSIONS:
            name = check_names[idx] if idx < len(check_names) else ""
            if name not in _IGNORED_CHECK_NAMES:
                return {
                    "action": "ESCALATE",
                    "escalate_type": "ci-red",
                    "reason": (
                        f"Check '{name or '(unknown)'}' has conclusion='{conclusion}' "
                        "— human must triage CI failure."
                    ),
                }

    # ── 10. Unresolved review threads ─────────────────────────────────────────
    if unresolved_threads:
        last_commit_dt = _parse_iso(latest_commit_at)
        last_review_dt = _parse_iso(latest_review_at)

        # Converged: all unresolved threads predate the last commit AND the
        # latest review was submitted after the last commit with zero new inline
        # comments.
        converged = (
            last_commit_dt is not None
            and last_review_dt is not None
            and last_review_dt > last_commit_dt
            and new_inline_from_latest_review == 0
            and _threads_all_predate_commit(unresolved_threads, last_commit_dt)
        )

        if converged:
            thread_ids = [t.get("id", "") for t in unresolved_threads]
            return {
                "action": "AUTO_RESOLVE_CONVERGED",
                "reason": (
                    "All unresolved threads predate last commit and post-fix "
                    "re-review added no new inline comments — safe to auto-resolve."
                ),
                "thread_ids": thread_ids,
            }

        # Round 1 (or post-fix but new comments appeared): escalate for classify.
        thread_summaries = []
        for t in unresolved_threads:
            comments = t.get("comments", [])
            first_comment = comments[0] if comments else {}
            thread_summaries.append(
                {
                    "id": t.get("id", ""),
                    "path": first_comment.get("path", ""),
                    "line": first_comment.get("line"),
                    "body": first_comment.get("body", ""),
                }
            )
        return {
            "action": "ESCALATE",
            "escalate_type": "review-classify",
            "reason": (
                "Unresolved review threads present without a converged post-fix "
                "re-review — human must classify."
            ),
            "threads": thread_summaries,
        }

    # ── 11. Stuck detection ───────────────────────────────────────────────────
    if pass_count >= _STUCK_THRESHOLD:
        return {
            "action": "ESCALATE",
            "escalate_type": "stuck",
            "reason": (
                f"No state change across {pass_count} passes "
                f"(threshold={_STUCK_THRESHOLD}) — PR may be stuck."
            ),
        }

    # ── 12. Clean: green + 0 unresolved + auto-merge armed ───────────────────
    if auto_merge_armed:
        return {
            "action": "AUTO_WAIT",
            "reason": "CI green, 0 unresolved threads, auto-merge armed — waiting for merge.",
        }

    # ── 13. Needs auto-merge re-arming ────────────────────────────────────────
    # CI is green and no threads; arm auto-merge via promote helper.
    return {
        "action": "AUTO_PROMOTE",
        "reason": "CI green, 0 unresolved threads, but auto-merge not armed — re-arm.",
    }


if __name__ == "__main__":
    import json as _json
    import sys as _sys

    if "--json-stdin" in _sys.argv:
        raw = _sys.stdin.read()
        state = _json.loads(raw)
        result = decide(state)
        print(_json.dumps(result))
    else:
        print("Usage: python pr_driver_decide.py --json-stdin  (reads JSON state from stdin)")
        _sys.exit(1)
