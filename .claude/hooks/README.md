# Claude Code Hooks

This directory contains [Claude Code hook](https://docs.anthropic.com/en/docs/claude-code/hooks)
scripts for the Kerrigan repo.

Hooks are configured in `.claude/settings.local.json` and run automatically
inside Claude Code sessions. They are **no-ops** when invoked outside Claude
Code (graceful degradation via environment-variable checks).

---

## `pre-tool-use.sh` — PreToolUse guard

**Event:** `PreToolUse` (fires before every tool call Claude makes)  
**Matcher:** `Bash` / `Shell` tool invocations only

### What it blocks

| Rule | Pattern | Routing scope |
|------|---------|---------------|
| Destructive filesystem | `rm -rf /`, `rm -rf ~`, `rm -rf $HOME`, `dd … of=/dev/sd*`, `mkfs.*`, fork-bomb `:|:&` | Always |
| `sudo` | Any command that begins with or pipes into `sudo` | Cloud-routed tasks only |

### Cloud-routing detection

A task is considered **cloud-routed** when either:

1. `.specify/briefings/<task-id>.md` contains the line  
   `routing_rule_matched: R-cloud-*` (any `R-cloud-` prefix), **or**
2. The environment variable `KERRIGAN_ROUTING_RULE` starts with `R-cloud-`.

`sudo` is blocked only in cloud-routed tasks because cloud containers run as
a non-privileged user and `sudo` commands typically indicate a local
environment assumption.

### Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Allow — proceed with the tool call |
| `2`  | Block — Claude Code shows the stderr message to the user |

### Graceful degradation

The script checks for `CLAUDE_TOOL_NAME`. If that variable is unset the script
exits `0` immediately, making it a no-op in any non-Claude-Code context
(CI, bare bash, pre-commit, etc.).

---

## `stop-verify.sh` — Stop verify chain

**Event:** `Stop` (fires when a Claude Code session is about to end)

Runs `kerrigan check` (all validators) so any artifact or dependency issues
are surfaced before the session closes. Output is printed to the session
transcript; a non-zero exit from `kerrigan check` is reported as a warning
but does **not** block session teardown (the hook always exits `0`).

### Kerrigan CLI resolution order

1. `kerrigan` on `$PATH` (e.g., installed with `pip install -e tools/cli/kerrigan`)
2. Local dev install at `tools/cli/kerrigan/kerrigan_cli/cli.py` via `python3 -m`
3. Skip with a warning if neither is found

### Graceful degradation

The script checks for `CLAUDE_SESSION_ID`. If unset the script exits `0`
immediately and is a no-op.

---

## Configuration

Hooks are wired in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|bash|shell|powershell",
        "hooks": [{ "type": "command", "command": ".claude/hooks/pre-tool-use.sh", "powershell": "...inline guard..." }]
      }
    ],
    "Stop": [
      {
        "hooks": [{ "type": "command", "command": ".claude/hooks/stop-verify.sh", "powershell": "exit 0" }]
      }
    ]
  }
}
```

`settings.local.json` is a **repo-level** settings file loaded by Claude Code
when it opens this repository. It complements (and does not replace) any
personal `~/.claude/settings.json`.

---

## Cross-tool note: GitHub Copilot CLI reads these hooks too

GitHub Copilot CLI also loads `.claude/settings.json` / `.claude/settings.local.json`
from the repository as one of its hook sources, and merges them with its own
(`.github/hooks/*.json`, user-level hooks, etc.). All sources fire; any one of
them can deny a tool call. That has two consequences on Windows:

1. **`command` is copied to both shells.** Copilot's command-hook schema has
   `bash`, `powershell`, and a cross-platform `command` fallback. An entry with
   only `command: "bash …"` is used verbatim on Windows, where `bash` is usually
   not on `PATH`.
2. **`preToolUse` is fail-closed.** A hook that crashes (including
   "command not found") *denies* the tool call. So a missing `bash` turns the
   guard into a blanket deny of every shell command, reported as
   `Denied by preToolUse hook from "repo settings" (hook errored)`.

Both entries therefore carry an explicit `powershell` field, which takes
precedence over `command` on Windows:

- `PreToolUse` — an inline PowerShell twin of the destructive-pattern guard. It
  reads the payload from stdin, emits a `permissionDecision: deny` object when a
  destructive pattern matches, and always exits `0` (so it can never fail-closed
  by accident). It is written inline rather than as a `.ps1` file so it does not
  depend on `PATH`, the hook's working directory, or PowerShell execution policy.
  The deny JSON is built with `ConvertTo-Json` instead of a quoted literal,
  because quotes are stripped when the command is passed through `-Command`.
- `Stop` — `exit 0`. The verify chain stays Claude-Code-only on purpose: Copilot
  maps `Stop` to `agentStop`, which fires after **every turn**, not once per
  session, so running `kerrigan check` there would be wrong (and slow).

The `matcher` is `Bash|bash|shell|powershell` so it matches both Claude's `Bash`
tool name and the runtime shell tool names Copilot surfaces.

Keep `command` pointing at the bash scripts — that is what Claude Code uses, and
what Copilot uses on Unix.

---

## Making hooks executable

After cloning, run once:

```bash
chmod +x .claude/hooks/pre-tool-use.sh .claude/hooks/stop-verify.sh
```

Or rely on the Git attribute — the scripts are committed with execute bits set.

---

## Out of scope

- Windows-specific hook *scripts* (no `.ps1` twins of `pre-tool-use.sh` /
  `stop-verify.sh`). Claude Code on Windows runs the bash scripts through Git
  Bash; Copilot CLI on Windows uses the inline `powershell` commands described
  above.
- Modifying Claude Code itself.
