#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py hardware/cad/build.py,hardware/cad/design.py,hardware/cad/mesh.py python harness.py
