#!/usr/bin/env bash
# .claude/hooks/stop-verify.sh — Stop hook for Claude Code
#
# Runs `kerrigan check` (all validators) before the Claude Code session ends.
# A non-zero exit from `kerrigan check` is surfaced as a warning in the
# Claude Code session summary but does NOT abort the Stop event (exit 0
# always, so the session can close cleanly).
#
# Graceful degradation:
#   When not running under Claude Code (CLAUDE_SESSION_ID not set), this
#   script exits 0 immediately and is a no-op.
#
# Usage (configured via .claude/settings.local.json):
#   { "hooks": { "Stop": [{ "hooks": [{ "type": "command",
#     "command": ".claude/hooks/stop-verify.sh" }] }] } }

set -uo pipefail

# --- Graceful degradation: not running under Claude Code ------------------
if [[ -z "${CLAUDE_SESSION_ID:-}" ]]; then
    exit 0
fi

# --- Locate repo root -----------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || echo "")"

if [[ -z "$REPO_ROOT" ]]; then
    echo "stop-verify: cannot determine repo root; skipping kerrigan check." >&2
    exit 0
fi

echo "=== stop-verify: running kerrigan check ==="

# --- Try to find a kerrigan executable ------------------------------------
KERRIGAN_CMD=""

# 1. kerrigan on PATH
if command -v kerrigan &>/dev/null; then
    KERRIGAN_CMD="kerrigan"
# 2. Local dev install (editable install from tools/cli/kerrigan)
elif [[ -f "$REPO_ROOT/tools/cli/kerrigan/kerrigan_cli/cli.py" ]]; then
    KERRIGAN_CMD="python3 -m kerrigan_cli.cli"
    export PYTHONPATH="$REPO_ROOT/tools/cli/kerrigan${PYTHONPATH:+:$PYTHONPATH}"
fi

if [[ -z "$KERRIGAN_CMD" ]]; then
    echo "stop-verify: kerrigan not found on PATH and local install not detected." >&2
    echo "  Skipping verify chain. Install with: pip install -e tools/cli/kerrigan" >&2
    exit 0
fi

# --- Run kerrigan check ---------------------------------------------------
cd "$REPO_ROOT"
EXIT_CODE=0
$KERRIGAN_CMD check || EXIT_CODE=$?

if [[ "$EXIT_CODE" -eq 0 ]]; then
    echo "=== stop-verify: kerrigan check PASSED ==="
else
    echo "=== stop-verify: kerrigan check FAILED (exit $EXIT_CODE) ===" >&2
    echo "    Review the output above and address any issues before merging." >&2
fi

# Always exit 0 — stop hooks must not block session teardown.
exit 0
