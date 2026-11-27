// Kick - pure impulse + spin model for striking the ball (task 1.3).
//
// Three mechanics, one model. Each produces a horizontal impulse, a vertical
// loft, and a spin vector; the differences are entirely in the tuning bands:
//   PASS - grounded and accurate; power interpolates speed between
//          pass.speed_min and pass.speed_max (the "weighted pass").
//   SHOT - power-hold strike: highest speed band, low loft, topspin (dips).
//   LOB  - lifted ball: highest loft, lowest speed, backspin (floats).
//
// Spin model (BallPhysics applies Magnus as magnus_coeff * (omega x v)):
// - Sidespin (omega along +Y) curves the ball left/right. It comes from the
//   approach angle: the signed lateral component of the striker's velocity
//   relative to the kick direction (2D cross product), scaled by
//   approach_spin_factor, plus a caller-supplied bias, clamped to max_side_spin.
// - Top/backspin (omega along up x travel) gives a purely vertical force:
//   axial_spin > 0 dips, < 0 floats.
//
// `build` itself performs no randomness: the caller supplies the seeded bias.
import { Vector2, Vector3, clampf, lerpf } from "./vec.ts";

export const KickType = { PASS: 0, SHOT: 1, LOB: 2 } as const;

// The input fields a strike reads (S3 brief, "kick input"): the requested
// mechanic, the 0..1 button-hold charge and the optional aim.
export type KickInput = {
  kick_type?: number;
  power?: number;
  aim?: Vector2;
};

const UP = new Vector3(0, 1, 0);

// Per-mechanic tuning band, built by MatchSim from tuning JSON.
export class KickProfile {
  speed_min: number;
  speed_max: number;
  loft_min: number;
  loft_max: number;
  // Spin about the across-travel axis: > 0 topspin (dips), < 0 backspin.
  axial_spin: number;

  constructor(speedMin: number, speedMax: number, loftMin: number, loftMax: number, axialSpin: number) {
    this.speed_min = speedMin;
    this.speed_max = speedMax;
    this.loft_min = loftMin;
    this.loft_max = loftMax;
    this.axial_spin = axialSpin;
  }
}

// Resulting impulse for one strike: a world-space ball velocity plus spin.
export class KickImpulse {
  velocity: Vector3;
  angular_velocity: Vector3;

  constructor(velocity: Vector3, angularVelocity: Vector3) {
    this.velocity = velocity;
    this.angular_velocity = angularVelocity;
  }
}

export class Kick {
  // `direction` is the aim (need not be normalised). `power` is the 0..1
  // charge. `strikerVelocity` is the player's ground-plane velocity.
  static build(
    profile: KickProfile,
    direction: Vector2,
    power: number,
    strikerVelocity: Vector2,
    approachSpinFactor: number,
    maxSideSpin: number,
    sideSpinBias = 0,
  ): KickImpulse {
    const charge = clampf(power, 0, 1);
    const dir = direction.normalized();
    const speed = lerpf(profile.speed_min, profile.speed_max, charge);
    const loft = lerpf(profile.loft_min, profile.loft_max, charge);

    const lateral = dir.cross(strikerVelocity);
    const sideSpin = clampf(lateral * approachSpinFactor + sideSpinBias, -maxSideSpin, maxSideSpin);

    const travel = new Vector3(dir.x, 0, dir.y);
    const spin = UP.mul(sideSpin).add(UP.cross(travel).mul(profile.axial_spin));
    return new KickImpulse(new Vector3(dir.x * speed, loft, dir.y * speed), spin);
  }

  // Map an input's requested kick type onto KickType, defaulting to PASS.
  static type_from_input(value: number): number {
    if (value === KickType.SHOT) return KickType.SHOT;
    if (value === KickType.LOB) return KickType.LOB;
    return KickType.PASS;
  }

  // Human-readable name for match-log events.
  static type_name(kickType: number): string {
    if (kickType === KickType.SHOT) return "shot";
    if (kickType === KickType.LOB) return "lob";
    return "pass";
  }
}
