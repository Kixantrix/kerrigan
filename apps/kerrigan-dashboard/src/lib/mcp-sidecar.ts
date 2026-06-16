import type { AdditionalMcpConfig } from "./acp-client.js";

export type KerriganMcpTool =
  | "kerrigan.dispatch"
  | "kerrigan.plan-update"
  | "kerrigan.block-resolve"
  | "kerrigan.conflict-predict";

export interface McpToolResultEvent {
  tool: KerriganMcpTool;
  result: unknown;
  affectedProjectId?: string;
}

export interface McpSidecarProcess {
  stdout: AsyncIterable<Uint8Array>;
  kill(): Promise<void> | void;
  exited?: Promise<number | null>;
}

export type McpSidecarSpawn = (
  command: string,
  args: readonly string[],
) => McpSidecarProcess;

export interface McpSidecar {
  start(): Promise<void>;
  stop(): Promise<void>;
  getAdditionalMcpConfig(): AdditionalMcpConfig;
  onToolResult(listener: (event: McpToolResultEvent) => void): () => void;
}

export class McpSidecarStartupError extends Error {
  constructor() {
    super("Kerrigan MCP server failed to start.");
    this.name = "McpSidecarStartupError";
  }
}

export interface CreateMcpSidecarOptions {
  command?: string;
  args?: readonly string[];
  additionalMcpConfigPath?: string;
  serverName?: string;
}

const DEFAULT_COMMAND = "node";
const DEFAULT_ARGS = ["tools/kerrigan-mcp/dist/server.js"] as const;
const DEFAULT_SERVER_NAME = "kerrigan";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isKerriganMcpTool(value: unknown): value is KerriganMcpTool {
  return (
    value === "kerrigan.dispatch" ||
    value === "kerrigan.plan-update" ||
    value === "kerrigan.block-resolve" ||
    value === "kerrigan.conflict-predict"
  );
}

function extractToolResultEvent(value: unknown): McpToolResultEvent | null {
  if (!isRecord(value)) return null;

  const tool = value["tool"];
  const result = value["result"];
  const affectedProjectId = value["affectedProjectId"];
  const envelopeType = value["type"];
  const envelopeEvent = value["event"];
  const isEnvelope =
    envelopeType === undefined ||
    envelopeType === "tool-result" ||
    envelopeEvent === "tool-result";

  if (!isEnvelope || !isKerriganMcpTool(tool)) return null;
  if (typeof affectedProjectId === "string") {
    return { tool, result, affectedProjectId };
  }
  return { tool, result };
}

class McpSidecarImpl implements McpSidecar {
  private readonly spawn: McpSidecarSpawn;
  private readonly command: string;
  private readonly args: readonly string[];
  private readonly additionalMcpConfigPath: string | undefined;
  private readonly serverName: string;
  private readonly listeners = new Set<(event: McpToolResultEvent) => void>();

  private process: McpSidecarProcess | null = null;
  private readerStarted = false;
  private buffer = "";

  constructor(spawn: McpSidecarSpawn, options: CreateMcpSidecarOptions) {
    this.spawn = spawn;
    this.command = options.command ?? DEFAULT_COMMAND;
    this.args = options.args ?? DEFAULT_ARGS;
    this.additionalMcpConfigPath = options.additionalMcpConfigPath;
    this.serverName = options.serverName ?? DEFAULT_SERVER_NAME;
  }

  async start(): Promise<void> {
    if (this.process !== null) return;

    try {
      this.process = this.spawn(this.command, this.args);
    } catch {
      throw new McpSidecarStartupError();
    }
    this.startReaderLoop(this.process);
  }

  async stop(): Promise<void> {
    const process = this.process;
    this.process = null;
    this.readerStarted = false;
    this.buffer = "";
    if (process === null) return;
    await Promise.resolve(process.kill());
  }

  getAdditionalMcpConfig(): AdditionalMcpConfig {
    if (this.additionalMcpConfigPath !== undefined) return this.additionalMcpConfigPath;
    return {
      mcpServers: {
        [this.serverName]: {
          command: this.command,
          args: [...this.args],
        },
      },
    };
  }

