// Trusted, answer-free integration scenarios: build the stack in-process and record observations.
import { readFileSync } from "node:fs";
const SRC = "/work/app/src";
const VOCABULARY = ["handshake-mismatch", "version-skew", "requirement-dropped", "content-in-telemetry",
  "unit-mismatch", "race-condition", "auth-bypass", "memory-leak"];
// Observations use protocol frames on the wire, not server-internal telemetry event names or id formats.
const parse = (raw) => { try { return JSON.parse(raw); } catch { return null; } };
function wire(server) {
  const frames = [];
  return { frames, server: { handle(connection, raw, reply) {
    frames.push({ connection, dir: "client", message: parse(raw) });
    return server.handle(connection, raw, (out) => { frames.push({ connection, dir: "server", message: parse(out) }); reply(out); });
  } } };
}
const served = (frames, type, connection) => frames.filter((f) => f.dir === "server" && f.message?.type === type
  && (connection === undefined || f.connection === connection)).map((f) => f.message);
async function stack(budgetSeconds = 120) {
  const { RealtimeServer } = await import(`${SRC}/server.ts`);
  const { LoopbackTransport } = await import(`${SRC}/transport.ts`);
  const { VoiceSession } = await import(`${SRC}/session.ts`);
  const telemetry = [];
  const heard = [];
  const server = new RealtimeServer({ tokens: new Set(["tok-ok"]), budgetSeconds,
    telemetry: (event) => telemetry.push(event),
    respond: (text) => { const reply = `reply-${heard.length + 1}`; heard.push({ text: String(text), reply }); return reply; } });
  const link = wire(server);
  const transport = new LoopbackTransport(link.server, "conn-1");
  const session = new VoiceSession(transport);
  return { session, transport, telemetry, heard, frames: link.frames };
}
const snap = (s) => ({ state: s.state, sessionId: s.sessionId, lastResponse: s.lastResponse, endReason: s.endReason });

