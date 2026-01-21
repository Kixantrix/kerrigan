# Git Operations Best Practices for Agents

This document provides guidelines for agents performing git operations, particularly for scenarios that could cause agent stalls or workflow interruptions.

## Critical: Preventing Interactive Editor Stalls

### Problem

When running git commands that require user input (like `git rebase --continue`, `git commit`, or `git merge`), git may open an interactive text editor (nano, vi, vim, emacs, etc.) to allow the user to edit commit messages or resolve issues.

For AI agents, entering an interactive editor mode causes **complete workflow stalls** because:
- The agent cannot send input to text editors
- The agent cannot escape from editor mode
- The entire workflow blocks until manual intervention
- Progress is lost and requires manual cleanup

### Solution: Always Set GIT_EDITOR

**ALWAYS** set the `GIT_EDITOR` environment variable to `'true'` before running any git command that might require user input:

```bash
# For single commands (preferred for agent operations)
GIT_EDITOR='true' git rebase --continue
GIT_EDITOR='true' git commit --amend
GIT_EDITOR='true' git merge --continue

# For shell sessions (if running multiple commands)
export GIT_EDITOR='true'
git rebase --continue
git commit --amend
```

The `true` command:
- Exits immediately with success status (exit code 0)
- Causes git to use default commit messages without opening an editor
- Prevents the agent from entering interactive mode
- Enables autonomous workflow completion

### PowerShell Syntax

For PowerShell scripts and Windows environments:

```powershell
# Set environment variable and run command
$env:GIT_EDITOR = 'true'; git rebase --continue
$env:GIT_EDITOR = 'true'; git commit --amend
$env:GIT_EDITOR = 'true'; git merge --continue
```

## Git Rebase Operations

### Basic Rebase Workflow

When rebasing a branch onto main:

```bash
# Checkout the branch
gh pr checkout <PR#>
# or
git checkout <branch-name>

# Fetch latest changes
git fetch origin

# Start rebase
git rebase origin/main
```

### Handling Rebase Conflicts

When conflicts occur during rebase:

```bash
# 1. View conflicts
git status

# 2. Resolve conflicts in files
# Edit files to resolve conflicts, then:

# 3. Stage resolved files
git add .

# 4. Continue rebase (CRITICAL: Use GIT_EDITOR='true')
GIT_EDITOR='true' git rebase --continue

# 5. Force push (use --force-with-lease for safety)
git push --force-with-lease
```

**Never** run `git rebase --continue` without `GIT_EDITOR='true'` in an agent context.

### Alternative: Use --no-edit Flag

Some git versions support a `--no-edit` flag that achieves the same result:

```bash
git rebase --continue --no-edit
```

However, this flag is not available in all git versions, so **always prefer using `GIT_EDITOR='true'`** for maximum compatibility.

## Commit Operations

### Amending Commits

When amending the last commit:

```bash
# Stage changes
git add .

# Amend without opening editor
GIT_EDITOR='true' git commit --amend

# Or specify message directly
git commit --amend -m "Updated commit message"
```

### Creating Commits

Always specify commit messages directly on the command line:

```bash
# Good: Message provided inline
git commit -m "Fix: Update validation logic"

# Avoid: This opens an editor
git commit
```

## Merge Operations

When performing manual merges:

```bash
# Merge with explicit message
git merge origin/main -m "Merge main into feature branch"

# If merge has conflicts and requires continuation:
git add .
GIT_EDITOR='true' git merge --continue
```

## Cherry-Pick Operations

When cherry-picking commits:

```bash
# Cherry-pick with explicit message
git cherry-pick <commit-sha> -m "Cherry-picked fix from main"

# If conflicts occur:
git add .
GIT_EDITOR='true' git cherry-pick --continue
```

## Global Configuration (Optional)

For development environments where agents frequently perform git operations, you can set `GIT_EDITOR` globally:

```bash
# Set globally (affects all git operations in this environment)
git config --global core.editor "true"
```

However, **this is not recommended for production environments** as it affects all users and may interfere with human developers who need interactive editing.

## Force Push Safety

When force-pushing after rebases:

```bash
# Safer: Only force push if remote hasn't changed
git push --force-with-lease

# Dangerous: Force push regardless of remote state
# Avoid unless absolutely necessary
git push --force
```

Always prefer `--force-with-lease` to prevent accidentally overwriting others' work.

## Common Git Operations Reference

### Check Status
```bash
# Always disable pager for agent operations
git --no-pager status
git --no-pager diff
```

### View Changes
```bash
# View diff without pager
git --no-pager diff
git --no-pager show <commit-sha>

# View specific file in commit
git --no-pager show <commit-sha>:<file-path>
```

### Abort Operations

If something goes wrong, you can abort most git operations:

```bash
# Abort rebase
git rebase --abort

# Abort merge
git merge --abort

# Abort cherry-pick
git cherry-pick --abort
```

## Error Recovery

### If Agent Enters Editor Mode

If an agent accidentally enters editor mode:

1. **Human intervention required** - A human must:
   - Press `Ctrl+C` or `Ctrl+X` to exit the editor
   - Or close the terminal/session
   
2. **Clean up git state**:
   ```bash
   # Check for in-progress operations
   git status
   
   # Abort the operation if needed
   git rebase --abort
   # or
   git merge --abort
   ```

3. **Restart the operation** with proper `GIT_EDITOR` setting

### Cleaning Up Failed Rebases

If a rebase fails and leaves the repository in a bad state:

```bash
# Check status
git status

# If rebase is in progress, abort it
git rebase --abort

# Reset to clean state
git fetch origin
git reset --hard origin/<branch-name>

# Start over with proper settings
GIT_EDITOR='true' git rebase origin/main
```

## Best Practices Summary

✅ **DO:**
- Always set `GIT_EDITOR='true'` for interactive git commands
- Use `--no-pager` for git commands that display output
- Specify commit messages inline with `-m` flag
- Use `--force-with-lease` instead of `--force`
- Check `git status` before and after operations
- Abort failed operations and restart cleanly

❌ **DON'T:**
- Run `git rebase --continue` without `GIT_EDITOR`
- Run `git commit` without `-m` flag in agent context
- Use `git commit --amend` without `GIT_EDITOR` or explicit message
- Use interactive git features (rebase -i, commit --interactive, etc.)
- Rely on git opening an editor for any operation

## See Also

- [Triage Playbook](../playbooks/triage.md) - Includes rebase workflows
- [Triage Agent Prompt](../.github/agents/role.triage.md) - Manual rebase section
- [Agent Feedback: Git Rebase Interactive Mode](../feedback/agent-feedback/2026-01-18-96-git-rebase-interactive-mode.yaml) - Original issue report that led to this document

## Feedback

If you encounter issues with git operations or discover additional patterns:
- Submit feedback using the template at `feedback/agent-feedback/TEMPLATE.yaml`
- Follow the naming convention: `YYYY-MM-DD-<issue-number>-<short-slug>.yaml`
- See [Agent Feedback Specification](../specs/kerrigan/080-agent-feedback.md) for complete details
