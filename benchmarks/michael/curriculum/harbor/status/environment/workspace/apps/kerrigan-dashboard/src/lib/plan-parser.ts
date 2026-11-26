export interface PlanStageNode {
  id: string;
  label: string;
  level: 2 | 3;
  parentId: string | null;
}

export interface PlanStageEdge {
  from: string;
  to: string;
  kind: "parent" | "dependency";
}

export interface PlanStageGraph {
  nodes: ReadonlyArray<PlanStageNode>;
  edges: ReadonlyArray<PlanStageEdge>;
}

export type PlanParseErrorCode =
  | "frontmatter-unclosed"
  | "frontmatter-malformed"
  | "dependency-key-invalid"
  | "dependency-shape-invalid"
  | "dependency-unknown-stage"
  | "dependency-unknown-target"
  | "orphan-substage"
  | "circular-dependency";

export interface PlanParseError {
  code: PlanParseErrorCode;
  message: string;
  line: number | null;
}

export interface PlanParseResult extends PlanStageGraph {
  errors: ReadonlyArray<PlanParseError>;
}

interface FrontmatterParseResult {
  body: string;
  dependencyMap: ReadonlyMap<string, ReadonlyArray<string>>;
  errors: PlanParseError[];
}

interface StageParseResult {
  nodes: PlanStageNode[];
  edges: PlanStageEdge[];
  errors: PlanParseError[];
}

