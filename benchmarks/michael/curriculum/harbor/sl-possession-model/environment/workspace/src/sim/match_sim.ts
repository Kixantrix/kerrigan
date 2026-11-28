// MatchSim - deterministic, headless-runnable simulation core.
//
// MatchSim owns all gameplay state (players, ball, score) and is advanced by
// fixed-tick calls to `tick()`. It is PURE and DETERMINISTIC: no rendering, no
// reads of presentation state, and no unseeded randomness (all random draws go
// through the seeded `SimRng`).
//
// Coordinate frame: X runs goal-to-goal (length), Z runs touchline-to-touchline
// (width); players live on that ground plane (Vector2 x = X, y = Z), the ball
// adds height Y. Team 0 attacks +X, team 1 attacks -X. Every numeric constant is
// read from the tuning JSON via MatchConfig.
//
// The scaffold establishes the fixed-tick loop, entity state and input plumbing.
// Ball aerodynamics (task 1.1, BallPhysics), player locomotion (task 1.2,
// Locomotion), kick mechanics (task 1.3, Kick) and first touch (task 1.4,
// FirstTouch) plug into it.
import { BallPhysics } from "./ball_physics.ts";
import { BallState } from "./ball_state.ts";
import { Dribble, DribbleSettings } from "./dribble.ts";
import { FirstTouch, FirstTouchSettings, TouchMode } from "./first_touch.ts";
import type { InputMap, InputProvider, PlayerInput } from "./input_provider.ts";
import { Kick, KickProfile, KickType } from "./kick.ts";
import { Locomotion } from "./locomotion.ts";
import { MatchConfig, type Tuning } from "./match_config.ts";
import { PlayerState } from "./player_state.ts";
import { SimRng } from "./sim_rng.ts";
import { SportRules } from "./sport_rules.ts";
import { SoccerRules } from "./sports/soccer_rules.ts";
import { Vector2, Vector3, clampf, maxi, snappedf } from "./vec.ts";

export const TICK_HZ = 60;
export const TICK_DELTA = 1.0 / TICK_HZ;

export type SimEvent = Record<string, unknown> & { event: string };

export class MatchSim {
  config: MatchConfig;
  // The sport supplying scoring, restarts and field rules. Defaults to soccer;
  // see multi-sport-core.md for why this is a seam rather than baked in.
  rules: SportRules;
  rng: SimRng;
  ball: BallState;
  players: PlayerState[] = [];
  score: Record<number, number> = { 0: 0, 1: 0 };
  possession_ticks: Record<number, number> = { 0: 0, 1: 0 };
  tick_count = 0;
  last_toucher_team = -1;

  // Cached tuning (pulled once so the hot loop avoids lookups).
  private _tick_delta = TICK_DELTA;
  private _team_size = 3;
  private _half_length = 20;
  private _half_width = 12.5;
  private _ball_radius = 0.11;
  private _gravity = 9.81;
  private _linear_drag = 0.15;
  private _magnus_coefficient = 0.12;
  private _spin_drag = 0.6;
  private _ground_restitution = 0.55;
  private _ground_friction = 2.5;
  private _rest_speed = 0.05;
  private _ball_max_speed = 45;
  private _player_radius = 0.4;
  private _player_max_speed = 7;
  private _sprint_multiplier = 1.35;
  private _acceleration = 30;
  private _turn_rate = 12;
  private _stamina_max = 100;
  private _stamina_drain_rate = 25;
  private _stamina_recovery_rate = 15;
  private _stamina_sprint_min = 5;
  private _control_radius = 1;
  private _reach_height = 1.6;
  private _touch_cooldown = 8;
  private _formation_depth = 8;
  private _formation_spread = 6;
  private _kick_profiles: Map<number, KickProfile> = new Map();
  private _approach_spin_factor = 1.2;
  private _max_side_spin = 14;
  private _side_spin_jitter = 0.6;
  private _first_touch: FirstTouchSettings = new FirstTouchSettings();
  private _first_touch_error_jitter = 1.0;
  private _dribble: DribbleSettings = new DribbleSettings();

  constructor(seedValue = 0, configSource: MatchConfig | Tuning | null = null, sport: SportRules | null = null) {
    this.config = configSource instanceof MatchConfig ? configSource : new MatchConfig(configSource);
    this.rules = sport !== null ? sport : new SoccerRules();
    this.rng = new SimRng(seedValue);
    this._cache_tuning();
    this.ball = new BallState();
    this._spawn_players();
    this.kickoff();
  }

