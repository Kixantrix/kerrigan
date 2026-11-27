# Brief S1 — task 1.1 ball physics

Owns: `src/sim/ball_physics.ts`, ball spin in `src/sim/ball_state.ts`.

- Add `angular_velocity` (rad/s) to `BallState`.
- `BallPhysics.apply_forces`: gravity, Magnus `magnus_coefficient * (w x v)`,
  linear drag, spin decay (`spin_drag`), then integrate position
  (semi-implicit Euler).
- `BallPhysics.bounce(ball, normal, restitution)` for ground and walls.
- `BallPhysics.resolve_ground_contact`: clamp to resting height, bounce,
  apply rolling friction to the ground-plane velocity using
  `ball.ground_friction`, snap tiny speeds to rest.
- `BallPhysics.clamp_speed`.
- Replace the scaffold's inline integrator in `MatchSim._integrate_ball` and
  the wall rebounds in `_resolve_bounds` with these functions.
- Unit tests against the analytic solutions (exponential drag decay, circular
  Magnus motion).
