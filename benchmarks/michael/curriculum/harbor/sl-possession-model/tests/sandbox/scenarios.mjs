// Trusted, answer-free scenarios for the explicit possession model. Each scenario builds the
// candidate's MatchSim in-process from src/sim, drives it with held-out inputs and returns
// observations; expected values live only in the host-side clauses.
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
const SIM = "/work/app/src/sim";
const TUNING = JSON.parse(readFileSync("/work/app/data/tuning.json", "utf8"));

async function mods() {
  const [sim, vec, cli, input, pos] = await Promise.all([
    import(`${SIM}/match_sim.ts`), import(`${SIM}/vec.ts`), import(`${SIM}/cli.ts`),
    import(`${SIM}/input_provider.ts`), import(`${SIM}/possession.ts`)]);
  return { MatchSim: sim.MatchSim, Vector2: vec.Vector2, Vector3: vec.Vector3, runMatchLog: cli.runMatchLog,
    AiProvider: input.AiProvider, Possession: pos.Possession, PossessionState: pos.PossessionState };
}
async function soccer() {
  const [sim, cli, input] = await Promise.all([import(`${SIM}/match_sim.ts`), import(`${SIM}/cli.ts`),
    import(`${SIM}/input_provider.ts`)]);
  return { MatchSim: sim.MatchSim, runMatchLog: cli.runMatchLog, AiProvider: input.AiProvider };
}
const tuning = (edit) => { const t = JSON.parse(JSON.stringify(TUNING)); edit(t); return t; };
const named = (m, value) => Object.keys(m.PossessionState).find((k) => m.PossessionState[k] === value) ?? String(value);
const snap = (m, p) => ({ state: named(m, p.state), holder: p.holder_id, team: p.team });
function entry(m, over = {}) {
  return { move: new m.Vector2(0, 0), aim: new m.Vector2(0, 0), sprint: false, kick: false,
    kick_type: 0, kick_power: 1, touch_mode: 0, ...over };
}
function isolate(m, sim, keep = []) {
  const spots = [[-17, -10], [-17, 10], [17, -10], [17, 10], [-14, -11], [14, 11]];
  sim.players.forEach((p, i) => {
    if (keep.includes(p.id)) return;
    p.position = new m.Vector2(...spots[i % spots.length]);
    p.velocity = new m.Vector2(0, 0);
    p.touch_cooldown = 0;
  });
}
const r4 = (x) => Math.round(x * 1e4) / 1e4;
// Where the stated carry rule puts the ball for this holder.
function expected(m, holder, offset, height) {
  const f = holder.facing; const l = Math.hypot(f.x, f.y);
  const lead = l > 0.0001 ? [f.x / l, f.y / l] : [0, 0];
  return { p: [holder.position.x + lead[0] * offset, height, holder.position.y + lead[1] * offset],
    v: [holder.velocity.x, 0, holder.velocity.y] };
}
function deviation(sim, e) {
  const b = sim.ball;
  return Math.max(Math.abs(b.position.x - e.p[0]), Math.abs(b.position.y - e.p[1]), Math.abs(b.position.z - e.p[2]),
    Math.abs(b.velocity.x - e.v[0]), Math.abs(b.velocity.y - e.v[1]), Math.abs(b.velocity.z - e.v[2]),
    Math.abs(b.angular_velocity.x), Math.abs(b.angular_velocity.y), Math.abs(b.angular_velocity.z));
}

// The Possession object's transitions.
export async function possessionObject() {
  const m = await mods();
  const p = new m.Possession();
  const out = { distinct: new Set(Object.values(m.PossessionState)).size === 3
    && ["LOOSE", "HELD", "IN_FLIGHT"].every((k) => k in m.PossessionState), steps: [] };
  const step = (label) => out.steps.push({ label, ...snap(m, p), held: p.is_held() });
  step("new");
  p.hold(3, 1); step("hold");
  p.release(); step("release-keeps-team");
  p.release(0); step("release-by-team");
  p.set_loose(); step("loose-keeps-team");
  p.set_loose(1); step("loose-by-team");
  p.hold(2, 0); p.clear(); step("clear");
  p.hold(4, 1);
  const d = p.to_dict();
  out.dict = { state: named(m, d.state), holder: d.holder, team: d.team };
  return out;
}

