// PlayerState - a footballer entity owned by MatchSim (pure state).
//
// Players live on the ground plane (X = length, Z = width); `position` and
// `velocity` are Vector2 in that plane (vector .y is the world Z axis). `home`
// is the AI formation anchor. `facing` is the player's aim / body-orientation
// unit vector, driven independently of `velocity` (task 1.2's decoupled aim).
// `stamina` fuels sprinting and is owned by Locomotion: it is measured in
// stamina points on the same scale as the tuning's player.stamina_max.
import { Vector2 } from "./vec.ts";

export class PlayerState {
  id = 0;
  team = 0;
  role = 0;
  position = new Vector2();
  velocity = new Vector2();
  home = new Vector2();
  facing = Vector2.RIGHT;
  stamina = 1.0;
  sprinting = false;
  touch_cooldown = 0;

  has_finite_state(): boolean {
    return this.position.isFinite() && this.velocity.isFinite() && this.facing.isFinite()
      && Number.isFinite(this.stamina);
  }

  to_dict(): Record<string, number | boolean> {
    return {
      id: this.id, team: this.team, role: this.role,
      px: this.position.x, pz: this.position.y,
      vx: this.velocity.x, vz: this.velocity.y,
      fx: this.facing.x, fz: this.facing.y,
      stamina: this.stamina, sprinting: this.sprinting,
    };
  }
}
