#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py apps/kerrigan-dashboard/src/lib/plan-conflict.ts,apps/kerrigan-dashboard/src/lib/plan-queue.ts node harness.mjs
