import { describe, expect, it } from "vitest";
import type { PlanStageGraph } from "./plan-parser.js";
import { buildDagLayout } from "./dag-layout.js";

describe("buildDagLayout", () => {
  it("returns positioned nodes and typed edges", () => {
    const graph: PlanStageGraph = {
      nodes: [
        { id: "m1", label: "M1", level: 2, parentId: null },
        { id: "m1a", label: "M1.a", level: 3, parentId: "m1" },
        { id: "m2", label: "M2", level: 2, parentId: null },
      ],
      edges: [
        { from: "m1", to: "m1a", kind: "parent" },
        { from: "m1", to: "m2", kind: "dependency" },
      ],
    };

    const layout = buildDagLayout(
      graph,
      new Map([
        ["m1", "blocked"],
        ["m1a", "in-review"],
      ]),
    );

    expect(layout.nodes).toHaveLength(3);
    expect(layout.edges).toHaveLength(2);

    const nodeById = new Map(layout.nodes.map((node) => [node.id, node]));
    expect(nodeById.get("m1")?.data.status).toBe("blocked");
    expect(nodeById.get("m1a")?.data.status).toBe("in-review");
    expect(nodeById.get("m2")?.data.status).toBe("planned");
    expect(nodeById.get("m1")?.width).toBe(240);
    expect(nodeById.get("m1")?.height).toBe(104);

    const parent = nodeById.get("m1");
    const child = nodeById.get("m1a");
    expect(parent?.position.y).toBeLessThan(child?.position.y ?? 0);

    expect(layout.edges).toContainEqual(
      expect.objectContaining({
        id: "parent:m1->m1a",
        source: "m1",
        target: "m1a",
        data: { kind: "parent" },
      }),
    );
    expect(layout.edges).toContainEqual(
      expect.objectContaining({
        id: "dependency:m1->m2",
        source: "m1",
        target: "m2",
        type: "smoothstep",
        animated: true,
        data: { kind: "dependency" },
      }),
    );
  });

  it("is deterministic for the same input", () => {
    const graph: PlanStageGraph = {
      nodes: [
        { id: "a", label: "A", level: 2, parentId: null },
        { id: "b", label: "B", level: 2, parentId: null },
      ],
      edges: [{ from: "a", to: "b", kind: "dependency" }],
    };

    const statuses = new Map<string, "planned">([
      ["a", "planned"],
      ["b", "planned"],
    ]);

    expect(buildDagLayout(graph, statuses)).toEqual(buildDagLayout(graph, statuses));
  });

  it("handles an empty graph", () => {
    const layout = buildDagLayout({ nodes: [], edges: [] }, new Map());
    expect(layout).toEqual({ nodes: [], edges: [] });
  });

  it("lays out <=200 nodes in well under 1s", () => {
    const nodeCount = 200;
    const graph: PlanStageGraph = {
      nodes: Array.from({ length: nodeCount }, (_, index) => ({
        id: `s-${index + 1}`,
        label: `Stage ${index + 1}`,
        level: index % 2 === 0 ? 2 : 3,
        parentId: index % 2 === 0 ? null : `s-${index}`,
      })),
      edges: Array.from({ length: nodeCount - 1 }, (_, index) => ({
        from: `s-${index + 1}`,
        to: `s-${index + 2}`,
        kind: index % 2 === 0 ? "parent" : "dependency",
      })),
    };

    const start = globalThis.performance.now();
    const layout = buildDagLayout(graph, new Map());
    const elapsedMs = globalThis.performance.now() - start;

    expect(layout.nodes).toHaveLength(nodeCount);
    expect(layout.edges).toHaveLength(nodeCount - 1);
    expect(elapsedMs).toBeLessThan(900);
  });
});
