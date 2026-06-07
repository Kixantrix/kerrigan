import dagre from "@dagrejs/dagre";
import type { Edge, Node } from "@xyflow/react";
import type { PlanStageEdge, PlanStageGraph, PlanStageNode } from "./plan-parser.js";
import type { StageStatus } from "./status.js";

export interface StageDagNodeData {
  [key: string]: unknown;
  label: string;
  level: PlanStageNode["level"];
  status: StageStatus;
}

export type StageDagNode = Node<StageDagNodeData, "stage">;
export type StageDagEdge = Edge<{ kind: PlanStageEdge["kind"] }>;

export interface DagLayoutResult {
  nodes: StageDagNode[];
  edges: StageDagEdge[];
}

const NODE_WIDTH = 240;
const NODE_HEIGHT = 84;

export function buildDagLayout(
  graph: PlanStageGraph,
  statuses: ReadonlyMap<string, StageStatus>,
): DagLayoutResult {
  if (graph.nodes.length === 0) {
    return { nodes: [], edges: [] };
  }

  const dag = new dagre.graphlib.Graph();
  dag.setDefaultEdgeLabel(() => ({}));
  dag.setGraph({
    rankdir: "TB",
    nodesep: 36,
    ranksep: 80,
    marginx: 24,
    marginy: 24,
  });

  for (const node of graph.nodes) {
    dag.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }

  for (const edge of graph.edges) {
    dag.setEdge(edge.from, edge.to);
  }

  dagre.layout(dag);

  return {
    nodes: graph.nodes.map((node) => {
      const position = dag.node(node.id);
      const x = typeof position?.x === "number" ? position.x - NODE_WIDTH / 2 : 0;
      const y = typeof position?.y === "number" ? position.y - NODE_HEIGHT / 2 : 0;

      return {
        id: node.id,
        type: "stage",
        position: { x, y },
        data: {
          label: node.label,
          level: node.level,
          status: statuses.get(node.id) ?? "planned",
        },
      } satisfies StageDagNode;
    }),
    edges: graph.edges.map((edge) => ({
      id: `${edge.kind}:${edge.from}->${edge.to}`,
      source: edge.from,
      target: edge.to,
      type: edge.kind === "dependency" ? "smoothstep" : "default",
      animated: edge.kind === "dependency",
      data: { kind: edge.kind },
    } satisfies StageDagEdge)),
  };
}
