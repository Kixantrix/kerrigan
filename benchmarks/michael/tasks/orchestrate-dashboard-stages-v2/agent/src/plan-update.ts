/**
 * kerrigan.plan-update (M5.2) — structured plan edits.
 *
 * Excerpt of `tools/kerrigan-mcp/src/tools/plan-update.ts`: the pure edit core.
 * The MCP registration, zod input schema and the git/gh side effects (branch
 * `plan-edits/<timestamp>-<short-sha>`, commit, push, draft PR) are not part of
 * this package; they call `applyPlanEdit` and publish its result unchanged.
 * Errors that the MCP layer reports as `InvalidParams` are `PlanUpdateError`s.
 */

// ---------------------------------------------------------------------------
// Edit types
// ---------------------------------------------------------------------------

export type PlanUpdateEdit =
  | { op: "replace-stage"; stageId: string; markdown: string }
  | { op: "add-stage"; afterStageId?: string; markdown: string }
  | { op: "edit-deps"; stageId: string; dependencies: ReadonlyArray<string> };

/** An edit the tool must refuse (reported to the MCP client as InvalidParams). */
export class PlanUpdateError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PlanUpdateError";
  }
}

// ---------------------------------------------------------------------------
// Markdown section editing helpers
// ---------------------------------------------------------------------------

/**
 * Slugify a heading label to match the plan-parser conventions:
 * normalize, lowercase, replace non-alphanumeric runs with hyphens, trim.
 */
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