  private _cache_tuning(): void {
    const c = this.config;
    this._tick_delta = 1.0 / c.get_int("match", "tick_hz", TICK_HZ);
    this._team_size = c.get_int("match", "team_size", 3);
    this._half_length = c.get_float("pitch", "length", 40.0) * 0.5;
    this._half_width = c.get_float("pitch", "width", 25.0) * 0.5;
    this._ball_radius = c.get_float("ball", "radius", 0.11);
    this._gravity = c.get_float("ball", "gravity", 9.81);
    this._linear_drag = c.get_float("ball", "linear_drag", 0.15);
    this._magnus_coefficient = c.get_float("ball", "magnus_coefficient", 0.12);
    this._spin_drag = c.get_float("ball", "spin_drag", 0.6);
    this._ground_restitution = c.get_float("ball", "ground_restitution", 0.55);
    this._ground_friction = c.get_float("ball", "ground_friction", 2.5);
    this._rest_speed = c.get_float("ball", "rest_speed", 0.05);
    this._ball_max_speed = c.get_float("ball", "max_speed", 45.0);
    this._player_radius = c.get_float("player", "radius", 0.4);
    this._player_max_speed = c.get_float("player", "max_speed", 7.0);
    this._sprint_multiplier = c.get_float("player", "sprint_multiplier", 1.35);
    this._acceleration = c.get_float("player", "acceleration", 30.0);
    this._turn_rate = c.get_float("player", "turn_rate_rad", 12.0);
    this._stamina_max = c.get_float("player", "stamina_max", 100.0);
    this._stamina_drain_rate = c.get_float("player", "stamina_drain_rate", 25.0);
    this._stamina_recovery_rate = c.get_float("player", "stamina_recovery_rate", 15.0);
    this._stamina_sprint_min = c.get_float("player", "stamina_sprint_min", 5.0);
    this._control_radius = c.get_float("player", "control_radius", 1.0);
    this._reach_height = c.get_float("player", "reach_height", 1.6);
    this._touch_cooldown = c.get_int("player", "touch_cooldown_ticks", 8);
    this._formation_depth = c.get_float("ai", "formation_depth", 8.0);
    this._formation_spread = c.get_float("ai", "formation_spread", 6.0);
    this._cache_kick_tuning();
    if (this.rules !== undefined && this.rules !== null) this.rules.configure(c);
  }

  private _cache_kick_tuning(): void {
    this._kick_profiles = new Map([
      [KickType.PASS, this._kick_profile("pass", 6.0, 16.0, 0.0, 0.6, 2.0)],
      [KickType.SHOT, this._kick_profile("shot", 14.0, 30.0, 0.8, 3.2, 6.0)],
      [KickType.LOB, this._kick_profile("lob", 5.0, 13.0, 4.0, 8.0, -4.0)],
    ]);
    this._approach_spin_factor = this.config.get_float("kick", "approach_spin_factor", 1.2);
    this._max_side_spin = this.config.get_float("kick", "max_side_spin", 14.0);
    this._side_spin_jitter = this.config.get_float("kick", "side_spin_jitter", 0.6);
    this._cache_first_touch_tuning();
  }

  private _cache_first_touch_tuning(): void {
    const c = this.config;
    const s = new FirstTouchSettings();
    s.trigger_speed = c.get_float("first_touch", "trigger_speed", s.trigger_speed);
    s.retention_poor = c.get_float("first_touch", "retention_poor", s.retention_poor);
    s.retention_good = c.get_float("first_touch", "retention_good", s.retention_good);
    s.kill_multiplier = c.get_float("first_touch", "kill_multiplier", s.kill_multiplier);
    s.knock_on_speed = c.get_float("first_touch", "knock_on_speed", s.knock_on_speed);
    s.max_error = c.get_float("first_touch", "max_error", s.max_error);
    s.reference_ball_speed = c.get_float("first_touch", "reference_ball_speed", s.reference_ball_speed);
    s.weight_orientation = c.get_float("first_touch", "weight_orientation", s.weight_orientation);
    s.weight_closing_speed = c.get_float("first_touch", "weight_closing_speed", s.weight_closing_speed);
    s.weight_ball_speed = c.get_float("first_touch", "weight_ball_speed", s.weight_ball_speed);
    s.sprint_penalty = c.get_float("first_touch", "sprint_penalty", s.sprint_penalty);
    s.cooldown_ticks = c.get_int("first_touch", "cooldown_ticks", s.cooldown_ticks);
    this._first_touch = s;
    this._first_touch_error_jitter = c.get_float("first_touch", "error_jitter", 1.0);
    this._cache_dribble_tuning();
  }

