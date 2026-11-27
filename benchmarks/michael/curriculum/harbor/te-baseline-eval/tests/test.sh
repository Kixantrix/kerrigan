#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py apps/taste-engine/eval/reports/ml-01-baselines.json,apps/taste-engine/src/taste_engine/eval/baselines.py,apps/taste-engine/src/taste_engine/eval/benchmark.py,apps/taste-engine/src/taste_engine/eval/metrics.py,apps/taste-engine/src/taste_engine/eval/split.py python harness.py