// MatchSim exposes a neutral possession and a player lookup.
export async function simSurface(args) {
  const m = await mods();
  const sim = new m.MatchSim(args.seed);
  const found = sim.player_by_id(args.id);
  return { possession: snap(m, sim.possession), found: found === null ? null : found.id,
    missing: sim.player_by_id(999) };
}

// A held ball rides with its carrier at the tuned offset and height while the carrier moves.
export async function carryFollows(args) {
  const m = await mods();
  const t = args.carry ? tuning((x) => { x.carry = args.carry; }) : tuning((x) => { delete x.carry; });
  const offset = args.carry ? args.carry.offset : 0.45, height = args.carry ? args.carry.height : 1.0;
  const sim = new m.MatchSim(args.seed, t);
  const id = args.holder;
  isolate(m, sim, [id]);
  sim.possession.hold(id, sim.player_by_id(id).team);
  let worst = 0; const kinds = [];
  for (let i = 0; i < args.ticks; i += 1) {
    const turn = i < args.ticks / 2 ? new m.Vector2(1, 0.4) : new m.Vector2(-0.3, 1);
    const inputs = new Map([[id, entry(m, { move: turn, aim: turn, sprint: i % 3 === 0 })]]);
    for (const e of sim.tick(inputs)) kinds.push(e.event);
    worst = Math.max(worst, deviation(sim, expected(m, sim.player_by_id(id), offset, height)));
  }
  return { worst: r4(worst), events: kinds, possession: snap(m, sim.possession) };
}

// The touch models leave a carried ball alone, even when an opponent stands on it and kicks.
export async function heldIgnoresTouches(args) {
  const m = await mods();
  const sim = new m.MatchSim(args.seed);
  isolate(m, sim, [0, 3]);
  sim.possession.hold(0, 0);
  const carrier = sim.player_by_id(0), rival = sim.player_by_id(3);
  carrier.position = new m.Vector2(2, 1); rival.position = new m.Vector2(2.45, 1);
  carrier.touch_cooldown = 0; rival.touch_cooldown = 0; // no kickoff standoff: the rival may play the ball
  const kinds = [];
  for (let i = 0; i < args.ticks; i += 1) {
    const inputs = new Map([[0, entry(m)], [3, entry(m, { kick: true, kick_type: 1, aim: new m.Vector2(-1, 0) })]]);
    for (const e of sim.tick(inputs)) kinds.push(e.event);
    rival.position = new m.Vector2(sim.ball.position.x, sim.ball.position.z);
  }
  return { events: kinds, possession: snap(m, sim.possession), height: r4(sim.ball.position.y) };
}

// Releasing a moving carrier's ball (a fumble) hands it their momentum, then physics takes over.
export async function fumble(args) {
  const m = await mods();
  const sim = new m.MatchSim(args.seed);
  const id = args.holder; const team = sim.player_by_id(id).team;
  isolate(m, sim, [id]);
  sim.player_by_id(id).position = new m.Vector2(-12, 0);
  sim.possession.hold(id, team);
  const run = new m.Vector2(1, 0);
  for (let i = 0; i < 40; i += 1) sim.tick(new Map([[id, entry(m, { move: run, aim: run, sprint: true })]]));
  const carried = sim.ball.velocity.x;
  sim.possession.set_loose(team);
  sim.player_by_id(id).position = new m.Vector2(-15, -9);
  sim.tick(new Map());
  const first = { vx: sim.ball.velocity.x, y: sim.ball.position.y };
  for (let i = 0; i < 20; i += 1) sim.tick(new Map());
  return { carriedFast: carried > 3, inherits: first.vx > 0.9 * carried && first.vx <= carried + 1e-9,
    falls: sim.ball.position.y < first.y - 0.05, possession: snap(m, sim.possession) };
}

