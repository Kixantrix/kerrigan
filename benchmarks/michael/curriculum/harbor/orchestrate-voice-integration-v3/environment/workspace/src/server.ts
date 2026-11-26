// Layer 4 (server boundary): authenticates joins, meters audio, answers turns.
import { decodeClient, encode } from "./protocol.ts";
import type { ClientMessage, ServerMessage, TelemetryEvent } from "./protocol.ts";

const SERVER_PROTOCOL = 1;

export interface ServerOptions {
  tokens: ReadonlySet<string>;
  budgetSeconds: number;
  telemetry: (event: TelemetryEvent) => void;
  respond: (transcript: string) => string;
}

interface Session {
  id: string;
  usedMs: number;
  transcript: string;
  pending: string | null;
  ended: boolean;
}

export class RealtimeServer {
  private readonly options: ServerOptions;
  private readonly sessions = new Map<string, Session>();
  private count = 0;

  constructor(options: ServerOptions) {
    this.options = options;
  }

  /** Handle one raw client frame for `connection`; replies go to `reply`. */
  handle(connection: string, raw: string, reply: (raw: string) => void): void {
    const send = (message: ServerMessage) => reply(encode(message));
    const message = decodeClient(raw);
    if (message === null) {
      send({ type: "rejected", reason: "malformed" });
      return;
    }
    if (message.type === "join") {
      this.join(connection, message, send);
      return;
    }
    const session = this.sessions.get(connection);
    if (!session || session.ended) {
      send({ type: "rejected", reason: "malformed" });
      return;
    }
    if (message.type === "audio") {
      session.usedMs += message.ms;
      session.transcript = message.transcript;
      this.options.telemetry({ ...message, name: "audio", sessionId: session.id });
      if (session.usedMs > this.options.budgetSeconds * 1000) {
        session.ended = true;
        this.options.telemetry({ name: "budget_exhausted", sessionId: session.id, ms: session.usedMs });
        send({ type: "ended", reason: "budget" });
      }
    } else if (message.type === "ptt") {
      if (!message.pressed) {
        session.pending = message.correlationId;
        const text = this.options.respond(session.transcript);
        this.options.telemetry({ name: "response", sessionId: session.id, correlationId: message.correlationId });
        send({ type: "response", correlationId: message.correlationId, text });
      }
    } else if (message.type === "cancel") {
      this.options.telemetry({ name: "cancelled", sessionId: session.id, correlationId: message.correlationId });
      if (session.pending === message.correlationId) session.pending = null;
    }
  }

  private join(connection: string, message: Extract<ClientMessage, { type: "join" }>,
               send: (message: ServerMessage) => void): void {
    if (message.version !== SERVER_PROTOCOL) {
      send({ type: "rejected", reason: "version" });
      return;
    }
    if (typeof message.roomId !== "string" || !message.roomId || !this.options.tokens.has(message.token)) {
      send({ type: "rejected", reason: "auth" });
      return;
    }
    this.count += 1;
    const id = `s${this.count}`;
    this.sessions.set(connection, { id, usedMs: 0, transcript: "", pending: null, ended: false });
    this.options.telemetry({ name: "joined", sessionId: id });
    send({ type: "joined", sessionId: id });
  }
}
