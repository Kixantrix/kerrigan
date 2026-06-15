// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DagLegend, PR_FLOW_ENTRIES, STATUS_ENTRIES } from "./DagLegend.js";

afterEach(() => {
  cleanup();
});

describe("DagLegend", () => {
  it("renders the toggle button", () => {
    render(<DagLegend />);
    expect(screen.getByTestId("dag-legend-toggle")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /show legend/i })).toBeInTheDocument();
  });

  it("panel is hidden by default", () => {
    render(<DagLegend />);
    expect(screen.queryByTestId("dag-legend-panel")).not.toBeInTheDocument();
  });

  it("shows panel when toggle button is clicked", () => {
    render(<DagLegend />);
    fireEvent.click(screen.getByTestId("dag-legend-toggle"));
    expect(screen.getByTestId("dag-legend-panel")).toBeInTheDocument();
  });

  it("collapses panel when toggle is clicked a second time", () => {
    render(<DagLegend />);
    const toggle = screen.getByTestId("dag-legend-toggle");
    fireEvent.click(toggle);
    expect(screen.getByTestId("dag-legend-panel")).toBeInTheDocument();
    fireEvent.click(toggle);
    expect(screen.queryByTestId("dag-legend-panel")).not.toBeInTheDocument();
  });

  it("updates aria-expanded on toggle", () => {
    render(<DagLegend />);
    const toggle = screen.getByTestId("dag-legend-toggle");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
  });

  it("renders all PR-flow legend entries", () => {
    render(<DagLegend />);
    fireEvent.click(screen.getByTestId("dag-legend-toggle"));

    const prFlowList = screen.getByTestId("dag-legend-pr-flows");
    expect(prFlowList).toBeInTheDocument();

    for (const entry of PR_FLOW_ENTRIES) {
      expect(screen.getByText(entry.label)).toBeInTheDocument();
      expect(prFlowList.querySelector(`[data-flow-kind="${entry.key}"]`)).toBeInTheDocument();
    }
  });

  it("renders all status swatches", () => {
    render(<DagLegend />);
    fireEvent.click(screen.getByTestId("dag-legend-toggle"));

    const statusList = screen.getByTestId("dag-legend-statuses");
    expect(statusList).toBeInTheDocument();

    for (const entry of STATUS_ENTRIES) {
      expect(screen.getByText(entry.label)).toBeInTheDocument();
      expect(statusList.querySelector(`[data-status="${entry.status}"]`)).toBeInTheDocument();
    }
  });

  it("omits animation classes when reducedMotion is true", () => {
    render(<DagLegend reducedMotion />);
    fireEvent.click(screen.getByTestId("dag-legend-toggle"));

    const panel = screen.getByTestId("dag-legend-panel");
    expect(panel.querySelector(".animate-ping")).not.toBeInTheDocument();
    expect(panel.querySelector(".animate-bounce")).not.toBeInTheDocument();
  });

  it("includes animation classes when reducedMotion is false", () => {
    render(<DagLegend reducedMotion={false} />);
    fireEvent.click(screen.getByTestId("dag-legend-toggle"));

    const panel = screen.getByTestId("dag-legend-panel");
    expect(panel.querySelector(".animate-ping")).toBeInTheDocument();
    expect(panel.querySelector(".animate-bounce")).toBeInTheDocument();
  });
});
