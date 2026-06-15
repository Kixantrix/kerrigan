import { describe, expect, it } from "vitest";
import type { IssueData, PullRequestData, ReviewData } from "./github.js";
import type { PlanStageGraph, PlanStageNode } from "./plan-parser.js";
import {
  defaultStageMatcher,
  deriveStageStatus,
  deriveStatuses,
  type BlockSummary,
  type StageStatus,
} from "./status.js";

function pr(overrides: Partial<PullRequestData> = {}): PullRequestData {
  return {
    number: 1,
    title: "M3.2 status work",
    state: "open",
    draft: false,
    user: { login: "agent" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    head: { ref: "feature", sha: "abc123" },
    base: { ref: "main" },
    html_url: "https://example.com/pr/1",
    ...overrides,
  };
}

function issue(overrides: Partial<IssueData> = {}): IssueData {
  return {
    number: 1,
    title: "M3.2 issue",
    state: "open",
    user: { login: "agent" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    labels: [],
    html_url: "https://example.com/issues/1",
    ...overrides,
  };
}

function review(overrides: Partial<ReviewData> = {}): ReviewData {
  return {
    id: 1,
    user: { login: "reviewer" },
    state: "COMMENTED",
    submitted_at: "2026-01-01T00:00:00Z",
    body: "lgtm",
    html_url: "https://example.com/reviews/1",
    ...overrides,
  };
}

function graph(nodes: PlanStageNode[]): PlanStageGraph {
  return { nodes, edges: [] };
}

describe("deriveStageStatus", () => {
  it.each<readonly [string, Parameters<typeof deriveStageStatus>[0], StageStatus]>([
    [
      "planned",
      { prs: [], issues: [], blocks: [] },
      "planned",
    ],
    [
      "dispatched",
      {
        prs: [pr()],
        issues: [issue({ labels: [{ name: "agent:go" }] })],
        blocks: [],
        reviewsByPr: new Map([[1, []]]),
      },
      "dispatched",
    ],
    [
      "in-review",
      {
        prs: [pr()],
        issues: [issue({ labels: [{ name: "agent:go" }] })],
        blocks: [],
        reviewsByPr: new Map([[1, [review({ state: "CHANGES_REQUESTED" })]]]),
      },
      "in-review",
    ],
    [
      "blocked",
      {
        prs: [pr()],
        issues: [issue({ labels: [{ name: "agent:go" }] })],
        blocks: [{ open: true }],
      },
      "blocked",
    ],
    [
      "needs-attestation",
      {
        prs: [],
        issues: [issue({ labels: [{ name: "agent:needs-attestation" }] })],
        blocks: [],
      },
      "needs-attestation",
    ],
    [
      "needs-human-test",
      {
        prs: [],
        issues: [issue({ labels: [{ name: "agent:needs-human-test" }] })],
        blocks: [],
      },
      "needs-human-test",
    ],
    [
      "merged",
      {
        prs: [pr({ state: "merged" })],
        issues: [],
        blocks: [],
      },
      "merged",
    ],
    [
      "merged via merged_at field",
      {
        prs: [pr({ state: "closed", merged_at: "2026-02-01T00:00:00Z" })],
        issues: [],
        blocks: [],
      },
      "merged",
    ],
  ])("returns %s", (_name, input, expected) => {
    expect(deriveStageStatus(input)).toBe(expected);
  });

  it("applies precedence when multiple signals are present", () => {
    const input = {
      prs: [pr()],
      issues: [
        issue({ labels: [{ name: "agent:go" }] }),
        issue({ number: 2, labels: [{ name: "agent:needs-attestation" }] }),
      ],
      blocks: [{ open: true } satisfies BlockSummary],
      reviewsByPr: new Map([[1, [review({ state: "CHANGES_REQUESTED" })]]]),
    };

    expect(deriveStageStatus(input)).toBe("blocked");
  });

  it("returns planned for empty input", () => {
    expect(deriveStageStatus({ prs: [], issues: [], blocks: [] })).toBe("planned");
  });

  it("closed issue without open PR does not trigger dispatched", () => {
    const input = {
      prs: [],
      issues: [issue({ state: "closed", labels: [{ name: "agent:go" }] })],
      blocks: [],
    };
    expect(deriveStageStatus(input)).toBe("planned");
  });

  it("closed PR without merged_at does not trigger merged", () => {
    const input = {
      prs: [pr({ state: "closed", merged_at: null })],
      issues: [],
      blocks: [],
    };
    expect(deriveStageStatus(input)).toBe("planned");
  });
});

describe("deriveStatuses", () => {
  it("aggregates matched multi-repo items by highest precedence", () => {
    const stage: PlanStageNode = {
      id: "m3-2",
      label: "M3.2 Status",
      level: 2,
      parentId: null,
    };

    const statuses = deriveStatuses(
      graph([stage]),
      {
        prs: [
          pr({ number: 1, title: "repo-a: M3.2 open" }),
          pr({ number: 2, title: "repo-b: M3.2 merged", state: "merged" }),
        ],
        issues: [
          issue({ title: "repo-a: M3.2 issue", labels: [{ name: "agent:go" }] }),
        ],
        blocks: [{ open: true, title: "repo-b: M3.2 blocker" }],
      },
    );

    expect(statuses.get("m3-2")).toBe("blocked");
  });

  it("supports an injectable matcher", () => {
    const stage: PlanStageNode = {
      id: "alpha",
      label: "Alpha",
      level: 2,
      parentId: null,
    };

    const statuses = deriveStatuses(
      graph([stage]),
      {
        prs: [pr({ title: "[ALPHA] implementation" })],
        issues: [issue({ title: "[ALPHA] tracking", labels: [{ name: "agent:go" }] })],
        blocks: [],
        matcher: (currentStage, item) =>
          item.title.includes(`[${currentStage.id.toUpperCase()}]`),
      },
    );

    expect(statuses.get("alpha")).toBe("dispatched");
  });

  it("shows merged when the stage has a merged PR (via merged_at) and no open work", () => {
    const stage: PlanStageNode = {
      id: "m5-1",
      label: "M5.1 Ship feature",
      level: 2,
      parentId: null,
    };

    const statuses = deriveStatuses(
      graph([stage]),
      {
        prs: [
          pr({ number: 10, title: "M5.1 ship feature", state: "closed", merged_at: "2026-05-01T00:00:00Z" }),
        ],
        issues: [],
        blocks: [],
      },
    );

    expect(statuses.get("m5-1")).toBe("merged");
  });
});

describe("defaultStageMatcher", () => {
  it("matches titles containing a normalized stage id", () => {
    const stage: PlanStageNode = {
      id: "m3-2",
      label: "Status taxonomy",
      level: 2,
      parentId: null,
    };

    expect(defaultStageMatcher(stage, { title: "Task M3.2: status taxonomy" })).toBe(true);
  });
});
