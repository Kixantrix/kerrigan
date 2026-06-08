import {
  mkdtemp,
  mkdir,
  readFile,
  writeFile,
  chmod,
  rm,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const packageRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);

const tempDirs: string[] = [];

afterEach(async () => {
  for (const dir of tempDirs.splice(0)) {
    await rm(dir, { recursive: true, force: true });
  }
});

function stringEnv(source: NodeJS.ProcessEnv): Record<string, string> {
  const result: Record<string, string> = {};
  for (const [key, value] of Object.entries(source)) {
    if (value !== undefined) {
      result[key] = value;
    }
  }
  return result;
}

/** Create a minimal git repo with a plan.md and return its path. */
async function createFixtureRepo(tmpDir: string, planContent: string): Promise<string> {
  const repoDir = path.join(tmpDir, "fixture-repo");
  await mkdir(repoDir, { recursive: true });

  // Init bare git repo
  execSync("git init -b main", { cwd: repoDir });
  execSync('git config user.email "test@example.com"', { cwd: repoDir });
  execSync('git config user.name "Test"', { cwd: repoDir });

  await writeFile(path.join(repoDir, "plan.md"), planContent, { encoding: "utf8" });
  execSync("git add plan.md", { cwd: repoDir });
  execSync('git commit -m "initial plan"', { cwd: repoDir });

  return repoDir;
}

/**
 * Create a fake `gh` script that:
 * - Records calls to GH_MOCK_CALLS_FILE
 * - For `pr create` returns a fake PR URL
 * - For other commands passes through to a real git or returns 0
 */
async function createFakeGh(binDir: string, _callsPath: string): Promise<string> {
  const fakeGhPath = path.join(binDir, "gh");
  await writeFile(
    fakeGhPath,
    `#!/usr/bin/env node
import { existsSync, readFileSync, writeFileSync } from "node:fs";
const args = process.argv.slice(2);
const bodyFileIndex = args.indexOf("--body-file");
const body = bodyFileIndex >= 0 ? readFileSync(args[bodyFileIndex + 1], "utf8") : "";
const callsPath = process.env.GH_MOCK_CALLS_FILE;
if (!callsPath) {
  process.stderr.write("GH_MOCK_CALLS_FILE missing\\n");
  process.exit(2);
}
const calls = existsSync(callsPath) ? JSON.parse(readFileSync(callsPath, "utf8")) : [];
calls.push({ args, cwd: process.cwd(), body });
writeFileSync(callsPath, JSON.stringify(calls), "utf8");
// Simulate pr create returning a URL
if (args[0] === "pr" && args[1] === "create") {
  process.stdout.write("https://github.com/example/fixture-repo/pull/42\\n");
}
`,
    { encoding: "utf8" },
  );
  await chmod(fakeGhPath, 0o755);
  return fakeGhPath;
}

/**
 * Create a fake `git` script that handles push (no-op) and delegates
 * everything else to the real git.
 */
async function createFakeGit(binDir: string): Promise<string> {
  const realGit = execSync("which git", { encoding: "utf8" }).trim();
  const fakeGitPath = path.join(binDir, "git");
  await writeFile(
    fakeGitPath,
    `#!/usr/bin/env node
import { spawnSync } from "node:child_process";
const args = process.argv.slice(2);
// Intercept push to avoid real remote
if (args[0] === "push") {
  process.exit(0);
}
const result = spawnSync(${JSON.stringify(realGit)}, args, {
  stdio: "inherit",
  env: process.env,
});
process.exit(result.status ?? 0);
`,
    { encoding: "utf8" },
  );
  await chmod(fakeGitPath, 0o755);
  return fakeGitPath;
}

const FIXTURE_PLAN = `# Plan: Test Project

Each milestone must end with green CI.

## Milestone 1

First milestone.

## Milestone 2

Second milestone.

## Milestone 3

Third milestone.
`;

