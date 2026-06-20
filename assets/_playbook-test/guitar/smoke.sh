#!/usr/bin/env bash
# assets/_playbook-test/guitar/smoke.sh
# Builds DXF exports and runs all 5 acceptance-criteria assertions via pytest.
#
# Acceptance criteria tested (one test per AC):
#   AC1  headstock DXF regenerates in correct units (mm / INSUNITS=4)
#   AC2  logo DXF bounding box ≤ headstock outline minus declared margin
#   AC3  logo passes brass manufacturability gate (min feature ≥ 0.02″)
#   AC4  changing nut_width propagates to headstock export
#   AC5  re-running build is deterministic (geometry identical on second run)
#
# Usage:
#   bash assets/_playbook-test/guitar/smoke.sh
#   (or ./smoke.sh from the guitar/ directory)

set -euo pipefail

GUITAR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$GUITAR_DIR/../../.." && pwd)"

echo "=== Guitar playbook smoke test ==="
echo "Asset root: $GUITAR_DIR"
echo ""

# Step 1: regenerate exports
echo "[ Build ]"
bash "$GUITAR_DIR/build.sh"
echo ""

# Step 2: run pytest assertions (tests live in repo-level tests/)
echo "[ Assertions ]"
python3 -m pytest "$REPO_ROOT/tests/test_guitar_playbook.py" -v --tb=short
