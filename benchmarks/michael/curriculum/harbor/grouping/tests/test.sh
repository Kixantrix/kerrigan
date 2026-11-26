#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py apps/kerrigan-dashboard/src/components/StageDetailPanel/groupStageItems.ts node harness.mjs
