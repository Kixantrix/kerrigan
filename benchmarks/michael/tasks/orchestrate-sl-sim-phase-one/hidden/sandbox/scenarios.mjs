// Trusted, answer-free integration scenarios for the phase-one MatchSim slice.
// Each scenario builds the integrated sim in-process from the candidate's src/sim
// modules, drives it with held-out seeds and inputs, and returns observations.
import { readFileSync } from "node:fs";
const ROOT = "/work/app";
const SIM = `${ROOT}/src/sim`;
const VOCABULARY = ["unseeded-random", "digest-incomplete", "unit-mismatch", "contract-mismatch",
  "requirement-dropped", "friction-model", "double-apply", "tick-order", "aim-coupling"];
const SOURCES = ["src/sim/ball_physics.ts", "src/sim/ball_state.ts", "src/sim/cli.ts", "src/sim/first_touch.ts",
  "src/sim/input_provider.ts", "src/sim/kick.ts", "src/sim/locomotion.ts", "src/sim/match_config.ts",
  "src/sim/match_log.ts", "src/sim/match_sim.ts", "src/sim/player_state.ts", "src/sim/sim_rng.ts", "src/sim/vec.ts"];

// Math.random is replaced by a fixed-seed mulberry32 stream that every exported scenario resets on
// entry, so a candidate's use of it is reproducible across grader runs (identical observations)
// while still drawing different values for repeated same-seed matches inside one scenario.
let randomState = 0;
function resetRandom() { randomState = 0x9e3779b9; }
Math.random = function random() {
  randomState = (randomState + 0x6d2b79f5) >>> 0;
  let x = randomState;
  x = Math.imul(x ^ (x >>> 15), x | 1);
  x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
  return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
};
resetRandom();

async function mods() {
  const [sim, vec, log, cli, input] = await Promise.all([
    import(`${SIM}/match_sim.ts`), import(`${SIM}/vec.ts`), import(`${SIM}/match_log.ts`),
    import(`${SIM}/cli.ts`), import(`${SIM}/input_provider.ts`)]);
  return { MatchSim: sim.MatchSim, Vector2: vec.Vector2, Vector3: vec.Vector3, MatchLog: log.MatchLog,
    runMatchLog: cli.runMatchLog, AiProvider: input.AiProvider, ScriptedProvider: input.ScriptedProvider };
}
// A complete input entry in the plan's input contract (plain object; no provider helpers).
function entry(m, over = {}) {
  return { move: new m.Vector2(0, 0), aim: new m.Vector2(0, 0), sprint: false, kick: false,
    kick_type: 0, kick_power: 1, touch_mode: 0, ...over };
}
// Park every player except `keep` far from the play area; they get no inputs, so they never touch.
function isolate(m, sim, keep = []) {
  const spots = [[-17, -10], [-17, 10], [17, -10], [17, 10], [-14, -11], [14, 11]];
  sim.players.forEach((p, i) => {
    if (keep.includes(p.id)) return;
    p.position = new m.Vector2(...spots[i % spots.length]);
    p.velocity = new m.Vector2(0, 0);
  });
}
const ground = (v) => Math.hypot(v.x, v.z);
const events = (jsonl) => jsonl.split("\n").map((line) => JSON.parse(line)).filter((r) => r.type === "event");
const count = (list, name) => list.filter((e) => e.event === name).length;

// R1: AI vs AI with the same seed reproduces a byte-identical log; another seed diverges.
export async function aiReplay(args) {
  resetRandom();
  const m = await mods();
  const a = m.runMatchLog(args.seed, args.ticks).to_jsonl();
  const b = m.runMatchLog(args.seed, args.ticks).to_jsonl();
  const c = m.runMatchLog(args.seed + 1, args.ticks).to_jsonl();
  const list = events(a);
  return { identical: a === b, diverges: a !== c, kicked: count(list, "kick") > 0,
    touched: count(list, "touch") > 0 };
}

// R1 record/replay: record the per-tick inputs of an AI match, then replay them twice through a
// ScriptedProvider with the same seed; the two replays must be byte-identical.
export async function recordReplay(args) {
  resetRandom();
  const m = await mods();
  const recorded = new Map();
  class Recorder {
    constructor(inner) { this.inner = inner; }
    collect(sim) {
      const out = new Map();
      for (const provider of this.inner) for (const [id, input] of provider.collect(sim)) out.set(id, input);
      const copy = new Map();
      for (const [id, input] of out) copy.set(id, { ...input, move: input.move.copy(), aim: input.aim.copy() });
      recorded.set(sim.tick_count, copy);
      return out;
    }
  }
  m.runMatchLog(args.seed, args.ticks, { providers: () => [new Recorder([new m.AiProvider(0), new m.AiProvider(1)])] });
  const replay = (seed) => m.runMatchLog(seed, args.ticks, { providers: () => {
    const scripted = new m.ScriptedProvider();
    scripted.per_tick = recorded;
    return [scripted];
  } }).to_jsonl();
  const first = replay(args.seed);
  const second = replay(args.seed);
  const list = events(first);
  return { identical: first === second, kicked: count(list, "kick") > 0, recordedTicks: recorded.size };
}

