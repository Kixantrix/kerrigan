#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py apps/kerrigan-dashboard/src/lib/status.ts node harness.mjs
