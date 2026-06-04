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
# Idempotent and side-effect-free by default (read-only checks only).
# Optional dashboard build checks can be enabled with:
#   KERRIGAN_SMOKE_DASHBOARD=1
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

# --- Check 5: Optional dashboard build + artifact ---
echo "[ Dashboard build ]"
DASHBOARD_DIR="$REPO_ROOT/apps/kerrigan-dashboard"
RUN_DASHBOARD_SMOKE="${KERRIGAN_SMOKE_DASHBOARD:-0}"
SKIP_DASHBOARD_BUILD="${KERRIGAN_SMOKE_DASHBOARD_SKIP_BUILD:-0}"

if [[ "$RUN_DASHBOARD_SMOKE" != "1" ]]; then
    pass "dashboard smoke skipped (set KERRIGAN_SMOKE_DASHBOARD=1 to enable)"
elif [[ ! -d "$DASHBOARD_DIR" ]]; then
    pass "dashboard smoke skipped (apps/kerrigan-dashboard not present)"
else
    if ! command -v pnpm >/dev/null 2>&1; then
        fail "pnpm is required for dashboard smoke checks"
    else
        if [[ "$SKIP_DASHBOARD_BUILD" != "1" ]]; then
            if pnpm -C "$DASHBOARD_DIR" tauri build; then
                pass "dashboard tauri build completed"
            else
                fail "dashboard tauri build failed"
            fi
        else
            pass "dashboard tauri build skipped (KERRIGAN_SMOKE_DASHBOARD_SKIP_BUILD=1)"
        fi

        BUNDLE_DIR="$DASHBOARD_DIR/src-tauri/target/release/bundle"
        PLATFORM="$(uname -s)"
        ARTIFACTS=()
        if [[ -d "$BUNDLE_DIR" ]]; then
            find_args=()
            case "$PLATFORM" in
                Linux*)
                    find_args=(-type f \( -name "*.AppImage" -o -name "*.deb" -o -name "*.rpm" \))
                    ;;
                Darwin*)
                    find_args=(\( -type f -name "*.dmg" -o -type d -name "*.app" \))
                    ;;
                *)
                    find_args=(-type f \( -name "*.msi" -o -name "*.exe" \))
                    ;;
            esac
            while IFS= read -r -d '' artifact; do
                ARTIFACTS+=("$artifact")
            done < <(find "$BUNDLE_DIR" "${find_args[@]}" -print0)
        fi

        if [[ "${#ARTIFACTS[@]}" -gt 0 ]]; then
            pass "dashboard artifact exists (${#ARTIFACTS[@]} found; first: ${ARTIFACTS[0]})"
        else
            fail "dashboard artifact missing under $BUNDLE_DIR"
        fi
    fi
fi
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