// R2: snapshots and the state digest change when any covered state changes.
export async function digestCoverage(args) {
  resetRandom();
  const m = await mods();
  const build = () => {
    const sim = new m.MatchSim(args.seed);
    for (let i = 0; i < 5; i += 1) {
      sim.tick(new Map([[1, entry(m, { move: new m.Vector2(0.6, 0.3), aim: new m.Vector2(0, 1) })]]));
    }
    return sim;
  };
  const snap = (sim) => { const log = new m.MatchLog(); log.snapshot(sim); return JSON.stringify(log.records[0]); };
  const compare = (mutate) => {
    const a = build(); const b = build();
    mutate(b);
    return { digest: a.state_digest() !== b.state_digest(), snapshot: snap(a) !== snap(b) };
  };
  const a = build(); const b = build();
  return {
    stable: a.state_digest() === b.state_digest() && snap(a) === snap(b),
    ballVelocity: compare((s) => { s.ball.velocity = new m.Vector3(s.ball.velocity.x + 0.5, s.ball.velocity.y, s.ball.velocity.z); }),
    ballSpin: compare((s) => { s.ball.angular_velocity = new m.Vector3(0.3, args.spin, -0.2); }),
    facing: compare((s) => { s.players[2].facing = new m.Vector2(0.6, 0.8); }),
    stamina: compare((s) => { s.players[4].stamina = s.players[4].stamina - args.staminaDrop; }),
    sprinting: compare((s) => { s.players[3].sprinting = !s.players[3].sprinting; }),
  };
}

// R3: rolling resistance is a constant deceleration (speed-independent apart from linear drag),
// stopping at zero; ground bounce uses ground_restitution.
export async function rolling(args) {
  resetRandom();
  const m = await mods();
  const roll = (speed, ticks) => {
    const sim = new m.MatchSim(args.seed);
    isolate(m, sim);
    sim.ball.position = new m.Vector3(-15, sim.ball_radius(), 10);
    sim.ball.velocity = new m.Vector3(speed, 0, 0);
    sim.ball.angular_velocity = new m.Vector3(0, 0, 0);
    for (let i = 0; i < ticks; i += 1) sim.tick(new Map());
    return sim.ball.velocity;
  };
  const drops = args.speeds.map((speed) => speed - ground(roll(speed, args.ticks)));
  const stopped = roll(args.slow, args.stopTicks);
  const drop = new m.MatchSim(args.seed);
  isolate(m, drop);
  drop.ball.position = new m.Vector3(-15, drop.ball_radius() + 0.01, 10);
  drop.ball.velocity = new m.Vector3(0, -args.fall, 0);
  drop.tick(new Map());
  return { drops, stoppedSpeed: ground(stopped), stoppedVx: stopped.x, bounceVy: drop.ball.velocity.y };
}

// R3: airborne ball - position integrates exactly once per tick, Magnus curve, spin decay, gravity,
// and the speed clamp.
export async function flight(args) {
  resetRandom();
  const m = await mods();
  const fly = (velocity, spin, ticks) => {
    const sim = new m.MatchSim(args.seed);
    isolate(m, sim);
    sim.ball.position = new m.Vector3(-10, 30, 0);
    sim.ball.velocity = new m.Vector3(...velocity);
    sim.ball.angular_velocity = new m.Vector3(...spin);
    for (let i = 0; i < ticks; i += 1) sim.tick(new Map());
    return sim.ball;
  };
  const straight = fly([args.speed, 0, 0], [0, 0, 0], args.ticks);
  const curved = fly([args.speed, 0, 0], [0, args.spin, 0], args.curveTicks);
  const fast = fly([args.fast, 0, 0], [0, 0, 0], 1);
  return { dx: straight.position.x + 10, vy: straight.velocity.y,
    curveZ: curved.position.z, spinAfter: curved.angular_velocity.y, fastSpeed: fast.velocity.length() };
}

