# Playbook: Bootstrap Kerrigan v2 in a repo

> For new repos and v1 satellites migrating. ~5 minutes.

## Prereqs

- Python 3.11+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (for spec-kit)
- Git
- VS Code with GitHub Copilot (or Claude Code, or Copilot CLI)

Install `uv` once on your machine if you don't have it:

```powershell
# Windows (winget)
winget install --id=astral-sh.uv -e
```

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## New repo: 3 commands

```powershell
# 1. Install spec-kit and scaffold
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify init . --ai copilot --ai claude

# 2. Add kerrigan v2 layer (placeholder — real command lands in Phase 1)
$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) 'kerrigan'
git clone https://github.com/Kixantrix/kerrigan --depth 1 $tmpDir
Copy-Item -Recurse -Force `
    (Join-Path $tmpDir 'AGENTS.md'), `
    (Join-Path $tmpDir 'CLAUDE.md'), `
    (Join-Path $tmpDir '.github/agents'), `
    (Join-Path $tmpDir '.github/skills'), `
    (Join-Path $tmpDir '.github/copilot-instructions.md'), `
    (Join-Path $tmpDir 'specs/kerrigan-v2'), `
    (Join-Path $tmpDir 'scripts/mirror-agents.ps1'), `
    (Join-Path $tmpDir 'tools/validators/agents_md.py'), `
    (Join-Path $tmpDir 'tools/pr_comments.py') `
    .
Remove-Item -Recurse -Force $tmpDir

# 3. Mirror agents into .claude/ for Claude Code
# If specify init created .claude/agents/ as a real directory, remove it first
if (Test-Path '.claude/agents' -PathType Container) {
    $item = Get-Item '.claude/agents' -Force
    if (-not $item.LinkType) { Remove-Item -Recurse -Force '.claude/agents' }
}
pwsh scripts/mirror-agents.ps1

# Sanity check
python tools/validators/agents_md.py
```

## Migrate a v1 satellite

```powershell
# From the satellite repo root
# 1. Install spec-kit
specify init . --ai copilot --ai claude

# 2. Pull v2 agent profiles, skills, AGENTS.md from kerrigan
#    (same as above — eventually replaced by a preset or script)

# 3. Move v1 role agents out of the way
git mv .github/agents/role.*.md .github/agents/_legacy/ 2>$null

# 4. Mirror for Claude Code
pwsh scripts/mirror-agents.ps1

# 5. Validate
python tools/validators/agents_md.py
```

## After bootstrap

1. **Add 4 v2 labels** (if you use GH issues):
   - `agent:go`, `agent:wait`, `agent:local`, `autonomy:override`
   - Script: TBD in Phase 1

2. **Enable Copilot PR review** for all PRs:
   - Follow [playbooks/copilot-review-setup.md](./copilot-review-setup.md) (Settings → Code review → Copilot → Enable for all pull requests).

3. **Set project principles** once:
   ```
   /speckit.constitution <describe your project's principles>
   ```

4. **Try your first task.** In VS Code chat (or Claude Code, or Copilot CLI), talk to the `local` profile:
   > @local I want to add X. Plan it and dispatch.

## What's installed after this

- `.specify/` — spec-kit state, templates, slash commands.
- `AGENTS.md` — canonical agent entry.
- `.github/agents/{local,cloud,kerrigan}.md` + `adapters/` — v2 profiles.
- `.claude/agents/` — junction into the same files, for Claude Code.
- `.github/skills/` — briefing-packet, block-report, delegation-rubric, smoke-test.
- `CLAUDE.md` + `.github/copilot-instructions.md` — redirects to AGENTS.md.
- `tools/validators/agents_md.py` — frontmatter + AGENTS.md validator.

## What's *not* yet installed (Phase 1+)

- `/kerrigan.dispatch` slash command (wraps `/speckit.taskstoissues`).
- `kerrigan-conflict-predictor` extension.
- `kerrigan-briefing` extension.
- `spec-kit-verify` + `spec-kit-verify-tasks` + `spec-kit-ci-guard` preset defaults.
- `scripts/smoke.sh` template + CI.
- 4-label installer script.

## Troubleshooting

**`specify` not found after install:** Check `uv tool list`. Add `%USERPROFILE%\.local\bin` to PATH (Windows) or `~/.local/bin` (Unix).

**Junction fails on Windows:** Make sure `.claude/agents/` doesn't exist as a real directory already. Delete it first.

**Validator fails "name does not match filename":** Your profile's `name:` field and filename must match. `local.md` must have `name: local`.
