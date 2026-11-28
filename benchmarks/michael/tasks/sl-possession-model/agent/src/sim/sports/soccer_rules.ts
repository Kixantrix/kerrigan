// SoccerRules - association football rules for MatchSim.
//
// Cage/street rules per spec.md's non-goals: no fouls, offside or cards. The
// ball rebounds off the touchlines rather than going out, and a goal restarts
// play at the centre spot. Everything here used to live inside MatchSim
// (multi-sport-core.md stage 1); the behaviour is unchanged.
import { BallPhysics } from "../ball_physics.ts";
import type { MatchConfig } from "../match_config.ts";
import type { MatchSim, SimEvent } from "../match_sim.ts";
import { SportRules } from "../sport_rules.ts";
import { Vector2, Vector3, clampf } from "../vec.ts";

export class SoccerRules extends SportRules {
  // Side taking the next kickoff.
  kickoff_team = 0;

  private _half_length = 20.0;
  private _half_width = 12.5;
  private _goal_half_width = 3.5;
  private _goal_height = 2.5;
  private _wall_restitution = 0.6;
  private _ball_radius = 0.11;
  private _spawn_height = 0.11;
  private _kickoff_reset_ticks = 45;

  override configure(config: MatchConfig): void {
    this._half_length = config.get_float("pitch", "length", 40.0) * 0.5;
    this._half_width = config.get_float("pitch", "width", 25.0) * 0.5;
    this._goal_half_width = config.get_float("pitch", "goal_width", 7.0) * 0.5;
    this._goal_height = config.get_float("pitch", "goal_height", 2.5);
    this._wall_restitution = config.get_float("pitch", "wall_restitution", 0.6);
    this._ball_radius = config.get_float("ball", "radius", 0.11);
    this._spawn_height = config.get_float("ball", "spawn_height", this._ball_radius);
    this._kickoff_reset_ticks = config.get_int("match", "kickoff_reset_ticks", 45);
  }

  override resolve_bounds(sim: MatchSim, events: SimEvent[]): void {
    const ball = sim.ball;
    const maxX = this._half_length - this._ball_radius;
    const maxZ = this._half_width - this._ball_radius;
    // End lines: goal if within the mouth, otherwise a cage-wall rebound.
    if (Math.abs(ball.position.x) >= maxX) {
      const attackingTeam = ball.position.x > 0.0 ? 0 : 1;
      const inGoal = Math.abs(ball.position.z) < this._goal_half_width && ball.position.y < this._goal_height;
      if (inGoal) {
        this._score_goal(sim, attackingTeam, events);
        return;
      }
      const pos = ball.position;
      ball.position = new Vector3(clampf(pos.x, -maxX, maxX), pos.y, pos.z);
      const xNormal = new Vector3(ball.position.x < 0.0 ? 1.0 : -1.0, 0.0, 0.0);
      BallPhysics.bounce(ball, xNormal, this._wall_restitution);
    }
    // Touchline walls (cage rebound).
    if (Math.abs(ball.position.z) >= maxZ) {
      const pos = ball.position;
      ball.position = new Vector3(pos.x, pos.y, clampf(pos.z, -maxZ, maxZ));
      const zNormal = new Vector3(0.0, 0.0, ball.position.z < 0.0 ? 1.0 : -1.0);
      BallPhysics.bounce(ball, zNormal, this._wall_restitution);
    }
  }

  private _score_goal(sim: MatchSim, team: number, events: SimEvent[]): void {
    sim.score[team] += 1;
    events.push({ event: "goal", team, score: { ...sim.score } });
    // Conceding team restarts (real-football kickoff).
    this.restart(sim, 1 - team);
  }

  // Reset ball to centre and players to their formation anchors (start /
  // post-goal). The kickoff team plays the first ball: opponents are held by a
  // short standoff cooldown, mirroring a real restart.
  override restart(sim: MatchSim, team: number): void {
    if (team >= 0) this.kickoff_team = team;
    sim.ball.reset(this._spawn_height);
    for (const p of sim.players) {
      p.position = p.home.copy();
      p.velocity = Vector2.ZERO;
      p.touch_cooldown = p.team === this.kickoff_team ? 0 : this._kickoff_reset_ticks;
    }
    sim.last_toucher_team = -1;
  }
}
