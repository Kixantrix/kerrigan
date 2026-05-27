## Summary

Three friction-points from the 2026-05-27 dispatch incident, encoded as small harness fixes. Stacks on top of #298 (pre-flight check) — will rebase cleanly after #298 merges.

## Changes

### `tools/new-issue.ps1` (new)
Single-issue dispatch wrapper that always reads body from a file (`--body-file`). Eliminates the PowerShell heredoc footgun that fired `gh issue create` twice on 2026-05-27, creating duplicate issues #293+#295 and duplicate PRs #294+#296. Use this in place of any inline `gh issue create --body "..."` with multi-line content.

### `tools/pr-promote.ps1` (fix)
`gh pr ready` and `gh pr update-branch` write their success banners to **stderr**. With `$ErrorActionPreference = 'Stop'`, PowerShell converted those stderr writes into terminating errors, which `Invoke-Step` caught and reported as `[FAIL]` even though the underlying gh commands succeeded. Fix: redirect `2>&1` so success banners flow through stdout.

### `.github/agents/cloud.md` (rule)
Two new self-verification rules:
- **Dep manifest must match imports.** If a test imports `bs4`, `beautifulsoup4` must be in `requirements.txt` *on the same branch*. Cloud CI runs in clean containers — missing manifest entries fail there even when the agent's local container has the package cached. Named cautionary case: 2026-05-27 PR #289 pushed a test importing `bs4` without updating `requirements.txt`.
- **Rebase + conflict block.** Cloud agent must `git fetch && git rebase origin/<base>` before pushing. If conflicts touch files outside the briefing's `Touch` list or can't be resolved confidently, emit a new `merge_conflict_unresolvable` block and stop. Previously the agent failed silently — PR #289 (M1.1 redispatch) needed conductor-side conflict resolution because the cloud agent had forked from older main and never reconciled.

### `.github/agents/kerrigan.md` (doc)
Updates the Dispatch subsection to point at `tools/new-issue.ps1` as the preferred single-issue path, calls out UTF-8 no-BOM encoding to prevent `ΓÇö`-style mojibake in issue bodies, and removes the misleading inline heredoc example.

## Note on `[WIP]`

A correction worth flagging: the `[WIP]` prefix in cloud-agent PR titles is **Copilot's own signal** — the cloud agent decides when to flip it. The reopen comment on #293 wrongly instructed the agent not to flip `[WIP]`; that's been retracted. The actual defense against premature flips is the mandatory pre-flight diff check landed in #298.

## Test plan

- [ ] `tools/new-issue.ps1 -DryRun -Title test -BodyFile README.md -Label agent:go` prints the planned command without executing
- [ ] `tools/pr-promote.ps1 <some-draft-pr> -DryRun` runs through all four steps with `[OK]` (no false `[FAIL]`)
- [ ] CI green (no Python/JS changes, validators unaffected)

## Stacking

This branch is based on `chore/promote-preflight` (#298). After #298 merges, this PR will auto-update against `main` cleanly.
