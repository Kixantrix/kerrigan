import { mkdtemp, mkdir, readFile, writeFile, chmod, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
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

describe("kerrigan.dispatch MCP tool", () => {
  it(
    "creates a single gh issue create call with expected labels and @copilot",
    async () => {
      const tmpDir = await mkdtemp(path.join(os.tmpdir(), "kerrigan-mcp-test-"));
      tempDirs.push(tmpDir);

      const fixtureRepo = path.join(tmpDir, "fixture-repo");
      const fakeBin = path.join(tmpDir, "bin");
      const callsPath = path.join(tmpDir, "gh-calls.json");

      await mkdir(fixtureRepo, { recursive: true });
      await mkdir(fakeBin, { recursive: true });

      const fakeGhPath = path.join(fakeBin, "gh");
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
process.stdout.write("https://github.com/example/fixture-repo/issues/123\\n");
`,
        { encoding: "utf8" },
      );
      await chmod(fakeGhPath, 0o755);

      const transport = new StdioClientTransport({
        command: "node",
        args: ["--import", "tsx", "src/server.ts"],
        cwd: packageRoot,
        stderr: "pipe",
        env: {
          ...stringEnv(process.env),
          PATH: `${fakeBin}${path.delimiter}${process.env.PATH ?? ""}`,
          GH_MOCK_CALLS_FILE: callsPath,
          KERRIGAN_MCP_CWD: fixtureRepo,
        },
      });

      const client = new Client({ name: "vitest", version: "1.0.0" });

      try {
        await client.connect(transport);

        const tools = await client.listTools();
        expect(tools.tools.some((tool) => tool.name === "kerrigan.dispatch")).toBe(true);

        const toolCall = await client.callTool({
          name: "kerrigan.dispatch",
          arguments: {
            title: "Test dispatch title",
            body: "# Briefing\n\nDispatch body",
            labels: ["agent:go", "bug"],
          },
        });

        expect(toolCall.isError).not.toBe(true);
        expect(toolCall.structuredContent).toEqual({
          number: 123,
          url: "https://github.com/example/fixture-repo/issues/123",
        });

        const calls = JSON.parse(await readFile(callsPath, "utf8")) as ReadonlyArray<{
          args: ReadonlyArray<string>;
          cwd: string;
          body: string;
        }>;

        expect(calls).toHaveLength(1);

        const call = calls[0];
        expect(call).toBeDefined();
        if (!call) {
          throw new Error("Expected one gh call entry");
        }

        expect(call.cwd).toBe(fixtureRepo);
        expect(call.body).toBe("# Briefing\n\nDispatch body");
        expect(call.args).toContain("issue");
        expect(call.args).toContain("create");
        expect(call.args).toContain("--title");
        expect(call.args).toContain("Test dispatch title");
        expect(call.args).toContain("--assignee");
        expect(call.args).toContain("@copilot");

        const labels = call.args
          .map((value, index, values) =>
            value === "--label" ? values[index + 1] : undefined,
          )
          .filter((value): value is string => value !== undefined);

        expect(labels).toEqual(["agent:go", "bug"]);
      } finally {
        await transport.close();
      }
    },
    20_000,
  );
});