/** Pattern matching H2/H3 headings, optionally with trailing `#`. */
const HEADING_PATTERN = /^(#{2,3})\s+(.+?)\s*#*\s*$/;

interface Section {
  /** Start line index (inclusive). */
  start: number;
  /** End line index (exclusive). */
  end: number;
  /** Heading marker, e.g. `##`. */
  marker: string;
  /** Heading label, trimmed. */
  label: string;
}

/**
 * Parse all H2/H3 sections from a plan body (below any frontmatter).
 * Each section spans from its heading line to (but not including) the next
 * heading of the same or higher level, or the end of the array.
 */
function parseSections(lines: ReadonlyArray<string>): Section[] {
  const headings: Array<{ lineIndex: number; marker: string; label: string }> = [];

  for (const [index, line] of lines.entries()) {
    const match = HEADING_PATTERN.exec(line);
    if (!match) continue;
    const [, marker = "", rawLabel = ""] = match;
    const label = rawLabel.trim();
    if (marker.length < 2 || label.length === 0) continue;
    headings.push({ lineIndex: index, marker, label });
  }

  const sections: Section[] = [];
  for (const [i, heading] of headings.entries()) {
    const nextSameOrHigher = headings.slice(i + 1).find(
      (h) => h.marker.length <= heading.marker.length,
    );
    const end = nextSameOrHigher?.lineIndex ?? lines.length;
    sections.push({
      start: heading.lineIndex,
      end,
      marker: heading.marker,
      label: heading.label,
    });
  }

  return sections;
}

/**
 * Find the section whose heading label slug matches `stageId`.
 * Also accepts a raw label match (case-insensitive) for convenience.
 */
function findSection(
  sections: ReadonlyArray<Section>,
  stageId: string,
): Section | undefined {
  const targetSlug = slugify(stageId);
  return sections.find((s) => {
    const labelSlug = slugify(s.label);
    return labelSlug === targetSlug || s.label.toLowerCase() === stageId.toLowerCase();
  });
}

/**
 * Split markdown into frontmatter lines and body lines.
 * Returns the index of the first body line in the original lines array.
 */
function splitFrontmatter(
  lines: ReadonlyArray<string>,
): { frontmatterLines: ReadonlyArray<string>; bodyStartIndex: number } {
  if ((lines[0] ?? "").trim() !== "---") {
    return { frontmatterLines: [], bodyStartIndex: 0 };
  }
  const closingIndex = lines.findIndex((line, idx) => idx > 0 && line.trim() === "---");
  if (closingIndex < 0) {
    return { frontmatterLines: [], bodyStartIndex: 0 };
  }
  return {
    frontmatterLines: lines.slice(0, closingIndex + 1),
    bodyStartIndex: closingIndex + 1,
  };
}

// ---------------------------------------------------------------------------
// Edit operations
// ---------------------------------------------------------------------------

function applyReplaceStage(
  lines: string[],
  bodyStartIndex: number,
  stageId: string,
  newMarkdown: string,
): string[] {
  const bodyLines = lines.slice(bodyStartIndex);
  const sections = parseSections(bodyLines);
  const section = findSection(sections, stageId);

  if (!section) {
    throw new PlanUpdateError(`Stage '${stageId}' not found in plan`);
  }

  const replacementLines = newMarkdown.split(/\r?\n/);
  const newBodyLines = [
    ...bodyLines.slice(0, section.start),
    ...replacementLines,
    ...bodyLines.slice(section.end),
  ];

  return [...lines.slice(0, bodyStartIndex), ...newBodyLines];
}

function applyAddStage(
  lines: string[],
  bodyStartIndex: number,
  afterStageId: string | undefined,
  newMarkdown: string,
): string[] {
  const bodyLines = lines.slice(bodyStartIndex);
  const sections = parseSections(bodyLines);

  let insertAt: number;
  if (afterStageId !== undefined) {
    const afterSection = findSection(sections, afterStageId);
    if (!afterSection) {
      throw new PlanUpdateError(`Stage '${afterStageId}' not found in plan`);
    }
    insertAt = afterSection.end;
  } else {
    // Insert at the end of all H2 sections (before any H1 sections at end, if any)
    const lastH2 = [...sections].reverse().find((s) => s.marker === "##");
    insertAt = lastH2?.end ?? bodyLines.length;
  }

  const newLines = newMarkdown.split(/\r?\n/);
  // Ensure a blank line separator before and after the new section
  const before =
    insertAt > 0 && bodyLines[insertAt - 1]?.trim() !== "" ? [""] : [];
  const after =
    insertAt < bodyLines.length && bodyLines[insertAt]?.trim() !== "" ? [""] : [];

  const newBodyLines = [
    ...bodyLines.slice(0, insertAt),
    ...before,
    ...newLines,
    ...after,
    ...bodyLines.slice(insertAt),
  ];

  return [...lines.slice(0, bodyStartIndex), ...newBodyLines];
}

function applyEditDeps(
  lines: string[],
  stageId: string,
  dependencies: ReadonlyArray<string>,
): string[] {
  // Dependencies are stored in YAML frontmatter, e.g.:
  //   ---
  //   dependencies:
  //     stageId:
  //       - dep1
  //       - dep2
  //   ---
  // If no frontmatter exists, we create it. If the stage entry exists, we replace it.

  const { frontmatterLines, bodyStartIndex: bodyStart } = splitFrontmatter(lines);

  if (frontmatterLines.length === 0) {
    // No frontmatter: create one with the dependency entry
    const depsBlock = buildDepsBlock(stageId, dependencies);
    const newFrontmatter = ["---", "dependencies:", ...depsBlock, "---", ""];
    return [...newFrontmatter, ...lines.slice(bodyStart)];
  }

  // Strip the outer --- markers from frontmatterLines for editing
  const innerFmLines = frontmatterLines.slice(1, frontmatterLines.length - 1);
  const updatedInner = upsertDependencyEntry(innerFmLines, stageId, dependencies);
  const newFrontmatter = ["---", ...updatedInner, "---"];

  return [...newFrontmatter, ...lines.slice(bodyStart)];
}

function buildDepsBlock(
  stageId: string,
  dependencies: ReadonlyArray<string>,
): string[] {
  if (dependencies.length === 0) {
    return [`  ${stageId}: []`];
  }
  return [`  ${stageId}:`, ...dependencies.map((d) => `    - ${d}`)];
}

function upsertDependencyEntry(
  innerFmLines: ReadonlyArray<string>,
  stageId: string,
  dependencies: ReadonlyArray<string>,
): string[] {
  const depsKeyIndex = innerFmLines.findIndex((l) => l.trim() === "dependencies:");

  if (depsKeyIndex < 0) {
    // No dependencies section: append one
    return [
      ...innerFmLines,
      "dependencies:",
      ...buildDepsBlock(stageId, dependencies),
    ];
  }

  // Find the stage entry inside the dependencies block
  const depsIndent = (innerFmLines[depsKeyIndex] ?? "").match(/^\s*/)?.[0]?.length ?? 0;
  const stageLineIndex = innerFmLines.findIndex((l, idx) => {
    if (idx <= depsKeyIndex) return false;
    const trimmed = l.trim();
    const indent = (l.match(/^\s*/)?.[0]?.length ?? 0);
    // Must be one level deeper than dependencies:
    if (indent <= depsIndent) return false;
    // Match key
    return (
      trimmed === `${stageId}:` ||
      trimmed.startsWith(`${stageId}:`) ||
      trimmed === `${stageId}: []`
    );
  });

  const newEntry = buildDepsBlock(stageId, dependencies);
  const entryIndent = "  ";

  if (stageLineIndex < 0) {
    // Stage not yet in deps: insert before next top-level key or end of deps block
    const insertAfter = findDepsBlockEnd(innerFmLines, depsKeyIndex, depsIndent);
    return [
      ...innerFmLines.slice(0, insertAfter),
      ...newEntry.map((l) => `${entryIndent}${l.trimStart()}`),
      ...innerFmLines.slice(insertAfter),
    ];
  }

  // Find the end of this stage's entry
  const stageIndent =
    (innerFmLines[stageLineIndex] ?? "").match(/^\s*/)?.[0]?.length ?? 0;
  let entryEnd = stageLineIndex + 1;
  while (entryEnd < innerFmLines.length) {
    const l = innerFmLines[entryEnd] ?? "";
    const trimmed = l.trim();
    if (trimmed.length === 0) {
      entryEnd++;
      continue;
    }
    const lineIndent = (l.match(/^\s*/)?.[0]?.length ?? 0);
    if (lineIndent <= stageIndent) break;
    entryEnd++;
  }

  return [
    ...innerFmLines.slice(0, stageLineIndex),
    ...newEntry,
    ...innerFmLines.slice(entryEnd),
  ];
}

function findDepsBlockEnd(
  lines: ReadonlyArray<string>,
  depsKeyIndex: number,
  depsIndent: number,
): number {
  for (let i = depsKeyIndex + 1; i < lines.length; i++) {
    const l = lines[i] ?? "";
    const trimmed = l.trim();
    if (trimmed.length === 0) continue;
    const indent = (l.match(/^\s*/)?.[0]?.length ?? 0);
    if (indent <= depsIndent) return i;
  }
  return lines.length;
}

// ---------------------------------------------------------------------------
// Core plan-update function
// ---------------------------------------------------------------------------

export function applyPlanEdit(originalMarkdown: string, edit: PlanUpdateEdit): string {
  const lines = originalMarkdown.split(/\r?\n/);
  const { bodyStartIndex } = splitFrontmatter(lines);

  let updatedLines: string[];

  if (edit.op === "replace-stage") {
    updatedLines = applyReplaceStage(lines, bodyStartIndex, edit.stageId, edit.markdown);
  } else if (edit.op === "add-stage") {
    updatedLines = applyAddStage(lines, bodyStartIndex, edit.afterStageId, edit.markdown);
  } else {
    // edit-deps
    updatedLines = applyEditDeps(lines, edit.stageId, edit.dependencies);
  }

  // Preserve trailing newline if original had one
  const result = updatedLines.join("\n");
  return originalMarkdown.endsWith("\n") && !result.endsWith("\n")
    ? result + "\n"
    : result;
}
