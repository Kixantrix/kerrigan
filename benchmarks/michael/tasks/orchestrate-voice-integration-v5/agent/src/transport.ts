// Layer 3 (media transport): in-process loopback link between a client session and the server.
import { decodeServer, encode, PROTOCOL_VERSION } from "./protocol.ts";
import type { ClientMessage, ServerMessage } from "./protocol.ts";
import type { RealtimeServer } from "./server.ts";

export function joinMessage(roomId: string, token: string): ClientMessage {
  return { type: "join", room: roomId, token, version: PROTOCOL_VERSION } as unknown as ClientMessage;
}

export class LoopbackTransport {
  private readonly server: RealtimeServer;
  private readonly connection: string;
  private listener: (message: ServerMessage) => void = () => {};

  constructor(server: RealtimeServer, connection: string) {
    this.server = server;
    this.connection = connection;
  }

  onMessage(listener: (message: ServerMessage) => void): void {
    this.listener = listener;
  }

  send(message: ClientMessage): void {
    this.server.handle(this.connection, encode(message), (raw) => {
      const decoded = decodeServer(raw);
      if (decoded !== null) this.listener(decoded);
    });
  }
}