// R4: players start with a full tank in stamina points and can sprint; sprint threshold is strict.
export async function sprint(args) {
  resetRandom();
  const m = await mods();
  const sim = new m.MatchSim(args.seed);
  const staminaMax = sim.config.get_float("player", "stamina_max", NaN);
  const initialFull = sim.players.every((p) => p.stamina === staminaMax);
  isolate(m, sim, [0]);
  const p = sim.players[0];
  p.position = new m.Vector2(-12, 0);
  p.velocity = new m.Vector2(0, 0);
  const run = new Map([[0, entry(m, { move: new m.Vector2(0, 1), sprint: true })]]);
  for (let i = 0; i < args.ticks; i += 1) sim.tick(run);
  const result = { initialFull, speed: p.velocity.length(), stamina: p.stamina, sprinting: p.sprinting,
    ticks: sim.tick_count };
  // One player, one tick, from a given state.
  const step = (state, over, ticks = 1) => {
    const s = new m.MatchSim(args.seed);
    isolate(m, s, [0]);
    const q = s.players[0];
    q.position = new m.Vector2(...(state.position ?? [-12, -5]));
    q.velocity = new m.Vector2(...(state.velocity ?? [0, 0]));
    if (state.stamina !== undefined) q.stamina = state.stamina;
    if (state.facing) q.facing = new m.Vector2(...state.facing);
    const inputs = new Map([[0, entry(m, over)]]);
    for (let i = 0; i < ticks; i += 1) s.tick(inputs);
    return q;
  };
  // Threshold: stamina exactly at stamina_sprint_min cannot sprint; just above can.
  const edge = (stamina) => step({ velocity: [0, 7], stamina }, { move: new m.Vector2(0, 1), sprint: true }).velocity.length();
  const turned = step({ facing: [1, 0] }, { aim: new m.Vector2(0, 1) }, args.turnTicks);
  const afterTurn = Math.atan2(turned.facing.y, turned.facing.x);
  const held = step({ facing: [turned.facing.x, turned.facing.y] }, { move: new m.Vector2(-1, 0) }, args.turnTicks);
  return { ...result, atMin: edge(args.min), aboveMin: edge(args.min + 0.5),
    analog: step({}, { move: new m.Vector2(0.5, 0) }, 60).velocity.length(),
    recovered: step({ stamina: args.recoverFrom }, { move: new m.Vector2(1, 0) }, 60).stamina,
    capped: step({ stamina: staminaMax - 1 }, {}, 60).stamina,
    facingAngle: afterTurn, facingHeld: Math.atan2(held.facing.y, held.facing.x) === afterTurn,
    clampedZ: step({ position: [-12, 11.5] }, { move: new m.Vector2(0, 1) }, 30).position.y };
}

// R5: kick type, power and aim from the input contract.
export async function kick(args) {
  resetRandom();
  const m = await mods();
  const out = [];
  for (const c of args.cases) {
    const sim = new m.MatchSim(args.seed);
    const id = c.player ?? 0;
    isolate(m, sim, [id]);
    const p = sim.players[id];
    p.position = new m.Vector2(...(c.at ?? [-0.6, 0]));
    p.velocity = new m.Vector2(0, 0);
    p.facing = new m.Vector2(...c.facing);
    p.touch_cooldown = 0;
    // Strike a ball resting in the air within reach height, so ground friction plays no part this tick.
    sim.ball.position = new m.Vector3(0, args.height, 0);
    const evs = sim.tick(new Map([[id, entry(m, { kick: true, kick_type: c.type, kick_power: c.power,
      aim: new m.Vector2(...c.aim) })]]));
    const kicks = evs.filter((e) => e?.event === "kick");
    const v = sim.ball.velocity;
    out.push({ kicks: kicks.length, kick: kicks[0]?.kick ?? null, power: kicks[0]?.power ?? null,
      player: kicks[0]?.player ?? null, team: kicks[0]?.team ?? null,
      speed: ground(v), vx: v.x, vy: v.y, heading: Math.atan2(v.z, v.x),
      possession: [sim.possession_ticks[0], sim.possession_ticks[1]] });
  }
  return { cases: out };
}

