import { describe, expect, it } from "vitest";
import {
  McpSidecarStartupError,
  createMcpSidecar,
  type McpSidecarProcess,
  type McpSidecarSpawn,
} from "./mcp-sidecar.js";

const encoder = new TextEncoder();

class AsyncByteQueue implements AsyncIterable<Uint8Array> {
  private readonly items: Uint8Array[] = [];
  private readonly waiters: Array<{
    resolve: (value: IteratorResult<Uint8Array>) => void;
    reject: (error: unknown) => void;
  }> = [];
  private ended = false;
  private failure: unknown = null;

  push(chunk: Uint8Array): void {
    if (this.ended || this.failure !== null) return;
    const waiter = this.waiters.shift();
    if (waiter !== undefined) {
      waiter.resolve({ value: chunk, done: false });
      return;
    }
    this.items.push(chunk);
  }

  end(): void {
    if (this.ended || this.failure !== null) return;
    this.ended = true;
    while (this.waiters.length > 0) {
      this.waiters.shift()?.resolve({ value: undefined, done: true });
    }
  }

  [Symbol.asyncIterator](): AsyncIterator<Uint8Array> {
    return {
      next: () => {
        if (this.items.length > 0) {
          const value = this.items.shift();
          if (value === undefined) return Promise.resolve({ value, done: true });
          return Promise.resolve({ value, done: false });
        }
        if (this.failure !== null) return Promise.reject(this.failure);
        if (this.ended) return Promise.resolve({ value: undefined, done: true });
        return new Promise((resolve, reject) => {
          this.waiters.push({ resolve, reject });
        });
      },
    };
  }
}

class MockSidecarProcess implements McpSidecarProcess {
  readonly stdoutQueue = new AsyncByteQueue();
  readonly stdout = this.stdoutQueue;
  killed = false;

  kill(): void {
    this.killed = true;
    this.stdoutQueue.end();
  }

  sendLine(value: unknown): void {
    this.stdoutQueue.push(encoder.encode(`${JSON.stringify(value)}\n`));
  }
}

function flushMicrotasks(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe("mcp-sidecar", () => {
  it("starts with injected spawn and generates inline MCP config", async () => {
    const process = new MockSidecarProcess();
    let seen: { command: string; args: readonly string[] } | null = null;
    const spawn: McpSidecarSpawn = (command, args) => {
      seen = { command, args };
      return process;
    };

    const sidecar = createMcpSidecar(spawn, {
      command: "node",
      args: ["tools/kerrigan-mcp/dist/server.js"],
    });
    await sidecar.start();

    expect(seen).toEqual({
      command: "node",
      args: ["tools/kerrigan-mcp/dist/server.js"],
    });
    expect(sidecar.getAdditionalMcpConfig()).toEqual({
      mcpServers: {
        kerrigan: {
          command: "node",
          args: ["tools/kerrigan-mcp/dist/server.js"],
        },
      },
    });
  });

  it("surfaces startup failures with typed error", async () => {
    const spawn: McpSidecarSpawn = () => {
      throw new Error("spawn failed");
    };
    const sidecar = createMcpSidecar(spawn);
    await expect(sidecar.start()).rejects.toBeInstanceOf(McpSidecarStartupError);
  });

  it("returns path config when additional config path is provided", () => {
    const sidecar = createMcpSidecar(() => new MockSidecarProcess(), {
      additionalMcpConfigPath: "/tmp/mcp-config.json",
    });
    expect(sidecar.getAdditionalMcpConfig()).toBe("/tmp/mcp-config.json");
  });

  it("emits typed tool-result events from sidecar output", async () => {
    const process = new MockSidecarProcess();
    const sidecar = createMcpSidecar(() => process);
    const events: unknown[] = [];
    const unsubscribe = sidecar.onToolResult((event) => events.push(event));
    await sidecar.start();

    process.sendLine({
      type: "tool-result",
      tool: "kerrigan.dispatch",
      result: { issueNumber: 399 },
      affectedProjectId: "proj-1",
    });
    process.sendLine({
      type: "tool-result",
      tool: "search",
      result: { ignored: true },
    });
    await flushMicrotasks();
    unsubscribe();

    expect(events).toEqual([
      {
        tool: "kerrigan.dispatch",
        result: { issueNumber: 399 },
        affectedProjectId: "proj-1",
      },
    ]);
  });

  it("stops cleanly and kills subprocess", async () => {
    const process = new MockSidecarProcess();
    const sidecar = createMcpSidecar(() => process);
    await sidecar.start();
    await sidecar.stop();
    expect(process.killed).toBe(true);
  });
});
