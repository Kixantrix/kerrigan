# CI Approval and PR Review Issues - Explained

## Issue 1: Script Keeps Trying to Add Copilot as Reviewer

### Problem
The script repeatedly tried to add "Copilot" as a PR reviewer but kept failing silently.

### Root Cause
**"Copilot" is not a valid GitHub user for PR reviews.** It's a special bot account that only works for:
- Issue assignments ✅
- PR authorship (as `copilot-swe-agent`) ✅  
- PR reviewer assignments ❌

### Solution
Updated `tools/review-prs.ps1` to:
- Remove attempts to add Copilot as reviewer
- Focus on workflow approval and status reporting
- Clarify in output that Copilot can't be a reviewer

### Workaround for Reviews
Since Copilot can't review PRs:
1. Rely on CI checks (validators, tests)
2. Manual review by repository collaborators
3. Use `@copilot` mentions in PR comments for questions
4. Approve based on CI passing + manual spot checks

---

## Issue 2: CI Needs Manual Approval

### Problem
GitHub Actions workflows show "Action required" and need manual approval in the web interface before running.

### Root Cause
GitHub's **security feature** for workflows from external contributors:
- PRs from `copilot-swe-agent` are treated as external
- Prevents malicious workflow code from running automatically
- Requires repository maintainer approval

This affects:
- First-time contributor workflows
- Bot account workflows  
- Fork-based PRs

### How to Approve (Web UI)
1. Go to https://github.com/Kixantrix/kerrigan/actions
2. Find workflows with yellow "Approval required" badge
3. Click "Review pending deployments"
4. Check workflows and click "Approve and run"

### Automated Solution (Attempted)
Created `-ApproveWorkflows` flag in script to approve via GitHub API:
```powershell
.\tools\review-prs.ps1 -ApproveWorkflows
```

**Result**: API calls fail - requires admin permissions that CLI token may not have.

### Better Solution: Configure Repository Settings

To avoid needing approval for every PR from copilot-swe-agent:

#### Option 1: Add copilot-swe-agent as Collaborator (if possible)
- Settings → Collaborators → Add `copilot-swe-agent`
- Grant "Write" permissions
- Workflows from collaborators don't need approval

#### Option 2: Disable First-Time Contributor Approval
**⚠️ Less secure**
- Settings → Actions → General
- Under "Fork pull request workflows from outside collaborators"
- Change to "Require approval for first-time contributors who recently created a GitHub account"
- Or "Run workflows from fork pull requests"

#### Option 3: Create GitHub App Token with More Permissions
- Create a GitHub App with `actions:write` permission
- Use app token instead of personal access token
- Script could then approve workflows programmatically

#### Option 4: Manual Approval (Current State)
- Keep security tight
- Manually approve each workflow run
- Use script to identify which runs need approval

---

## Current Recommended Workflow

### Daily PR Management
```powershell
# 1. Check PR status and identify workflows needing approval
.\tools\review-prs.ps1

# 2. Approve workflows in web UI
# https://github.com/Kixantrix/kerrigan/actions

# 3. Wait for CI to complete, then check again
.\tools\review-prs.ps1

# 4. Review and merge approved PRs
gh pr view <number>
gh pr review <number> --approve
gh pr merge <number> --squash
```

### For Multiple PRs
```powershell
# Get list of PRs needing attention
gh pr list

# For each PR, review and merge if ready
foreach ($pr in 26,27,28,29) {
    gh pr checks $pr
    # If checks pass:
    gh pr review $pr --approve --body "CI passing, looks good!"
    gh pr merge $pr --squash --delete-branch
}
```

---

## Updated Script Features

The `tools/review-prs.ps1` script now:

✅ Detects workflows with `action_required` status  
✅ Shows which workflows need approval  
✅ Reports CI pass/fail status  
✅ Shows review status (approved, changes requested, pending)  
✅ Identifies ready-to-merge PRs  
❌ Cannot automatically approve workflows (API limitations)  
❌ Does not try to add Copilot as reviewer (not possible)

---

## Next Steps

1. **Short term**: Manually approve the ~35 pending workflow runs via web UI
2. **Medium term**: Consider adding copilot-swe-agent as repository collaborator if supported
3. **Long term**: Implement in issue #33 - full agentic PR management with proper permissions
