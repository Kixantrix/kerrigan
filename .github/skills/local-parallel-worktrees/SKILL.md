# Skill: local-parallel-worktrees

**When:** running >=2 local agents on one machine, or when you want an isolated experiment branch without disturbing the main checkout.
**Why:** each local agent needs an isolated working tree/branch to avoid collisions in branch state, build artifacts, and dependency directories.

## Lifecycle

1. **Create**: `scripts/worktree.ps1 new <task-id>` (Windows) or `scripts/worktree.sh new <task-id>` (POSIX).
2. **Work**: open the new worktree path, implement the task, and commit/push from that worktree.
3. **Clean up**: after PR merge, remove with `scripts/worktree.ps1 remove <task-id>` (or `scripts/worktree.sh remove <task-id>`).

## Commands

- `new <task-id>`: create `../<repo>-worktrees/<task-id>/` on `task/<task-id>` from current HEAD. Copies repo-root `.env` if present.
- `list`: show active worktrees with branch + dirty state.
- `remove <task-id>`: remove the worktree and delete `task/<task-id>` branch (warns on unmerged branch unless forced).
- `prune`: run `git worktree prune` to clear stale metadata.

Optional flags:
- `-Bootstrap` / `--bootstrap` (on `new`): install dependencies in the new worktree.
- `-Force` / `--force` (on `remove`): remove dirty worktrees and force-delete unmerged branch.

## Windows gotchas

- If `git config --get core.longpaths` is not `true`, enable it: `git config core.longpaths true`.
- `node_modules` and virtualenv folders are per-worktree by design; do not symlink them because isolation must hold.
- In VS Code, use **Open Folder** on the specific worktree path; do not share one window across the main checkout and multiple worktrees.

## Cross-platform notes

- Use PowerShell (`scripts/worktree.ps1`) on Windows and bash (`scripts/worktree.sh`) elsewhere.
- WSL users can optionally use `claude-squad` (`cs`) as a TUI over the same git-worktree primitive; this harness does not couple to that tool.

## Interaction with Kerrigan briefings

When a local-routed task is dispatched, the briefing's suggested worktree id should match the task id. Create it directly with:
- `scripts/worktree.ps1 new <task-id>` or
- `scripts/worktree.sh new <task-id>`

Then do all task work inside that worktree directory.

## Cleanup discipline

- After each merged PR: `scripts/worktree.ps1 remove <task-id>` (or bash equivalent).
- After bulk/manual cleanup: `scripts/worktree.ps1 prune` (or bash equivalent) to clean stale entries.
