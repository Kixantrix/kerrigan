# pr-driver: a loop that auto-advances PRs through the mechanical lifecycle and escalates only decisions

Harness tool. Single-dispatch. Touches `tools/` + `tests/` only.

## Goal

Automate the mechanical PR-loop steps the conductor currently does by hand
(is-it-done? → mark ready → update-branch → request review → rerun CI → arm
auto-merge → resolve converged threads → detect merge), and **escalate back to a
human only at genuine decision points**. The conductor's turns should go to
judgment, not plumbing.

This is an **orchestrator over existing helpers** — do NOT reinvent them. Compose:
`tools/pr-doctor.ps1` (state signals), `tools/pr-promote.ps1` (ready/update/review/arm),
`tools/pr-rerun-pending.ps1` (CI kick), `tools/pr_reply_resolve.py` (reply+resolve one
thread), `tools/pr-redispatch.ps1` (re-dispatch comment). Reuse their logic/queries;
factor shared GraphQL/REST reads into a small helper if needed rather than duplicating.

## Deliverable

`tools/pr-driver.ps1` (PowerShell 5.1) + a unit-tested **pure decision function**
the script calls. The decision logic MUST be separable from the gh side-effects so it
can be tested without network. Put the testable core where the existing Python test
suite can reach it if that's cleaner (e.g. a small `tools/pr_driver_decide.py` pure
function returning the next action for a given state dict) — your call, but the
state→action mapping MUST have unit tests covering every row of the table below.

## Per-PR state machine

Given a PR's state (draft?, title, files, commits, check-runs, action_required runs,
review threads resolved/unresolved, latest review submittedAt vs last commit date,
mergeable, mergeStateStatus, state):

| State | Signal | Action |
|-------|--------|--------|
| WIP | `[WIP]` in title | SKIP (agent still working) |
| Empty | files==0 OR commits only `Initial plan`/merge | **ESCALATE** `empty-pr` (never auto-close) |
| Draft+real | not WIP, pre-flight pass, isDraft | AUTO `promote` (pr-promote.ps1) |
| Behind | mergeStateStatus==BEHIND | AUTO `update-branch` + re-arm auto-merge |
| CI gated | action_required runs present | AUTO `rerun-ci` (pr-rerun-pending.ps1) |
| CI running | checks in_progress/queued | AUTO `wait` |
| CI red | any check failure/cancelled/timed_out/startup_failure (excluding the known non-required `Budget Telemetry`) | **ESCALATE** `ci-red` |
| Threads (round 1) | unresolved threads, NO post-fix re-review | **ESCALATE** `review-classify` (include each thread's file:line + body) |
| Threads (converged) | unresolved threads that PREDATE the last commit AND a review submitted AFTER the last commit added ZERO new inline comments | AUTO `resolve-converged` (GATED — see safety) |
| Conflict | mergeable==CONFLICTING | **ESCALATE** `conflict` |
| Clean | green + 0 unresolved + auto-merge armed | AUTO `wait` (for merge) |
| Merged | state==MERGED | AUTO `done`; emit `dependent-unblocked` note if applicable |
| Stuck | no state change across N passes | **ESCALATE** `stuck` |

Pre-flight (the empty-PR gate) is MANDATORY and HARD: files>0 AND at least one commit
whose headline is not `Initial plan` and not a merge commit. Fail → ESCALATE, never promote.

## Safety rails (non-negotiable — encode as hard stops)

1. **Never auto-close** a PR. Empty/stalled → escalate.
2. **Never push code** to a PR. Never `gh pr merge --admin` / never bypass branch
   protection. Only ever arm `--auto` and let protection gate.
3. **Never auto-dispatch new work.** When a dependency merges, emit a
   `dependent-unblocked` suggestion in the report; do not create issues.
4. **Thread auto-resolve (B behavior) is GATED behind `-AutoResolveConverged`.**
   Without the flag, the `resolve-converged` state is reported (dry-run intent shown:
   "would resolve thread X because re-review at <ts> added 0 new comments") but NOT
   executed — it escalates as `review-confirm` instead. This lets the conductor watch
   the convergence detector make the right call on a real wave before trusting it.
5. **`resolve-converged` NEVER fires on a first review.** Only pre-existing threads
   after a post-fix clean re-review. If the latest re-review added ANY new inline
   comment, escalate everything on that PR as `review-classify` (do not resolve).
6. **Idempotent.** Every AUTO action must be safe to repeat (ready/arm/request-review
   already no-op when satisfied).
7. **`-DryRun`** prints every intended action for every PR and executes nothing.

## Inputs / modes

- `pr-driver.ps1 -Pr 308,310,312` — explicit list, OR
- `pr-driver.ps1` — auto-discover open PRs authored by the Copilot coding agent
  (`gh pr list --author app/copilot-swe-agent --state open`) plus any open PR the
  current user authored with an `agent:`-ish chore branch (keep discovery simple;
  explicit list is the primary path).
- `-Watch [-IntervalSeconds 60]` — re-run passes until every PR is MERGED or ESCALATED;
  default is a single pass.
- `-AutoResolveConverged` — enable the gated B behavior (off by default).
- `-DryRun` — show intent, change nothing.

## Output contract

Per pass, print a compact per-PR status line, then a single **`== NEEDS YOU ==`**
section listing only the escalations, each as: `#<pr> <reason> — <one-line context>`
(for `review-classify`, include the thread file:line + comment body so the conductor
can decide without opening the PR). If there are no escalations and all PRs merged,
print `ALL CLEAR`. The conductor reads only the NEEDS YOU section.

## What "done" looks like

1. `tools/pr-driver.ps1 -Pr <list> -DryRun` prints the correct next action for each PR
   without side effects.
2. The pure decision function has unit tests covering EVERY table row, including:
   empty-PR → escalate; round-1 threads → escalate; converged threads (predate last
   commit + post-fix re-review with 0 new comments) → resolve-converged; converged but
   re-review added a new comment → escalate; CI red → escalate; conflict → escalate.
3. Without `-AutoResolveConverged`, converged threads are reported as `review-confirm`,
   not resolved. With the flag, they call `pr_reply_resolve.py` per thread.
4. Live run advances a real ready PR through promote → CI → merge with no manual gh calls.
5. `python -m pytest -q` green (new tests + existing). `kerrigan check` passes.
6. Static-content tests for the new script in the style of `tests/test_pr_loop_helpers.py`
   (assert the safety rails are present: no `--admin`, no `gh pr close`, the
   `-AutoResolveConverged` gate guards the resolve call).

## Out of scope

- Classifying critical vs advisory review comments by content (round-1 always escalates).
- Re-dispatching fixes (the conductor decides + uses pr-redispatch.ps1).
- Any change to the existing helper scripts' behavior (compose, don't modify) — if a
  helper needs a tiny read-only addition, prefer a new thin function over editing.
- A long-running daemon/service; `-Watch` is a bounded poll loop, not a background service.

## Notes

- gh writes success confirmations to stderr (the checkmark mojibake) → exit-code-1
  false positives; mirror the `2>&1 | Out-Null` handling pr-promote.ps1 already uses.
- `reviewThreads` is GraphQL-only (not a `gh pr view --json` field) — reuse pr-doctor's
  query. Pass owner/name as `-f` variables, number as `-F`.
- "post-fix re-review with 0 new comments" = the convergence signal proven on #304/#301:
  a review submitted after the agent's fix commit that added no new inline review
  comments means the prior round's threads are satisfied. That is the ONLY auto-resolve
  trigger.
