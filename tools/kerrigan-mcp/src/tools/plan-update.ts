import { randomUUID } from "node:crypto";
import { writeFile, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

// ---------------------------------------------------------------------------
// Input schema
// ---------------------------------------------------------------------------

const replaceStageSchema = z.object({
  op: z.literal("replace-stage"),
  stageId: z.string().min(1),
  markdown: z.string().min(1),
});

const addStageSchema = z.object({
  op: z.literal("add-stage"),
  afterStageId: z.string().min(1).optional(),
  markdown: z.string().min(1),
});

const editDepsSchema = z.object({
  op: z.literal("edit-deps"),
  stageId: z.string().min(1),
  dependencies: z.array(z.string().min(1)),
});

export const planUpdateInputSchema = {
  repo: z.string().min(1).optional(),
  planPath: z.string().min(1),
  edit: z.discriminatedUnion("op", [replaceStageSchema, addStageSchema, editDepsSchema]),
};

// ---------------------------------------------------------------------------
// Internal types
// ---------------------------------------------------------------------------

type PlanUpdateEdit =
  | { op: "replace-stage"; stageId: string; markdown: string }
  | { op: "add-stage"; afterStageId?: string; markdown: string }
  | { op: "edit-deps"; stageId: string; dependencies: ReadonlyArray<string> };

interface PlanUpdateInput {
  repo: string | undefined;
  planPath: string;
  edit: PlanUpdateEdit;
}

export interface PlanUpdateResult extends Record<string, unknown> {
  branch: string;
  prNumber: number;
  prUrl: string;
  diff: string;
}

interface CommandResult {
  code: number | null;
  stdout: string;
  stderr: string;
}

interface PlanUpdateDeps {
  ghExecutable: string;
  gitExecutable: string;
  cwd: string;
}

function getPlanUpdateDeps(): PlanUpdateDeps {
  return {
    ghExecutable: process.env.KERRIGAN_MCP_GH_BIN ?? "gh",
    gitExecutable: process.env.KERRIGAN_MCP_GIT_BIN ?? "git",
    cwd: process.env.KERRIGAN_MCP_CWD ?? process.cwd(),
  };
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
    throw new McpError(
      ErrorCode.InvalidParams,
      `Stage '${stageId}' not found in plan`,
    );
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
      throw new McpError(
        ErrorCode.InvalidParams,
        `Stage '${afterStageId}' not found in plan`,
      );
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

function applyEdit(originalMarkdown: string, edit: PlanUpdateEdit): string {
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

async function runCommand(
  executable: string,
  args: ReadonlyArray<string>,
  cwd: string,
  input?: string,
): Promise<CommandResult> {
  return await new Promise<CommandResult>((resolve, reject) => {
    const child = spawn(executable, args, {
      cwd,
      stdio: [input !== undefined ? "pipe" : "ignore", "pipe", "pipe"],
      env: process.env,
    });

    let stdout = "";
    let stderr = "";

    child.stdout?.on("data", (chunk: Buffer) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr?.on("data", (chunk: Buffer) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", reject);
    child.on("close", (code) => resolve({ code, stdout, stderr }));

    if (input !== undefined && child.stdin) {
      child.stdin.write(input, "utf8");
      child.stdin.end();
    }
  });
}

function parsePrUrl(stdout: string): { prNumber: number; prUrl: string } {
  const PR_URL_REGEX = /\/pull\/(\d+)$/m;
  const trimmed = stdout.trim();
  const lines = trimmed.split(/\r?\n/).filter((l) => l.length > 0);
  const lastLine = lines.at(-1) ?? "";
  const match = PR_URL_REGEX.exec(lastLine);

  if (!match?.[1]) {
    throw new Error(`Unable to parse PR URL from gh output: ${lastLine}`);
  }

  const prNumber = Number.parseInt(match[1], 10);
  if (!Number.isInteger(prNumber) || prNumber <= 0) {
    throw new Error(`Invalid PR number in URL: ${lastLine}`);
  }

  return { prNumber, prUrl: lastLine };
}

export async function updatePlan(
  input: PlanUpdateInput,
  deps: PlanUpdateDeps = getPlanUpdateDeps(),
): Promise<PlanUpdateResult> {
  const { ghExecutable, gitExecutable, cwd } = deps;

  // 1. Read plan file
  const absolutePlanPath = path.isAbsolute(input.planPath)
    ? input.planPath
    : path.join(cwd, input.planPath);

  let originalMarkdown: string;
  try {
    originalMarkdown = await readFile(absolutePlanPath, { encoding: "utf8" });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    throw new McpError(
      ErrorCode.InvalidParams,
      `Cannot read plan file '${input.planPath}': ${message}`,
    );
  }

  // 2. Apply the edit
  let updatedMarkdown: string;
  try {
    updatedMarkdown = applyEdit(originalMarkdown, input.edit);
  } catch (err) {
    if (err instanceof McpError) throw err;
    const message = err instanceof Error ? err.message : String(err);
    throw new McpError(ErrorCode.InternalError, `Failed to apply edit: ${message}`);
  }

  // 3. Compute short SHA for branch name
  const shaResult = await runCommand(gitExecutable, ["rev-parse", "--short", "HEAD"], cwd);
  const shortSha = shaResult.stdout.trim() || randomUUID().slice(0, 8);
  const timestamp = Date.now();
  const branch = `plan-edits/${timestamp}-${shortSha}`;

  // 4. Create and switch to new branch
  const checkoutResult = await runCommand(
    gitExecutable,
    ["checkout", "-b", branch],
    cwd,
  );
  if (checkoutResult.code !== 0) {
    throw new McpError(
      ErrorCode.InternalError,
      "Failed to create git branch",
      {
        exitCode: checkoutResult.code,
        stderr: checkoutResult.stderr.trim(),
      },
    );
  }

  // 5. Write the updated plan file
  const tempPath = path.join(
    tmpdir(),
    `kerrigan-plan-update-${randomUUID()}.md`,
  );
  await writeFile(tempPath, updatedMarkdown, { encoding: "utf8" });

  let prNumber: number;
  let prUrl: string;

  try {
    // Copy temp file to actual plan path
    await writeFile(absolutePlanPath, updatedMarkdown, { encoding: "utf8" });

    // 6. Stage and commit
    const addResult = await runCommand(
      gitExecutable,
      ["add", absolutePlanPath],
      cwd,
    );
    if (addResult.code !== 0) {
      throw new McpError(
        ErrorCode.InternalError,
        "Failed to stage plan file",
        { exitCode: addResult.code, stderr: addResult.stderr.trim() },
      );
    }

    const opDescription =
      input.edit.op === "replace-stage"
        ? `replace stage '${input.edit.stageId}'`
        : input.edit.op === "add-stage"
          ? `add stage${input.edit.afterStageId ? ` after '${input.edit.afterStageId}'` : ""}`
          : `edit deps for stage '${input.edit.stageId}'`;

    const commitMsg = `plan: ${opDescription} in ${path.basename(input.planPath)}`;
    const commitResult = await runCommand(
      gitExecutable,
      ["commit", "-m", commitMsg],
      cwd,
    );
    if (commitResult.code !== 0) {
      throw new McpError(
        ErrorCode.InternalError,
        "Failed to commit plan changes",
        { exitCode: commitResult.code, stderr: commitResult.stderr.trim() },
      );
    }

    // 7. Push the branch
    const pushArgs = ["push", "--set-upstream", "origin", branch];
    const pushResult = await runCommand(gitExecutable, pushArgs, cwd);
    if (pushResult.code !== 0) {
      throw new McpError(
        ErrorCode.InternalError,
        "Failed to push branch",
        { exitCode: pushResult.code, stderr: pushResult.stderr.trim() },
      );
    }

    // 8. Compute diff
    const diffResult = await runCommand(
      gitExecutable,
      ["diff", "HEAD~1", "HEAD", "--", absolutePlanPath],
      cwd,
    );
    const diff = diffResult.stdout;

    // 9. Open draft PR via gh
    const prTitle = `plan: ${opDescription}`;
    const prBodyPath = path.join(
      tmpdir(),
      `kerrigan-pr-body-${randomUUID()}.md`,
    );

    const prBody = `Automated plan edit via \`kerrigan.plan-update\`.\n\n**Operation:** \`${input.edit.op}\`\n\`\`\`diff\n${diff}\`\`\`\n`;
    await writeFile(prBodyPath, prBody, { encoding: "utf8" });

    try {
      const prArgs: string[] = [
        "pr",
        "create",
        "--draft",
        "--title",
        prTitle,
        "--body-file",
        prBodyPath,
        "--head",
        branch,
      ];

      if (input.repo) {
        prArgs.push("--repo", input.repo);
      }

      const prResult = await runCommand(ghExecutable, prArgs, cwd);
      if (prResult.code !== 0) {
        throw new McpError(
          ErrorCode.InternalError,
          "Failed to create draft PR",
          {
            exitCode: prResult.code,
            stderr: prResult.stderr.trim(),
            stdout: prResult.stdout.trim(),
          },
        );
      }

      const parsed = parsePrUrl(prResult.stdout);
      prNumber = parsed.prNumber;
      prUrl = parsed.prUrl;

      return { branch, prNumber, prUrl, diff };
    } finally {
      await rm(prBodyPath, { force: true });
    }
  } catch (err) {
    if (err instanceof McpError) throw err;
    const message = err instanceof Error ? err.message : "Unknown error";
    throw new McpError(ErrorCode.InternalError, "Failed to update plan", { message });
  } finally {
    await rm(tempPath, { force: true });
  }
}

// ---------------------------------------------------------------------------
// MCP tool registration
// ---------------------------------------------------------------------------

export function registerPlanUpdateTool(server: McpServer): void {
  server.tool(
    "kerrigan.plan-update",
    "Apply a structured edit to a project plan.md, commit to a branch, and open a draft PR",
    planUpdateInputSchema,
    async (input, _extra) => {
      const result = await updatePlan({
        repo: input.repo,
        planPath: input.planPath,
        edit: input.edit as PlanUpdateEdit,
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result),
          },
        ],
        structuredContent: result,
      };
    },
  );
}
