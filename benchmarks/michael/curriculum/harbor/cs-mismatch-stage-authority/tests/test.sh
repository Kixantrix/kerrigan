#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py REVIEW.json,src/lib/report/mismatch.ts node harness.mjs
