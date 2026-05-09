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
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": ".claude/hooks/pre-tool-use.sh" }]
      }
    ],
    "Stop": [
      {
        "hooks": [{ "type": "command", "command": ".claude/hooks/stop-verify.sh" }]
      }
    ]
  }
}
```

`settings.local.json` is a **repo-level** settings file loaded by Claude Code
when it opens this repository. It complements (and does not replace) any
personal `~/.claude/settings.json`.

---

## Making hooks executable

After cloning, run once:

```bash
chmod +x .claude/hooks/pre-tool-use.sh .claude/hooks/stop-verify.sh
```

Or rely on the Git attribute — the scripts are committed with execute bits set.

---

## Out of scope

- Windows-specific hooks (PowerShell equivalents are not provided; hooks are
  skipped on Windows because `CLAUDE_TOOL_NAME` / `CLAUDE_SESSION_ID` are not
  set in that context).
- Modifying Claude Code itself.
