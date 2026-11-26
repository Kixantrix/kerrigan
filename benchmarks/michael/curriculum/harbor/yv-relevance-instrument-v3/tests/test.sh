#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py evals/relevance/audit.ts,evals/relevance/blind.ts,evals/relevance/score.ts node harness.mjs
