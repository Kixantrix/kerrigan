import { describe, expect, it } from "vitest";
import type { IssueData, PullRequestData, ReviewData } from "./github.js";
import type { PlanStageGraph, PlanStageNode } from "./plan-parser.js";
import {
  defaultStageMatcher,
  deriveStageStatus,
  deriveStatuses,
  groupPRsByStage,
  groupStageWorkByStage,
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

  it("matches via milestone prefix for heading-derived ids (e.g. m3-project-detail-dag → M3)", () => {
    const stage: PlanStageNode = {
      id: "m3-project-detail-dag",
      label: "Project Detail DAG",
      level: 2,
      parentId: null,
    };

    expect(defaultStageMatcher(stage, { title: "M3 tracking issue" })).toBe(true);
    expect(defaultStageMatcher(stage, { title: "feat: M3.1 ship it" })).toBe(true);
    expect(defaultStageMatcher(stage, { title: "fix M3.4 bug" })).toBe(true);
  });

  it("does not match M30 when milestone prefix is m3", () => {
    const stage: PlanStageNode = {
      id: "m3-project-detail-dag",
      label: "Project Detail DAG",
      level: 2,
      parentId: null,
    };

    // "M30" normalises to "m30" — a different standalone word from "m3"
    expect(defaultStageMatcher(stage, { title: "M30 unrelated milestone" })).toBe(false);
    // "M31" also should not match
    expect(defaultStageMatcher(stage, { title: "feat M31 unrelated" })).toBe(false);
  });

  it("does NOT match via body-only milestone mention (false-positive prevention)", () => {
    const stage: PlanStageNode = {
      id: "m3-project-detail-dag",
      label: "Project Detail DAG",
      level: 2,
      parentId: null,
    };

    // Body-only matches are excluded: a PR that incidentally mentions "M3" in
    // its description (e.g. a dispatch briefing using M3 as an example) must
    // NOT be seeded to the M3 stage.
    expect(
      defaultStageMatcher(stage, {
        title: "fix: some hotfix with no milestone in title",
      }),
    ).toBe(false);
  });

  it("matches via milestone prefix in head branch ref", () => {
    const stage: PlanStageNode = {
      id: "m3-project-detail-dag",
      label: "Project Detail DAG",
      level: 2,
      parentId: null,
    };

    expect(
      defaultStageMatcher(stage, {
        title: "fix: hotfix",
        head: { ref: "feature/m3-dag-polish" },
      }),
    ).toBe(true);
  });

  it("does not apply milestone-prefix matching to sub-indexed stages (m3-2, m3-4-some-feature)", () => {
    // Sub-indexed stages have a pure-digit second segment; the prefix matching is
    // intentionally not applied — they rely on the existing compact-match paths.
    const subIndexed: PlanStageNode = {
      id: "m3-2",
      label: "M3.2 status taxonomy",
      level: 2,
      parentId: null,
    };

    // Still matches via normalizedId/stageIdPattern compact check
    expect(defaultStageMatcher(subIndexed, { title: "Task M3.2: status taxonomy" })).toBe(true);
    // Does NOT match M3.1 or M3.4 — prefix matching is disabled for sub-indexed stages
    expect(defaultStageMatcher(subIndexed, { title: "M3.4 unrelated sub-task" })).toBe(false);
  });
});

