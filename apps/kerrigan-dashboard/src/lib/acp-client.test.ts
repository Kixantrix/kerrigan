import { describe, expect, it } from "vitest";
import {
  AcpDisposedError,
  AcpProtocolError,
  AcpProcessCrashedError,
  type AcpEvent,
  type AcpProcess,
  type AcpSpawn,
  CopilotCliNotFoundError,
  CopilotCliTooOldError,
  createAcpClient,
} from "./acp-client.js";

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
      const waiter = this.waiters.shift();
      waiter?.resolve({ value: undefined, done: true });
    }
  }

  fail(error: unknown): void {
    if (this.ended || this.failure !== null) return;
    this.failure = error;
    while (this.waiters.length > 0) {
      const waiter = this.waiters.shift();
      waiter?.reject(error);
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

interface JsonRpcMessage {
  jsonrpc: "2.0";
  method?: string;
  params?: unknown;
  id?: number;
  result?: unknown;
}

function encodeMessage(message: JsonRpcMessage): Uint8Array {
  const json = JSON.stringify(message);
  const payload = encoder.encode(json);
  return encoder.encode(`Content-Length: ${payload.length}\r\n\r\n${json}`);
}

class MockAcpProcess implements AcpProcess {
  readonly stdoutQueue = new AsyncByteQueue();
  readonly stdout = this.stdoutQueue;
  readonly writes: JsonRpcMessage[] = [];
  killed = false;
  exitedResolve: ((value: number | null) => void) | null = null;
  readonly exited = new Promise<number | null>((resolve) => {
    this.exitedResolve = resolve;
  });
  private stdinBuffer = "";
  onRequest: ((request: JsonRpcMessage) => void) | null = null;

  stdin = {
    write: (chunk: string): void => {
      this.stdinBuffer += chunk;
      this.drainClientMessages();
    },
  };

  kill(): void {
    this.killed = true;
    this.exitedResolve?.(0);
    this.stdoutQueue.end();
  }

  send(message: JsonRpcMessage): void {
    this.stdoutQueue.push(encodeMessage(message));
  }

  crash(): void {
    this.exitedResolve?.(1);
    this.stdoutQueue.fail(new Error("crash"));
  }

  private drainClientMessages(): void {
    while (true) {
      const delimiterIndex = this.stdinBuffer.indexOf("\r\n\r\n");
      if (delimiterIndex < 0) return;
      const header = this.stdinBuffer.slice(0, delimiterIndex);
      const match = /Content-Length:\s*(\d+)/i.exec(header);
      if (match === null) throw new Error("missing content length");
      const rawLength = match[1]!;
      const length = Number.parseInt(rawLength, 10);
      const bodyStart = delimiterIndex + 4;
      const bodyEnd = bodyStart + length;
      if (this.stdinBuffer.length < bodyEnd) return;
      const body = this.stdinBuffer.slice(bodyStart, bodyEnd);
      const parsed = JSON.parse(body) as JsonRpcMessage;
      this.writes.push(parsed);
      this.onRequest?.(parsed);
      this.stdinBuffer = this.stdinBuffer.slice(bodyEnd);
    }
  }
}

async function collectEvents(stream: AsyncIterable<AcpEvent>): Promise<AcpEvent[]> {
  const output: AcpEvent[] = [];
  for await (const event of stream) {
    output.push(event);
  }
  return output;
}

function buildSpawn(
  server: MockAcpProcess,
  onRequest?: (request: JsonRpcMessage) => void,
): AcpSpawn {
  return () => {
    server.onRequest = onRequest ?? null;
    return server;
  };
}

describe("acp-client", () => {
  it("handles session lifecycle and emits all event variants in order", async () => {
    const server = new MockAcpProcess();
    const spawn = buildSpawn(server, (request) => {
      if (request.method === "initialize" && request.id !== undefined) {
        server.send({ jsonrpc: "2.0", id: request.id, result: { ok: true } });
        return;
      }
      if (request.method === "user_message" && request.id !== undefined) {
        server.send({
          jsonrpc: "2.0",
          method: "message_chunk",
          params: { text: "Hello " },
        });
        server.send({
          jsonrpc: "2.0",
          method: "thought",
          params: { text: "thinking" },
        });
        server.send({
          jsonrpc: "2.0",
          method: "tool_call",
          params: { name: "search", arguments: { q: "x" } },
        });
        server.send({
          jsonrpc: "2.0",
          method: "tool_result",
          params: { name: "search", result: { ok: true } },
        });
        server.send({
          jsonrpc: "2.0",
          method: "message_chunk",
          params: { text: "world" },
        });
        server.send({
          jsonrpc: "2.0",
          method: "turn_end",
          params: { reason: "done" },
        });
        server.send({ jsonrpc: "2.0", id: request.id, result: { accepted: true } });
      }
    });

    const client = createAcpClient(spawn);
    const events = await collectEvents(client.sendUserTurn("Hi"));

    expect(events).toEqual([
      { type: "message_chunk", text: "Hello " },
      { type: "thought", text: "thinking" },
      { type: "tool_call", name: "search", input: { q: "x" } },
      { type: "tool_result", name: "search", output: { ok: true } },
      { type: "message_chunk", text: "world" },
      { type: "turn_end", reason: "done" },
    ]);

    const combinedText = events
      .filter((event): event is Extract<AcpEvent, { type: "message_chunk" }> => {
        return event.type === "message_chunk";
      })
      .map((event) => event.text)
      .join("");
    expect(combinedText).toBe("Hello world");
    await client.dispose();
    expect(server.killed).toBe(true);
  });

  it("surfaces actionable error when copilot CLI is missing", async () => {
    const spawn: AcpSpawn = () => {
      throw new Error("spawn ENOENT");
    };
    const client = createAcpClient(spawn);

    await expect(async () => {
      await collectEvents(client.sendUserTurn("hello"));
    }).rejects.toBeInstanceOf(CopilotCliNotFoundError);
  });

  it("surfaces actionable error when copilot CLI is too old", async () => {
    const spawn: AcpSpawn = () => {
      throw new Error("unknown option --acp");
    };
    const client = createAcpClient(spawn);

    await expect(async () => {
      await collectEvents(client.sendUserTurn("hello"));
    }).rejects.toBeInstanceOf(CopilotCliTooOldError);
  });

  it("rejects an in-flight turn when subprocess crashes", async () => {
    const server = new MockAcpProcess();
    const spawn = buildSpawn(server, (request) => {
      if (request.method === "initialize" && request.id !== undefined) {
        server.send({ jsonrpc: "2.0", id: request.id, result: { ok: true } });
      }
      if (request.method === "user_message") {
        server.send({
          jsonrpc: "2.0",
          method: "message_chunk",
          params: { text: "partial" },
        });
        server.crash();
      }
    });

    const client = createAcpClient(spawn);
    const iterator = client.sendUserTurn("hello")[Symbol.asyncIterator]();
    const first = await iterator.next();
    expect(first.value).toEqual({ type: "message_chunk", text: "partial" });

    await expect(iterator.next()).rejects.toBeInstanceOf(AcpProcessCrashedError);
    await client.dispose();
  });

  it("dispose kills subprocess and ends active turn iterators", async () => {
    const server = new MockAcpProcess();
    const spawn = buildSpawn(server, (request) => {
      if (request.method === "initialize" && request.id !== undefined) {
        server.send({ jsonrpc: "2.0", id: request.id, result: { ok: true } });
      }
      if (request.method === "user_message") {
        server.send({
          jsonrpc: "2.0",
          method: "message_chunk",
          params: { text: "still streaming" },
        });
      }
    });

    const client = createAcpClient(spawn);
    const iterator = client.sendUserTurn("hi")[Symbol.asyncIterator]();
    await iterator.next();

    await client.dispose();
    expect(server.killed).toBe(true);
    await expect(iterator.next()).rejects.toBeInstanceOf(AcpDisposedError);
  });

  it("surfaces malformed framing as typed protocol error", async () => {
    const server = new MockAcpProcess();
    const spawn = buildSpawn(server, (request) => {
      if (request.method === "initialize" && request.id !== undefined) {
        server.send({ jsonrpc: "2.0", id: request.id, result: { ok: true } });
      }
      if (request.method === "user_message") {
        server.stdoutQueue.push(encoder.encode("Content-Length: bad\r\n\r\n{}"));
      }
    });

    const client = createAcpClient(spawn);

    await expect(collectEvents(client.sendUserTurn("hi"))).rejects.toBeInstanceOf(
      AcpProtocolError,
    );
    await client.dispose();
  });
});
