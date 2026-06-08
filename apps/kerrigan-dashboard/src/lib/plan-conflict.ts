/**
 * lib/plan-conflict.ts — Conflict detection for the plan-save flow (M6.3).
 *
 * Detects whether any open PR created in the context of an `agent:go`-labeled
 * issue touches the plan file currently being edited, and surfaces the
 * conflicting PR so the save flow can block and return a structured failure.
 *
 * Design constraints:
 *  - Pure-ish: all GitHub data is injected; no real network in unit tests.
 *  - Uses only what GitHubClient already exposes (no widening of github.ts).
 *  - Known gap: the GitHub REST API can return a PR's changed-file list, but
 *    `GitHubClient` does not expose that endpoint.  As a well-documented
 *    approximation we match plan-editing PRs by head-branch prefix
 *    (`plan-edits/`) — the naming convention enforced by plan-save.ts —
 *    combined with the presence of at least one `agent:go`-labeled open issue.
 *    A future iteration can widen `github.ts` with `listPRFiles` and tighten
 *    the match against `planPath`.
 */

import type {
  GitHubClient,
  GitHubResult,
  PullRequestData,
} from "./github.js";
import type { RepoRef } from "./projects.js";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

/** Compact representation of a conflicting PR surfaced to the caller. */
export interface ConflictingPR {
  number: number;
  url: string;
  branch: string;
}

/** Discriminated result returned by detectPlanConflict. */
export type ConflictResult =
  | { conflicted: true; pr: ConflictingPR }
  | { conflicted: false };

/** Options accepted by detectPlanConflict. */
export interface DetectPlanConflictOptions {
  /** GitHub client for fetching live issue data. */
  ghClient: GitHubClient;
  /** Repository to inspect. */
  repo: RepoRef;
  /**
   * Path of the plan file currently being saved (used for documentation /
   * future tighter matching once `listPRFiles` is available).
   */
  planPath: string;
  /**
   * Pre-fetched open PRs for the repository.  Injected so the caller can
   * batch the fetch and share it across multiple checks without extra round
   * trips.
   */
  openPRs: PullRequestData[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Label name that marks an issue as being handled by a go-agent. */
const AGENT_GO_LABEL = "agent:go";

/**
 * Head-branch prefix used by `plan-save.ts` for every plan-edit session.
 * A PR whose head branch starts with this prefix is almost certainly a
 * plan-editing PR (approximation standing in for PR-file-list inspection).
 */
const PLAN_EDIT_BRANCH_PREFIX = "plan-edits/";

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Detect whether an open PR — created under an `agent:go`-labeled issue —
 * would conflict with a pending save to `planPath`.
 *
 * Returns `GitHubResult<ConflictResult>` so the caller can propagate offline
 * failures without extra error handling layers.
 *
 * Approximation note: because `github.ts` does not expose a `listPRFiles`
 * method, we identify plan-editing PRs by their `plan-edits/` head-branch
 * prefix (the convention from `plan-save.ts`).  If the prefix is present AND
 * at least one open issue carries the `agent:go` label, we treat the situation
 * as conflicted.  Passing `planPath` is required by the interface for forward
 * compatibility; it is not used in the current matching logic.
 */
export async function detectPlanConflict(
  options: DetectPlanConflictOptions,
): Promise<GitHubResult<ConflictResult>> {
  const { ghClient, repo, openPRs } = options;

  // --- Fetch open issues to discover agent:go-labeled work ---
  const issuesResult = await ghClient.listIssues(repo.owner, repo.repo);
  if (!issuesResult.ok) {
    // Propagate offline / auth failures to the caller.
    return issuesResult;
  }

  const hasAgentGoIssue = issuesResult.data.some((issue) =>
    issue.labels.some((label) => label.name === AGENT_GO_LABEL),
  );

  if (!hasAgentGoIssue) {
    // No agent:go issues → no conflict possible.
    return { ok: true, data: { conflicted: false } };
  }

  // --- Find an open plan-editing PR (head branch approximation) ---
  const conflictingPR = openPRs.find((pr) =>
    pr.head.ref.startsWith(PLAN_EDIT_BRANCH_PREFIX),
  );

  if (conflictingPR === undefined) {
    // No plan-editing PR in flight → clean.
    return { ok: true, data: { conflicted: false } };
  }

  return {
    ok: true,
    data: {
      conflicted: true,
      pr: {
        number: conflictingPR.number,
        url: conflictingPR.html_url,
        branch: conflictingPR.head.ref,
      },
    },
  };
}