  private _cache_dribble_tuning(): void {
    const c = this.config;
    const d = new DribbleSettings();
    d.reach = c.get_float("dribble", "reach", d.reach);
    d.push_factor = c.get_float("dribble", "push_factor", d.push_factor);
    d.lead_bias = c.get_float("dribble", "lead_bias", d.lead_bias);
    d.min_player_speed = c.get_float("dribble", "min_player_speed", d.min_player_speed);
    d.max_relative_speed = c.get_float("dribble", "max_relative_speed", d.max_relative_speed);
    d.touch_interval_ticks = c.get_int("dribble", "touch_interval_ticks", d.touch_interval_ticks);
    this._dribble = d;
  }

  // One mechanic's tuning band: the `kick` section nests an object per
  // mechanic; fall back per key for partial tuning.
  private _kick_profile(
    name: string, speedMin: number, speedMax: number, loftMin: number, loftMax: number, axialSpin: number,
  ): KickProfile {
    const raw = this.config.get_value("kick", name, {});
    const band = (raw !== null && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
    const pick = (key: string, fallback: number) => Number(key in band ? band[key] : fallback);
    return new KickProfile(
      pick("speed_min", speedMin), pick("speed_max", speedMax),
      pick("loft_min", loftMin), pick("loft_max", loftMax), pick("axial_spin", axialSpin),
    );
  }

  // Re-read cached tuning after the config data has been edited in place (the
  // playable build's live-tuning overlay). Only re-reads data: a running match
  // keeps its positions, score and RNG stream.
  reload_tuning(): void {
    this._cache_tuning();
  }

  private _spawn_players(): void {
    this.players = [];
    let nextId = 0;
    for (const team of [0, 1]) {
      const dir = team === 0 ? 1.0 : -1.0;
      for (let role = 0; role < this._team_size; role += 1) {
        const p = new PlayerState();
        p.id = nextId;
        p.team = team;
        p.role = role;
        // Fan players across their defensive half; role 0 sits deepest.
        const lane = this._team_size <= 1 ? 0.0 : (role / (this._team_size - 1) - 0.5) * 2.0;
        const depth = -dir * this._formation_depth * (1.0 - role / maxi(this._team_size, 1));
        p.home = new Vector2(depth, lane * this._formation_spread);
        p.facing = new Vector2(dir, 0.0);
        p.stamina = this._stamina_max;
        this.players.push(p);
        nextId += 1;
      }
    }
  }

  // Restart play. Delegates to the sport's rules (soccer: kickoff at the centre
  // spot). Kept as a method on the sim because callers and tests treat "restart
  // the match" as a sim-level operation.
  kickoff(kickTeam = -1): void {
    this.rules.restart(this, kickTeam);
  }

  // --- Read-only helpers used by input providers ---------------------------

  opponent_goal_center(team: number): Vector2 {
    return new Vector2(team === 0 ? this._half_length : -this._half_length, 0.0);
  }

  control_radius(): number {
    return this._control_radius;
  }

  ball_radius(): number {
    return this._ball_radius;
  }

  // Merge inputs from every provider into one per-tick Map (later providers win).
  gather_inputs(providers: InputProvider[]): InputMap {
    const merged: InputMap = new Map();
    for (const provider of providers) {
      for (const [pid, input] of provider.collect(this)) merged.set(pid, input);
    }
    return merged;
  }

  // Convenience: gather inputs from providers then advance one tick.
  advance(providers: InputProvider[], delta = -1.0): SimEvent[] {
    return this.tick(this.gather_inputs(providers), delta);
  }

  // Advance the simulation exactly one fixed tick. Pure: same (state, inputs)
  // in -> same state out. Returns the discrete events that fired this tick.
  tick(inputs: InputMap, delta = -1.0): SimEvent[] {
    const dt = delta <= 0.0 ? this._tick_delta : delta;
    const events: SimEvent[] = [];
    this._update_players(inputs, dt);
    this._resolve_touches(inputs, events);
    this._integrate_ball(dt);
    this._resolve_bounds(events);
    this._track_possession();
    this.tick_count += 1;
    return events;
  }

  private _update_players(inputs: InputMap, dt: number): void {
    for (const p of this.players) {
      if (p.touch_cooldown > 0) p.touch_cooldown -= 1;
      let move = Vector2.ZERO;
      let aim = Vector2.ZERO;
      let sprint = false;
      const cmd = inputs.get(p.id);
      if (cmd !== undefined) {
        move = cmd.move ?? Vector2.ZERO;
        aim = cmd.aim ?? Vector2.ZERO;
        sprint = Boolean(cmd.sprint ?? false);
      }
      Locomotion.update(
        p, move, aim, sprint, dt,
        this._player_max_speed, this._sprint_multiplier, this._acceleration, this._turn_rate,
        this._stamina_max, this._stamina_drain_rate, this._stamina_recovery_rate, this._stamina_sprint_min,
      );
      this._clamp_to_pitch(p);
    }
  }

  private _clamp_to_pitch(p: PlayerState): void {
    const lx = this._half_length - this._player_radius;
    const lz = this._half_width - this._player_radius;
    p.position = new Vector2(clampf(p.position.x, -lx, lx), clampf(p.position.y, -lz, lz));
  }

  private _resolve_touches(inputs: InputMap, events: SimEvent[]): void {
    // The player closest to the ball wins the touch; ties break by id so the
    // result stays deterministic, but distance decides first.
    if (this.ball.position.y > this._reach_height) return;
    const ballGround = new Vector2(this.ball.position.x, this.ball.position.z);
    const reach = this._control_radius + this._ball_radius + this._player_radius;
    let winner: PlayerState | null = null;
    let winnerDistance = Infinity;
    for (const p of this.players) {
      if (p.touch_cooldown > 0) continue;
      if (!inputs.has(p.id)) continue;
      const distance = p.position.distanceTo(ballGround);
      if (distance > reach) continue;
      if (distance < winnerDistance) {
        winner = p;
        winnerDistance = distance;
      }
    }
    if (winner === null) return;
    const cmd = inputs.get(winner.id) as PlayerInput;
    if (Boolean(cmd.kick ?? false)) {
      this._kick_ball(winner, cmd, events);
      this._commit_challengers(winner, ballGround, reach);
    } else {
      this._receive_ball(winner, cmd, events);
    }
  }

  // Receive a moving ball (task 1.4). A player in the ball's path who is not
  // striking it still meets it, through the FirstTouch model. A ball already
  // trickling below `trigger_speed` needs no touch simulating.
  private _receive_ball(p: PlayerState, cmd: PlayerInput, events: SimEvent[]): void {
    const ground = new Vector2(this.ball.velocity.x, this.ball.velocity.z);
    const speed = ground.length();
    // How fast is the ball moving *relative to the player*? A ball running just
    // ahead of a sprinter, or a still ball they are running onto, are both
    // dribbling situations; only a ball genuinely flying past them is a
    // reception. Dribbling gets first refusal.
    const relativeSpeed = ground.sub(p.velocity).length();
    if (Dribble.can_touch(this._dribble, p.position, p.velocity.length(), this._ball_ground(), relativeSpeed)) {
      this._dribble_ball(p, events);
      return;
    }
    if (speed < this._first_touch.trigger_speed) return;
    const mode = FirstTouch.mode_from_input(Math.trunc(Number(cmd.touch_mode ?? TouchMode.CUSHION)));
    const quality = FirstTouch.quality_for(
      this._first_touch, p.facing, p.velocity, ground.normalized(), speed,
      this._player_max_speed, p.sprinting,
    );
    const result = FirstTouch.receive(
      this._first_touch, mode, quality, p.facing, this.ball.velocity, this.ball.angular_velocity,
      this.rng.jitter(this._first_touch_error_jitter),
    );
    this.ball.velocity = result.velocity;
    this.ball.angular_velocity = result.angular_velocity;
    p.touch_cooldown = this._first_touch.cooldown_ticks;
    this.last_toucher_team = p.team;
    events.push({
      event: "touch",
      player: p.id,
      team: p.team,
      touch: FirstTouch.mode_name(mode),
      quality: snappedf(quality, 0.001),
    });
  }

  // A challenge commits every player already contesting the ball (they lunged
  // and were beaten), so the kick can't be instantly returned.
  private _commit_challengers(kicker: PlayerState, ballGround: Vector2, reach: number): void {
    for (const p of this.players) {
      if (p === kicker) continue;
      if (p.position.distanceTo(ballGround) <= reach) {
        p.touch_cooldown = maxi(p.touch_cooldown, this._touch_cooldown);
      }
    }
  }

  // Strike the ball with whichever mechanic the input requested (task 1.3).
  // Aim comes from the input when supplied, otherwise from the player's
  // facing, otherwise toward the opponent goal. The seeded side-spin jitter is
  // drawn here so Kick.build stays pure.
  private _kick_ball(p: PlayerState, cmd: PlayerInput, events: SimEvent[]): void {
    const kickType = Kick.type_from_input(Math.trunc(Number(cmd.kick_type ?? KickType.PASS)));
    const power = clampf(Number(cmd.kick_power ?? 1.0), 0.0, 1.0);
    let aim: Vector2 = cmd.aim ?? Vector2.ZERO;
    if (aim.length() < 0.0001) aim = p.facing;
    if (aim.length() < 0.0001) aim = this.opponent_goal_center(p.team).sub(p.position);
    const profile = this._kick_profiles.get(kickType) as KickProfile;
    const impulse = Kick.build(
      profile, aim, power, p.velocity,
      this._approach_spin_factor, this._max_side_spin,
      this.rng.jitter(this._side_spin_jitter),
    );
    this.ball.velocity = impulse.velocity;
    this.ball.angular_velocity = impulse.angular_velocity;
    p.touch_cooldown = this._touch_cooldown;
    this.last_toucher_team = p.team;
    events.push({ event: "kick", player: p.id, team: p.team, kick: Kick.type_name(kickType), power });
  }

  // Knock a loose ball into the space ahead (dribbling, architecture.md). Not
  // possession: the ball stays a free physics object between touches, so an
  // opponent standing in the way can take it.
  private _dribble_ball(p: PlayerState, events: SimEvent[]): void {
    this.ball.velocity = Dribble.touch_velocity(this._dribble, p.velocity, p.facing, this.ball.velocity.y);
    this.ball.angular_velocity = Vector3.ZERO;
    p.touch_cooldown = this._dribble.touch_interval_ticks;
    this.last_toucher_team = p.team;
    events.push({ event: "dribble", player: p.id, team: p.team });
  }

  private _ball_ground(): Vector2 {
    return new Vector2(this.ball.position.x, this.ball.position.z);
  }

  private _integrate_ball(dt: number): void {
    BallPhysics.apply_forces(this.ball, dt, this._gravity, this._linear_drag, this._magnus_coefficient, this._spin_drag);
    BallPhysics.resolve_ground_contact(
      this.ball, dt, this._ball_radius, this._ground_restitution, this._ground_friction, this._rest_speed,
    );
    BallPhysics.clamp_speed(this.ball, this._ball_max_speed);
  }

  private _resolve_bounds(events: SimEvent[]): void {
    this.rules.resolve_bounds(this, events);
  }

  private _track_possession(): void {
    if (this.last_toucher_team >= 0) this.possession_ticks[this.last_toucher_team] += 1;
  }

  // Deterministic digest of the full sim state. Two runs with the same seed and
  // inputs must produce identical digests - the basis of the golden-replay check.
  state_digest(): number {
    const parts: string[] = [];
    parts.push(`t=${this.tick_count}`);
    parts.push(`s=${this.score[0]}:${this.score[1]}`);
    parts.push(MatchSim._quantize_vec3(this.ball.position));
    parts.push(MatchSim._quantize_vec3(this.ball.velocity));
    parts.push(MatchSim._quantize_vec3(this.ball.angular_velocity));
    for (const p of this.players) {
      parts.push(`${p.id}|${MatchSim._quantize_vec2(p.position)}|${MatchSim._quantize_vec2(p.velocity)}|`
        + `${MatchSim._quantize_vec2(p.facing)}|${p.stamina.toFixed(4)}`);
    }
    return MatchSim._hash(parts.join("\n"));
  }

  // Godot String.hash(): djb2 over the string's code points, as uint32.
  private static _hash(text: string): number {
    let hash = 5381;
    for (const ch of text) hash = (Math.imul(hash, 33) + (ch.codePointAt(0) as number)) >>> 0;
    return hash;
  }

  private static _quantize_vec3(v: Vector3): string {
    return `${v.x.toFixed(4)},${v.y.toFixed(4)},${v.z.toFixed(4)}`;
  }

  private static _quantize_vec2(v: Vector2): string {
    return `${v.x.toFixed(4)},${v.y.toFixed(4)}`;
  }

  // Invariant check: all entity state is finite (no NaN/inf).
  state_is_finite(): boolean {
    if (!this.ball.has_finite_state()) return false;
    return this.players.every((p) => p.has_finite_state());
  }
}