describe("kerrigan.plan-update MCP tool", () => {
  it(
    "replace-stage: replaces the markdown for a given stage",
    async () => {
      const tmpDir = await mkdtemp(path.join(os.tmpdir(), "kerrigan-plan-update-test-"));
      tempDirs.push(tmpDir);

      const callsPath = path.join(tmpDir, "gh-calls.json");
      const binDir = path.join(tmpDir, "bin");
      await mkdir(binDir, { recursive: true });

      const fixtureRepo = await createFixtureRepo(tmpDir, FIXTURE_PLAN);
      await createFakeGh(binDir, callsPath);
      await createFakeGit(binDir);

      const transport = new StdioClientTransport({
        command: "node",
        args: ["--import", "tsx", "src/server.ts"],
        cwd: packageRoot,
        stderr: "pipe",
        env: {
          ...stringEnv(process.env),
          PATH: `${binDir}${path.delimiter}${process.env.PATH ?? ""}`,
          GH_MOCK_CALLS_FILE: callsPath,
          KERRIGAN_MCP_CWD: fixtureRepo,
          KERRIGAN_MCP_GIT_BIN: path.join(binDir, "git"),
        },
      });

      const client = new Client({ name: "vitest", version: "1.0.0" });

      try {
        await client.connect(transport);

        const tools = await client.listTools();
        expect(tools.tools.some((t) => t.name === "kerrigan.plan-update")).toBe(true);

        const result = await client.callTool({
          name: "kerrigan.plan-update",
          arguments: {
            planPath: "plan.md",
            edit: {
              op: "replace-stage",
              stageId: "milestone-1",
              markdown: "## Milestone 1\n\nReplaced content.",
            },
          },
        });

        expect(result.isError).not.toBe(true);

        const structured = result.structuredContent as {
          branch: string;
          prNumber: number;
          prUrl: string;
          diff: string;
        };
        expect(structured.branch).toMatch(/^plan-edits\//);
        expect(structured.prNumber).toBe(42);
        expect(structured.prUrl).toBe(
          "https://github.com/example/fixture-repo/pull/42",
        );

        // The updated plan file should contain the replacement
        const updatedContent = await readFile(
          path.join(fixtureRepo, "plan.md"),
          "utf8",
        );
        expect(updatedContent).toContain("Replaced content.");
        expect(updatedContent).not.toContain("First milestone.");

        // gh was called once to create a PR
        const calls = JSON.parse(await readFile(callsPath, "utf8")) as ReadonlyArray<{
          args: ReadonlyArray<string>;
        }>;
        expect(calls).toHaveLength(1);
        const call = calls[0];
        expect(call?.args).toContain("pr");
        expect(call?.args).toContain("create");
        expect(call?.args).toContain("--draft");
      } finally {
        await transport.close();
      }
    },
    30_000,
  );

  it(
    "add-stage: inserts a new stage after a given stage",
    async () => {
      const tmpDir = await mkdtemp(path.join(os.tmpdir(), "kerrigan-plan-update-test-"));
      tempDirs.push(tmpDir);

      const callsPath = path.join(tmpDir, "gh-calls.json");
      const binDir = path.join(tmpDir, "bin");
      await mkdir(binDir, { recursive: true });

      const fixtureRepo = await createFixtureRepo(tmpDir, FIXTURE_PLAN);
      await createFakeGh(binDir, callsPath);
      await createFakeGit(binDir);

      const transport = new StdioClientTransport({
        command: "node",
        args: ["--import", "tsx", "src/server.ts"],
        cwd: packageRoot,
        stderr: "pipe",
        env: {
          ...stringEnv(process.env),
          PATH: `${binDir}${path.delimiter}${process.env.PATH ?? ""}`,
          GH_MOCK_CALLS_FILE: callsPath,
          KERRIGAN_MCP_CWD: fixtureRepo,
          KERRIGAN_MCP_GIT_BIN: path.join(binDir, "git"),
        },
      });

      const client = new Client({ name: "vitest", version: "1.0.0" });

      try {
        await client.connect(transport);

        const result = await client.callTool({
          name: "kerrigan.plan-update",
          arguments: {
            planPath: "plan.md",
            edit: {
              op: "add-stage",
              afterStageId: "milestone-1",
              markdown: "## Milestone 1.5\n\nNew intermediate milestone.",
            },
          },
        });

        expect(result.isError).not.toBe(true);

        const updatedContent = await readFile(
          path.join(fixtureRepo, "plan.md"),
          "utf8",
        );
        expect(updatedContent).toContain("## Milestone 1.5");
        expect(updatedContent).toContain("New intermediate milestone.");

        // Milestone 1.5 should appear between Milestone 1 and Milestone 2
        const m1Index = updatedContent.indexOf("## Milestone 1\n");
        const m15Index = updatedContent.indexOf("## Milestone 1.5");
        const m2Index = updatedContent.indexOf("## Milestone 2");
        expect(m1Index).toBeLessThan(m15Index);
        expect(m15Index).toBeLessThan(m2Index);
      } finally {
        await transport.close();
      }
    },
    30_000,
  );

  it(
    "edit-deps: writes dependencies frontmatter for a stage",
    async () => {
      const tmpDir = await mkdtemp(path.join(os.tmpdir(), "kerrigan-plan-update-test-"));
      tempDirs.push(tmpDir);

      const callsPath = path.join(tmpDir, "gh-calls.json");
      const binDir = path.join(tmpDir, "bin");
      await mkdir(binDir, { recursive: true });

      const fixtureRepo = await createFixtureRepo(tmpDir, FIXTURE_PLAN);
      await createFakeGh(binDir, callsPath);
      await createFakeGit(binDir);

      const transport = new StdioClientTransport({
        command: "node",
        args: ["--import", "tsx", "src/server.ts"],
        cwd: packageRoot,
        stderr: "pipe",
        env: {
          ...stringEnv(process.env),
          PATH: `${binDir}${path.delimiter}${process.env.PATH ?? ""}`,
          GH_MOCK_CALLS_FILE: callsPath,
          KERRIGAN_MCP_CWD: fixtureRepo,
          KERRIGAN_MCP_GIT_BIN: path.join(binDir, "git"),
        },
      });

      const client = new Client({ name: "vitest", version: "1.0.0" });

      try {
        await client.connect(transport);

        const result = await client.callTool({
          name: "kerrigan.plan-update",
          arguments: {
            planPath: "plan.md",
            edit: {
              op: "edit-deps",
              stageId: "milestone-2",
              dependencies: ["milestone-1"],
            },
          },
        });

        expect(result.isError).not.toBe(true);

        const updatedContent = await readFile(
          path.join(fixtureRepo, "plan.md"),
          "utf8",
        );
        expect(updatedContent).toContain("dependencies:");
        expect(updatedContent).toContain("milestone-2:");
        expect(updatedContent).toContain("- milestone-1");
      } finally {
        await transport.close();
      }
    },
    30_000,
  );

  it(
    "returns a structured MCP error when stageId is not found",
    async () => {
      const tmpDir = await mkdtemp(path.join(os.tmpdir(), "kerrigan-plan-update-test-"));
      tempDirs.push(tmpDir);

      const callsPath = path.join(tmpDir, "gh-calls.json");
      const binDir = path.join(tmpDir, "bin");
      await mkdir(binDir, { recursive: true });

      const fixtureRepo = await createFixtureRepo(tmpDir, FIXTURE_PLAN);
      await createFakeGh(binDir, callsPath);
      await createFakeGit(binDir);

      const transport = new StdioClientTransport({
        command: "node",
        args: ["--import", "tsx", "src/server.ts"],
        cwd: packageRoot,
        stderr: "pipe",
        env: {
          ...stringEnv(process.env),
          PATH: `${binDir}${path.delimiter}${process.env.PATH ?? ""}`,
          GH_MOCK_CALLS_FILE: callsPath,
          KERRIGAN_MCP_CWD: fixtureRepo,
          KERRIGAN_MCP_GIT_BIN: path.join(binDir, "git"),
        },
      });

      const client = new Client({ name: "vitest", version: "1.0.0" });

      try {
        await client.connect(transport);

        const result = await client.callTool({
          name: "kerrigan.plan-update",
          arguments: {
            planPath: "plan.md",
            edit: {
              op: "replace-stage",
              stageId: "nonexistent-stage",
              markdown: "## Nonexistent\n\nShould not appear.",
            },
          },
        });

        expect(result.isError).toBe(true);
      } finally {
        await transport.close();
      }
    },
    30_000,
  );
});
