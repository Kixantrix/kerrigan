// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PrFlowOverlay } from "./PrFlowOverlay.js";

class ResizeObserverMock {
  public observe(): void {
    return;
  }

  public disconnect(): void {
    return;
  }
}

describe("PrFlowOverlay", () => {
  beforeEach(() => {
    vi.stubGlobal("ResizeObserver", ResizeObserverMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders a transparent non-interactive canvas overlay", () => {
    render(
      <div style={{ height: "320px", position: "relative", width: "600px" }}>
        <PrFlowOverlay
          flows={[
            {
              id: "flow-1",
              from: { x: 50, y: 60 },
              to: { x: 250, y: 160 },
              state: "streaming",
            },
          ]}
          reducedMotion
        />
      </div>,
    );

    const canvas = screen.getByTestId("pr-flow-overlay");
    expect(canvas).toBeInTheDocument();
    expect(canvas).toHaveStyle({
      pointerEvents: "none",
      position: "absolute",
    });
  });
});
