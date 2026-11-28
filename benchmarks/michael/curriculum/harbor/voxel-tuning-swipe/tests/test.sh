#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py src/engine/swipe.ts,src/engine/tuning.ts node harness.mjs
