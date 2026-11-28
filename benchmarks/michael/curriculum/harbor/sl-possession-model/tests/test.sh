#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py data/tuning.json,src/sim/match_sim.ts,src/sim/possession.ts,src/sim/sports/soccer_rules.ts node harness.mjs
