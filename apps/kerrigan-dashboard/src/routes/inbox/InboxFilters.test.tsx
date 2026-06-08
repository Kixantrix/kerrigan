// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { applyFilters, INITIAL_FILTER_STATE } from "./inboxFilterUtils.js";
import { InboxFilters } from "./InboxFilters.js";

afterEach(() => {
  cleanup();
});

const sampleItems = [
  { projectId: "proj-a", kind: "block" as const, ageMs: 3 * 24 * 60 * 60 * 1000 },
  { projectId: "proj-b", kind: "review" as const, ageMs: 2 * 60 * 60 * 1000 },
  { projectId: "proj-a", kind: "capture-issue" as const, ageMs: 10 * 24 * 60 * 60 * 1000 },
  { projectId: "proj-b", kind: "attestation" as const, ageMs: 0 },
];

describe("applyFilters", () => {
  it("returns all true when filters are at initial state", () => {
    const mask = applyFilters(sampleItems, INITIAL_FILTER_STATE);
    expect(mask).toEqual([true, true, true, true]);
  });

  it("filters by projectId", () => {
    const mask = applyFilters(sampleItems, {
      ...INITIAL_FILTER_STATE,
      projectId: "proj-a",
    });
    expect(mask).toEqual([true, false, true, false]);
  });

  it("filters by kind", () => {
    const mask = applyFilters(sampleItems, {
      ...INITIAL_FILTER_STATE,
      kind: "block",
    });
    expect(mask).toEqual([true, false, false, false]);
  });

  it("filters by age >1d", () => {
    const mask = applyFilters(sampleItems, {
      ...INITIAL_FILTER_STATE,
      age: ">1d",
    });
    // 3d: pass, 2h: fail, 10d: pass, 0: fail
    expect(mask).toEqual([true, false, true, false]);
  });

  it("filters by age >7d", () => {
    const mask = applyFilters(sampleItems, {
      ...INITIAL_FILTER_STATE,
      age: ">7d",
    });
    expect(mask).toEqual([false, false, true, false]);
  });

  it("combines projectId and kind filters", () => {
    const mask = applyFilters(sampleItems, {
      projectId: "proj-a",
      kind: "capture-issue",
      age: "all",
    });
    expect(mask).toEqual([false, false, true, false]);
  });
});

describe("InboxFilters", () => {
  it("renders all filter controls", () => {
    render(
      <InboxFilters
        projects={["proj-a", "proj-b"]}
        filters={INITIAL_FILTER_STATE}
        onChange={vi.fn()}
        totalCount={4}
        filteredCount={4}
      />,
    );

    expect(screen.getByTestId("inbox-filter-project")).toBeInTheDocument();
    expect(screen.getByTestId("inbox-filter-kind")).toBeInTheDocument();
    expect(screen.getByTestId("inbox-filter-age")).toBeInTheDocument();
  });

  it("shows item count", () => {
    render(
      <InboxFilters
        projects={["proj-a"]}
        filters={INITIAL_FILTER_STATE}
        onChange={vi.fn()}
        totalCount={5}
        filteredCount={5}
      />,
    );

    expect(screen.getByTestId("inbox-filter-count")).toHaveTextContent("5 items");
  });

  it("shows filtered count when filters are active", () => {
    render(
      <InboxFilters
        projects={["proj-a"]}
        filters={{ ...INITIAL_FILTER_STATE, kind: "block" }}
        onChange={vi.fn()}
        totalCount={5}
        filteredCount={2}
      />,
    );

    expect(screen.getByTestId("inbox-filter-count")).toHaveTextContent("2 of 5");
  });

  it("shows reset button when a filter is active", () => {
    render(
      <InboxFilters
        projects={["proj-a"]}
        filters={{ ...INITIAL_FILTER_STATE, kind: "block" }}
        onChange={vi.fn()}
        totalCount={5}
        filteredCount={2}
      />,
    );

    expect(screen.getByTestId("inbox-filter-reset")).toBeInTheDocument();
  });

  it("does not show reset button when no filter is active", () => {
    render(
      <InboxFilters
        projects={["proj-a"]}
        filters={INITIAL_FILTER_STATE}
        onChange={vi.fn()}
        totalCount={5}
        filteredCount={5}
      />,
    );

    expect(screen.queryByTestId("inbox-filter-reset")).not.toBeInTheDocument();
  });

  it("calls onChange when kind filter changes", () => {
    const onChange = vi.fn();

    render(
      <InboxFilters
        projects={["proj-a"]}
        filters={INITIAL_FILTER_STATE}
        onChange={onChange}
        totalCount={4}
        filteredCount={4}
      />,
    );

    fireEvent.change(screen.getByTestId("inbox-filter-kind"), {
      target: { value: "review" },
    });

    expect(onChange).toHaveBeenCalledWith({
      ...INITIAL_FILTER_STATE,
      kind: "review",
    });
  });

  it("calls onChange with reset state when reset is clicked", () => {
    const onChange = vi.fn();

    render(
      <InboxFilters
        projects={["proj-a"]}
        filters={{ ...INITIAL_FILTER_STATE, kind: "block" }}
        onChange={onChange}
        totalCount={5}
        filteredCount={2}
      />,
    );

    fireEvent.click(screen.getByTestId("inbox-filter-reset"));
    expect(onChange).toHaveBeenCalledWith(INITIAL_FILTER_STATE);
  });
});
