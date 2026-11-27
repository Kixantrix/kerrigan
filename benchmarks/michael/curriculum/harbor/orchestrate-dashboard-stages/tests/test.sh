#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py INTEGRATION.json,src/github.ts,src/plan-update.ts,src/project-status.ts,src/status.ts node harness.mjs