describe("deriveStatuses — closing-PR traversal (Option C)", () => {
  it("shows merged when a matched issue was closed by a merged PR even if PR title lacks milestone", () => {
    const stage: PlanStageNode = {
      id: "m3-project-detail-dag",
      label: "Project Detail DAG",
      level: 2,
      parentId: null,
    };

    const statuses = deriveStatuses(
      graph([stage]),
      {
        prs: [],
        issues: [
          issue({
            title: "M3 tracking issue",
            state: "closed",
            closingPRs: [
              { number: 42, merged: true, title: "fix(dashboard): some unrelated title", url: "https://example.com/pr/42" },
            ],
          }),
        ],
        blocks: [],
      },
    );

    expect(statuses.get("m3-project-detail-dag")).toBe("merged");
  });

  it("shows planned when the closing PR of a matched issue was NOT merged (only closed)", () => {
    const stage: PlanStageNode = {
      id: "m3-project-detail-dag",
      label: "Project Detail DAG",
      level: 2,
      parentId: null,
    };

    const statuses = deriveStatuses(
      graph([stage]),
      {
        prs: [],
        issues: [
          issue({
            title: "M3 tracking issue",
            state: "closed",
            closingPRs: [
              { number: 42, merged: false, title: "fix: closed without merge", url: "https://example.com/pr/42" },
            ],
          }),
        ],
        blocks: [],
      },
    );

    expect(statuses.get("m3-project-detail-dag")).toBe("planned");
  });

  it("blocked takes precedence over closing-PR merged signal", () => {
    const stage: PlanStageNode = {
      id: "m3-project-detail-dag",
      label: "Project Detail DAG",
      level: 2,
      parentId: null,
    };

    const statuses = deriveStatuses(
      graph([stage]),
      {
        prs: [],
        issues: [
          issue({
            title: "M3 tracking issue",
            state: "closed",
            closingPRs: [
              { number: 42, merged: true, title: "fix: merged hotfix", url: "https://example.com/pr/42" },
            ],
          }),
        ],
        blocks: [{ open: true, title: "M3 blocker" }],
      },
    );

    expect(statuses.get("m3-project-detail-dag")).toBe("blocked");
  });

  it("direct merged-PR title match (#385) still works alongside closing-PR traversal", () => {
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

describe("groupPRsByStage", () => {
  const stageA: PlanStageNode = {
    id: "m3-2",
    label: "M3.2 Status",
    level: 2,
    parentId: null,
  };
  const stageB: PlanStageNode = {
    id: "m3-3",
    label: "M3.3 DAG",
    level: 2,
    parentId: null,
  };

  it("returns an empty map when no PRs are provided", () => {
    const result = groupPRsByStage(graph([stageA, stageB]), []);
    expect(result.size).toBe(0);
  });

  it("maps a PR to the correct stage", () => {
    const matchedPr = pr({ number: 1, title: "M3.2 status work" });
    const result = groupPRsByStage(graph([stageA, stageB]), [matchedPr]);
    expect(result.get("m3-2")).toEqual([matchedPr]);
    expect(result.has("m3-3")).toBe(false);
  });

  it("groups multiple PRs across multiple stages", () => {
    const prA1 = pr({ number: 1, title: "M3.2 open PR", html_url: "https://github.com/o/r/pull/1" });
    const prA2 = pr({ number: 2, title: "M3.2 merged PR", state: "closed", merged_at: "2026-05-01T00:00:00Z", html_url: "https://github.com/o/r/pull/2" });
    const prB1 = pr({ number: 3, title: "M3.3 dag work", html_url: "https://github.com/o/r/pull/3" });

    const result = groupPRsByStage(graph([stageA, stageB]), [prA1, prA2, prB1]);
    expect(result.get("m3-2")).toEqual([prA1, prA2]);
    expect(result.get("m3-3")).toEqual([prB1]);
  });

  it("does not include stages that have no matching PRs", () => {
    const unrelatedPr = pr({ number: 99, title: "chore: unrelated change", html_url: "https://github.com/o/r/pull/99" });
    const result = groupPRsByStage(graph([stageA, stageB]), [unrelatedPr]);
    expect(result.has("m3-2")).toBe(false);
    expect(result.has("m3-3")).toBe(false);
  });

  it("supports a custom matcher override", () => {
    const customMatcher = () => true;
    const singlePr = pr({ number: 5, title: "anything", html_url: "https://github.com/o/r/pull/5" });
    const result = groupPRsByStage(graph([stageA, stageB]), [singlePr], customMatcher);
    expect(result.get("m3-2")).toEqual([singlePr]);
    expect(result.get("m3-3")).toEqual([singlePr]);
  });
});

describe("groupStageWorkByStage", () => {
  const stage: PlanStageNode = {
    id: "m3",
    label: "M3",
    level: 2,
    parentId: null,
  };

  it("groups matched issues and PRs together for a stage", () => {
    const matchedIssue = issue({ number: 24, title: "M3.4: tracking issue" });
    const matchedPr = pr({
      number: 42,
      title: "M3.4 status work",
      html_url: "https://github.com/o/r/pull/42",
    });

    const result = groupStageWorkByStage(
      graph([stage]),
      { prs: [matchedPr], issues: [matchedIssue] },
    );

    expect(result.get("m3")).toEqual({
      prs: [matchedPr],
      issues: [matchedIssue],
    });
  });

  it("includes merged closing PRs for matched issues without duplicating direct matches", () => {
    const directPr = pr({
      number: 88,
      title: "fix(dashboard): detail panel polish",
      state: "closed",
      merged_at: "2026-05-01T00:00:00Z",
      html_url: "https://github.com/o/r/pull/88",
    });
    const matchedIssue = issue({
      title: "M3.4: tracking issue",
      closingPRs: [
        {
          number: 88,
          merged: true,
          title: "fix(dashboard): detail panel polish",
          url: "https://github.com/o/r/pull/88",
        },
        {
          number: 89,
          merged: true,
          title: "fix(dashboard): follow-up",
          url: "https://github.com/o/r/pull/89",
        },
      ],
    });

    const result = groupStageWorkByStage(
      graph([stage]),
      { prs: [directPr], issues: [matchedIssue] },
    );

    expect(result.get("m3")?.issues).toEqual([matchedIssue]);
    expect(result.get("m3")?.prs).toEqual([
      directPr,
      expect.objectContaining({
        number: 89,
        title: "fix(dashboard): follow-up",
        state: "merged",
        html_url: "https://github.com/o/r/pull/89",
      }),
    ]);
  });
});
