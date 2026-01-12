# PR Review Script

Systematic script for managing Copilot reviews on open pull requests with enhanced agentic capabilities for auto-merge, next-step issue generation, and workflow orchestration.

## Usage

### Check PR status
```powershell
.\tools\review-prs.ps1
```

### Check PR status (dry run)
```powershell
.\tools\review-prs.ps1 -DryRun
```

### Mark draft PRs as ready for review
```powershell
.\tools\review-prs.ps1 -MarkReadyForReview
```

### Approve pending workflow runs (fix CI approval issues)
```powershell
.\tools\review-prs.ps1 -ApproveWorkflows
```

### Auto-merge approved PRs (⚠️ Use with caution)
```powershell
# Dry run first to see what would be merged
.\tools\review-prs.ps1 -AutoMerge -DryRun

# Actually merge approved PRs
.\tools\review-prs.ps1 -AutoMerge
```

### Generate next-step issues after merging
```powershell
.\tools\review-prs.ps1 -AutoMerge -GenerateNextIssues
```

### Full agentic workflow (merge + issues + status update)
```powershell
# Dry run to test the full workflow
.\tools\review-prs.ps1 -AutoMerge -GenerateNextIssues -UpdateStatus -DryRun

# Execute full workflow
.\tools\review-prs.ps1 -AutoMerge -GenerateNextIssues -UpdateStatus
```

## What it does

### Basic Features (Original)
1. **Finds all open PRs** (lists drafts but doesn't modify them by default)
2. **Marks PRs ready** (with `-MarkReadyForReview` flag)
3. **Approves pending CI workflows** (with `-ApproveWorkflows` flag)
4. **Checks review status** and reports:
   - Pending reviews
   - Approved PRs (ready to merge)
   - PRs with requested changes

### Enhanced Agentic Features (New)

#### 🤖 Intelligent PR Triage
- Analyzes PR content and CI status
- Checks for merge conflicts
- Validates PR description and linked issues
- Determines if PR is ready for merge based on:
  - ✅ CI passing
  - ✅ No merge conflicts
  - ✅ Approved reviews
  - ✅ No unresolved review comments

#### 🔀 Auto-Merge Capability
With `-AutoMerge` flag, the script will:
- Automatically merge PRs that meet all criteria
- Use squash merge for clean history
- Delete branch after merge
- Post notification comment on merged PR
- Track linked issues for closure

**Safety Features:**
- Requires explicit `-AutoMerge` flag (off by default)
- Verifies no unresolved review comments
- Checks that CI is truly green (not just pending)
- Validates merge conflicts are resolved
- Always use `-DryRun` first to preview actions

#### 📝 Next-Step Issue Generation
With `-GenerateNextIssues` flag, the script will:
- Parse `specs/projects/kerrigan/tasks.md` to understand task dependencies
- Identify what was completed in merged PR
- Determine next logical step in the milestone
- Create issues for next tasks with:
  - Appropriate labels (`kerrigan`, `agent:go`)
  - Links to merged PR
  - Context about milestone and task dependencies
- Avoid creating duplicate issues

#### 📊 Workflow Orchestration
With `-UpdateStatus` flag, the script will:
- Update `specs/projects/kerrigan/status.json` after merges
- Track milestone completion progress
- Add timestamp and notes about updates
- Enable project status visibility

## Why CI Needs Approval

GitHub requires manual approval for workflows from certain contributors for security reasons:
- PRs from `copilot-swe-agent` or similar bots need approval
- This prevents malicious code in workflows from running automatically
- Use `-ApproveWorkflows` flag to approve pending CI runs via CLI
- Or approve manually at: https://github.com/Kixantrix/kerrigan/actions

## Why Copilot Can't Be a PR Reviewer

"Copilot" is not a standard GitHub user account and cannot be assigned as a PR reviewer. It only works for issue assignments. For PR reviews, use:
- Manual review by repository collaborators
- GitHub's built-in review features
- Rely on CI checks and validators

## Workflow Examples

### Daily PR Management
```powershell
# 1. Check PR status and identify workflows needing approval
.\tools\review-prs.ps1

# 2. Approve workflows in web UI or via script
.\tools\review-prs.ps1 -ApproveWorkflows

# 3. Wait for CI to complete, then check again
.\tools\review-prs.ps1

# 4. Review and optionally auto-merge approved PRs
.\tools\review-prs.ps1 -AutoMerge -GenerateNextIssues -UpdateStatus -DryRun
.\tools\review-prs.ps1 -AutoMerge -GenerateNextIssues -UpdateStatus
```

### Safe Testing Workflow
```powershell
# Always test with dry run first
.\tools\review-prs.ps1 -AutoMerge -GenerateNextIssues -UpdateStatus -DryRun

# Review output, then execute if satisfied
.\tools\review-prs.ps1 -AutoMerge -GenerateNextIssues -UpdateStatus
```

### Manual Merge (Traditional)
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

## Parameters

- `-DryRun`: Show what would happen without making changes
- `-MarkReadyForReview`: Convert draft PRs to ready for review  
- `-ApproveWorkflows`: Approve pending GitHub Actions workflow runs
- `-AutoMerge`: **⚠️ Automatically merge approved PRs** (use with caution!)
- `-GenerateNextIssues`: Create issues for next logical steps after merging
- `-UpdateStatus`: Update project status.json after merges

## Requirements

- GitHub CLI (`gh`) must be installed and authenticated
- Write access to repository for merging PRs
- Tasks tracking file at `specs/projects/kerrigan/tasks.md` (for issue generation)

## Safety Notes

⚠️ **Important**: The `-AutoMerge` flag will automatically merge PRs without additional confirmation. Always:
1. Test with `-DryRun` first
2. Review the output carefully
3. Ensure you understand which PRs will be merged
4. Have a rollback plan if needed

The script includes multiple safety checks:
- Verifies review approval
- Checks CI status comprehensively
- Validates no merge conflicts
- Ensures no unresolved review comments
- Posts notification comments on actions taken

## Example Output

```
========================================
Systematic PR Review - Kerrigan
========================================

AUTO-MERGE MODE: Will merge approved PRs
ISSUE GENERATION MODE: Will create next-step issues
STATUS UPDATE MODE: Will update status.json

Found 3 open PR(s)

Processing PR #42: Implement feature X
  CI: 2 workflow(s) passing
  Review: APPROVED
   Ready to merge!

  🤖 Evaluating for auto-merge...
  ✅ All merge criteria met!
  🔀 Merging PR #42...
  ✅ PR merged successfully!
  📝 Posted merge notification

========================================
Generating Next-Step Issues
========================================

📋 Loaded 45 tasks from specs/projects/kerrigan/tasks.md

Processing merged PR #42: Implement feature X
  📝 Next task identified: Add tests for feature X
     Milestone: Milestone 3: Testing
  📤 Creating issue: Add tests for feature X
  ✅ Created issue: #43
  📊 Updating project status...
  ✅ Updated status.json

========================================
Review complete!
✅ Merged 1 PR(s)
========================================
```
