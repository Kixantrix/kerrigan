# Brief S3 — task 1.3 kick mechanics

Owns: `src/sim/kick.ts`.

- `Kick.build(profile, direction, power, striker_velocity, approach_spin_factor,
  max_side_spin, side_spin_bias)` returns velocity + spin; pure, no
  randomness inside.
- Mechanics PASS / SHOT / LOB from the `kick` tuning bands; speed and loft
  interpolate by the 0..1 charge.
- Sidespin from the approach angle plus a small side-spin jitter
  (`kick.side_spin_jitter`) supplied by the caller; top/backspin from the
  band's `axial_spin`.
- Kick input: `kick_type` and the charge `power`, plus optional `aim`.
- Wire `MatchSim._kick_ball` (aim from input, else facing, else goal) and
  emit the `kick` event.
- Receiving a ball without kicking belongs to task 1.4.
