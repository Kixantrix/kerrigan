#!/usr/bin/env bash
# scripts/smoke.sh — Kerrigan repo health smoke test
#
# Runs read-only checks to verify the repo is in a healthy state:
#   1. Python is importable
#   2. Key validator scripts exist
#   3. Kerrigan CLI package is loadable
#   4. Key repository directories exist
#
# Exit 0 on success, exit 1 on first failure.
# Idempotent and side-effect-free (read-only checks only).
#
# Usage: bash scripts/smoke.sh
#        (or make it executable and run: ./scripts/smoke.sh)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  ✓ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }

echo "=== Kerrigan smoke test ==="
echo "Repo root: $REPO_ROOT"
echo ""

# --- Check 1: Python importable ---
echo "[ Python ]"
if python3 -c "import sys, pathlib, json, re" 2>/dev/null; then
    pass "python3 importable (sys, pathlib, json, re)"
else
    fail "python3 not importable or missing stdlib modules"
fi
echo ""

# --- Check 2: Validators exist ---
echo "[ Validators ]"
VALIDATORS_DIR="$REPO_ROOT/tools/validators"
for v in agents_md.py check_artifacts.py check_dependencies.py check_placeholders.py; do
    if [ -f "$VALIDATORS_DIR/$v" ]; then
        pass "validators/$v exists"
    else
        fail "validators/$v missing"
    fi
done
echo ""

# --- Check 3: Kerrigan CLI loadable ---
echo "[ Kerrigan CLI ]"
CLI_PKG="$REPO_ROOT/tools/cli/kerrigan"
if python3 -c "
import sys
sys.path.insert(0, '$CLI_PKG')
from kerrigan_cli import cli as _cli
" 2>/dev/null; then
    pass "kerrigan_cli package loadable"
else
    fail "kerrigan_cli package not loadable (check tools/cli/kerrigan)"
fi
echo ""

# --- Check 4: Key directories exist ---
echo "[ Key directories ]"
for dir in tools tools/validators tools/cli scripts .github/agents specs playbooks; do
    if [ -d "$REPO_ROOT/$dir" ]; then
        pass "$dir/"
    else
        fail "$dir/ missing"
    fi
done
echo ""

# --- Summary ---
TOTAL=$((PASS + FAIL))
echo "=== Results: $PASS/$TOTAL passed ==="
if [ "$FAIL" -gt 0 ]; then
    echo "SMOKE FAILED — $FAIL check(s) did not pass."
    exit 1
fi
echo "SMOKE PASSED"
exit 0
