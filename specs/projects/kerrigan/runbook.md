# Runbook: Kerrigan

## Deploy
Kerrigan is a Git repository template, not a deployed service. "Deployment" means:
1. Fork or clone this repo
2. Enable GitHub Actions
3. Create required labels (see Operate section)
4. Customize `specs/constitution.md` to your team's values
5. Commit initial state to `main` branch

**Prerequisites**: GitHub account, Git CLI or GitHub Desktop

**Rollback**: revert to previous commit or re-clone template

## Operate

### Daily operation
1. **Start new project**: follow `playbooks/kickoff.md`
2. **Set autonomy mode**: choose mode in `playbooks/autonomy-modes.md`, apply labels accordingly
3. **Invoke agents**: use prompts from `.github/agents/` in your agent runtime (e.g., GitHub Copilot, Claude, etc.)
4. **Review PRs**: focus on scope/direction, not code quality (agents handle that)
5. **Merge**: once CI is green and direction is approved

### Control swarm behavior
- **Pause agent work**: remove `agent:go` label or set `status.json` to "blocked"
- **Resume agent work**: add `agent:go` label or set status to "active"
- **Override autonomy gate**: add `autonomy:override` label to PR (human-only)
- **Allow large file**: add `allow:large-file` label to PR (use sparingly)

### Monitor health
- **CI status**: check `.github/workflows/` for failures
- **Validator output**: read error messages for artifact/quality violations
- **PR velocity**: track open PRs per agent role
- **Cost**: monitor agent API usage (see cost-plan.md)

### Required GitHub labels
Create these labels in your repo (Settings → Labels):

**Autonomy**:
- `agent:go` (green) - allow agents to work on this issue
- `agent:sprint` (yellow) - sprint mode for milestone
- `autonomy:override` (red) - human override for autonomy gates
- `allow:large-file` (orange) - bypass quality bar file size limit

**Roles** (optional, for organization):
- `kerrigan` (purple)
- `spec` (blue)
- `architecture` (blue)
- `swe` (blue)
- `testing` (blue)
- `deploy` (blue)
- `security` (blue)

## Debug

### CI failing on artifacts
1. Read validator output: `python tools/validators/check_artifacts.py`
2. Check which files or sections are missing
3. Add missing content or fix file paths
4. Re-run validators locally before pushing

### CI failing on quality bar
1. Identify large file: `python tools/validators/check_quality_bar.py`
2. Refactor file into smaller modules
3. OR add `allow:large-file` label if justified (document why in PR)

### Agent produces wrong artifacts
1. Check agent prompt matches role in `.github/agents/role.<name>.md`
2. Verify agent has access to:
   - Constitution (`specs/constitution.md`)
   - Artifact contracts (`specs/kerrigan/020-artifact-contracts.md`)
   - Project spec (`specs/projects/<name>/spec.md`)
3. Provide corrective feedback in PR comments
4. Update agent prompts if pattern repeats

### Agent ignores autonomy mode
- Confirm labels are correctly set on issue, not just PR
- Check if `autonomy:override` was accidentally added
- Verify `.github/workflows/agent-gates.yml` is enabled
- Note: autonomy enforcement may require GitHub API integration (manual fallback: human PR review)

### Status tracking not working
- Verify `status.json` exists in project folder
- Check JSON is valid (no syntax errors)
- Confirm agent prompts include status check step
- Document issue in `playbooks/handoffs.md` for future refinement

## Rollback
- **Revert merged PR**: use `git revert <commit-hash>` or GitHub UI
- **Abandon project**: delete `specs/projects/<name>/` folder
- **Disable swarm**: remove all `agent:go` labels and stop invoking agent prompts
- **Reset to baseline**: restore from known-good commit in Git history

## Secrets & access
- **No secrets required**: Kerrigan operates on public repo content
- **Agent API keys**: stored per user/team in their agent runtime (e.g., GitHub Copilot, Anthropic API)
- **GitHub tokens**: only needed if implementing advanced autonomy gates via GitHub API (optional)
- **Principle**: follow least-privilege access; agents read repo, humans approve merges
