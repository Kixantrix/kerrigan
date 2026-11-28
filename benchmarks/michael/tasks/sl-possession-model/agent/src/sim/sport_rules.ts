// SportRules - the contract a sport supplies to MatchSim.
//
// MatchSim owns what every sport shares: a deterministic fixed-tick loop,
// entities, locomotion, ball physics and input plumbing. It should not know
// what a goal is, how a match restarts, or how points are awarded - those are
// sport rules, and they are the pieces that differ most between soccer,
// American football and basketball (multi-sport-core.md, stage 1).
//
// Implementations must preserve the sim's binding invariants: no unseeded
// randomness (draw from `sim.rng`), no engine or rendering calls.
import type { MatchConfig } from "./match_config.ts";
import type { MatchSim, SimEvent } from "./match_sim.ts";

export class SportRules {
  // Cache whatever geometry and constants the rules need from tuning data.
  // Called by MatchSim whenever tuning is (re)loaded, so live edits apply.
  configure(_config: MatchConfig): void {}

  // Resolve the ball leaving the field of play: scoring, rebounds, restarts.
  // Called once per tick after the ball has been integrated.
  resolve_bounds(_sim: MatchSim, _events: SimEvent[]): void {}

  // Put the match into its starting state (kickoff, snap, tip-off). `team` is
  // the side restarting; -1 means "keep the current one".
  restart(_sim: MatchSim, _team: number): void {}
}
