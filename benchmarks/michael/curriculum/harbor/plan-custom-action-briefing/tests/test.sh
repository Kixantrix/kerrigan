#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py BRIEFING.json python harness.py