// A carrier who no longer exists drops the ball instead of freezing it.
export async function vanishedCarrier(args) {
  const m = await mods();
  const sim = new m.MatchSim(args.seed);
  sim.possession.hold(999, 1);
  sim.tick(new Map());
  const after = snap(m, sim.possession);
  for (let i = 0; i < 5; i += 1) sim.tick(new Map());
  return { after, finite: sim.state_is_finite() };
}

// Restarts clear possession: an explicit kickoff, and the kickoff after a goal.
export async function restartClears(args) {
  const m = await mods();
  const sim = new m.MatchSim(args.seed);
  sim.possession.hold(1, 0);
  sim.kickoff(1);
  const kickoff = snap(m, sim.possession);
  isolate(m, sim, []);
  sim.possession.release(0);
  sim.ball.position = new m.Vector3(18.5, 0.5, 0); sim.ball.velocity = new m.Vector3(12, 0, 0);
  const kinds = [];
  for (let i = 0; i < 30 && !kinds.includes("goal"); i += 1) for (const e of sim.tick(new Map())) kinds.push(e.event);
  return { kickoff, scored: kinds.includes("goal"), afterGoal: snap(m, sim.possession) };
}

// IN_FLIGHT is physics-driven exactly like LOOSE, and a travelling ball can still be received.
export async function inFlight(args) {
  const m = await mods();
  const trace = (state) => {
    const sim = new m.MatchSim(args.seed);
    isolate(m, sim, [args.receiver]);
    if (state === "flight") sim.possession.release(0);
    sim.ball.position = new m.Vector3(-6, 0.4, 0); sim.ball.velocity = new m.Vector3(12, 1, 0.2);
    sim.ball.angular_velocity = new m.Vector3(0, 4, 0);
    const r = sim.player_by_id(args.receiver); r.position = new m.Vector2(2, 0.3);
    const kinds = []; const path = [];
    for (let i = 0; i < 60; i += 1) {
      for (const e of sim.tick(new Map([[args.receiver, entry(m)]]))) kinds.push(e.event);
      path.push([sim.ball.position.x, sim.ball.position.y, sim.ball.position.z].map(r4).join(","));
    }
    return { kinds, path: createHash("sha256").update(path.join(";")).digest("hex"), state: snap(m, sim.possession) };
  };
  const loose = trace("loose"), flight = trace("flight");
  return { samePath: loose.path === flight.path, sameEvents: loose.kinds.join() === flight.kinds.join(),
    received: flight.kinds.includes("touch") || flight.kinds.includes("dribble"), flightState: flight.state.state };
}

// Soccer never leaves a neutral LOOSE ball and its AI matches are unchanged (state digests and full logs).
export async function soccerUnchanged(args) {
  const m = await soccer();
  const out = {};
  for (const seed of args.seeds) {
    const sim = new m.MatchSim(seed);
    const providers = [new m.AiProvider(0), new m.AiProvider(1)];
    // Soccer stays in its initial (LOOSE, neutral) possession for the whole match.
    const initial = JSON.stringify(sim.possession ?? null, ["state", "holder_id", "team"]);
    let leftLoose = false;
    for (let i = 0; i < args.ticks; i += 1) {
      sim.advance(providers);
      if (JSON.stringify(sim.possession ?? null, ["state", "holder_id", "team"]) !== initial) leftLoose = true;
    }
    out[seed] = { digest: sim.state_digest(), leftLoose };
  }
  return out;
}

export async function soccerLog(args) {
  const m = await soccer();
  const log = m.runMatchLog(args.seed, args.ticks).to_jsonl();
  return { sha256: createHash("sha256").update(log).digest("hex") };
}
