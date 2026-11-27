// InputProvider - the input abstraction feeding MatchSim.
//
// Every input source (local pads, network peers, AI bots, recorded replays)
// implements `collect(sim)` and returns a per-tick Map keyed by player id. The
// sim stays agnostic about where inputs come from - it receives one merged Map
// per tick. Each input entry is a PlayerInput (see the plan's input contract):
//   move: Vector2 (desired ground-plane direction, magnitude <= 1)
//   aim: Vector2 (desired facing; zero means "keep current facing")
//   sprint: boolean, kick: boolean
//   kick_type: number (KickType: 0 PASS, 1 SHOT, 2 LOB)
//   kick_power: number (0..1 button-hold charge)
//   touch_mode: number (TouchMode: 0 CUSHION, 1 KILL, 2 KNOCK_ON - applied
//     when receiving rather than striking)
import { KickType } from "./kick.ts";
import { TouchMode } from "./first_touch.ts";
import type { PlayerState } from "./player_state.ts";
import { Vector2, clampf, maxf } from "./vec.ts";

export type PlayerInput = {
  move: Vector2;
  aim: Vector2;
  sprint: boolean;
  kick: boolean;
  kick_type: number;
  kick_power: number;
  touch_mode: number;
};

export type InputMap = Map<number, PlayerInput>;

// Deep copy of one input entry (GDScript Dictionary.duplicate(true)).
export function clone_input(input: PlayerInput): PlayerInput {
  const copy = { ...input } as PlayerInput;
  if (input.move instanceof Vector2) copy.move = input.move.copy();
  if (input.aim instanceof Vector2) copy.aim = input.aim.copy();
  return copy;
}

export function clone_inputs(inputs: InputMap): InputMap {
  const out: InputMap = new Map();
  for (const [id, input] of inputs) out.set(id, clone_input(input));
  return out;
}

export class InputProvider {
  // Player ids this provider is responsible for. Empty means "all".
  player_ids: number[];

  constructor(ids: number[] = []) {
    this.player_ids = ids;
  }

  // Override: return a Map { player_id: input } for owned players.
  collect(_sim: any): InputMap {
    return new Map();
  }

  static make_input(
    move: Vector2,
    sprint = false,
    kick = false,
    aim: Vector2 = Vector2.ZERO,
    kickType: number = KickType.PASS,
    kickPower = 1.0,
    touchMode: number = TouchMode.CUSHION,
  ): PlayerInput {
    if (move.length() > 1) move = move.normalized();
    if (aim.length() > 1) aim = aim.normalized();
    return {
      move,
      aim,
      sprint,
      kick,
      kick_type: kickType,
      kick_power: clampf(kickPower, 0, 1),
      touch_mode: touchMode,
    };
  }

  static idle(): PlayerInput {
    return InputProvider.make_input(Vector2.ZERO, false, false);
  }
}

// AI bot: chases the ball with the nearest player, holds formation with the
// rest, and requests a kick toward the opponent goal when in control range.
// All randomness is drawn from the sim's seeded RNG so matches stay reproducible.
export class AiProvider extends InputProvider {
  team: number;

  constructor(teamId: number, ids: number[] = []) {
    super(ids);
    this.team = teamId;
  }

  collect(sim: any): InputMap {
    const out: InputMap = new Map();
    const owned = this.owned_players(sim);
    if (owned.length === 0) return out;
    const ballPos = new Vector2(sim.ball.position.x, sim.ball.position.z);
    const chaser = this.nearest_to_ball(owned, ballPos);
    const jitter = sim.config.get_float("ai", "chase_jitter", 0.1);
    const control = sim.control_radius() + sim.ball_radius();
    for (const p of owned) {
      if (p === chaser) {
        let dir = ballPos.sub(p.position);
        dir = dir.add(new Vector2(sim.rng.jitter(jitter), sim.rng.jitter(jitter)));
        const sprint = p.position.distanceTo(ballPos) > 4.0;
        const kick = p.position.distanceTo(ballPos) <= control;
        // The chaser aims at the target goal while steering toward the ball.
        const goal: Vector2 = sim.opponent_goal_center(this.team);
        const aim = goal.sub(p.position);
        // Shoot when the goal is in range, otherwise play a pass upfield.
        const goalDistance = p.position.distanceTo(goal);
        const shootRange = sim.config.get_float("ai", "shoot_range", 14.0);
        let kickType: number = KickType.PASS;
        let kickPower = 0.6;
        if (goalDistance <= shootRange) {
          kickType = KickType.SHOT;
          kickPower = clampf(goalDistance / maxf(shootRange, 0.001), 0.35, 1.0);
        }
        out.set(p.id, InputProvider.make_input(dir, sprint, kick, aim, kickType, kickPower));
      } else {
        // Off the ball: run to the formation anchor while watching the ball.
        out.set(p.id, InputProvider.make_input(p.home.sub(p.position), false, false, ballPos.sub(p.position)));
      }
    }
    return out;
  }

  owned_players(sim: any): PlayerState[] {
    return sim.players.filter((p: PlayerState) => p.team === this.team
      && (this.player_ids.length === 0 || this.player_ids.includes(p.id)));
  }

  nearest_to_ball(owned: PlayerState[], ballPos: Vector2): PlayerState {
    let best = owned[0];
    let bestD = best.position.distanceSquaredTo(ballPos);
    for (const p of owned) {
      const d = p.position.distanceSquaredTo(ballPos);
      if (d < bestD) {
        bestD = d;
        best = p;
      }
    }
    return best;
  }
}

// Scripted/local provider: replays a fixed input per player, or a per-tick
// table keyed by tick. Stands in for local gamepads and recorded-input replays.
export class ScriptedProvider extends InputProvider {
  script_inputs: InputMap = new Map();
  per_tick: Map<number, InputMap> = new Map();

  collect(sim: any): InputMap {
    const table = this.per_tick.get(sim.tick_count);
    return clone_inputs(table !== undefined ? table : this.script_inputs);
  }
}

// Network provider (Phase 3 stub): serves inputs pushed by remote peers for a
// given tick, defaulting to idle when a packet has not arrived yet.
export class NetworkProvider extends InputProvider {
  private buffer: Map<number, InputMap> = new Map();

  push(tick: number, inputs: InputMap): void {
    this.buffer.set(tick, inputs);
  }

  collect(sim: any): InputMap {
    const buffered = this.buffer.get(sim.tick_count);
    if (buffered !== undefined) return buffered;
    const out: InputMap = new Map();
    for (const pid of this.player_ids) out.set(pid, InputProvider.idle());
    return out;
  }
}
