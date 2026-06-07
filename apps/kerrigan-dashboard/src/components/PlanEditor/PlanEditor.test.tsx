// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PlanEditor } from "./PlanEditor.js";

afterEach(() => {
  cleanup();
});

describe("PlanEditor", () => {
  it("renders markdown headings with stable stage anchors", async () => {
    render(<PlanEditor markdown={"## Build API\n\n### Compile"} selectedStageId={null} />);

    expect(await screen.findByTestId("plan-heading-build-api")).toHaveTextContent("Build API");
    expect(await screen.findByTestId("plan-heading-compile")).toHaveTextContent("Compile");
  });

  it("scrolls to the selected stage heading", async () => {
    const scrolledStageIds: string[] = [];
    const scrollIntoViewMock = vi.fn(function thisBound(this: HTMLElement) {
      scrolledStageIds.push(this.dataset.stageId ?? "");
    });

    const originalScrollIntoView = HTMLElement.prototype.scrollIntoView;
    HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;
    try {
      const { rerender } = render(
        <PlanEditor markdown={"## Build\n\n## Ship"} selectedStageId={null} />,
      );
      rerender(<PlanEditor markdown={"## Build\n\n## Ship"} selectedStageId="ship" />);

      await waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalled();
      });
      expect(scrolledStageIds).toContain("ship");
    } finally {
      HTMLElement.prototype.scrollIntoView = originalScrollIntoView;
    }
  });
});
