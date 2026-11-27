// BallPhysics - pure aerodynamic + bounce functions for BallState (task 1.1).
//
// Implements the "rigid body + drag + Magnus + surface bounce" ball model.
// Every function here is a stateless transform of a BallState plus
// caller-supplied constants (all sourced from tuning JSON by MatchSim).
//
// Analytic references:
// - Linear (Stokes) drag alone: F/m = -linear_drag * v, so speed decays
//   exponentially, v(t) = v0 * exp(-linear_drag * t).
// - Magnus alone: F/m = magnus_coeff * (omega x v), always perpendicular to v,
//   so it preserves speed and rotates the velocity (circular motion of radius
//   |v| / (magnus_coeff * |omega|) when omega is perpendicular to the motion).
// - Ground/wall bounce: outgoing speed along the surface normal is
//   `restitution` times the incoming normal speed; tangential speed is kept by
//   `bounce()` and damped separately by rolling friction on the ground.
import { BallState } from "./ball_state.ts";
import { Vector3, maxf } from "./vec.ts";

export class BallPhysics {
  // Apply gravity, Magnus (spin-curve), and linear drag for one tick, then
  // integrate position. Spin decays via `spin_drag`. Semi-implicit Euler:
  // forces update velocity first, then velocity updates position.
  static apply_forces(
    ball: BallState,
    dt: number,
    gravity: number,
    linearDrag: number,
    magnusCoeff: number,
    spinDrag: number,
  ): void {
    ball.velocity = new Vector3(ball.velocity.x, ball.velocity.y - gravity * dt, ball.velocity.z);
    if (magnusCoeff !== 0 && !ball.angular_velocity.isZero()) {
      const magnusAccel = ball.angular_velocity.cross(ball.velocity).mul(magnusCoeff);
      ball.velocity = ball.velocity.add(magnusAccel.mul(dt));
    }
    const drag = maxf(0, 1 - linearDrag * dt);
    ball.velocity = ball.velocity.mul(drag);
    const spinDecay = maxf(0, 1 - spinDrag * dt);
    ball.angular_velocity = ball.angular_velocity.mul(spinDecay);
    ball.position = ball.position.add(ball.velocity.mul(dt));
  }

  // Reflect velocity off a surface with the given unit `normal`, losing
  // `(1 - restitution)` of the speed along that normal and leaving the
  // tangential component untouched. No-op if the ball is already moving away.
  static bounce(ball: BallState, normal: Vector3, restitution: number): boolean {
    const normalSpeed = ball.velocity.dot(normal);
    if (normalSpeed >= 0) return false;
    ball.velocity = ball.velocity.sub(normal.mul((1 + restitution) * normalSpeed));
    return true;
  }

  // Ground contact: clamp the ball to resting height, bounce the vertical
  // component, and apply rolling friction to the ground-plane velocity.
  // Speeds below `rest_speed` snap to zero so the ball can come to a genuine
  // rest instead of drifting forever on tiny floats.
  static resolve_ground_contact(
    ball: BallState,
    dt: number,
    ballRadius: number,
    restitution: number,
    groundFriction: number,
    restSpeed: number,
  ): void {
    if (ball.position.y > ballRadius) return;
    ball.position = new Vector3(ball.position.x, ballRadius, ball.position.z);
    BallPhysics.bounce(ball, Vector3.UP, restitution);
    if (Math.abs(ball.velocity.y) < restSpeed) {
      ball.velocity = new Vector3(ball.velocity.x, 0, ball.velocity.z);
    }
    const friction = maxf(0, 1 - groundFriction * dt);
    ball.velocity = new Vector3(ball.velocity.x * friction, ball.velocity.y, ball.velocity.z * friction);
    if (ball.ground_speed() < restSpeed) {
      ball.velocity = new Vector3(0, ball.velocity.y, 0);
    }
  }

  // Clamp ball speed to a physical top speed to keep the sim bounded.
  static clamp_speed(ball: BallState, maxSpeed: number): void {
    if (ball.velocity.length() > maxSpeed) {
      ball.velocity = ball.velocity.normalized().mul(maxSpeed);
    }
  }
}
