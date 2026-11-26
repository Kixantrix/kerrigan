# T012 plan: push-to-talk realtime voice (sanitized excerpt)

The slice was split into four layers and dispatched to parallel agents. Their
branches have all landed in `src/`. This plan is authoritative; layer briefs
were derived from it.

## Requirements

- R1 Canonical join handshake: clients join with the protocol's `join`
  message (`roomId`, `token`, `version`), the server answers `joined` with an
  opaque session id.
- R2 Unknown tokens are rejected with reason `auth`.
- R3 Telemetry is content-free: event name, opaque ids and durations only;
  never transcript text or other message content.
- R4 Push-to-talk turn: press starts listening, audio streams with the turn's
  correlation id, release moves to thinking, the matching response moves the
  session to speaking.
- R5 Barge-in: pressing talk while the assistant is speaking cancels the
  in-flight response (a `cancel` for its correlation id) and starts a new turn.
- R6 Clients on another protocol version are rejected with reason `version`.
- R7 Each session may stream at most 120 seconds of audio; beyond that the
  server ends it with reason `budget`.
- R8 Correlation ids are opaque and unique per turn.

## Layers

| Layer | Owns | Requirements |
|---|---|---|
| L1 core | `src/protocol.ts` | R1 (message shapes), R3 (event type), R8 |
| L2 orchestration | `src/session.ts` | R4, R5, R7 (client side) |
| L3 transport | `src/transport.ts` | R1 (client handshake) |
| L4 server | `src/server.ts` | R1 (server side), R2, R3, R6, R7 |
