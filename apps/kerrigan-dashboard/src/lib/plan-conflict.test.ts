import { describe, expect, it } from "vitest";
import {
  detectPlanConflict,
  type ConflictResult,
  type DetectPlanConflictOptions,
} from "./plan-conflict.js";
import type {
  GitHubClient,
  GitHubResult,
  IssueData,
  PullRequestData,
} from "./github.js";
import type { RepoRef } from "./projects.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TEST_REPO: RepoRef = { owner: "acme", repo: "rocket" };
const PLAN_PATH = "/fixtures/rocket/specs/plan.md";

function makeIssue(
  number: number,
  labels: string[] = [],
): IssueData {
  return {
    number,
    title: `Issue ${number}`,
    state: "open",
    user: { login: "bot" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    labels: labels.map((name) => ({ name })),
    html_url: `https://github.com/acme/rocket/issues/${number}`,
  };
}

function makePR(
  number: number,
  headRef: string,
): PullRequestData {
  return {
    number,
    title: `PR ${number}`,
    state: "open",
    draft: true,
    user: { login: "bot" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    head: { ref: headRef, sha: "abc1234" },
    base: { ref: "main" },
    html_url: `https://github.com/acme/rocket/pull/${number}`,
  };
}

/** Minimal fake GitHubClient that returns issues on demand. */
function makeGhClient(
  issues: IssueData[],
): GitHubClient {
  return {
    getRepo: async () => ({ ok: false, offline: true, reason: "not-implemented" }),
    listOpenPRs: async () => ({ ok: false, offline: true, reason: "not-implemented" }),
    getPRReviews: async () => ({ ok: false, offline: true, reason: "not-implemented" }),
    listIssues: async (): Promise<GitHubResult<IssueData[]>> => ({
      ok: true,
      data: issues,
    }),
    listRecentlyMergedPRs: async () => ({ ok: true, data: [] }),
    listClosedIssues: async () => ({ ok: true, data: [] }),
    listIssuesWithClosingPRs: async () => ({ ok: true, data: [] }),
  };
}

/** Fake client that returns an offline error for listIssues. */
function makeOfflineGhClient(): GitHubClient {
  return {
    getRepo: async () => ({ ok: false, offline: true, reason: "unreachable" }),
    listOpenPRs: async () => ({ ok: false, offline: true, reason: "unreachable" }),
    getPRReviews: async () => ({ ok: false, offline: true, reason: "unreachable" }),
    listIssues: async (): Promise<GitHubResult<IssueData[]>> => ({
      ok: false,
      offline: true,
      reason: "unreachable",
    }),
    listRecentlyMergedPRs: async () => ({ ok: false, offline: true, reason: "unreachable" }),
    listClosedIssues: async () => ({ ok: false, offline: true, reason: "unreachable" }),
    listIssuesWithClosingPRs: async () => ({ ok: false, offline: true, reason: "unreachable" }),
  };
}

function makeOptions(
  overrides: Partial<DetectPlanConflictOptions> & {
    issues?: IssueData[];
    prs?: PullRequestData[];
  },
): DetectPlanConflictOptions {
  const { issues = [], prs = [], ...rest } = overrides;
  return {
    ghClient: makeGhClient(issues),
    repo: TEST_REPO,
    planPath: PLAN_PATH,
    openPRs: prs,
    ...rest,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("detectPlanConflict", () => {
  it("returns conflicted=true when an agent:go issue exists and a plan-edit PR is open", async () => {
    const result = await detectPlanConflict(
      makeOptions({
        issues: [makeIssue(1, ["agent:go"]), makeIssue(2, ["bug"])],
        prs: [makePR(10, "plan-edits/20260601T120000Z-abcdef1")],
      }),
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const data: ConflictResult = result.data;
    expect(data.conflicted).toBe(true);
    if (!data.conflicted) return;

    expect(data.pr.number).toBe(10);
    expect(data.pr.branch).toBe("plan-edits/20260601T120000Z-abcdef1");
    expect(data.pr.url).toBe("https://github.com/acme/rocket/pull/10");
  });

  it("returns the first plan-edit PR when multiple are open", async () => {
    const result = await detectPlanConflict(
      makeOptions({
        issues: [makeIssue(1, ["agent:go"])],
        prs: [
          makePR(5, "plan-edits/20260601T100000Z-aaa0001"),
          makePR(6, "plan-edits/20260601T110000Z-bbb0002"),
        ],
      }),
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const data = result.data;
    expect(data.conflicted).toBe(true);
    if (!data.conflicted) return;
    expect(data.pr.number).toBe(5);
  });

  it("returns conflicted=false when there are no agent:go issues", async () => {
    const result = await detectPlanConflict(
      makeOptions({
        issues: [makeIssue(1, ["bug"]), makeIssue(2, ["enhancement"])],
        prs: [makePR(10, "plan-edits/20260601T120000Z-abcdef1")],
      }),
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.data.conflicted).toBe(false);
  });

  it("returns conflicted=false when there are no open plan-edit PRs", async () => {
    const result = await detectPlanConflict(
      makeOptions({
        issues: [makeIssue(1, ["agent:go"])],
        prs: [makePR(20, "feature/add-tests"), makePR(21, "fix/typo")],
      }),
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.data.conflicted).toBe(false);
  });

  it("returns conflicted=false when both issues and PRs lists are empty", async () => {
    const result = await detectPlanConflict(
      makeOptions({ issues: [], prs: [] }),
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.data.conflicted).toBe(false);
  });

  it("does not treat a non-plan-edit PR as conflicting even with agent:go issues", async () => {
    const result = await detectPlanConflict(
      makeOptions({
        issues: [makeIssue(3, ["agent:go"])],
        prs: [makePR(99, "main")],
      }),
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.data.conflicted).toBe(false);
  });

  it("propagates the offline error when listIssues is unavailable", async () => {
    const result = await detectPlanConflict({
      ghClient: makeOfflineGhClient(),
      repo: TEST_REPO,
      planPath: PLAN_PATH,
      openPRs: [makePR(10, "plan-edits/20260601T120000Z-abcdef1")],
    });

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.offline).toBe(true);
    expect(result.reason).toBe("unreachable");
  });

  it("does not flag a partial branch-name match (prefix must be exact)", async () => {
    const result = await detectPlanConflict(
      makeOptions({
        issues: [makeIssue(1, ["agent:go"])],
        prs: [makePR(30, "refactor/plan-edits-cleanup")],
      }),
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.data.conflicted).toBe(false);
  });
});
