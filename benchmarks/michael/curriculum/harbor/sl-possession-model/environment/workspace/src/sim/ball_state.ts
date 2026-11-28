// BallState - ball entity owned by MatchSim (pure state, no rendering).
//
// Position/velocity are in metres and m/s on the sim's coordinate frame:
// X runs goal-to-goal (length), Z runs touchline-to-touchline (width), Y is
// height above the pitch. `angular_velocity` is the ball's spin in rad/s
// (right-hand rule around each axis) and drives the Magnus curve force
// computed by BallPhysics (task 1.1). The ball is never parented to a player.
import { Vector2, Vector3 } from "./vec.ts";

export class BallState {
  position = new Vector3();
  velocity = new Vector3();
  angular_velocity = new Vector3();

  reset(spawnHeight: number): void {
    this.position = new Vector3(0, spawnHeight, 0);
    this.velocity = new Vector3();
    this.angular_velocity = new Vector3();
  }

  // Horizontal (ground-plane) speed, ignoring height component.
  ground_speed(): number {
    return new Vector2(this.velocity.x, this.velocity.z).length();
  }

  has_finite_state(): boolean {
    return this.position.isFinite() && this.velocity.isFinite() && this.angular_velocity.isFinite();
  }

  to_dict(): Record<string, number> {
    return {
      px: this.position.x, py: this.position.y, pz: this.position.z,
      vx: this.velocity.x, vy: this.velocity.y, vz: this.velocity.z,
      wx: this.angular_velocity.x, wy: this.angular_velocity.y, wz: this.angular_velocity.z,
    };
  }
}
