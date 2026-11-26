// Layer 2 (orchestration): push-to-talk client session state machine.
import { correlation } from "./protocol.ts";
import type { ServerMessage } from "./protocol.ts";
import { joinMessage } from "./transport.ts";
import type { LoopbackTransport } from "./transport.ts";

export type SessionState = "idle" | "joining" | "ready" | "listening" | "thinking" | "speaking" | "ended";

export class VoiceSession {
  state: SessionState = "idle";
  sessionId: string | null = null;
  lastResponse: string | null = null;
  endReason: string | null = null;
  private turn = 0;
  private current: string | null = null;
  private readonly transport: LoopbackTransport;

  constructor(transport: LoopbackTransport) {
    this.transport = transport;
    transport.onMessage((message) => this.onServer(message));
  }

  start(roomId: string, token: string): void {
    this.state = "joining";
    this.transport.send(joinMessage(roomId, token));
  }

  /** Push-to-talk pressed. While the assistant is speaking this is a barge-in. */
  pressTalk(): void {
    if (this.state !== "ready") return;
    this.turn += 1;
    this.current = correlation(this.sessionId ?? "pending", this.turn);
    this.state = "listening";
    this.transport.send({ type: "ptt", correlationId: this.current, pressed: true });
  }

  /** Microphone chunk; `seconds` is the chunk duration reported by the capture layer. */
  audio(seconds: number, transcript: string): void {
    if (this.state !== "listening" || this.current === null) return;
    this.transport.send({ type: "audio", correlationId: this.current, ms: seconds, transcript });
  }

  releaseTalk(): void {
    if (this.state !== "listening" || this.current === null) return;
    this.state = "thinking";
    this.transport.send({ type: "ptt", correlationId: this.current, pressed: false });
  }

  finishSpeaking(): void {
    if (this.state === "speaking") this.state = "ready";
  }

  private onServer(message: ServerMessage): void {
    if (message.type === "joined") {
      this.sessionId = message.sessionId;
      this.state = "ready";
    } else if (message.type === "rejected") {
      this.state = "ended";
      this.endReason = message.reason;
    } else if (message.type === "ended") {
      this.state = "ended";
      this.endReason = message.reason;
    } else if (message.type === "response" && message.correlationId === this.current && this.state === "thinking") {
      this.lastResponse = message.text;
      this.state = "speaking";
    }
  }
}
