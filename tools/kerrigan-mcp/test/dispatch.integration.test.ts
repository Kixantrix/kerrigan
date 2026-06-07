import { mkdtemp, mkdir, readFile, writeFile, chmod, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";

interface JsonRpcResponse {
  readonly jsonrpc: "2.0";
  readonly id: number;
  readonly result?: unknown;
  readonly error?: {
    readonly code: number;
    readonly message: string;
    readonly data?: unknown;
  };
}

class JsonRpcStdioClient {
  private readonly child: ChildProcessWithoutNullStreams;
  private readonly pending = new Map<number, (response: JsonRpcResponse) => void>();
  private buffer = Buffer.alloc(0);
  private nextId = 1;

  constructor(child: ChildProcessWithoutNullStreams) {
    this.child = child;
    this.child.stdout.on("data", (chunk: Buffer) => {
      this.buffer = Buffer.concat([this.buffer, chunk]);
      this.drainBuffer();
    });
  }

  async call(method: string, params: unknown): Promise<JsonRpcResponse> {
    const id = this.nextId;
    this.nextId += 1;

    const payload = JSON.stringify({
      jsonrpc: "2.0",
      id,
      method,
      params,
    });

    this.child.stdin.write(`Content-Length: ${Buffer.byteLength(payload, "utf8")}\r\n\r\n${payload}`);

    return await new Promise<JsonRpcResponse>((resolve) => {
      this.pending.set(id, resolve);
    });
  }

  notify(method: string, params: unknown): void {
    const payload = JSON.stringify({
      jsonrpc: "2.0",
      method,
      params,
    });

    this.child.stdin.write(`Content-Length: ${Buffer.byteLength(payload, "utf8")}\r\n\r\n${payload}`);
  }

  private drainBuffer(): void {
    while (true) {
      const headerEnd = this.buffer.indexOf("\r\n\r\n");
      if (headerEnd === -1) {
        return;
      }

      const headerText = this.buffer.subarray(0, headerEnd).toString("utf8");
      const contentLengthHeader = headerText
        .split("\r\n")
        .find((line) => line.toLowerCase().startsWith("content-length:"));

      if (!contentLengthHeader) {
        throw new Error("Missing Content-Length header");
      }

      const lengthValue = contentLengthHeader.split(":")[1]?.trim();
      const contentLength = Number.parseInt(lengthValue ?? "", 10);
      if (!Number.isFinite(contentLength) || contentLength < 0) {
        throw new Error(`Invalid Content-Length: ${lengthValue}`);
      }

      const messageStart = headerEnd + 4;
      const messageEnd = messageStart + contentLength;
      if (this.buffer.length < messageEnd) {
        return;
      }

      const payload = this.buffer.subarray(messageStart, messageEnd).toString("utf8");
      this.buffer = this.buffer.subarray(messageEnd);

      const message = JSON.parse(payload) as JsonRpcResponse;
      if (typeof message.id === "number") {
        const resolve = this.pending.get(message.id);
        if (resolve) {
          this.pending.delete(message.id);
          resolve(message);
        }
      }
    }
  }
}

const packageRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);

const childProcesses: ChildProcessWithoutNullStreams[] = [];
const tempDirs: string[] = [];

afterEach(async () => {
  for (const child of childProcesses.splice(0)) {
    child.kill();
  }

  for (const dir of tempDirs.splice(0)) {
    await rm(dir, { recursive: true, force: true });
  }
});

describe("kerrigan.dispatch MCP tool", () => {
  it("creates a single gh issue create call with expected labels and @copilot", async () => {
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

    const child = spawn("node", ["--import", "tsx", "src/server.ts"], {
      cwd: packageRoot,
      env: {
        ...process.env,
        PATH: `${fakeBin}${path.delimiter}${process.env.PATH ?? ""}`,
        GH_MOCK_CALLS_FILE: callsPath,
        KERRIGAN_MCP_CWD: fixtureRepo,
      },
      stdio: "pipe",
    });
    childProcesses.push(child);

    const client = new JsonRpcStdioClient(child);

    const initialize = await client.call("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "vitest", version: "1.0.0" },
    });
    expect(initialize.error).toBeUndefined();

    client.notify("notifications/initialized", {});

    const toolCall = await client.call("tools/call", {
      name: "kerrigan.dispatch",
      arguments: {
        title: "Test dispatch title",
        body: "# Briefing\n\nDispatch body",
        labels: ["agent:go", "bug"],
      },
    });

    expect(toolCall.error).toBeUndefined();

    const resultRecord = toolCall.result as {
      content: ReadonlyArray<{ type: string; text?: string }>;
      structuredContent?: { number: number; url: string };
    };

    expect(resultRecord.structuredContent).toEqual({
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
    expect(call.cwd).toBe(fixtureRepo);
    expect(call.body).toBe("# Briefing\n\nDispatch body");
    expect(call.args).toContain("issue");
    expect(call.args).toContain("create");
    expect(call.args).toContain("--title");
    expect(call.args).toContain("Test dispatch title");
    expect(call.args).toContain("--assignee");
    expect(call.args).toContain("@copilot");

    const labels = call.args
      .map((value, index, values) => (value === "--label" ? values[index + 1] : undefined))
      .filter((value): value is string => value !== undefined);

    expect(labels).toEqual(["agent:go", "bug"]);
  });
});
