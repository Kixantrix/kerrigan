#!/usr/bin/env bash
# .claude/hooks/pre-tool-use.sh — PreToolUse hook for Claude Code
#
# Guards against dangerous shell commands.
# Rejects:
#   1. `sudo` commands when the task is cloud-routed
#      (briefing contains `routing_rule_matched: R-cloud-*`)
#   2. Destructive patterns: `rm -rf /`, `rm -rf ~`, `:(){ ... }` fork bombs, etc.
#
# Protocol (Claude Code PreToolUse):
#   - Receives tool invocation JSON on stdin.
#   - Exit 0  → allow the tool call to proceed.
#   - Exit 2  → block the tool call; stderr is shown to the user.
#
# Graceful degradation:
#   When not running under Claude Code (CLAUDE_TOOL_NAME not set), this
#   script exits 0 immediately and is a no-op.

set -euo pipefail

# --- Graceful degradation: not running under Claude Code ------------------
if [[ -z "${CLAUDE_TOOL_NAME:-}" ]]; then
    exit 0
fi

# --- Only guard Bash / shell tool invocations ----------------------------
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
if [[ "$TOOL_NAME" != "Bash" && "$TOOL_NAME" != "Shell" ]]; then
    exit 0
fi

# --- Read the JSON payload from stdin ------------------------------------
INPUT="$(cat)"

# Extract the command string (handles both `command` and `cmd` keys)
COMMAND=""
if command -v python3 &>/dev/null; then
    COMMAND="$(printf '%s' "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Claude Code passes tool input under different shapes
cmd = data.get('command') or data.get('cmd') or ''
print(cmd)
" 2>/dev/null || true)"
fi

# Fallback: plain grep if python3 unavailable
if [[ -z "$COMMAND" ]]; then
    COMMAND="$(printf '%s' "$INPUT" | grep -oP '(?<="command"\s*:\s*")[^"]*' | head -1 || true)"
fi

if [[ -z "$COMMAND" ]]; then
    # Cannot extract command; allow and let Claude Code handle it.
    exit 0
fi

# --- Rule 1: Destructive-pattern block (always active) -------------------
# These patterns are dangerous regardless of routing.
DESTRUCTIVE_PATTERNS=(
    'rm[[:space:]]+-[^[:space:]]*r[^[:space:]]*[[:space:]]+-[^[:space:]]*f[^[:space:]]*[[:space:]]*/[[:space:]]*$'
    'rm[[:space:]]+-[^[:space:]]*f[^[:space:]]*[[:space:]]+-[^[:space:]]*r[^[:space:]]*[[:space:]]*/[[:space:]]*$'
    'rm[[:space:]]+-rf[[:space:]]*/[[:space:]]*$'
    'rm[[:space:]]+-fr[[:space:]]*/[[:space:]]*$'
    'rm[[:space:]]+-rf[[:space:]]+/\*'
    'rm[[:space:]]+-rf[[:space:]]+~'
    'rm[[:space:]]+-rf[[:space:]]+\$HOME'
    'mkfs\.'
    ':[[:space:]]*([[:space:]]*)[[:space:]]*{[[:space:]]*:[[:space:]]*|[[:space:]]*&[[:space:]]*}[[:space:]]*;[[:space:]]*:'  # fork bomb :(){ :|:& };:
    'dd[[:space:]].*of=/dev/[sh]d'
    '>[[:space:]]*/dev/[sh]d'
    'chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+'
    'shred[[:space:]].*--remove'
)

for pattern in "${DESTRUCTIVE_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qE "$pattern" 2>/dev/null; then
        echo "pre-tool-use: BLOCKED — destructive command pattern detected: $pattern" >&2
        echo "Command: $COMMAND" >&2
        exit 2
    fi
done

# --- Rule 2: sudo block for cloud-routed tasks ---------------------------
if echo "$COMMAND" | grep -qE '(^|[[:space:]|;&`$])sudo[[:space:]]'; then
    # Check whether the current task is cloud-routed.
    # Look for any briefing file that contains `routing_rule_matched: R-cloud-`
    REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel 2>/dev/null || echo "")"
    IS_CLOUD_ROUTED=0

    if [[ -n "$REPO_ROOT" ]]; then
        BRIEFINGS_DIR="$REPO_ROOT/.specify/briefings"
        if [[ -d "$BRIEFINGS_DIR" ]]; then
            if grep -rlE 'routing_rule_matched:[[:space:]]*R-cloud-' "$BRIEFINGS_DIR" 2>/dev/null | grep -q .; then
                IS_CLOUD_ROUTED=1
            fi
        fi

        # Also check env var set by kerrigan dispatch
        if [[ "${KERRIGAN_ROUTING_RULE:-}" == R-cloud-* ]]; then
            IS_CLOUD_ROUTED=1
        fi
    fi

    if [[ "$IS_CLOUD_ROUTED" -eq 1 ]]; then
        echo "pre-tool-use: BLOCKED — sudo is not permitted in cloud-routed tasks." >&2
        echo "  Routing rule matched: ${KERRIGAN_ROUTING_RULE:-see .specify/briefings/}" >&2
        echo "  Command: $COMMAND" >&2
        exit 2
    fi
fi

exit 0