// R6: a non-kicking player in reach receives a moving ball through FirstTouch.
export async function firstTouch(args) {
  resetRandom();
  const m = await mods();
  const setup = (seed, ballSpeed, over = {}, withInput = true) => {
    const sim = new m.MatchSim(seed);
    isolate(m, sim, [3]);
    const p = sim.players[3];
    p.position = new m.Vector2(4, 0);
    p.velocity = new m.Vector2(0, 0);
    p.facing = new m.Vector2(1, 0);
    p.touch_cooldown = 0;
    // Airborne within reach height, so ground friction plays no part in the observed velocities.
    sim.ball.position = new m.Vector3(5, args.height, 0);
    sim.ball.velocity = new m.Vector3(-ballSpeed, 0, 0);
    sim.ball.angular_velocity = new m.Vector3(0, args.spin, 0);
    const inputs = withInput ? new Map([[3, entry(m, over)]]) : new Map();
    const evs = sim.tick(inputs);
    return { sim, inputs, evs, touches: evs.filter((e) => e?.event === "touch") };
  };
  const modes = {};
  for (const [name, mode] of Object.entries({ cushion: 0, kill: 1, knock_on: 2 })) {
    const { sim, inputs, touches } = setup(args.seed, args.speed, { touch_mode: mode });
    const v = sim.ball.velocity;
    const spin = sim.ball.angular_velocity.y;
    const possession = [sim.possession_ticks[0], sim.possession_ticks[1]];
    let nextTouch = null;
    for (let i = 1; i <= args.watch && nextTouch === null; i += 1) {
      if (sim.tick(inputs).some((e) => e?.event === "touch")) nextTouch = i;
    }
    modes[name] = { touches: touches.length, touch: touches[0]?.touch ?? null, player: touches[0]?.player ?? null,
      team: touches[0]?.team ?? null, quality: touches[0]?.quality ?? null,
      alongX: v.x, lateral: Math.abs(v.z), spin, possession, nextTouch };
  }
  const errorBound = (() => {
    const sim = new m.MatchSim(args.seed);
    const q = modes.cushion.quality ?? 0;
    return sim.config.get_float("first_touch", "error_jitter", NaN) * sim.config.get_float("first_touch", "max_error", NaN) * (1 - q);
  })();
  const laterals = args.seeds.map((seed) => setup(seed, args.speed).sim.ball.velocity.z);
  const atTrigger = setup(args.seed, args.trigger).touches.length;
  const belowTrigger = setup(args.seed, args.trigger - 0.01).touches.length;
  const kicking = setup(args.seed, args.speed, { kick: true, kick_power: 0.5 });
  const noInput = setup(args.seed, args.speed, {}, false);
  return { modes, atTrigger, belowTrigger,
    kickerKicks: kicking.evs.filter((e) => e?.event === "kick").length === 1 && kicking.touches.length === 0,
    noInputTouches: noInput.touches.length,
    seededError: setup(args.seed, args.speed).sim.ball.velocity.z === laterals[0]
      && new Set(laterals).size === laterals.length,
    errorWithinBound: laterals.every((z) => Math.abs(z) <= errorBound + 1e-9) };
}

// Preserved scaffold behavior: goals, restarts, wall rebounds.
export async function restarts(args) {
  resetRandom();
  const m = await mods();
  const sim = new m.MatchSim(args.seed);
  isolate(m, sim);
  const r = sim.ball_radius();
  sim.ball.position = new m.Vector3(19.8, r, 1.0);
  sim.ball.velocity = new m.Vector3(10, 0, 0);
  const first = sim.tick(new Map()).filter((e) => e?.event === "goal");
  const afterFirst = { ball: [sim.ball.position.x, sim.ball.position.y, sim.ball.position.z, sim.ball.velocity.length()],
    spawn: sim.config.get_float("ball", "spawn_height", NaN),
    atHome: sim.players.every((p) => p.position.x === p.home.x && p.position.y === p.home.y),
    cooldowns: sim.players.map((p) => p.touch_cooldown),
    possession: [sim.possession_ticks[0], sim.possession_ticks[1]] };
  isolate(m, sim);
  sim.ball.position = new m.Vector3(-19.8, r, -1.0);
  sim.ball.velocity = new m.Vector3(-10, 0, 0);
  const second = sim.tick(new Map()).filter((e) => e?.event === "goal");
  const firstScore = first[0]?.score ?? {};
  const secondScore = second[0]?.score ?? {};
  // Shots at the line: only inside the mouth (|z| < goal_width/2, below goal_height) score.
  const shot = (z, y) => {
    const s = new m.MatchSim(args.seed);
    isolate(m, s);
    s.ball.position = new m.Vector3(19.8, y, z);
    s.ball.velocity = new m.Vector3(10, 0, 0);
    return { goals: s.tick(new Map()).filter((e) => e?.event === "goal").length, vx: s.ball.velocity.x };
  };
  const side = new m.MatchSim(args.seed);
  isolate(m, side);
  side.ball.position = new m.Vector3(0, r, 12.35);
  side.ball.velocity = new m.Vector3(0, 0, 5);
  side.tick(new Map());
  return { firstTeam: first[0]?.team ?? null, firstScore: [firstScore[0] ?? null, firstScore[1] ?? null],
    secondTeam: second[0]?.team ?? null, secondScore: [secondScore[0] ?? null, secondScore[1] ?? null],
    score: [sim.score[0], sim.score[1]], ...afterFirst,
    insidePost: shot(3.49, r).goals, onPost: shot(3.5, r).goals, wide: shot(6, r),
    underBar: shot(0, 2.45).goals, overBar: shot(0, 2.6).goals, sideVz: side.ball.velocity.z };
}