export async function e2eTurn() {
  const { session, heard, frames } = await stack();
  session.start("room-a", "tok-ok");
  const joined = snap(session);
  session.pressTalk(); const listening = session.state;
  session.audio(2, "turn on the lights"); session.releaseTalk();
  const answered = snap(session);
  // The response for this turn is the one the server produced from a transcript carrying the turn's words.
  const answeredMatches = heard.some((h) => h.reply === answered.lastResponse && h.text.includes("turn on the lights"));
  // R4: audio streams with the turn's correlation id (the id of the turn's press/release and response).
  const sent = frames.filter((f) => f.dir === "client").map((f) => f.message);
  const turnIds = new Set(sent.filter((m) => m?.type === "ptt").map((m) => m.correlationId));
  const audioIds = sent.filter((m) => m?.type === "audio").map((m) => m.correlationId);
  const responseIds = served(frames, "response").map((m) => m.correlationId);
  const audioCorrelated = turnIds.size === 1 && audioIds.length > 0 && audioIds.every((id) => turnIds.has(id))
    && responseIds.length === 1 && turnIds.has(responseIds[0]);
  session.finishSpeaking();
  return { joined, listening, answered, answeredMatches, audioCorrelated, after: session.state };
}
export async function rejectsBadToken() {
  const { session } = await stack(); session.start("room-a", "tok-bad"); return snap(session);
}
// R1 opaque session ids: any non-empty string, stable for the session, distinct across concurrent sessions,
// and the session's later frames are accepted. The id's format is deliberately unconstrained.
export async function sessionIds() {
  const { RealtimeServer } = await import(`${SRC}/server.ts`);
  const { LoopbackTransport } = await import(`${SRC}/transport.ts`);
  const { VoiceSession } = await import(`${SRC}/session.ts`);
  const telemetry = [];
  const server = new RealtimeServer({ tokens: new Set(["tok-ok"]), budgetSeconds: 120,
    telemetry: (event) => telemetry.push(event), respond: () => "ok" });
  const link = wire(server);
  const clients = ["conn-a", "conn-b"].map((name) => ({ name, session: new VoiceSession(new LoopbackTransport(link.server, name)) }));
  for (const c of clients) {
    const mark = telemetry.length;
    c.session.start("room-a", "tok-ok");
    c.joinedId = c.session.sessionId;
    c.joinTelemetry = telemetry.slice(mark);
  }
  for (const c of clients) {
    const mark = telemetry.length;
    c.session.pressTalk(); c.session.audio(1, "hello"); c.session.releaseTalk();
    c.answered = c.session.state === "speaking" && c.session.lastResponse === "ok";
    c.session.finishSpeaking();
    c.session.pressTalk(); c.session.audio(1, "again"); c.session.releaseTalk();
    c.answeredAgain = c.session.state === "speaking";
    c.turnTelemetry = telemetry.slice(mark);
  }
  const ids = clients.map((c) => served(link.frames, "joined", c.name).map((m) => m.sessionId));
  const valid = clients.every((c, i) => ids[i].length === 1 && typeof ids[i][0] === "string" && ids[i][0].length > 0
    && c.joinedId === ids[i][0]);
  const stable = clients.every((c, i) => c.session.sessionId === ids[i][0]
    && [...c.joinTelemetry, ...c.turnTelemetry].every((e) => e?.sessionId === undefined || e.sessionId === ids[i][0])
    && c.turnTelemetry.some((e) => e?.sessionId === ids[i][0]));
  const distinct = valid && ids[0][0] !== ids[1][0];
  const accepted = clients.every((c) => c.answered && c.answeredAgain
    && !served(link.frames, "rejected", c.name).length);
  return { valid, stable, distinct, accepted };
}
export async function rejectsOldVersion() {
  const { transport, frames } = await stack();
  transport.send({ type: "join", roomId: "room-a", token: "tok-ok", version: 1 });
  return { versionRejected: served(frames, "rejected").some((m) => m.reason === "version"),
    joined: served(frames, "joined").length > 0 };
}
export async function bargeIn() {
  const { session, frames } = await stack();
  const sentCancels = () => frames.filter((f) => f.dir === "client" && f.message?.type === "cancel").map((f) => f.message.correlationId);
  const responseIds = () => served(frames, "response").map((m) => m.correlationId);
  session.start("room-a", "tok-ok");
  session.pressTalk(); session.audio(1, "tell me a long story"); session.releaseTalk();
  const speaking = session.state;
  const responded = responseIds();
  session.pressTalk();
  const cancelled = sentCancels();
  session.audio(1, "stop"); session.releaseTalk();
  const responses = responseIds();
  return { speaking, after: session.state, cancelledFirst: cancelled.length === 1 && cancelled[0] === responded[0],
    newTurnAnswered: responses.length === 2 && responses[1] !== responses[0], state: session.state };
}
export async function telemetryContentFree() {
  const { session, telemetry } = await stack();
  session.start("room-a", "tok-ok");
  session.pressTalk(); session.audio(1.25, "PRIVATE-PHRASE-42 my address"); session.releaseTalk();
  const text = JSON.stringify(telemetry);
  const keys = [...new Set(telemetry.flatMap((e) => Object.keys(e)))].sort();
  // Durations are milliseconds (L1); the event carrying the 1.25 s chunk is identified by value, not by name.
  const msValues = telemetry.filter((e) => typeof e?.ms === "number").map((e) => e.ms);
  return { events: telemetry.length, leaked: text.includes("PRIVATE-PHRASE") || text.includes("address"),
    keys, msValues };
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
  const { session, frames } = await stack();
  session.start("room-a", "tok-ok");
  for (const words of ["first secret", "second secret"]) {
    session.pressTalk(); session.audio(1, words); session.releaseTalk(); session.finishSpeaking();
  }
  const ids = served(frames, "response").map((m) => m.correlationId);
  return { count: ids.length, unique: new Set(ids).size, opaque: ids.every((id) => typeof id === "string" && !id.includes("secret")) };
}
export async function malformedRejected() {
  const { transport, frames } = await stack();
  const { RealtimeServer } = await import(`${SRC}/server.ts`);
  transport.send({ type: "ptt", correlationId: "x", pressed: true });
  const beforeJoin = frames.filter((f) => f.dir === "server").map((f) => f.message);
  const server = new RealtimeServer({ tokens: new Set(), budgetSeconds: 1, telemetry() {}, respond: () => "" });
  const garbage = []; server.handle("c", "{not json", (r) => garbage.push(parse(r)));
  const rejectedOnly = (list) => list.length > 0 && list.every((m) => m?.type === "rejected");
  // A frame before join may be rejected with any protocol reason; unparsable input can only be malformed.
  return { beforeJoinRejected: rejectedOnly(beforeJoin),
    garbageRejected: rejectedOnly(garbage) && garbage.every((m) => m.reason === "malformed") };
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
    const SOURCES = ["src/protocol.ts", "src/session.ts", "src/transport.ts", "src/server.ts"];
    // Where each audited defect is located in the landed code (either side of a cross-layer mismatch counts).
    const LOCATED = { "handshake-mismatch": ["src/transport.ts", "src/server.ts"], "version-skew": ["src/server.ts", "src/transport.ts"],
      "requirement-dropped": ["src/session.ts"], "content-in-telemetry": ["src/server.ts"],
      "unit-mismatch": ["src/session.ts", "src/server.ts"], "memory-leak": ["src/server.ts"], "race-condition": ["src/server.ts"] };
    const fileList = (files) => Array.isArray(files) && files.length > 0 && files.every((f) => SOURCES.includes(f));
    const requirements = value?.requirements && typeof value.requirements === "object" ? Object.values(value.requirements) : [];
    return { ...value, categoriesSorted: [...categories].sort(),
      requirementFilesKnown: requirements.length > 0 && requirements.every((r) => fileList(r?.files)),
      defectFilesKnown: defects.every((d) => fileList(d?.files)),
      defectsLocated: defects.every((d) => !(String(d?.category) in LOCATED)
        || (Array.isArray(d?.files) && d.files.some((f) => LOCATED[String(d.category)].includes(f)))),
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
  return { allEnded: ended.every(Boolean), retained: retainedEntries(server) };
}
// Entries held in server-owned collections (two levels deep). Constant state such as a stored token set is
// allowed; only growth with the number of ended sessions counts as retention.
function retainedEntries(server) {
  let total = 0;
  const seen = new Set();
  const visit = (value, depth) => {
    if (value === null || typeof value !== "object" || seen.has(value) || depth > 2) return;
    seen.add(value);
    if (value instanceof Map) { total += value.size; for (const v of value.values()) visit(v, depth + 1); return; }
    if (value instanceof Set) { total += value.size; return; }
    if (Array.isArray(value)) { total += value.length; return; }
    for (const v of Object.values(value)) visit(v, depth + 1);
  };
  for (const [key, value] of Object.entries(server)) if (key !== "options") visit(value, 0);
  return total;
}
export async function leakCheck() {
  const ledgerValue = ledger();
  const claimed = Array.isArray(ledgerValue?.defects) && ledgerValue.defects.some((d) => d?.category === "memory-leak");
  const small = await retainedAfterEndedSessions(40);
  const large = await retainedAfterEndedSessions(80);
  const allEnded = small.allEnded && large.allEnded;
  return { claimed, allEnded, retained: [small.retained, large.retained],
    claimFixed: !claimed || (allEnded && large.retained === small.retained) };
}

// Re-entrant cancel: respond() delivers a cancel for the pending turn on the same connection.
export async function cancelCheck() {
  const ledgerValue = ledger();
  const claimed = Array.isArray(ledgerValue?.defects) && ledgerValue.defects.some((d) => d?.category === "race-condition");
  const { RealtimeServer } = await import(`${SRC}/server.ts`);
  const { PROTOCOL_VERSION } = await import(`${SRC}/protocol.ts`);
  const log = [];
  let server;
  let cancelAt = -1;
  let cancelReplies = null;
  const reply = (raw) => { log.push(parse(raw)?.type); };
  server = new RealtimeServer({ tokens: new Set(["tok-ok"]), budgetSeconds: 120, telemetry() {},
    respond: () => {
      const replies = [];
      server.handle("c", JSON.stringify({ type: "cancel", correlationId: "turn-1" }), (raw) => { replies.push(parse(raw)?.type); reply(raw); });
      cancelAt = log.length; cancelReplies = replies; return "late"; } });
  server.handle("c", JSON.stringify({ type: "join", roomId: "room-a", token: "tok-ok", version: PROTOCOL_VERSION }), reply);
  server.handle("c", JSON.stringify({ type: "ptt", correlationId: "turn-1", pressed: true }), reply);
  server.handle("c", JSON.stringify({ type: "ptt", correlationId: "turn-1", pressed: false }), reply);
  const joined = log.includes("joined");
  const cancelAccepted = cancelAt >= 0 && !cancelReplies.includes("rejected");
  const after = cancelAt < 0 ? null : log.slice(cancelAt).filter((t) => t === "response").length;
  return { claimed, joined, cancelAccepted, responsesAfterCancel: after,
    claimFixed: !claimed || (joined && cancelAccepted && after === 0) };
}
