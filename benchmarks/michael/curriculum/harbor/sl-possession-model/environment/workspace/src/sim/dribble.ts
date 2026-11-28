// Dribble - carrying the ball as repeated physics touches.
//
// architecture.md is explicit about the model: "The ball is never parented to
// a player. 'Dribbling' = repeated small touches by the locomotion system,
// each one a physics impulse." So there is no possession flag and no ball
// attachment anywhere in the sim - a dribbling player is simply one who keeps
// knocking a loose ball into the space ahead of them, and an opponent can take
// it at any moment because it is always a free physics object.
//
// Pure and stateless like the other sim models; all constants come from tuning
// JSON.
import { Vector2, Vector3, clampf, minf } from "./vec.ts";

// Tuning band for carrying the ball.
export class DribbleSettings {
  // How close the ball must be for a dribble touch to be available.
  reach = 1.3;
  // Ball speed after a touch, as a multiple of the player's speed.
  push_factor = 1.25;
  // Blend between the player's run direction (0) and where they are facing (1).
  lead_bias = 0.55;
  // Below this the player is not really moving, so the ball is left alone.
  min_player_speed = 0.6;
  // Above this *relative* speed the ball is getting away from the player.
  max_relative_speed = 9.0;
  // Ticks between touches. Longer means fewer, bigger knocks.
  touch_interval_ticks = 7;
}

export const Dribble = {
  // Is this player in a position to knock the ball on? `relativeSpeed` is the
  // ball's speed relative to the player, not its absolute speed.
  can_touch(
    settings: DribbleSettings, playerPosition: Vector2, playerSpeed: number, ballGround: Vector2,
    relativeSpeed: number,
  ): boolean {
    if (playerSpeed < settings.min_player_speed) return false;
    if (relativeSpeed > settings.max_relative_speed) return false;
    return playerPosition.distanceTo(ballGround) <= settings.reach;
  },

  // The ball velocity produced by one dribble touch: direction blends the run
  // with the body orientation; a dribble touch never lifts the ball.
  touch_velocity(settings: DribbleSettings, playerVelocity: Vector2, facing: Vector2, ballHeight: number): Vector3 {
    const run = playerVelocity.length() > 0.0001 ? playerVelocity.normalized() : Vector2.ZERO;
    const look = facing.length() > 0.0001 ? facing.normalized() : run;
    const weight = clampf(settings.lead_bias, 0.0, 1.0);
    let direction = run.add(look.sub(run).mul(weight)).normalized();
    if (direction.length() < 0.0001) direction = run;
    const speed = playerVelocity.length() * settings.push_factor;
    return new Vector3(direction.x * speed, minf(ballHeight, 0.0), direction.y * speed);
  },
};