  onToolResult(listener: (event: McpToolResultEvent) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private startReaderLoop(process: McpSidecarProcess): void {
    if (this.readerStarted) return;
    this.readerStarted = true;
    const decoder = new TextDecoder();
    void (async () => {
      try {
        for await (const chunk of process.stdout) {
          this.buffer += decoder.decode(chunk, { stream: true });
          this.drainBuffer();
        }
        this.buffer += decoder.decode();
        this.drainBuffer();
      } catch {
        // no-op: best effort side-channel parser.
      }
    })();
  }

  private drainBuffer(): void {
    while (true) {
      const index = this.buffer.indexOf("\n");
      if (index < 0) return;
      const line = this.buffer.slice(0, index).trim();
      this.buffer = this.buffer.slice(index + 1);
      if (line.length === 0) continue;
      let parsed: unknown;
      try {
        parsed = JSON.parse(line);
      } catch {
        continue;
      }
      const event = extractToolResultEvent(parsed);
      if (event !== null) {
        for (const listener of this.listeners) listener(event);
      }
    }
  }
}

interface ShellCommandLike {
  spawn(): Promise<ShellChildLike>;
}

interface ShellChildLike {
  readonly stdout: AsyncIterable<Uint8Array>;
  kill(): Promise<void> | void;
}

interface ShellModuleLike {
  Command: {
    create(command: string, args: readonly string[]): ShellCommandLike;
  };
}

function isShellModuleLike(value: unknown): value is ShellModuleLike {
  if (!isRecord(value)) return false;
  const command = value["Command"];
  if (!isRecord(command)) return false;
  return typeof command["create"] === "function";
}

class AsyncQueue<T> implements AsyncIterable<T> {
  private readonly items: T[] = [];
  private readonly waiters: Array<{
    resolve: (result: IteratorResult<T>) => void;
    reject: (error: unknown) => void;
  }> = [];
  private ended = false;
  private failure: unknown = null;

  push(item: T): void {
    if (this.ended || this.failure !== null) return;
    const waiter = this.waiters.shift();
    if (waiter !== undefined) {
      waiter.resolve({ value: item, done: false });
      return;
    }
    this.items.push(item);
  }

  close(): void {
    if (this.ended || this.failure !== null) return;
    this.ended = true;
    while (this.waiters.length > 0) {
      this.waiters.shift()?.resolve({ value: undefined, done: true });
    }
  }

  fail(error: unknown): void {
    if (this.ended || this.failure !== null) return;
    this.failure = error;
    while (this.waiters.length > 0) {
      this.waiters.shift()?.reject(error);
    }
  }

  [Symbol.asyncIterator](): AsyncIterator<T> {
    return {
      next: (): Promise<IteratorResult<T>> => {
        if (this.items.length > 0) {
          const item = this.items.shift();
          if (item === undefined) {
            return Promise.resolve({ value: undefined, done: true });
          }
          return Promise.resolve({ value: item, done: false });
        }
        if (this.failure !== null) return Promise.reject(this.failure);
        if (this.ended) return Promise.resolve({ value: undefined, done: true });
        return new Promise<IteratorResult<T>>((resolve, reject) => {
          this.waiters.push({ resolve, reject });
        });
      },
    };
  }
}

export function createDefaultMcpSidecarSpawn(): McpSidecarSpawn {
  return (command: string, args: readonly string[]): McpSidecarProcess => {
    const pendingProcess: Promise<McpSidecarProcess> = (async () => {
      const moduleName = "@tauri-apps/plugin-shell";
      const shellModuleUnknown: unknown = await import(moduleName);
      if (!isShellModuleLike(shellModuleUnknown)) {
        throw new McpSidecarStartupError();
      }

      const shellCommand = shellModuleUnknown.Command.create(command, args);
      const child = await shellCommand.spawn();

      const stdoutQueue = new AsyncQueue<Uint8Array>();
      void (async () => {
        try {
          for await (const chunk of child.stdout) stdoutQueue.push(chunk);
          stdoutQueue.close();
        } catch (error) {
          stdoutQueue.fail(error);
        }
      })();

      return {
        stdout: stdoutQueue,
        kill: () => child.kill(),
      };
    })();

    return {
      stdout: {
        async *[Symbol.asyncIterator](): AsyncIterator<Uint8Array> {
          let processResolved = false;
          try {
            const process = await pendingProcess;
            processResolved = true;
            for await (const chunk of process.stdout) yield chunk;
          } catch (error) {
            if (!processResolved) throw new McpSidecarStartupError();
            throw error;
          }
        },
      },
      kill: async (): Promise<void> => {
        try {
          const process = await pendingProcess;
          await Promise.resolve(process.kill());
        } catch {
          // no-op
        }
      },
    };
  };
}

export function createMcpSidecar(
  spawn: McpSidecarSpawn = createDefaultMcpSidecarSpawn(),
  options: CreateMcpSidecarOptions = {},
): McpSidecar {
  return new McpSidecarImpl(spawn, options);
}
