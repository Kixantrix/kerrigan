import type { PullRequestData } from "../../lib/github.js";
import type { PlanStageNode } from "../../lib/plan-parser.js";
import { defaultStageMatcher, type StageStatus } from "../../lib/status.js";
import type { PrFlow, PrFlowPoint } from "./types.js";

interface MatchedPrFlow {
  flowId: string;
  prKey: string;
  stageId: string;
  from: PrFlowPoint;
  to: PrFlowPoint;
}

interface AbsorbingFlow extends MatchedPrFlow {
  startedAt: number;
}

export interface PrFlowBindingState {
  previousOpenByKey: Map<string, MatchedPrFlow>;
  absorbingByKey: Map<string, AbsorbingFlow>;
}

export interface PrFlowBindingInput {
  openPRs: ReadonlyArray<PullRequestData>;
  mergedPRs?: ReadonlyArray<PullRequestData>;
  stages: ReadonlyArray<Pick<PlanStageNode, "id" | "label">>;
  stageStatuses: ReadonlyMap<string, StageStatus>;
  nodePositions: ReadonlyMap<string, PrFlowPoint>;
  sourceOrigin: PrFlowPoint;
}

export interface PrFlowBindingResult {
  flows: ReadonlyArray<PrFlow>;
  flowStageIds: ReadonlyMap<string, string>;
  state: PrFlowBindingState;
}

const ABSORBING_FLOW_MS = 1_200;
const FLOW_SOURCE_SPACING_Y = 24;

export function createPrFlowBindingState(): PrFlowBindingState {
  return {
    previousOpenByKey: new Map(),
    absorbingByKey: new Map(),
  };
}

export function derivePrFlows(
  input: PrFlowBindingInput,
  state: PrFlowBindingState,
  nowMs: number = Date.now(),
): PrFlowBindingResult {
  const nextOpenByKey = new Map<string, MatchedPrFlow>();
  const nextAbsorbingByKey = new Map(state.absorbingByKey);
  const mergedKeys = new Set((input.mergedPRs ?? []).map(prKey));
  const stageById = new Map(input.stages.map((stage) => [stage.id, stage]));
  const streamingFlows: PrFlow[] = [];
  const flowStageIds = new Map<string, string>();

  input.openPRs.forEach((pr, index) => {
    const match = matchPrToStage(pr, stageById, input.nodePositions);
    if (match === null) {
      return;
    }

    const source = {
      x: input.sourceOrigin.x,
      y: input.sourceOrigin.y + index * FLOW_SOURCE_SPACING_Y,
    } satisfies PrFlowPoint;
    const key = prKey(pr);
    const flowId = flowIdFor(key, match.stage.id);
    const matched = {
      flowId,
      from: source,
      prKey: key,
      stageId: match.stage.id,
      to: match.target,
    } satisfies MatchedPrFlow;

    nextOpenByKey.set(key, matched);
    nextAbsorbingByKey.delete(key);
    flowStageIds.set(flowId, match.stage.id);
    streamingFlows.push({
      id: flowId,
      from: source,
      to: match.target,
      state: "streaming",
    });
  });

  for (const [key, previous] of state.previousOpenByKey.entries()) {
    if (nextOpenByKey.has(key)) {
      continue;
    }

    const status = input.stageStatuses.get(previous.stageId);
    const shouldAbsorb =
      input.mergedPRs === undefined || mergedKeys.has(key) || status === "merged";
    if (!shouldAbsorb) {
      continue;
    }

    if (!nextAbsorbingByKey.has(key)) {
      nextAbsorbingByKey.set(key, { ...previous, startedAt: nowMs });
    }
  }

  const absorbingFlows: PrFlow[] = [];
  for (const [key, absorbing] of nextAbsorbingByKey.entries()) {
    if (nowMs - absorbing.startedAt > ABSORBING_FLOW_MS) {
      nextAbsorbingByKey.delete(key);
      continue;
    }

    flowStageIds.set(absorbing.flowId, absorbing.stageId);
    absorbingFlows.push({
      id: absorbing.flowId,
      from: absorbing.from,
      to: absorbing.to,
      state: "absorbing",
    });
  }

  return {
    flows: [...streamingFlows, ...absorbingFlows],
    flowStageIds,
    state: {
      previousOpenByKey: nextOpenByKey,
      absorbingByKey: nextAbsorbingByKey,
    },
  };
}

export function stageIdFromFlowId(flowId: string): string | null {
  const marker = "::stage:";
  const markerIndex = flowId.lastIndexOf(marker);
  if (markerIndex === -1) {
    return null;
  }
  return flowId.slice(markerIndex + marker.length);
}

function matchPrToStage(
  pr: PullRequestData,
  stageById: ReadonlyMap<string, Pick<PlanStageNode, "id" | "label">>,
  nodePositions: ReadonlyMap<string, PrFlowPoint>,
): { stage: Pick<PlanStageNode, "id" | "label">; target: PrFlowPoint } | null {
  for (const stage of stageById.values()) {
    const target = nodePositions.get(stage.id);
    if (target === undefined) {
      continue;
    }
    if (defaultStageMatcher({ ...stage, level: 2, parentId: null }, pr)) {
      return { stage, target };
    }
  }

  return null;
}

function prKey(pr: Pick<PullRequestData, "html_url">): string {
  return pr.html_url;
}

function flowIdFor(key: string, stageId: string): string {
  return `pr:${key}::stage:${stageId}`;
}
