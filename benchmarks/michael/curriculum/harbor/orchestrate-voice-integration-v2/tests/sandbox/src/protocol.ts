// Layer 1 (core): canonical realtime protocol v2. Provider-neutral; content never enters telemetry.
export const PROTOCOL_VERSION = 2;

export type ClientMessage =
  | { type: "join"; roomId: string; token: string; version: number }
  | { type: "ptt"; correlationId: string; pressed: boolean }
  | { type: "audio"; correlationId: string; ms: number; transcript: string }
  | { type: "cancel"; correlationId: string };

export type ServerMessage =
  | { type: "joined"; sessionId: string }
  | { type: "rejected"; reason: "auth" | "version" | "malformed" }
  | { type: "response"; correlationId: string; text: string }
  | { type: "ended"; reason: "budget" | "client" };

/** Telemetry is content-free: names, opaque ids and durations only. */
export interface TelemetryEvent {
  name: string;
  sessionId: string;
  correlationId?: string;
  ms?: number;
}

const CLIENT_TYPES = new Set(["join", "ptt", "audio", "cancel"]);
const SERVER_TYPES = new Set(["joined", "rejected", "response", "ended"]);

export function encode(message: ClientMessage | ServerMessage): string {
  return JSON.stringify(message);
}

export function decodeClient(raw: string): ClientMessage | null {
  try {
    const value = JSON.parse(raw);
    return value && typeof value === "object" && CLIENT_TYPES.has(value.type) ? (value as ClientMessage) : null;
  } catch {
    return null;
  }
}

export function decodeServer(raw: string): ServerMessage | null {
  try {
    const value = JSON.parse(raw);
    return value && typeof value === "object" && SERVER_TYPES.has(value.type) ? (value as ServerMessage) : null;
  } catch {
    return null;
  }
}

/** Opaque, per-turn unique correlation id. */
export function correlation(sessionId: string, turn: number): string {
  return `${sessionId}.t${turn}`;
}
