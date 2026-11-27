#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py foal-rescue-meadow.html,index.html,review-findings.json node harness.mjs
