import { describe, expect, it } from "vitest";
import type { IssueData, PullRequestData } from "../../lib/github.js";
import { groupStageItemsBySubMilestone, parseSubMilestoneId } from "./groupStageItems.js";

function issue(overrides: Partial<IssueData> = {}): IssueData {
  return {
    number: 1,
    title: "M3.4: issue",
    state: "open",
    user: { login: "agent" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    labels: [],
    html_url: "https://github.com/o/r/issues/1",
    ...overrides,
  };
}

function pr(overrides: Partial<PullRequestData> = {}): PullRequestData {
  return {
    number: 2,
    title: "M3.4: PR",
    state: "open",
    draft: false,
    user: { login: "agent" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    merged_at: null,
    head: { ref: "feature/m3-4", sha: "abc123" },
    base: { ref: "main" },
    html_url: "https://github.com/o/r/pull/2",
    ...overrides,
  };
}

describe("parseSubMilestoneId", () => {
  it("parses canonical milestone tokens from titles", () => {
    expect(parseSubMilestoneId("M3.4: dashboard work")).toBe("M3.4");
    expect(parseSubMilestoneId("feat: m2.10 follow-up")).toBe("M2.10");
  });

  it("returns null when no sub-milestone token is present", () => {
    expect(parseSubMilestoneId("M3 milestone tracking")).toBeNull();
    expect(parseSubMilestoneId("general cleanup")).toBeNull();
  });
});

describe("groupStageItemsBySubMilestone", () => {
  it("sorts sub-milestone groups by minor number and keeps issues plus PRs together", () => {
    const grouped = groupStageItemsBySubMilestone(
      [
        issue({ number: 11, title: "M3.10: issue" }),
        issue({ number: 12, title: "M3.2: issue" }),
      ],
      [
        pr({ number: 21, title: "M3.2: PR" }),
        pr({ number: 22, title: "M3.10: PR" }),
      ],
      3,
    );

    expect(grouped.map((group) => group.label)).toEqual(["M3.2", "M3.10"]);
    expect(grouped[0]).toMatchObject({
      label: "M3.2",
      issues: [expect.objectContaining({ number: 12 })],
      prs: [expect.objectContaining({ number: 21 })],
    });
    expect(grouped[1]).toMatchObject({
      label: "M3.10",
      issues: [expect.objectContaining({ number: 11 })],
      prs: [expect.objectContaining({ number: 22 })],
    });
  });

  it("places unmatched items into an Other bucket", () => {
    const grouped = groupStageItemsBySubMilestone(
      [issue({ number: 31, title: "Milestone tracking issue" })],
      [pr({ number: 41, title: "fix(dashboard): polish" })],
      3,
    );

    expect(grouped).toEqual([
      {
        id: null,
        label: "Other",
        issues: [expect.objectContaining({ number: 31 })],
        prs: [expect.objectContaining({ number: 41 })],
      },
    ]);
  });

  it("does not create a foreign milestone bucket when only foreign sub-ids are present", () => {
    const grouped = groupStageItemsBySubMilestone(
      [issue({ number: 51, title: "M2.1: docs clean-up" })],
      [pr({ number: 61, title: "M2.1: misc follow-up" })],
      3,
    );

    expect(grouped).toEqual([
      {
        id: null,
        label: "Other",
        issues: [expect.objectContaining({ number: 51 })],
        prs: [expect.objectContaining({ number: 61 })],
      },
    ]);
  });

  it("prefers an in-milestone sub-id when titles contain multiple sub-ids", () => {
    const grouped = groupStageItemsBySubMilestone(
      [issue({ number: 71, title: "fix: examples M2.1, M3.4 in description" })],
      [pr({ number: 81, title: "docs: mentions M2.9 then M3.4" })],
      3,
    );

    expect(grouped).toEqual([
      {
        id: "M3.4",
        label: "M3.4",
        issues: [expect.objectContaining({ number: 71 })],
        prs: [expect.objectContaining({ number: 81 })],
      },
    ]);
  });
});
