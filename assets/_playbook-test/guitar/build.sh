#!/usr/bin/env bash
# assets/_playbook-test/guitar/build.sh
# Regenerates all DXF exports from parametric Python sources.
# Run from any directory; paths are relative to this script.
#
# Usage:
#   bash assets/_playbook-test/guitar/build.sh
#   (or ./build.sh from the guitar/ directory)

set -euo pipefail

GUITAR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$GUITAR_DIR/source"

echo "=== Guitar playbook: building DXF exports ==="
echo "Asset root: $GUITAR_DIR"
echo ""

python3 "$SOURCE_DIR/headstock.py"
python3 "$SOURCE_DIR/brass_logo.py"

echo ""
echo "Build complete. Exports in $GUITAR_DIR/exports/"
