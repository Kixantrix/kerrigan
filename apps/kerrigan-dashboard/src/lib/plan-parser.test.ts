import { describe, expect, it } from "vitest";
import { parsePlanMarkdown } from "./plan-parser.js";

describe("parsePlanMarkdown", () => {
  it("extracts H2 stages as nodes", () => {
    const result = parsePlanMarkdown("## Build\n\n## Test");

    expect(result.nodes.map((node) => node.id)).toEqual(["build", "test"]);
    expect(result.edges).toEqual([]);
    expect(result.errors).toEqual([]);
  });

  it("extracts H3 stages and parent relationships", () => {
    const result = parsePlanMarkdown("## Build\n### Compile\n### Package");

    expect(result.nodes).toEqual([
      { id: "build", label: "Build", level: 2, parentId: null },
      { id: "compile", label: "Compile", level: 3, parentId: "build" },
      { id: "package", label: "Package", level: 3, parentId: "build" },
    ]);
    expect(result.edges).toEqual([
      { from: "build", to: "compile", kind: "parent" },
      { from: "build", to: "package", kind: "parent" },
    ]);
  });

  it("re-parents H3 stages when a new H2 appears", () => {
    const result = parsePlanMarkdown("## Build\n### Compile\n## Ship\n### Release");

    const release = result.nodes.find((node) => node.id === "release");
    expect(release?.parentId).toBe("ship");
  });

  it("creates deterministic deduped slugs", () => {
    const result = parsePlanMarkdown("## Build API\n## Build API\n## Build API");

    expect(result.nodes.map((node) => node.id)).toEqual([
      "build-api",
      "build-api-2",
      "build-api-3",
    ]);
  });

  it("slugifies punctuation and unicode safely", () => {
    const result = parsePlanMarkdown("## Déploy / 🚀");

    expect(result.nodes[0]?.id).toBe("deploy");
  });

  it("parses frontmatter dependencies as inline lists", () => {
    const result = parsePlanMarkdown(`---
dependencies:
  test: [build]
---
## Build
## Test`);

    expect(result.edges).toContainEqual({
      from: "build",
      to: "test",
      kind: "dependency",
    });
    expect(result.errors).toEqual([]);
  });

  it("parses frontmatter dependencies as block lists", () => {
    const result = parsePlanMarkdown(`---
dependencies:
  ship:
    - build
    - test
---
## Build
## Test
## Ship`);

    expect(result.edges).toEqual(
      expect.arrayContaining([
        { from: "build", to: "ship", kind: "dependency" },
        { from: "test", to: "ship", kind: "dependency" },
      ]),
    );
  });

  it("ignores frontmatter when dependencies key is absent", () => {
    const result = parsePlanMarkdown(`---
name: Example
---
## Build`);

    expect(result.nodes).toHaveLength(1);
    expect(result.edges).toEqual([]);
    expect(result.errors).toEqual([]);
  });

  it("reports an unclosed frontmatter block", () => {
    const result = parsePlanMarkdown("---\ndependencies:\n  test: [build]\n## Build");

    expect(result.errors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: "frontmatter-unclosed" }),
      ]),
    );
  });

  it("reports malformed dependency keys", () => {
    const result = parsePlanMarkdown(`---
dependencies:
  - bad
---
## Build`);

    expect(result.errors.some((error) => error.code === "dependency-key-invalid")).toBe(
      true,
    );
  });

  it("reports invalid dependency shape for scalar values", () => {
    const result = parsePlanMarkdown(`---
dependencies:
  ship: build
---
## Build
## Ship`);

    expect(
      result.errors.some((error) => error.code === "dependency-shape-invalid"),
    ).toBe(true);
  });

  it("reports dependency declarations for unknown stages", () => {
    const result = parsePlanMarkdown(`---
dependencies:
  missing: [build]
---
## Build`);

    expect(
      result.errors.some((error) => error.code === "dependency-unknown-stage"),
    ).toBe(true);
  });

  it("reports unknown dependency targets", () => {
    const result = parsePlanMarkdown(`---
dependencies:
  test: [missing]
---
## Test`);

    expect(
      result.errors.some((error) => error.code === "dependency-unknown-target"),
    ).toBe(true);
  });

  it("detects circular dependencies", () => {
    const result = parsePlanMarkdown(`---
dependencies:
  build: [test]
  test: [build]
---
## Build
## Test`);

    expect(
      result.errors.some((error) => error.code === "circular-dependency"),
    ).toBe(true);
  });

  it("handles orphan H3 stages gracefully", () => {
    const result = parsePlanMarkdown("### Lonely");

    expect(result.nodes[0]).toEqual({
      id: "lonely",
      label: "Lonely",
      level: 3,
      parentId: null,
    });
    expect(result.errors.some((error) => error.code === "orphan-substage")).toBe(true);
  });

  it("returns an empty graph for an empty plan", () => {
    const result = parsePlanMarkdown("");

    expect(result).toEqual({ nodes: [], edges: [], errors: [] });
  });

  it("deduplicates repeated dependency edges", () => {
    const result = parsePlanMarkdown(`---
dependencies:
  test: [build, build]
---
## Build
## Test`);

    const dependencyEdges = result.edges.filter((edge) => edge.kind === "dependency");
    expect(dependencyEdges).toEqual([
      {
        from: "build",
        to: "test",
        kind: "dependency",
      },
    ]);
  });
});
