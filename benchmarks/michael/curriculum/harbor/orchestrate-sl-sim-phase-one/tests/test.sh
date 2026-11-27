#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py INTEGRATION.json,src/sim/ball_physics.ts,src/sim/ball_state.ts,src/sim/first_touch.ts,src/sim/input_provider.ts,src/sim/kick.ts,src/sim/locomotion.ts,src/sim/match_log.ts,src/sim/match_sim.ts,src/sim/player_state.ts node harness.mjs
