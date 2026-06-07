import "@xyflow/react/dist/style.css";
import {
  Background,
  Controls,
  ReactFlow,
  type NodeTypes,
} from "@xyflow/react";
import { useMemo } from "react";
import {
  buildDagLayout,
  type StageDagEdge,
} from "../../lib/dag-layout.js";
import type { PlanStageGraph } from "../../lib/plan-parser.js";
import type { StageStatus } from "../../lib/status.js";
import { StageNode } from "./StageNode.js";

interface DagProps {
  graph: PlanStageGraph;
  statuses: ReadonlyMap<string, StageStatus>;
}

const nodeTypes = {
  stage: StageNode,
} satisfies NodeTypes;

const edgeColorByKind: Record<"parent" | "dependency", string> = {
  parent: "#2A3342",
  dependency: "#5965F2",
};

export function Dag({ graph, statuses }: DagProps) {
  const layout = useMemo(() => buildDagLayout(graph, statuses), [graph, statuses]);

  const edges = useMemo<StageDagEdge[]>(
    () =>
      layout.edges.map((edge) => ({
        ...edge,
        style: { stroke: edgeColorByKind[edge.data?.kind ?? "parent"], strokeWidth: 1.5 },
      })),
    [layout.edges],
  );

  if (layout.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-[#1E2530] bg-[#101724] text-micro text-[#8B94A6]">
        No stages found in this project plan.
      </div>
    );
  }

  return (
    <div className="h-full w-full rounded-lg border border-[#1E2530] bg-[#101724]" data-testid="project-dag">
      <ReactFlow
        nodes={layout.nodes}
        edges={edges}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        nodeTypes={nodeTypes}
      >
        <Background color="#1E2530" gap={24} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
