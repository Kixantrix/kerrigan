# Phase 1 plan: core mechanics on the MatchSim scaffold

The headless `MatchSim` core (task 0.4) and the golden-replay determinism
harness (task 0.5) have landed. Phase 1 tasks 1.1–1.4 were split into four
slices and dispatched to parallel agents from the scaffold, with the briefs in
this folder. All four branches have landed in `src/sim/`, but each slice only
passed its own unit checks; nobody has integrated them. This plan is
authoritative wherever a slice brief disagrees with it.

The code is a TypeScript port of the GDScript sim. Units are metres, seconds,
m/s and rad/s. Ground-plane vectors are `Vector2(x, z)`; the ball adds height
`y`. All constants come from `data/tuning.json` through `MatchConfig`.

## Slices and dependencies

| Slice | Task | Delivers | Depends on |
|---|---|---|---|
| S1 | 1.1 ball physics | `ball_physics.ts`, ball spin in `ball_state.ts` | core |
| S2 | 1.2 locomotion | `locomotion.ts`, facing/stamina in `player_state.ts` | core |
| S3 | 1.3 kick mechanics | `kick.ts` | S1, S2 |
| S4 | 1.4 first touch | `first_touch.ts` | S3 |

Core: `vec.ts`, `sim_rng.ts`, `match_config.ts`, `cli.ts` and
`data/tuning.json` are read-only; `match_sim.ts`, `input_provider.ts` and
`match_log.ts` are shared integration points.

## Requirements

- **R1 Deterministic replay.** A match is a pure function of its seed, its
  tuning and its per-tick inputs. Running `runMatchLog` twice with the same
  seed and the same inputs must produce byte-identical JSONL, both for AI
  matches and for a recorded per-tick input table replayed through
  `ScriptedProvider.per_tick`. Every random draw in the simulation comes from
  the match's seeded `sim.rng`, so different seeds give different AI matches.
- **R2 Replay records cover all simulated state.** Every snapshot record
  carries the ball's position, velocity and spin (angular velocity) and every
  player's position, velocity, facing, stamina and sprinting flag.
  `state_digest()` covers the ball's position, velocity and spin and every
  player's position, velocity, facing and stamina. A change to any of these
  (larger than the digest's 4-decimal quantisation) changes the digest.
- **R3 Ball physics (1.1).** Every tick the ball gets gravity, Magnus
  (`magnus_coefficient * (spin x velocity)`), linear drag and spin decay, and
  then its position advances exactly once by the updated velocity times `dt`.
  On the ground it bounces with `ground_restitution`, and rolling resistance
  slows its ground speed by a constant deceleration of `ground_friction`
  m/s² (independent of speed; it stops at zero). End-line and touchline walls
  rebound with `wall_restitution`. Ball speed is clamped to `max_speed`.
- **R4 Locomotion (1.2).** Movement is analog up to `player.max_speed`.
  Sprinting multiplies top speed by `sprint_multiplier` only while stamina is
  strictly greater than `stamina_sprint_min`. Stamina is measured in points
  on the tuning's scale: every player starts a match with `stamina_max`
  points, sprinting drains `stamina_drain_rate` points per second, and
  otherwise stamina recovers `stamina_recovery_rate` points per second up to
  `stamina_max`. Facing turns toward the aim input at up to `turn_rate_rad`
  rad/s; a zero aim keeps the current facing.
- **R5 Kick mechanics (1.3).** When the touch winner's input has
  `kick: true`, the player strikes with the input's `kick_type` and
  `kick_power`: speed and loft interpolate across that mechanic's tuning band
  by `kick_power` (clamped to 0..1); an unrecognised `kick_type` is a pass.
  The strike direction is the input's aim, else the player's facing, else
  toward the opponent goal. A `kick` event is emitted.
- **R6 First touch (1.4).** When the touch winner's input has no kick and the
  ball's ground speed is at least `first_touch.trigger_speed`, the player
  receives the ball through `FirstTouch` with the input's `touch_mode`: the
  ball takes the result's velocity and spin, the player's touch cooldown is
  set to `first_touch.cooldown_ticks`, and a `touch` event is emitted. The
  lateral mis-control bias passed to `FirstTouch.receive` is drawn from
  `sim.rng` as a jitter of magnitude `first_touch.error_jitter`. Below the
  trigger speed nothing happens.
- **R7 Scaffold behavior is preserved.** Touch arbitration, goals, restarts
  and wall rebounds keep working as in the scaffold (see "Touches" and
  "Goals and restarts" below).

## Requirement ownership

| Requirement | Implemented in |
|---|---|
| R1 | `match_sim.ts` (all draws through `sim.rng`) |
| R2 | `match_sim.ts` (`state_digest`), snapshot dictionaries |
| R3 | `ball_physics.ts`, `match_sim.ts` |
| R4 | `locomotion.ts`, player spawn in `match_sim.ts` |
| R5 | `kick.ts`, `match_sim.ts` |
| R6 | `first_touch.ts`, `match_sim.ts` |
| R7 | `match_sim.ts` |

## Roster

The scaffold spawns `team_size` players per team: `players[i].id === i`,
ids `0..team_size-1` are team 0 (attacking +x) and the rest team 1
(attacking -x). This stays as it is.

## Input contract

`MatchSim.tick(inputs)` takes a `Map<playerId, PlayerInput>`. A
`PlayerInput` is `{ move: Vector2, aim: Vector2, sprint: boolean,
kick: boolean, kick_type: number (0 pass, 1 shot, 2 lob), kick_power: number
(0..1), touch_mode: number (0 cushion, 1 kill, 2 knock_on) }`.

## Event contract

`tick()` returns the events that fired this tick:

- `{ event: "kick", player, team, kick: "pass" | "shot" | "lob", power }`
  (`power` is the clamped `kick_power` used);
- `{ event: "touch", player, team, touch: "cushion" | "kill" | "knock_on",
  quality }` (`quality` rounded to 0.001);
- `{ event: "goal", team, score }` (`score` is a copy of the score after the
  goal, keyed by team).

## Tick order

1. Players: decrement touch cooldowns, apply locomotion, clamp to the pitch.
2. Touches (see below).
3. Ball integration (R3).
4. Bounds: goals and wall rebounds.
5. Possession: the team that last kicked or received the ball (none since
   the last restart) is credited one tick in `possession_ticks`; then
   `tick_count` increments.

## Touches

A touch happens only while the ball is at or below `reach_height`. Touch
cooldowns count down by one in step 1 of every tick; eligible players have a
cooldown of zero after that step, have an input entry this tick, and are
within `control_radius + ball_radius + player.radius` of the ball on the
ground plane. The closest eligible player wins; an exact tie goes to the lower
id. Players without an input entry this tick never touch the ball. After a
kick, the kicker's cooldown is set to `touch_cooldown_ticks` and every other
player within that reach gets a cooldown of at least `touch_cooldown_ticks`.

## Goals and restarts

When the ball reaches an end line (`|x| >= length/2 - ball radius`) inside
the goal mouth (`|z| < goal_width/2` and below `goal_height`), the attacking
team scores, a `goal` event is emitted and the match restarts: the ball
returns to the centre spot at rest, every player returns to their home
position, and the conceding team kicks off (the scoring team's players get a
`kickoff_reset_ticks` touch cooldown, the conceding team's none). Outside the
goal mouth the ball rebounds off the wall.
