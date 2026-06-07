import { randomUUID } from "node:crypto";
import { writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

const ISSUE_URL_REGEX = /\/issues\/(\d+)$/;

export const dispatchInputSchema = {
  title: z.string().min(1),
  body: z.string().min(1),
  labels: z.array(z.string().min(1)).optional(),
  repo: z.string().min(1).optional(),
};

interface DispatchInput {
  title: string;
  body: string;
  labels?: ReadonlyArray<string>;
  repo?: string;
}

interface DispatchResult {
  number: number;
  url: string;
}

interface CommandResult {
  code: number | null;
  stdout: string;
  stderr: string;
}

interface DispatchDeps {
  ghExecutable: string;
  cwd: string;
}

function getDispatchDeps(): DispatchDeps {
  return {
    ghExecutable: process.env.KERRIGAN_MCP_GH_BIN ?? "gh",
    cwd: process.env.KERRIGAN_MCP_CWD ?? process.cwd(),
  };
}

async function runGhIssueCreate(
  deps: DispatchDeps,
  args: ReadonlyArray<string>,
): Promise<CommandResult> {
  return await new Promise<CommandResult>((resolve, reject) => {
    const child = spawn(deps.ghExecutable, args, {
      cwd: deps.cwd,
      stdio: ["ignore", "pipe", "pipe"],
      env: process.env,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString("utf8");
    });

    child.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString("utf8");
    });

    child.on("error", (error) => {
      reject(error);
    });

    child.on("close", (code) => {
      resolve({ code, stdout, stderr });
    });
  });
}

function parseIssue(stdout: string): DispatchResult {
  const trimmed = stdout.trim();
  const lines = trimmed.split(/\r?\n/).filter((line) => line.length > 0);
  const lastLine = lines.at(-1);

  if (!lastLine) {
    throw new Error("gh issue create did not return an issue URL");
  }

  const match = ISSUE_URL_REGEX.exec(lastLine);
  if (!match) {
    throw new Error(`Unable to parse issue URL from output: ${lastLine}`);
  }

  const issueNumber = Number.parseInt(match[1], 10);
  if (!Number.isInteger(issueNumber) || issueNumber <= 0) {
    throw new Error(`Invalid issue number in URL: ${lastLine}`);
  }

  return {
    number: issueNumber,
    url: lastLine,
  };
}

export async function dispatchIssue(
  input: DispatchInput,
  deps: DispatchDeps = getDispatchDeps(),
): Promise<DispatchResult> {
  const bodyFile = path.join(tmpdir(), `kerrigan-dispatch-${randomUUID()}.md`);
  await writeFile(bodyFile, input.body, { encoding: "utf8" });

  try {
    const args: string[] = [
      "issue",
      "create",
      "--title",
      input.title,
      "--body-file",
      bodyFile,
      "--assignee",
      "@copilot",
    ];

    if (input.repo) {
      args.push("--repo", input.repo);
    }

    for (const label of input.labels ?? []) {
      args.push("--label", label);
    }

    const result = await runGhIssueCreate(deps, args);

    if (result.code !== 0) {
      throw new McpError(
        ErrorCode.InternalError,
        "Failed to create GitHub issue",
        {
          exitCode: result.code,
          stderr: result.stderr.trim(),
          stdout: result.stdout.trim(),
        },
      );
    }

    return parseIssue(result.stdout);
  } catch (error) {
    if (error instanceof McpError) {
      throw error;
    }

    const message = error instanceof Error ? error.message : "Unknown dispatch error";
    throw new McpError(ErrorCode.InternalError, "Failed to dispatch issue", {
      message,
    });
  } finally {
    await rm(bodyFile, { force: true });
  }
}

export function registerDispatchTool(server: McpServer): void {
  server.tool(
    "kerrigan.dispatch",
    "Create a GitHub issue from a briefing and assign @copilot",
    dispatchInputSchema,
    async (input) => {
      const issue = await dispatchIssue(input);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(issue),
          },
        ],
        structuredContent: issue,
      };
    },
  );
}
