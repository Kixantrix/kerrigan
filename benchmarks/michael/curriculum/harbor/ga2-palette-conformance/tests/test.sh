#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py scripts/ga2/palette_conformance.py python harness.py
