// Locomotion - pure player movement, stamina, and decoupled-aim integrator (task 1.2).
//
// Stateless transforms of a PlayerState plus caller-supplied constants (all
// sourced from tuning JSON by MatchSim), stepped at the fixed tick.
//
// Two independent layers per tick, matching the two analog sticks:
//   - Movement: `moveInput` (magnitude <= 1) scales speed continuously;
//     `sprintRequested` raises the top speed by `sprintMultiplier` but only
//     while `stamina` is above `staminaSprintMin`. Sprinting drains stamina
//     (points per second); otherwise it recovers, capped at `staminaMax`.
//   - Aim: `aimInput` drives `facing`, turning toward the aim direction at a
//     bounded `turnRate` (rad/s), decoupled from velocity. A zero aim input
//     leaves `facing` unchanged.
import { PlayerState } from "./player_state.ts";
import { Vector2, clampf, maxf, minf, wrapf } from "./vec.ts";

export class Locomotion {
  static update(
    player: PlayerState,
    moveInput: Vector2,
    aimInput: Vector2,
    sprintRequested: boolean,
    dt: number,
    maxSpeed: number,
    sprintMultiplier: number,
    acceleration: number,
    turnRate: number,
    staminaMax: number,
    staminaDrainRate: number,
    staminaRecoveryRate: number,
    staminaSprintMin: number,
  ): void {
    Locomotion.update_movement(
      player, moveInput, sprintRequested, dt,
      maxSpeed, sprintMultiplier, acceleration,
      staminaMax, staminaDrainRate, staminaRecoveryRate, staminaSprintMin,
    );
    Locomotion.update_aim(player, aimInput, turnRate, dt);
  }

  static update_movement(
    player: PlayerState,
    moveInput: Vector2,
    sprintRequested: boolean,
    dt: number,
    maxSpeed: number,
    sprintMultiplier: number,
    acceleration: number,
    staminaMax: number,
    staminaDrainRate: number,
    staminaRecoveryRate: number,
    staminaSprintMin: number,
  ): void {
    const moveMagnitude = clampf(moveInput.length(), 0, 1);
    let moveDirection = Vector2.ZERO;
    if (moveInput.length() > 0.0001) moveDirection = moveInput.normalized();

    const canSprint = sprintRequested && player.stamina > staminaSprintMin;
    const topSpeed = maxSpeed * (canSprint ? sprintMultiplier : 1);
    // Analog speed: the stick's own magnitude scales the target speed.
    const desiredVelocity = moveDirection.mul(moveMagnitude * topSpeed);

    player.velocity = player.velocity.moveToward(desiredVelocity, acceleration * dt);
    player.position = player.position.add(player.velocity.mul(dt));

    player.sprinting = canSprint && moveMagnitude > 0.01;
    if (player.sprinting) {
      player.stamina = maxf(0, player.stamina - staminaDrainRate * dt);
    } else {
      player.stamina = minf(staminaMax, player.stamina + staminaRecoveryRate * dt);
    }
  }

  static update_aim(player: PlayerState, aimInput: Vector2, turnRate: number, dt: number): void {
    if (aimInput.length() <= 0.0001) {
      // Decoupled aim: no stick input means "keep looking where I was".
      return;
    }
    const targetDirection = aimInput.normalized();
    const currentAngle = player.facing.angle();
    const targetAngle = targetDirection.angle();
    const deltaAngle = wrapf(targetAngle - currentAngle, -Math.PI, Math.PI);
    const maxStep = turnRate * dt;
    const step = clampf(deltaAngle, -maxStep, maxStep);
    player.facing = player.facing.rotated(step).normalized();
  }
}
