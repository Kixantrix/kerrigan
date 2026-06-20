#!/usr/bin/env bash
# assets/_playbook-test/voxel/smoke.sh
# Re-builds the hero ship from source and validates all acceptance criteria.
#
# Acceptance criteria tested (one-to-one):
#   AC1 exports/ship.glb regenerates from source via build.sh (no GUI)
#   AC2 glTF validates (pygltflib loads without error)
#   AC3 mesh is manifold AND tri count ≤ budget
#   AC4 texture dimensions are power-of-two
#   AC5 re-running build.sh is deterministic (SHA-256 matches)
#
# Usage: bash smoke.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== voxel hero ship smoke ==="
echo ""

# --- Step 1: (re-)build ---
echo "[ step 1: build ]"
bash "$SCRIPT_DIR/build.sh"
echo ""

# --- Step 2: validate ---
echo "[ step 2: validate ]"
python3 "$SCRIPT_DIR/validate.py" \
    --exports-dir "$SCRIPT_DIR/exports" \
    --source-dir  "$SCRIPT_DIR/source"  \
    --check-determinism
