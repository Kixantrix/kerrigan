// Trusted, answer-free integration scenarios: build the stack in-process and record observations.
import { readFileSync } from "node:fs";
const SRC = "/work/app/src";
const VOCABULARY = ["handshake-mismatch", "version-skew", "requirement-dropped", "content-in-telemetry",
  "unit-mismatch", "race-condition", "auth-bypass", "memory-leak"];
async function stack(budgetSeconds = 120) {
  const { RealtimeServer } = await import(`${SRC}/server.ts`);
  const { LoopbackTransport } = await import(`${SRC}/transport.ts`);
  const { VoiceSession } = await import(`${SRC}/session.ts`);
  const telemetry = [];
  const server = new RealtimeServer({ tokens: new Set(["tok-ok"]), budgetSeconds,
    telemetry: (event) => telemetry.push(event), respond: (text) => `reply:${text.length}` });
  const transport = new LoopbackTransport(server, "conn-1");
  const session = new VoiceSession(transport);
  return { session, transport, telemetry };
}
const snap = (s) => ({ state: s.state, sessionId: s.sessionId, lastResponse: s.lastResponse, endReason: s.endReason });

export async function e2eTurn() {
  const { session } = await stack();
  session.start("room-a", "tok-ok");
  const joined = snap(session);
  session.pressTalk(); const listening = session.state;
  session.audio(2, "turn on the lights"); session.releaseTalk();
  const answered = snap(session);
  session.finishSpeaking();
  return { joined, listening, answered, after: session.state };
}
export async function rejectsBadToken() {
  const { session } = await stack(); session.start("room-a", "tok-bad"); return snap(session);
}
export async function rejectsOldVersion() {
  const { transport } = await stack();
  const seen = []; transport.onMessage((m) => seen.push(m));
  transport.send({ type: "join", roomId: "room-a", token: "tok-ok", version: 1 });
  return seen;
}
export async function bargeIn() {
  const { session, telemetry } = await stack();
  session.start("room-a", "tok-ok");
  session.pressTalk(); session.audio(1, "tell me a long story"); session.releaseTalk();
  const speaking = session.state;
  const responded = telemetry.filter((e) => e.name === "response").map((e) => e.correlationId);
  session.pressTalk();
  const cancelled = telemetry.filter((e) => e.name === "cancelled").map((e) => e.correlationId);
  session.audio(1, "stop"); session.releaseTalk();
  const responses = telemetry.filter((e) => e.name === "response").map((e) => e.correlationId);
  return { speaking, after: session.state, cancelledFirst: cancelled.length === 1 && cancelled[0] === responded[0],
    newTurnAnswered: responses.length === 2 && responses[1] !== responses[0], state: session.state };
}
export async function telemetryContentFree() {
  const { session, telemetry } = await stack();
  session.start("room-a", "tok-ok");
  session.pressTalk(); session.audio(1.25, "PRIVATE-PHRASE-42 my address"); session.releaseTalk();
  const text = JSON.stringify(telemetry);
  const keys = [...new Set(telemetry.flatMap((e) => Object.keys(e)))].sort();
  const audio = telemetry.find((e) => e.name === "audio");
  return { events: telemetry.length, leaked: text.includes("PRIVATE-PHRASE") || text.includes("address"),
    keys, audioMs: audio ? audio.ms : null };
}
export async function budget() {
  const { session } = await stack(120);
  session.start("room-a", "tok-ok"); session.pressTalk();
  for (let i = 0; i < 12; i += 1) session.audio(10, "chunk");
  const at120 = session.state;
  session.audio(0.5, "chunk");
  return { at120, after: session.state, endReason: session.endReason };
}
export async function correlationUnique() {
  const { session, telemetry } = await stack();
  session.start("room-a", "tok-ok");
  for (const words of ["first secret", "second secret"]) {
    session.pressTalk(); session.audio(1, words); session.releaseTalk(); session.finishSpeaking();
  }
  const ids = telemetry.filter((e) => e.name === "response").map((e) => e.correlationId);
  return { count: ids.length, unique: new Set(ids).size, opaque: ids.every((id) => typeof id === "string" && !id.includes("secret")) };
}
export async function malformedRejected() {
  const { transport } = await stack();
  const { RealtimeServer } = await import(`${SRC}/server.ts`);
  const seen = []; transport.onMessage((m) => seen.push(m));
  transport.send({ type: "ptt", correlationId: "x", pressed: true });
  const server = new RealtimeServer({ tokens: new Set(), budgetSeconds: 1, telemetry() {}, respond: () => "" });
  const raw = []; server.handle("c", "{not json", (r) => raw.push(JSON.parse(r)));
  return { beforeJoin: seen, garbage: raw };
}
export async function guards() {
  const { session } = await stack();
  session.releaseTalk(); session.audio(1, "x");
  const idle = session.state;
  session.start("room-a", "tok-ok"); session.releaseTalk();
  return { idle, ready: session.state };
}
export function ledger() {
  try {
    const value = JSON.parse(readFileSync("/work/app/INTEGRATION.json", "utf8"));
    const defects = Array.isArray(value?.defects) ? value.defects : [];
    const categories = defects.map((d) => String(d?.category));
    return { ...value, categoriesSorted: [...categories].sort(),
      duplicates: categories.length - new Set(categories).size,
      unknownCategories: categories.filter((c) => !VOCABULARY.includes(c)).sort() };
  }
  catch (error) { return { $error: String(error?.name) }; }
}

