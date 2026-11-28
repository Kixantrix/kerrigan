# Implement: an explicit ball-possession model for the match sim

`src/sim/` is a deterministic, fixed-tick match simulation (a faithful
TypeScript port of the game's GDScript core) that runs under Node 24 with
built-in type stripping and no npm packages. It plays soccer, whose design rule
is that the ball is never attached to a player: dribbling is repeated touches
on a free physics object (`dribble.ts`). Sports plug in through `SportRules`
(`sport_rules.ts`, soccer in `sports/soccer_rules.ts`).

`docs/multi-sport-core.md` explains why carrying sports (American football,
basketball) need more than that. Implement **stage 3 of its staged plan, the
explicit possession state**, so that a sport can hold, carry and release the
ball while soccer stays exactly as it is.

## Requirements

1. **`src/sim/possession.ts`** (currently an empty stub) exports:
   - `PossessionState`: an object with the keys `LOOSE`, `HELD` and
     `IN_FLIGHT`, whose three values are distinct;
   - class `Possession`, with fields `state` (a `PossessionState` value),
     `holder_id` (the carrying player's id, `-1` when nobody carries it) and
     `team` (the side deemed to have possession, `-1` when neutral). A new
     instance is `LOOSE` with `holder_id` and `team` both `-1`. Methods:
     - `is_held()`: true exactly when the state is `HELD`;
     - `hold(playerId, team)`: `HELD`, carried by that player for that side;
     - `release(byTeam = -1)`: `IN_FLIGHT`, no holder;
     - `set_loose(byTeam = -1)`: `LOOSE`, no holder;
     - for `release` and `set_loose`, `team` becomes `byTeam` when it is
       `>= 0` and is otherwise kept;
     - `clear()`: `LOOSE` and neutral (`holder_id` and `team` both `-1`);
     - `to_dict()`: `{ state, holder, team }`.
2. **`MatchSim`** gets a public `possession` field (a `Possession`, starting
   neutral and `LOOSE`) and a method `player_by_id(id)` returning that player,
   or `null` when there is none. Sports (and tests) change possession by
   calling the methods above on `sim.possession`. The core itself changes it
   only as in items 3 and 5.
3. **While the ball is `HELD`**, on every tick:
   - The ball is not integrated: no forces, ground contact or speed clamp.
     Instead it rides with its holder. Its position is the holder's ground
     position plus the holder's normalized `facing` times the carry offset, at
     a height equal to the carry height (ground `x` → world `x`, ground `y` →
     world `z`; no lead when `facing` has length ≤ 0.0001). Its velocity is
     the holder's velocity on the ground with zero vertical component, and
     its spin is zero. The holder's position, facing and velocity are their
     values after this tick's player update.
   - The carry offset and height come from a `carry` tuning section, keys
     `offset` (default `0.45`) and `height` (default `1.0`). They are re-read
     by `reload_tuning()` like other tuning.
   - The touch models (kick, first-touch reception, dribble) do not run on
     that tick. Taking the ball off a carrier is tackling's job, which is out
     of scope.
   - If no player has the holder's id, the ball is dropped:
     `possession.set_loose()`, keeping `team`.
4. **`LOOSE` and `IN_FLIGHT`** balls are physics-driven and can be touched
   exactly as before. An `IN_FLIGHT` ball behaves identically to a `LOOSE` one
   in every respect except its recorded state. So after `set_loose` or
   `release`, the ball moves on under ball physics from the velocity the
   carry gave it, which means a fumble inherits the carrier's momentum.
5. **Restarts clear possession** to neutral `LOOSE`, both an explicit
   `kickoff()` and the kickoff after a goal.
6. **Soccer is untouched.** Soccer never changes possession, so it stays
   neutral `LOOSE` for a whole match. Every match that does not use
   possession produces exactly the same states, events, state digests and
   match logs as before this change.

You may edit only `src/sim/possession.ts`, `src/sim/match_sim.ts`,
`src/sim/sports/soccer_rules.ts` and `data/tuning.json`. Keep every existing
export and signature. The sim's invariants still hold: no unseeded randomness
and no rendering or engine calls.

## Grading

Hidden checks build the sim from `src/sim/` and drive `sim.possession`
directly. They use held-out seeds, tuning and inputs, check the requirements
above by outcome, and compare soccer matches with their state before this
change. Read/write and tool/network boundaries are in `policy.json`.
