// FirstTouch - how a player receives a moving ball (task 1.4, "the core mechanic").
//
// A continuous quality score decides how much incoming momentum the player
// kills and how far the ball squirts away when they get it wrong.
//
// Quality: three factors normalised to 0..1 and combined by tuning weights -
// orientation (facing into the oncoming ball), closing speed (standing still
// is easiest; sprinting costs an extra penalty) and ball speed.
//
// Outcome: quality selects `retention` (speed surviving the touch), shaped by
// the requested mode - CUSHION (default), KILL (multiplies retention down) or
// KNOCK_ON (push along the player's facing at a quality-scaled speed). A
// failed touch also deflects laterally by `errorBias * max_error * (1 - q)`;
// `errorBias` is supplied by the caller (MatchSim draws it from the seeded
// RNG) so this module stays pure.
import { Vector2, Vector3, clampf, lerpf, minf } from "./vec.ts";

export const TouchMode = { CUSHION: 0, KILL: 1, KNOCK_ON: 2 } as const;

export class FirstTouchSettings {
  trigger_speed = 1.0;
  retention_poor = 0.85;
  retention_good = 0.12;
  kill_multiplier = 0.25;
  knock_on_speed = 5.0;
  max_error = 4.0;
  reference_ball_speed = 18.0;
  weight_orientation = 0.5;
  weight_closing_speed = 0.3;
  weight_ball_speed = 0.2;
  sprint_penalty = 0.15;
  cooldown_ticks = 6;
}

export class FirstTouchResult {
  velocity: Vector3;
  angular_velocity: Vector3;
  quality: number;
  mode: number;

  constructor(velocity: Vector3, angularVelocity: Vector3, quality: number, mode: number) {
    this.velocity = velocity;
    this.angular_velocity = angularVelocity;
    this.quality = quality;
    this.mode = mode;
  }
}

export class FirstTouch {
  static quality_for(
    settings: FirstTouchSettings,
    facing: Vector2,
    velocity: Vector2,
    ballDirection: Vector2,
    ballSpeed: number,
    playerMaxSpeed: number,
    sprinting: boolean,
  ): number {
    let orientation = 0.5;
    if (facing.length() > 0.0001 && ballDirection.length() > 0.0001) {
      orientation = (facing.normalized().dot(ballDirection.normalized().neg()) + 1) * 0.5;
    }
    let speedNorm = 0;
    if (playerMaxSpeed > 0.0001) speedNorm = clampf(velocity.length() / playerMaxSpeed, 0, 1);
    let ballNorm = 0;
    if (settings.reference_ball_speed > 0.0001) {
      ballNorm = clampf(ballSpeed / settings.reference_ball_speed, 0, 1);
    }
    let score = settings.weight_orientation * orientation
      + settings.weight_closing_speed * (1 - speedNorm)
      + settings.weight_ball_speed * (1 - ballNorm);
    if (sprinting) score -= settings.sprint_penalty;
    return clampf(score, 0, 1);
  }

  static receive(
    settings: FirstTouchSettings,
    mode: number,
    quality: number,
    facing: Vector2,
    ballVelocity: Vector3,
    ballSpin: Vector3 = Vector3.ZERO,
    errorBias = 0,
  ): FirstTouchResult {
    const q = clampf(quality, 0, 1);
    const ground = new Vector2(ballVelocity.x, ballVelocity.z);
    const speed = ground.length();
    const direction = speed > 0.0001 ? ground.normalized() : Vector2.ZERO;

    let outgoing = Vector2.ZERO;
    if (mode === TouchMode.KNOCK_ON && facing.length() > 0.0001) {
      const push = settings.knock_on_speed * (0.4 + 0.6 * q);
      outgoing = facing.normalized().mul(push);
    } else {
      let retention = lerpf(settings.retention_poor, settings.retention_good, q);
      if (mode === TouchMode.KILL) retention *= settings.kill_multiplier;
      outgoing = direction.mul(speed * retention);
    }

    // Mis-control: perpendicular-and-add (no trig) keeps this exact everywhere.
    if (direction.length() > 0.0001) {
      const lateral = new Vector2(-direction.y, direction.x);
      outgoing = outgoing.add(lateral.mul(errorBias * settings.max_error * (1 - q)));
    }

    // Receiving flattens the ball and scrubs spin in proportion to quality.
    const vertical = minf(ballVelocity.y * (1 - q), ballVelocity.y);
    const spin = ballSpin.mul(1 - q);
    return new FirstTouchResult(new Vector3(outgoing.x, vertical, outgoing.y), spin, q, mode);
  }

  static mode_from_input(value: number): number {
    if (value === TouchMode.KILL) return TouchMode.KILL;
    if (value === TouchMode.KNOCK_ON) return TouchMode.KNOCK_ON;
    return TouchMode.CUSHION;
  }

  static mode_name(mode: number): string {
    if (mode === TouchMode.KILL) return "kill";
    if (mode === TouchMode.KNOCK_ON) return "knock_on";
    return "cushion";
  }
}
