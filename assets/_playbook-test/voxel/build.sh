#!/usr/bin/env bash
# assets/_playbook-test/voxel/build.sh
# Re-generate exports/ship.vox and exports/ship.glb from source/gen_ship.py.
# No GUI required. Deterministic.
#
# Usage: bash build.sh [--output-dir <path>]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="$SCRIPT_DIR/source/gen_ship.py"
OUTPUT_DIR="${1:-$SCRIPT_DIR/exports}"

echo "=== voxel hero ship build ==="
echo "generator : $GENERATOR"
echo "output-dir: $OUTPUT_DIR"
echo ""

python3 "$GENERATOR" --output-dir "$OUTPUT_DIR"

echo ""
echo "build complete."
echo "  ship.vox : $(wc -c < "$OUTPUT_DIR/ship.vox") bytes"
echo "  ship.glb : $(wc -c < "$OUTPUT_DIR/ship.glb") bytes"
