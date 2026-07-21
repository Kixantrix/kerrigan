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
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/pre-tool-use.sh" }]
      }
    ],
    "Stop": [
      {
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/stop-verify.sh" }]
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

## Cross-platform invocation (Windows)

Hook `command` strings **must** be prefixed with `bash` (e.g.
`bash .claude/hooks/pre-tool-use.sh`), not a bare `.sh` path.

On Windows a bare `.sh` path is handed to the shell, which has no file
association for `.sh` and pops the **"How do you want to open this file? /
Pick an app"** dialog. Because `PreToolUse` fires before every Bash tool call,
those dialogs pile up. Prefixing with `bash` routes the script through Git Bash
(shipped with Git for Windows), so it runs instead of prompting. The scripts
still self-degrade to no-ops outside Claude Code via their environment-variable
checks.

---

## Out of scope

- Windows-specific hook logic (PowerShell equivalents are not provided; the
  Bash scripts run under Git Bash and are no-ops when `CLAUDE_TOOL_NAME` /
  `CLAUDE_SESSION_ID` are not set).
- Modifying Claude Code itself.