const HEADING_PATTERN = /^(#{2,3})\s+(.+?)\s*#*\s*$/;
const MILESTONE_SECTION_PATTERN = /^\s*(milestones?|phases?)\b/i;

export function parsePlanMarkdown(markdown: string): PlanParseResult {
  const frontmatter = parseFrontmatter(markdown);
  const stages = parseStages(frontmatter.body);

  const nodeById = new Map(stages.nodes.map((node) => [node.id, node]));
  const dependencyEdges: PlanStageEdge[] = [];
  const errors: PlanParseError[] = [
    ...frontmatter.errors,
    ...stages.errors,
  ];
  const seenDependencyEdges = new Set<string>();

  for (const [stageId, deps] of frontmatter.dependencyMap.entries()) {
    if (!nodeById.has(stageId)) {
      errors.push({
        code: "dependency-unknown-stage",
        message: `Dependency declaration references unknown stage '${stageId}'.`,
        line: null,
      });
      continue;
    }

    for (const depId of deps) {
      if (!nodeById.has(depId)) {
        errors.push({
          code: "dependency-unknown-target",
          message: `Stage '${stageId}' depends on unknown stage '${depId}'.`,
          line: null,
        });
        continue;
      }

      const edgeKey = `${depId}->${stageId}`;
      if (seenDependencyEdges.has(edgeKey)) {
        continue;
      }
      seenDependencyEdges.add(edgeKey);

      dependencyEdges.push({
        from: depId,
        to: stageId,
        kind: "dependency",
      });
    }
  }

  const cycle = detectDependencyCycle(stages.nodes, dependencyEdges);
  if (cycle !== null) {
    errors.push({
      code: "circular-dependency",
      message: `Circular dependency detected: ${cycle.join(" -> ")}.`,
      line: null,
    });
  }

  return {
    nodes: stages.nodes,
    edges: [...stages.edges, ...dependencyEdges],
    errors,
  };
}

function parseStages(body: string): StageParseResult {
  const nodes: PlanStageNode[] = [];
  const edges: PlanStageEdge[] = [];
  const errors: PlanParseError[] = [];

  const slugCounts = new Map<string, number>();
  let currentH2Id: string | null = null;
  const milestoneSectionIds = new Set<string>();
  const orphanHeadingLineById = new Map<string, number>();

  for (const [index, line] of body.split(/\r?\n/).entries()) {
    const match = line.match(HEADING_PATTERN);
    if (!match) {
      continue;
    }

    const [, marker = "", rawLabel = ""] = match;
    if (marker.length === 0 || rawLabel.length === 0) {
      continue;
    }

    const level = marker.length as 2 | 3;
    if (level !== 2 && level !== 3) {
      continue;
    }

    const label = rawLabel.trim();
    if (label.length === 0) {
      continue;
    }

    const id = uniqueSlug(label, slugCounts);

    let parentId: string | null = null;
    if (level === 2) {
      currentH2Id = id;
      if (MILESTONE_SECTION_PATTERN.test(label)) {
        milestoneSectionIds.add(id);
      }
    } else {
      parentId = currentH2Id;
      if (parentId === null) {
        orphanHeadingLineById.set(id, index + 1);
      }
    }

    nodes.push({ id, label, level, parentId });
  }

  if (milestoneSectionIds.size > 0) {
    const milestoneNodes = nodes.filter(
      (node) => node.level === 3 && node.parentId !== null && milestoneSectionIds.has(node.parentId),
    );

    let previousNode: PlanStageNode | undefined;
    for (const node of milestoneNodes) {
      if (previousNode !== undefined) {
        edges.push({ from: previousNode.id, to: node.id, kind: "parent" });
      }
      previousNode = node;
    }

    return { nodes: milestoneNodes, edges, errors };
  }

  for (const node of nodes) {
    if (node.level === 3 && node.parentId === null) {
      errors.push({
        code: "orphan-substage",
        message: `H3 stage '${node.label}' has no parent H2 stage.`,
        line: orphanHeadingLineById.get(node.id) ?? null,
      });
      continue;
    }

    if (node.parentId !== null) {
      edges.push({ from: node.parentId, to: node.id, kind: "parent" });
    }
  }

  return { nodes, edges, errors };
}

function parseFrontmatter(markdown: string): FrontmatterParseResult {
  const errors: PlanParseError[] = [];
  const lines = markdown.split(/\r?\n/);

  if ((lines[0] ?? "").trim() !== "---") {
    return {
      body: markdown,
      dependencyMap: new Map<string, ReadonlyArray<string>>(),
      errors,
    };
  }

  const closingIndex = lines.findIndex((line, idx) => idx > 0 && line.trim() === "---");
  if (closingIndex < 0) {
    errors.push({
      code: "frontmatter-unclosed",
      message: "YAML frontmatter starts with '---' but has no closing '---'.",
      line: 1,
    });
    return {
      body: markdown,
      dependencyMap: new Map<string, ReadonlyArray<string>>(),
      errors,
    };
  }

  const frontmatterLines = lines.slice(1, closingIndex);
  const body = lines.slice(closingIndex + 1).join("\n");
  const dependencyMap = parseDependencyMap(frontmatterLines, errors);

  return { body, dependencyMap, errors };
}

function parseDependencyMap(
  lines: ReadonlyArray<string>,
  errors: PlanParseError[],
): ReadonlyMap<string, ReadonlyArray<string>> {
  const map = new Map<string, ReadonlyArray<string>>();

  const dependenciesIndex = lines.findIndex(
    (line) => line.trim().startsWith("dependencies:"),
  );
  if (dependenciesIndex < 0) {
    return map;
  }

  const dependenciesLine = lines[dependenciesIndex] ?? "";
  const depsIndent = indentationLevel(dependenciesLine);
  const afterColon = dependenciesLine.split(":").slice(1).join(":").trim();
  if (afterColon.length > 0) {
    errors.push({
      code: "dependency-shape-invalid",
      message:
        "Frontmatter 'dependencies' must be a mapping of stage ids, not an inline scalar.",
      line: dependenciesIndex + 2,
    });
    return map;
  }

  let i = dependenciesIndex + 1;
  while (i < lines.length) {
    const line = lines[i] ?? "";
    const trimmed = line.trim();

    if (trimmed.length === 0 || trimmed.startsWith("#")) {
      i += 1;
      continue;
    }

    const indent = indentationLevel(line);
    if (indent <= depsIndent) {
      break;
    }

    const keyMatch = line.match(/^\s*([^:#\s][^:]*)\s*:\s*(.*)$/);
    if (!keyMatch) {
      errors.push({
        code: "dependency-key-invalid",
        message: "Invalid dependency key format in frontmatter.",
        line: i + 2,
      });
      i += 1;
      continue;
    }

    const [, keyRaw = "", valueMaybe] = keyMatch;
    const valueRaw = valueMaybe ?? "";
    if (keyRaw.length === 0) {
      i += 1;
      continue;
    }

    const stageId = stripQuotes(keyRaw.trim());
    const keyIndent = indentationLevel(line);
    const deps: string[] = [];

    if (valueRaw.trim().length > 0) {
      const inline = parseInlineList(valueRaw.trim());
      if (inline === null) {
        errors.push({
          code: "dependency-shape-invalid",
          message: `Dependencies for stage '${stageId}' must be a YAML list.`,
          line: i + 2,
        });
      } else {
        deps.push(...inline);
      }
      map.set(stageId, deps);
      i += 1;
      continue;
    }

    i += 1;
    while (i < lines.length) {
      const depLine = lines[i] ?? "";
      const depTrimmed = depLine.trim();

      if (depTrimmed.length === 0 || depTrimmed.startsWith("#")) {
        i += 1;
        continue;
      }

      const depIndent = indentationLevel(depLine);
      if (depIndent <= keyIndent) {
        break;
      }

      const listMatch = depLine.match(/^\s*-\s*(.+)$/);
      if (!listMatch || listMatch[1] === undefined) {
        errors.push({
          code: "dependency-shape-invalid",
          message: `Dependencies for stage '${stageId}' must use list items ('- value').`,
          line: i + 2,
        });
        i += 1;
        continue;
      }

      const depValue = stripQuotes(listMatch[1].trim());
      if (depValue.length > 0) {
        deps.push(depValue);
      }
      i += 1;
    }

    map.set(stageId, deps);
  }

  return map;
}

function parseInlineList(raw: string): string[] | null {
  if (!raw.startsWith("[") || !raw.endsWith("]")) {
    return null;
  }

  const inner = raw.slice(1, -1).trim();
  if (inner.length === 0) {
    return [];
  }

  return inner
    .split(",")
    .map((part) => stripQuotes(part.trim()))
    .filter((part) => part.length > 0);
}

function indentationLevel(line: string): number {
  const match = line.match(/^\s*/);
  return (match?.[0] ?? "").length;
}

function stripQuotes(value: string): string {
  return value.replace(/^['"]|['"]$/g, "");
}

function uniqueSlug(label: string, counts: Map<string, number>): string {
  const base = slugify(label);
  const count = counts.get(base) ?? 0;
  const nextCount = count + 1;
  counts.set(base, nextCount);
  return nextCount === 1 ? base : `${base}-${nextCount}`;
}

function slugify(label: string): string {
  const normalized = label
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

  const slug = normalized
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return slug.length > 0 ? slug : "stage";
}

function detectDependencyCycle(
  nodes: ReadonlyArray<PlanStageNode>,
  edges: ReadonlyArray<PlanStageEdge>,
): string[] | null {
  const adjacency = new Map<string, string[]>();
  for (const node of nodes) {
    adjacency.set(node.id, []);
  }

  for (const edge of edges) {
    const list = adjacency.get(edge.from);
    if (list !== undefined) {
      list.push(edge.to);
    }
  }

  const visiting = new Set<string>();
  const visited = new Set<string>();

  for (const node of nodes) {
    const cycle = dfsCycle(node.id, adjacency, visiting, visited, []);
    if (cycle !== null) {
      return cycle;
    }
  }

  return null;
}

function dfsCycle(
  nodeId: string,
  adjacency: ReadonlyMap<string, ReadonlyArray<string>>,
  visiting: Set<string>,
  visited: Set<string>,
  stack: string[],
): string[] | null {
  if (visiting.has(nodeId)) {
    const startIndex = stack.indexOf(nodeId);
    if (startIndex < 0) {
      throw new Error(
        `Cycle detection invariant violated: visiting node '${nodeId}' missing from stack. This indicates an internal parser bug.`,
      );
    }
    const cycle = stack.slice(startIndex);
    cycle.push(nodeId);
    return cycle;
  }

  if (visited.has(nodeId)) {
    return null;
  }

  visiting.add(nodeId);
  stack.push(nodeId);

  const neighbors = adjacency.get(nodeId) ?? [];
  for (const neighbor of neighbors) {
    const cycle = dfsCycle(neighbor, adjacency, visiting, visited, stack);
    if (cycle !== null) {
      return cycle;
    }
  }

  stack.pop();
  visiting.delete(nodeId);
  visited.add(nodeId);
  return null;
}