// Retained server state after many sessions end by budget (inputs only; counts are observations).
async function retainedAfterEndedSessions(count = 40) {
  const { RealtimeServer } = await import(`${SRC}/server.ts`);
  const { LoopbackTransport } = await import(`${SRC}/transport.ts`);
  const { VoiceSession } = await import(`${SRC}/session.ts`);
  const server = new RealtimeServer({ tokens: new Set(["tok-ok"]), budgetSeconds: 1, telemetry() {}, respond: () => "" });
  const ended = [];
  for (let i = 0; i < count; i += 1) {
    const session = new VoiceSession(new LoopbackTransport(server, `conn-${i}`));
    session.start("room-a", "tok-ok"); session.pressTalk(); session.audio(2, "x");
    ended.push(session.state === "ended" && session.endReason === "budget");
  }
  let retained = 0;
  for (const value of Object.values(server)) if (value instanceof Map || value instanceof Set) retained += value.size;
  return { allEnded: ended.every(Boolean), retained };
}
export async function leakCheck() {
  const ledgerValue = ledger();
  const claimed = Array.isArray(ledgerValue?.defects) && ledgerValue.defects.some((d) => d?.category === "memory-leak");
  const { allEnded, retained } = await retainedAfterEndedSessions();
  return { claimed, allEnded, retained, claimFixed: !claimed || (allEnded && retained === 0) };
}

// Re-entrant cancel: respond() delivers a cancel for the pending turn on the same connection.
export async function cancelCheck() {
  const ledgerValue = ledger();
  const claimed = Array.isArray(ledgerValue?.defects) && ledgerValue.defects.some((d) => d?.category === "race-condition");
  const { RealtimeServer } = await import(`${SRC}/server.ts`);
  const { PROTOCOL_VERSION } = await import(`${SRC}/protocol.ts`);
  const log = [];
  let server;
  const reply = (raw) => { const m = JSON.parse(raw); log.push(`frame:${m.type}`); };
  server = new RealtimeServer({ tokens: new Set(["tok-ok"]), budgetSeconds: 120,
    telemetry: (event) => log.push(`telemetry:${event.name}`),
    respond: () => { server.handle("c", JSON.stringify({ type: "cancel", correlationId: "turn-1" }), reply); return "late"; } });
  server.handle("c", JSON.stringify({ type: "join", roomId: "room-a", token: "tok-ok", version: PROTOCOL_VERSION }), reply);
  server.handle("c", JSON.stringify({ type: "ptt", correlationId: "turn-1", pressed: true }), reply);
  server.handle("c", JSON.stringify({ type: "ptt", correlationId: "turn-1", pressed: false }), reply);
  const cancelAt = log.indexOf("telemetry:cancelled");
  const after = cancelAt < 0 ? null : log.slice(cancelAt + 1).filter((e) => e.endsWith(":response")).length;
  return { claimed, joined: log.includes("frame:joined"), cancelled: cancelAt >= 0, responsesAfterCancel: after,
    claimFixed: !claimed || (log.includes("frame:joined") && cancelAt >= 0 && after === 0) };
}
