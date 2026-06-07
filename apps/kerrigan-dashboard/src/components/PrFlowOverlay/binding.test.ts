import { describe, expect, it } from "vitest";
import type { PullRequestData } from "../../lib/github.js";
import { createPrFlowBindingState, derivePrFlows } from "./binding.js";

const STAGES = [
  { id: "m3-1-parse", label: "M3.1 Parse" },
  { id: "m5-2-ui", label: "M5.2 UI" },
] as const;

const NODE_POSITIONS = new Map([
  ["m3-1-parse", { x: 120, y: 160 }],
  ["m5-2-ui", { x: 380, y: 200 }],
]);

describe("derivePrFlows", () => {
  it("maps open PRs into streaming flows", () => {
    const state = createPrFlowBindingState();
    const result = derivePrFlows(
      {
        openPRs: [makePr("https://github.com/Kixantrix/kerrigan/pull/42", "M3.1 Parse: wire overlay")],
        stages: STAGES,
        stageStatuses: new Map([["m3-1-parse", "dispatched"]]),
        nodePositions: NODE_POSITIONS,
        sourceOrigin: { x: 520, y: 60 },
      },
      state,
      10,
    );

    expect(result.flows).toEqual([
      expect.objectContaining({
        state: "streaming",
        to: { x: 120, y: 160 },
      }),
    ]);
  });

  it("emits absorbing once when PR leaves open set by default", () => {
    const first = derivePrFlows(
      {
        openPRs: [makePr("https://github.com/Kixantrix/kerrigan/pull/45", "M5.2 UI polish")],
        stages: STAGES,
        stageStatuses: new Map([["m5-2-ui", "dispatched"]]),
        nodePositions: NODE_POSITIONS,
        sourceOrigin: { x: 520, y: 60 },
      },
      createPrFlowBindingState(),
      100,
    );

    const second = derivePrFlows(
      {
        openPRs: [],
        stages: STAGES,
        stageStatuses: new Map([["m5-2-ui", "planned"]]),
        nodePositions: NODE_POSITIONS,
        sourceOrigin: { x: 520, y: 60 },
      },
      first.state,
      200,
    );

    expect(second.flows).toEqual([
      expect.objectContaining({
        state: "absorbing",
        to: { x: 380, y: 200 },
      }),
    ]);
  });

  it("treats non-merged departures as fade when merged set is explicit", () => {
    const first = derivePrFlows(
      {
        openPRs: [makePr("https://github.com/Kixantrix/kerrigan/pull/47", "M3.1 Parse cleanup")],
        stages: STAGES,
        stageStatuses: new Map([["m3-1-parse", "dispatched"]]),
        nodePositions: NODE_POSITIONS,
        sourceOrigin: { x: 520, y: 60 },
        mergedPRs: [],
      },
      createPrFlowBindingState(),
      100,
    );

    const second = derivePrFlows(
      {
        openPRs: [],
        stages: STAGES,
        stageStatuses: new Map([["m3-1-parse", "planned"]]),
        nodePositions: NODE_POSITIONS,
        sourceOrigin: { x: 520, y: 60 },
        mergedPRs: [],
      },
      first.state,
      150,
    );

    expect(second.flows).toEqual([]);
  });

  it("uses title matching to resolve PR to stage", () => {
    const result = derivePrFlows(
      {
        openPRs: [makePr("https://github.com/Kixantrix/kerrigan/pull/49", "m52ui tighten states")],
        stages: STAGES,
        stageStatuses: new Map([["m5-2-ui", "dispatched"]]),
        nodePositions: NODE_POSITIONS,
        sourceOrigin: { x: 520, y: 60 },
      },
      createPrFlowBindingState(),
      100,
    );

    expect(result.flows[0]).toEqual(
      expect.objectContaining({
        state: "streaming",
        to: { x: 380, y: 200 },
      }),
    );
  });

  it("does not add extra absorbing flows when open set is unchanged", () => {
    const first = derivePrFlows(
      {
        openPRs: [makePr("https://github.com/Kixantrix/kerrigan/pull/52", "M3.1 Parse improvements")],
        stages: STAGES,
        stageStatuses: new Map([["m3-1-parse", "dispatched"]]),
        nodePositions: NODE_POSITIONS,
        sourceOrigin: { x: 520, y: 60 },
      },
      createPrFlowBindingState(),
      100,
    );

    const second = derivePrFlows(
      {
        openPRs: [makePr("https://github.com/Kixantrix/kerrigan/pull/52", "M3.1 Parse improvements")],
        stages: STAGES,
        stageStatuses: new Map([["m3-1-parse", "dispatched"]]),
        nodePositions: NODE_POSITIONS,
        sourceOrigin: { x: 520, y: 60 },
      },
      first.state,
      150,
    );

    expect(second.flows).toHaveLength(1);
    expect(second.flows[0]?.state).toBe("streaming");
  });
});

function makePr(url: string, title: string): PullRequestData {
  return {
    number: 1,
    title,
    state: "open",
    draft: false,
    user: { login: "copilot" },
    created_at: "2026-06-01T00:00:00Z",
    updated_at: "2026-06-01T00:00:00Z",
    head: { ref: "feature", sha: "abc123" },
    base: { ref: "main" },
    html_url: url,
  };
}