// Preserved touch arbitration: closest eligible player, ties to the lower id, reach, height, cooldowns.
export async function arbitration(args) {
  resetRandom();
  const m = await mods();
  const contest = (d1, d4, ballY = null, cooldown1 = 0) => {
    const sim = new m.MatchSim(args.seed);
    isolate(m, sim, [1, 4]);
    sim.players[1].position = new m.Vector2(-d1, 0);
    sim.players[4].position = new m.Vector2(d4, 0);
    for (const id of [1, 4]) { sim.players[id].velocity = new m.Vector2(0, 0); sim.players[id].touch_cooldown = 0; }
    sim.players[1].touch_cooldown = cooldown1;
    if (ballY !== null) sim.ball.position = new m.Vector3(0, ballY, 0);
    const kickNow = entry(m, { kick: true, kick_power: 0.5 });
    const evs = sim.tick(new Map([[1, kickNow], [4, kickNow]]));
    const kicks = evs.filter((e) => e?.event === "kick");
    const kicker = kicks.length === 1 ? kicks[0].player : null;
    return { kicker,
      kickerCooldown: kicker === null ? null : sim.players[kicker].touch_cooldown,
      committed: kicker === null ? null : sim.players[kicker === 1 ? 4 : 1].touch_cooldown };
  };
  return { closer: contest(0.9, 0.5), tie: contest(0.7, 0.7),
    inReach: contest(args.inside, 9).kicker, outOfReach: contest(args.outside, 9).kicker,
    atReachHeight: contest(0.5, 9, args.reachHeight).kicker, aboveReachHeight: contest(0.5, 9, args.reachHeight + 0.01).kicker,
    cooldownOne: contest(0.5, 9, null, 1).kicker, cooldownTwo: contest(0.5, 9, null, 2).kicker };
}

export function ledger() {
  resetRandom();
  try {
    const value = JSON.parse(readFileSync(`${ROOT}/INTEGRATION.json`, "utf8"));
    const defects = Array.isArray(value?.defects) ? value.defects : [];
    const categories = defects.map((d) => String(d?.category));
    // Where each audited defect is located in the landed code (any listed side of a mismatch counts).
    const LOCATED = {
      "unseeded-random": ["src/sim/match_sim.ts"],
      "digest-incomplete": ["src/sim/match_sim.ts", "src/sim/ball_state.ts", "src/sim/player_state.ts", "src/sim/match_log.ts"],
      "unit-mismatch": ["src/sim/match_sim.ts", "src/sim/player_state.ts", "src/sim/locomotion.ts"],
      "contract-mismatch": ["src/sim/match_sim.ts", "src/sim/kick.ts", "src/sim/input_provider.ts"],
      "requirement-dropped": ["src/sim/match_sim.ts"],
      "friction-model": ["src/sim/ball_physics.ts"],
      "double-apply": ["src/sim/match_sim.ts", "src/sim/ball_physics.ts"],
    };
    const fileList = (files) => Array.isArray(files) && files.length > 0 && files.every((f) => SOURCES.includes(f));
    const requirements = value?.requirements && typeof value.requirements === "object" && !Array.isArray(value.requirements)
      ? Object.values(value.requirements) : [];
    const order = Array.isArray(value?.landing_order) ? value.landing_order.map(String) : [];
    const at = (slice) => order.indexOf(slice);
    const slices = ["S1", "S2", "S3", "S4"];
    const orderValid = order.length === 4 && slices.every((s) => at(s) >= 0)
      && at("S1") < at("S3") && at("S2") < at("S3") && at("S3") < at("S4");
    return { requirements: value?.requirements ?? null, categoriesSorted: [...categories].sort(),
      requirementFilesKnown: requirements.length > 0 && requirements.every((r) => fileList(r?.files)),
      defectFilesKnown: defects.every((d) => fileList(d?.files)),
      defectsLocated: defects.every((d) => !(String(d?.category) in LOCATED)
        || (Array.isArray(d?.files) && d.files.some((f) => LOCATED[String(d.category)].includes(f)))),
      duplicates: categories.length - new Set(categories).size,
      unknownCategories: categories.filter((c) => !VOCABULARY.includes(c)).sort(),
      orderValid };
  } catch (error) {
    return { $error: String(error?.name) };
  }
}
