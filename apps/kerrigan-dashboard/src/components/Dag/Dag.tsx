import "@xyflow/react/dist/style.css";
import {
  Background,
  Controls,
  ReactFlow,
  type NodeTypes,
  useNodesInitialized,
  useReactFlow,
} from "@xyflow/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { PullRequestData } from "../../lib/github.js";
import {
  buildDagLayout,
  type StageDagNode,
  type StageDagEdge,
} from "../../lib/dag-layout.js";
import type { PlanStageGraph } from "../../lib/plan-parser.js";
import type { StageStatus } from "../../lib/status.js";
import { PrFlowOverlay } from "../PrFlowOverlay/PrFlowOverlay.js";
import { ABSORBING_FLOW_DURATION_MS } from "../PrFlowOverlay/constants.js";
import {
  createPrFlowBindingState,
  derivePrFlows,
  stageIdFromFlowId,
} from "../PrFlowOverlay/binding.js";
import type { PrFlow, PrFlowPoint } from "../PrFlowOverlay/types.js";
import { StageNode } from "./StageNode.js";
import { DagLegend } from "./DagLegend.js";

interface DagProps {
  graph: PlanStageGraph;
  statuses: ReadonlyMap<string, StageStatus>;
  openPRs: ReadonlyArray<PullRequestData>;
  onStageSelect?: (stageId: string) => void;
}

const nodeTypes = {
  stage: StageNode,
} satisfies NodeTypes;

const edgeColorByKind: Record<"parent" | "dependency", string> = {
  parent: "#2A3342",
  dependency: "#5965F2",
};
// Pulse starts just before absorb completion for smoother visual handoff.
const ABSORB_PULSE_LEAD_MS = 250;
const ABSORB_PULSE_DELAY_MS = ABSORBING_FLOW_DURATION_MS - ABSORB_PULSE_LEAD_MS;
const FLOW_SOURCE_MIN_X = 24;
const FLOW_SOURCE_OFFSET_X = 40;
const FLOW_SOURCE_OFFSET_Y = 40;
const FIT_PADDING = 0.2;
const FIT_MAX_ZOOM = 1;

interface FitViewOnNodesReadyProps {
  fitRevision: number;
}

function FitViewOnNodesReady({ fitRevision }: FitViewOnNodesReadyProps) {
  const { fitView } = useReactFlow();
  const nodesInitialized = useNodesInitialized();

  useEffect(() => {
    if (!nodesInitialized) {
      return;
    }

    void fitView({ padding: FIT_PADDING, maxZoom: FIT_MAX_ZOOM });
  }, [fitView, fitRevision, nodesInitialized]);

  return null;
}

