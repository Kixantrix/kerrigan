# Brief S4 — task 1.4 first touch

Owns: `src/sim/first_touch.ts`.

- `FirstTouch.quality_for(settings, facing, velocity, ball_direction,
  ball_speed, player_max_speed, sprinting)`: weighted orientation / closing
  speed / ball speed, sprint penalty, clamped to 0..1.
- `FirstTouch.receive(settings, mode, quality, facing, ball_velocity,
  ball_spin, error_bias)`: CUSHION / KILL / KNOCK_ON outcomes, lateral
  mis-control `error_bias * max_error * (1 - quality)`, spin scrubbed by
  quality. Pure: the caller supplies `error_bias`.
- `FirstTouch.mode_from_input`, `FirstTouch.mode_name`.
- Tuning lives in the `first_touch` section of `data/tuning.json`.
- Strike wiring in `MatchSim` is owned by task 1.3.
