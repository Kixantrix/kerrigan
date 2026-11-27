#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py hardware/ASSEMBLY.md,hardware/BOM.md,hardware/README.md,hardware/stack.py python harness.py
