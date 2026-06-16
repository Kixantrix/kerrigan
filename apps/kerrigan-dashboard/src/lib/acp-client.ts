const JSON_RPC_VERSION = "2.0";
const HEADER_DELIMITER = new Uint8Array([13, 10, 13, 10]); // \r\n\r\n

export type AcpEvent =
  | { type: "message_chunk"; text: string }
  | { type: "tool_call"; name: string; input: unknown }
  | { type: "tool_result"; name: string; output: unknown }
  | { type: "thought"; text: string }
  | { type: "turn_end"; reason?: string }
  | { type: "error"; error: AcpClientError };

export interface AcpStdin {
  write(chunk: string): Promise<void> | void;
}

export interface AcpProcess {
  stdin: AcpStdin;
  stdout: AsyncIterable<Uint8Array>;
  kill(): Promise<void> | void;
  exited?: Promise<number | null>;
}

export type AcpSpawn = (cmd: string, args: readonly string[]) => AcpProcess;

export type AdditionalMcpConfig = string | Record<string, unknown>;

export interface AcpClient {
  sendUserTurn(text: string): AsyncIterable<AcpEvent>;
  dispose(): Promise<void>;
}

export interface CreateAcpClientOptions {
  additionalMcpConfig?: AdditionalMcpConfig;
}

export class AcpClientError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "AcpClientError";
    this.code = code;
  }
}

export class CopilotCliNotFoundError extends AcpClientError {
  constructor() {
    super(
      "copilot-cli-not-found",
      "Copilot CLI not found — install with: npm i -g @github/copilot",
    );
    this.name = "CopilotCliNotFoundError";
  }
}

export class CopilotCliTooOldError extends AcpClientError {
  constructor() {
    super(
      "copilot-cli-too-old",
      "Copilot CLI v1.0+ required for ACP — update with: npm i -g @github/copilot@latest",
    );
    this.name = "CopilotCliTooOldError";
  }
}

export class AcpProcessCrashedError extends AcpClientError {
  constructor() {
    super(
      "acp-process-crashed",
      "Copilot CLI process exited unexpectedly - restart chat and try again.",
    );
    this.name = "AcpProcessCrashedError";
  }
}

export class AcpProtocolError extends AcpClientError {
  constructor(message: string) {
    super("acp-protocol-error", message);
    this.name = "AcpProtocolError";
  }
}

