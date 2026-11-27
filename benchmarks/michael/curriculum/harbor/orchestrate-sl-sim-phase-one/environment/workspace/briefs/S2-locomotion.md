# Brief S2 — task 1.2 player locomotion

Owns: `src/sim/locomotion.ts`, `facing`/`stamina`/`sprinting` in
`src/sim/player_state.ts`.

- `Locomotion.update(player, move, aim, sprint, dt, ...tuning)`: analog speed
  from the move stick's magnitude, acceleration-limited.
- Sprint: top speed x `sprint_multiplier` while stamina is above
  `stamina_sprint_min`; drain `stamina_drain_rate` while sprinting, recover
  `stamina_recovery_rate` otherwise, capped at `stamina_max`.
- PlayerState gains `stamina` for the tank (1.0 = a full tank) and
  `sprinting`.
- Decoupled aim: `facing` turns toward the aim stick at `turn_rate_rad`;
  zero aim keeps facing.
- Call `Locomotion.update` from `MatchSim._update_players` (input key `aim`).
