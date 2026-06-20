#!/usr/bin/env bash
# assets/_playbook-test/voxel/build.sh
# Re-generate exports/ship.vox and exports/ship.glb from source/gen_ship.py.
# No GUI required. Deterministic.
#
# Usage: bash build.sh [--output-dir <path>]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="$SCRIPT_DIR/source/gen_ship.py"
OUTPUT_DIR="$SCRIPT_DIR/exports"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output-dir)
            shift
            if [[ $# -eq 0 ]]; then
                echo "error: --output-dir requires a path" >&2
                exit 2
            fi
            OUTPUT_DIR="$1"
            shift
            ;;
        -h|--help)
            echo "Usage: bash build.sh [--output-dir <path>]"
            exit 0
            ;;
        *)
            echo "error: unknown argument: $1" >&2
            echo "Usage: bash build.sh [--output-dir <path>]" >&2
            exit 2
            ;;
    esac
done

echo "=== voxel hero ship build ==="
echo "generator : $GENERATOR"
echo "output-dir: $OUTPUT_DIR"
echo ""

python3 "$GENERATOR" --output-dir "$OUTPUT_DIR"

echo ""
echo "build complete."
echo "  ship.vox : $(wc -c < "$OUTPUT_DIR/ship.vox") bytes"
echo "  ship.glb : $(wc -c < "$OUTPUT_DIR/ship.glb") bytes"
