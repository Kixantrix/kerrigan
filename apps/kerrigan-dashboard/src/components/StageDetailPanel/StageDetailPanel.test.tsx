// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { IssueData, PullRequestData } from "../../lib/github.js";
import { StageDetailPanel } from "./StageDetailPanel.js";

afterEach(() => {
  cleanup();
});

function issue(overrides: Partial<IssueData> = {}): IssueData {
  const number = overrides.number ?? 1;
  return {
    number,
    title: "M3.4: issue",
    state: "open",
    user: { login: "agent" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-06-01T00:00:00Z",
    labels: [{ name: "agent:go" }],
    html_url: `https://github.com/Kixantrix/kerrigan/issues/${number}`,
    ...overrides,
  };
}

function pr(overrides: Partial<PullRequestData> = {}): PullRequestData {
  const number = overrides.number ?? 2;
  return {
    number,
    title: "M3.4: PR",
    state: "open",
    draft: false,
    user: { login: "agent" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-06-01T00:00:00Z",
    merged_at: null,
    head: { ref: "feature/m3-4", sha: "abc123" },
    base: { ref: "main" },
    html_url: `https://github.com/Kixantrix/kerrigan/pull/${number}`,
    ...overrides,
  };
}

describe("StageDetailPanel", () => {
  it("groups issues and PRs by sub-milestone and keeps unmatched items under Other", () => {
    render(
      <StageDetailPanel
        stageId="m3"
        stageName="M3"
        issues={[
          issue({ number: 33, title: "M3.3: tracking issue" }),
          issue({ number: 34, title: "M3.4: shipped issue", state: "closed", labels: [{ name: "done" }] }),
          issue({ number: 36, title: "fix: examples M2.1, M3.4 in title" }),
          issue({ number: 35, title: "Milestone-level coordination" }),
        ]}
        prs={[
          pr({ number: 43, title: "M3.3: DAG polish" }),
          pr({ number: 44, title: "M3.4: merge detail panel", state: "closed", merged_at: "2026-06-02T00:00:00Z" }),
          pr({ number: 46, title: "M2.1: foreign milestone mention only" }),
          pr({ number: 45, title: "fix(dashboard): milestone-level cleanup" }),
        ]}
        onClose={vi.fn()}
      />,
    );

    const headings = screen.getAllByTestId(/stage-detail-group-heading-/).map((node) => node.textContent);
    expect(headings).toEqual(["M3.3", "M3.4", "Other"]);
    expect(screen.queryByTestId("stage-detail-group-heading-m2-1")).not.toBeInTheDocument();

    const m33Group = screen.getByTestId("stage-detail-group-m3-3");
    expect(within(m33Group).getByTestId("stage-detail-issue-33")).toBeInTheDocument();
    expect(within(m33Group).getByTestId("stage-detail-pr-43")).toBeInTheDocument();

    const m34Group = screen.getByTestId("stage-detail-group-m3-4");
    expect(within(m34Group).getByTestId("stage-detail-issue-34")).toBeInTheDocument();
    expect(within(m34Group).getByTestId("stage-detail-issue-36")).toBeInTheDocument();
    expect(within(m34Group).getByTestId("stage-detail-pr-44")).toBeInTheDocument();
    expect(within(m34Group).getByTestId("stage-detail-pr-state-44")).toHaveTextContent("Merged");

    const otherGroup = screen.getByTestId("stage-detail-group-other");
    expect(within(otherGroup).getByTestId("stage-detail-issue-35")).toBeInTheDocument();
    expect(within(otherGroup).getByTestId("stage-detail-pr-45")).toBeInTheDocument();
    expect(within(otherGroup).getByTestId("stage-detail-pr-46")).toBeInTheDocument();
  });

  it("keeps the existing empty state text when no items are present", () => {
    render(
      <StageDetailPanel
        stageId="m3"
        stageName="M3"
        issues={[]}
        prs={[]}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByTestId("stage-detail-empty")).toHaveTextContent("No PRs found for this stage.");
  });
});