export class AcpDisposedError extends AcpClientError {
  constructor() {
    super("acp-disposed", "Chat session closed.");
    this.name = "AcpDisposedError";
  }
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
      const waiter = this.waiters.shift();
      if (waiter !== undefined) waiter.resolve({ value: undefined, done: true });
    }
  }

  fail(error: unknown): void {
    if (this.ended || this.failure !== null) return;
    this.failure = error;
    while (this.waiters.length > 0) {
      const waiter = this.waiters.shift();
      if (waiter !== undefined) waiter.reject(error);
    }
  }

  [Symbol.asyncIterator](): AsyncIterator<T> {
    return {
      next: (): Promise<IteratorResult<T>> => {
        if (this.items.length > 0) {
          const item = this.items.shift();
          return Promise.resolve({ value: item, done: false } as IteratorResult<T>);
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

interface JsonRpcRequest {
  jsonrpc: string;
  id: number;
  method: string;
  params?: unknown;
}

interface JsonRpcNotification {
  jsonrpc: string;
  method: string;
  params?: unknown;
}

interface JsonRpcResponse {
  jsonrpc: string;
  id: number;
  result?: unknown;
  error?: {
    code: number;
    message: string;
  };
}

type JsonRpcMessage = JsonRpcRequest | JsonRpcNotification | JsonRpcResponse;

function concatBytes(left: Uint8Array, right: Uint8Array): Uint8Array {
  const merged = new Uint8Array(left.length + right.length);
  merged.set(left, 0);
  merged.set(right, left.length);
  return merged;
}

function indexOfBytes(haystack: Uint8Array, needle: Uint8Array): number {
  if (needle.length === 0 || haystack.length < needle.length) return -1;
  for (let i = 0; i <= haystack.length - needle.length; i += 1) {
    let matches = true;
    for (let j = 0; j < needle.length; j += 1) {
      if (haystack[i + j] !== needle[j]) {
        matches = false;
        break;
      }
    }
    if (matches) return i;
  }
  return -1;
}

class JsonRpcFramer {
  private buffer = new Uint8Array(0);
  private readonly textDecoder = new TextDecoder();

  push(chunk: Uint8Array): JsonRpcMessage[] {
    this.buffer = concatBytes(this.buffer, chunk);
    const messages: JsonRpcMessage[] = [];

    while (true) {
      const headerEnd = indexOfBytes(this.buffer, HEADER_DELIMITER);
      if (headerEnd < 0) break;

      const headerText = this.textDecoder.decode(this.buffer.slice(0, headerEnd));
      const lengthMatch = /(?:^|\r\n)Content-Length:\s*(\d+)(?:\r\n|$)/i.exec(headerText);
      if (lengthMatch === null) {
        throw new AcpProtocolError("Malformed ACP output: missing Content-Length header.");
      }

      const rawLength = lengthMatch[1]!;
      const contentLength = Number.parseInt(rawLength, 10);
      if (!Number.isFinite(contentLength) || contentLength < 0) {
        throw new AcpProtocolError("Malformed ACP output: invalid Content-Length header.");
      }

      const payloadStart = headerEnd + HEADER_DELIMITER.length;
      const payloadEnd = payloadStart + contentLength;
      if (this.buffer.length < payloadEnd) break;

      const payloadText = this.textDecoder.decode(this.buffer.slice(payloadStart, payloadEnd));
      let parsed: unknown;
      try {
        parsed = JSON.parse(payloadText);
      } catch {
        throw new AcpProtocolError("Malformed ACP output: invalid JSON payload.");
      }

      if (!isJsonRpcMessage(parsed)) {
        throw new AcpProtocolError("Malformed ACP output: expected JSON-RPC payload.");
      }

      messages.push(parsed);
      this.buffer = this.buffer.slice(payloadEnd);
    }

    return messages;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isJsonRpcMessage(value: unknown): value is JsonRpcMessage {
  if (!isRecord(value)) return false;
  if (value["jsonrpc"] !== JSON_RPC_VERSION) return false;
  if ("method" in value && typeof value["method"] !== "string") return false;
  if ("id" in value && typeof value["id"] !== "number") return false;
  return true;
}

function normalizeMethod(method: string): string {
  return method.toLowerCase().replace(/[./-]/g, "_");
}

function stringifyJsonRpc(message: JsonRpcMessage): string {
  const payload = JSON.stringify(message);
  const length = new TextEncoder().encode(payload).length;
  return `Content-Length: ${length}\r\n\r\n${payload}`;
}

function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "string") return err;
  return "";
}

function toStartupError(err: unknown): AcpClientError {
  const text = getErrorMessage(err).toLowerCase();
  if (text.includes("enoent") || text.includes("not found")) {
    return new CopilotCliNotFoundError();
  }
  if (
    text.includes("--acp") ||
    text.includes("unknown option") ||
    text.includes("unsupported")
  ) {
    return new CopilotCliTooOldError();
  }
  return new AcpProcessCrashedError();
}

interface PendingRequest {
  resolve: (value: unknown) => void;
  reject: (error: unknown) => void;
}

class AcpClientImpl implements AcpClient {
  private readonly spawn: AcpSpawn;
  private readonly command: string;
  private readonly args: readonly string[];

  private process: AcpProcess | null = null;
  private readerStarted = false;
  private disposed = false;
  private nextId = 1;
  private readonly pendingById = new Map<number, PendingRequest>();
  private activeTurn: AsyncQueue<AcpEvent> | null = null;
  private readonly framer = new JsonRpcFramer();

  constructor(spawn: AcpSpawn, command: string, args: readonly string[]) {
    this.spawn = spawn;
    this.command = command;
    this.args = args;
  }

  sendUserTurn(text: string): AsyncIterable<AcpEvent> {
    if (this.disposed) throw new AcpDisposedError();
    if (this.activeTurn !== null) {
      throw new AcpClientError(
        "acp-turn-active",
        "A chat turn is already in progress. Wait for it to finish before sending another.",
      );
    }

    const queue = new AsyncQueue<AcpEvent>();
    this.activeTurn = queue;

    void this.runTurn(text, queue);
    return queue;
  }

  async dispose(): Promise<void> {
    if (this.disposed) return;
    this.disposed = true;

    const disposeError = new AcpDisposedError();
    this.rejectPending(disposeError);
    this.failActiveTurn(disposeError);

    if (this.process !== null) {
      const current = this.process;
      this.process = null;
      await Promise.resolve(current.kill());
    }
  }

  private async runTurn(text: string, queue: AsyncQueue<AcpEvent>): Promise<void> {
    try {
      await this.ensureStarted();
      await this.sendRequest("user_message", { content: text });
    } catch (error) {
      const typed =
        error instanceof AcpClientError ? error : new AcpProcessCrashedError();
      queue.fail(typed);
      if (this.activeTurn === queue) this.activeTurn = null;
    }
  }

  private async ensureStarted(): Promise<void> {
    if (this.disposed) throw new AcpDisposedError();
    if (this.process !== null) return;

    let process: AcpProcess;
    try {
      process = this.spawn(this.command, this.args);
    } catch (error) {
      throw toStartupError(error);
    }

    this.process = process;
    this.startReaderLoop(process);
    await this.sendRequest("initialize", {
      clientInfo: { name: "kerrigan-dashboard", version: "0.1.0" },
    });
  }

  private startReaderLoop(process: AcpProcess): void {
    if (this.readerStarted) return;
    this.readerStarted = true;

    void (async () => {
      try {
        for await (const chunk of process.stdout) {
          const messages = this.framer.push(chunk);
          for (const message of messages) {
            this.handleIncomingMessage(message);
          }
        }
        this.onProcessFailure(new AcpProcessCrashedError());
      } catch (error) {
        const typed =
          error instanceof AcpClientError
            ? error
            : new AcpProtocolError("Malformed ACP output: stream decoding failed.");
        this.onProcessFailure(typed);
      }
    })();

    if (process.exited !== undefined) {
      void process.exited.then(() => {
        this.onProcessFailure(new AcpProcessCrashedError());
      });
    }
  }

  private async sendRequest(method: string, params: unknown): Promise<unknown> {
    const process = this.process;
    if (process === null) throw new AcpProcessCrashedError();

    const id = this.nextId;
    this.nextId += 1;
    const request: JsonRpcRequest = {
      jsonrpc: JSON_RPC_VERSION,
      id,
      method,
      params,
    };

    const pending = new Promise<unknown>((resolve, reject) => {
      this.pendingById.set(id, { resolve, reject });
    });

    const payload = stringifyJsonRpc(request);
    try {
      await Promise.resolve(process.stdin.write(payload));
    } catch (error) {
      this.pendingById.delete(id);
      throw error;
    }

    return pending;
  }

  private handleIncomingMessage(message: JsonRpcMessage): void {
    if ("id" in message && ("result" in message || "error" in message)) {
      const pending = this.pendingById.get(message.id);
      if (pending === undefined) return;
      this.pendingById.delete(message.id);
      if (message.error !== undefined) {
        pending.reject(
          new AcpClientError(
            "acp-request-failed",
            message.error.message || "ACP request failed.",
          ),
        );
      } else {
        pending.resolve(message.result);
      }
      return;
    }

    if (!("method" in message)) return;
    this.handleNotification(message.method, message.params);
  }

  private handleNotification(method: string, params: unknown): void {
    if (this.activeTurn === null) return;

    const normalized = normalizeMethod(method);
    const fromParams = isRecord(params) ? params : {};

    const eventType =
      typeof fromParams["type"] === "string" ? normalizeMethod(fromParams["type"]) : null;
    const kind = eventType ?? normalized;

    if (kind.endsWith("message_chunk")) {
      const text = extractText(fromParams);
      this.activeTurn.push({ type: "message_chunk", text });
      return;
    }
    if (kind.endsWith("thought")) {
      this.activeTurn.push({ type: "thought", text: extractText(fromParams) });
      return;
    }
    if (kind.endsWith("tool_call")) {
      this.activeTurn.push({
        type: "tool_call",
        name: extractName(fromParams),
        input: fromParams["input"] ?? fromParams["arguments"] ?? null,
      });
      return;
    }
    if (kind.endsWith("tool_result")) {
      this.activeTurn.push({
        type: "tool_result",
        name: extractName(fromParams),
        output: fromParams["output"] ?? fromParams["result"] ?? null,
      });
      return;
    }
    if (kind.endsWith("turn_end")) {
      const reason =
        typeof fromParams["reason"] === "string" ? fromParams["reason"] : null;
      if (reason === null) {
        this.activeTurn.push({ type: "turn_end" });
      } else {
        this.activeTurn.push({ type: "turn_end", reason });
      }
      this.activeTurn.close();
      this.activeTurn = null;
      return;
    }
    if (kind.endsWith("error")) {
      const error = new AcpClientError(
        "acp-turn-error",
        typeof fromParams["message"] === "string"
          ? fromParams["message"]
          : "ACP turn failed.",
      );
      this.activeTurn.push({ type: "error", error });
      this.activeTurn.fail(error);
      this.activeTurn = null;
    }
  }

  private onProcessFailure(error: AcpClientError): void {
    if (this.disposed) return;
    this.process = null;
    this.rejectPending(error);
    this.failActiveTurn(error);
  }

  private rejectPending(error: AcpClientError): void {
    for (const pending of this.pendingById.values()) pending.reject(error);
    this.pendingById.clear();
  }

  private failActiveTurn(error: AcpClientError): void {
    if (this.activeTurn === null) return;
    this.activeTurn.fail(error);
    this.activeTurn = null;
  }
}

function extractText(params: Record<string, unknown>): string {
  const candidates = ["text", "content", "chunk", "delta"];
  for (const key of candidates) {
    const value = params[key];
    if (typeof value === "string") return value;
  }
  return "";
}

function extractName(params: Record<string, unknown>): string {
  const candidates = ["name", "tool", "toolName", "id"];
  for (const key of candidates) {
    const value = params[key];
    if (typeof value === "string") return value;
  }
  return "unknown";
}

export function createAcpClient(
  spawn: AcpSpawn = createDefaultAcpSpawn(),
  options: CreateAcpClientOptions = {},
): AcpClient {
  const args = ["--acp"];
  const additionalMcpConfig = options.additionalMcpConfig;
  if (additionalMcpConfig !== undefined) {
    args.push(
      "--additional-mcp-config",
      typeof additionalMcpConfig === "string"
        ? additionalMcpConfig
        : JSON.stringify(additionalMcpConfig),
    );
  }
  return new AcpClientImpl(spawn, "copilot", args);
}

interface ShellCommandLike {
  spawn(): Promise<ShellChildLike>;
}

interface ShellChildLike {
  readonly stdout: AsyncIterable<Uint8Array>;
  readonly stdin?: {
    write(input: string): Promise<void> | void;
  };
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

export function createDefaultAcpSpawn(): AcpSpawn {
  return (command: string, args: readonly string[]): AcpProcess => {
    const pendingProcess: Promise<AcpProcess> = (async () => {
      const moduleName = "@tauri-apps/plugin-shell";
      const shellModuleUnknown: unknown = await import(moduleName);
      if (!isShellModuleLike(shellModuleUnknown)) {
        throw new Error(
          "Failed to initialize Copilot CLI: @tauri-apps/plugin-shell module is incompatible.",
        );
      }

      const shellCommand = shellModuleUnknown.Command.create(command, args);
      const child = await shellCommand.spawn();
      const stdin = child.stdin;
      if (stdin === undefined) {
        throw new Error("Failed to initialize Copilot CLI: stdin not available.");
      }

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
        stdin: {
          write(chunk: string): Promise<void> | void {
            return stdin.write(chunk);
          },
        },
        stdout: stdoutQueue,
        kill: () => child.kill(),
      };
    })();

    return {
      stdin: {
        async write(chunk: string): Promise<void> {
          const process = await pendingProcess.catch((error: unknown) => {
            throw toStartupError(error);
          });
          await Promise.resolve(process.stdin.write(chunk));
        },
      },
      stdout: {
        async *[Symbol.asyncIterator](): AsyncIterator<Uint8Array> {
          try {
            const process = await pendingProcess;
            for await (const chunk of process.stdout) {
              yield chunk;
            }
          } catch (error) {
            throw toStartupError(error);
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