export function Dag({ graph, statuses, openPRs, onStageSelect }: DagProps) {
  const layout = useMemo(() => buildDagLayout(graph, statuses), [graph, statuses]);
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const bindingStateRef = useRef(createPrFlowBindingState());
  const flowStageIdsRef = useRef<ReadonlyMap<string, string>>(new Map());
  const absorbingTimerByFlowRef = useRef<Map<string, number>>(new Map());
  const [flows, setFlows] = useState<ReadonlyArray<PrFlow>>([]);
  const [nodePositions, setNodePositions] = useState<ReadonlyMap<string, PrFlowPoint>>(new Map());
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const [pulseAtByStage, setPulseAtByStage] = useState<ReadonlyMap<string, number>>(new Map());
  const [viewportRevision, setViewportRevision] = useState(0);
  const [fitRevision, setFitRevision] = useState(0);

  const edges = useMemo<StageDagEdge[]>(
    () =>
      layout.edges.map((edge) => ({
        ...edge,
        style: { stroke: edgeColorByKind[edge.data?.kind ?? "parent"], strokeWidth: 1.5 },
      })),
    [layout.edges],
  );

  const nodes = useMemo<StageDagNode[]>(
    () =>
      layout.nodes.map((node) => {
        const pulseAt = pulseAtByStage.get(node.id);
        return {
          ...node,
          data: {
            ...node.data,
            ...(pulseAt === undefined ? {} : { pulseAt }),
          },
        };
      }),
    [layout.nodes, pulseAtByStage],
  );
  useEffect(() => {
    setFitRevision((previous) => previous + 1);
  }, [graph]);

  const recomputeNodePositions = useCallback(() => {
    const wrapper = wrapperRef.current;
    if (wrapper === null) {
      return;
    }

    const wrapperRect = wrapper.getBoundingClientRect();
    setContainerSize({ width: wrapperRect.width, height: wrapperRect.height });

    const next = new Map<string, PrFlowPoint>();
    for (const node of layout.nodes) {
      const element = wrapper.querySelector(`[data-testid="stage-node-${node.id}"]`);
      if (!(element instanceof HTMLElement)) {
        continue;
      }

      const rect = element.getBoundingClientRect();
      next.set(node.id, {
        x: rect.left - wrapperRect.left + rect.width / 2,
        y: rect.top - wrapperRect.top + rect.height / 2,
      });
    }
    setNodePositions(next);
  }, [layout.nodes]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(recomputeNodePositions);
    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [recomputeNodePositions, viewportRevision]);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (wrapper === null) {
      return;
    }

    const observer = new ResizeObserver(() => {
      recomputeNodePositions();
    });
    observer.observe(wrapper);
    return () => {
      observer.disconnect();
    };
  }, [recomputeNodePositions]);

  const pulseStage = useCallback((stageId: string) => {
    setPulseAtByStage((previous) => {
      const next = new Map(previous);
      next.set(stageId, Date.now());
      return next;
    });
  }, []);

  const pulseForFlow = useCallback((flowId: string) => {
    const stageId = flowStageIdsRef.current.get(flowId) ?? stageIdFromFlowId(flowId);
    if (stageId === null) {
      return;
    }
    pulseStage(stageId);
  }, [pulseStage]);

  const onAbsorbed = useCallback((flowId: string) => {
    pulseForFlow(flowId);
  }, [pulseForFlow]);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (wrapper === null || containerSize.width <= 0) {
      setFlows([]);
      return;
    }

    const sourceOrigin = {
      x: Math.max(FLOW_SOURCE_MIN_X, containerSize.width - FLOW_SOURCE_OFFSET_X),
      y: FLOW_SOURCE_OFFSET_Y,
    };
    const result = derivePrFlows(
      {
        openPRs,
        stages: layout.nodes.map((node) => ({
          id: node.id,
          label: String(node.data.label),
        })),
        stageStatuses: statuses,
        nodePositions,
        sourceOrigin,
      },
      bindingStateRef.current,
    );
    bindingStateRef.current = result.state;
    flowStageIdsRef.current = result.flowStageIds;
    const activeAbsorbingFlowIds = new Set(
      result.flows
        .filter((flow) => flow.state === "absorbing")
        .map((flow) => flow.id),
    );
    for (const flowId of activeAbsorbingFlowIds) {
      if (absorbingTimerByFlowRef.current.has(flowId)) {
        continue;
      }

      const stageId = result.flowStageIds.get(flowId);
      if (stageId === undefined) {
        continue;
      }
      const timer = window.setTimeout(() => {
        pulseForFlow(flowId);
        absorbingTimerByFlowRef.current.delete(flowId);
      }, ABSORB_PULSE_DELAY_MS);
      absorbingTimerByFlowRef.current.set(flowId, timer);
    }
    for (const [flowId, timer] of absorbingTimerByFlowRef.current.entries()) {
      if (!activeAbsorbingFlowIds.has(flowId)) {
        window.clearTimeout(timer);
        absorbingTimerByFlowRef.current.delete(flowId);
      }
    }
    setFlows(result.flows);
  }, [containerSize.width, layout.nodes, nodePositions, openPRs, pulseForFlow, statuses]);

  useEffect(
    () => () => {
      for (const timer of absorbingTimerByFlowRef.current.values()) {
        window.clearTimeout(timer);
      }
      absorbingTimerByFlowRef.current.clear();
    },
    [],
  );

  if (layout.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-[#1E2530] bg-[#101724] text-micro text-[#8B94A6]">
        No stages found in this project plan.
      </div>
    );
  }

  return (
    <div
      className="relative h-full w-full rounded-lg border border-[#1E2530] bg-[#101724]"
      data-testid="project-dag"
      ref={wrapperRef}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: FIT_PADDING, maxZoom: FIT_MAX_ZOOM }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => {
          onStageSelect?.(node.id);
        }}
        onMove={() => {
          setViewportRevision((value) => value + 1);
        }}
      >
        <FitViewOnNodesReady fitRevision={fitRevision} />
        <Background color="#1E2530" gap={24} />
        <Controls />
      </ReactFlow>
      <PrFlowOverlay
        className="z-10"
        flows={flows}
        onAbsorbed={onAbsorbed}
        style={{ pointerEvents: "none" }}
      />
      <DagLegend />
      <div
        data-flow-count={String(flows.length)}
        data-flow-states={flows.map((flow) => flow.state).join(",")}
        data-testid="dag-pr-flows"
        hidden
      />
    </div>
  );
}
