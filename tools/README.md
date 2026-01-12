# PR Review Script

Systematic script for managing Copilot reviews on open pull requests.

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

## What it does

1. **Finds all open PRs** (lists drafts but doesn't modify them by default)
2. **Marks PRs ready** (with `-MarkReadyForReview` flag)
3. **Approves pending CI workflows** (with `-ApproveWorkflows` flag)
4. **Checks review status** and reports:
   - Pending reviews
   - Approved PRs (ready to merge)
   - PRs with requested changes

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

## Workflow

Run this script periodically to:
- Ensure all PRs have Copilot assigned for review
- Check which PRs are ready to merge
- Ping @copilot on PRs with requested changes

## Parameters

- `-DryRun`: Show what would happen without making changes
- `-MarkReadyForReview`: Convert draft PRs to ready for review  
- `-ApproveWorkflows`: Approve pending GitHub Actions workflow runs

## Requirements

- GitHub CLI (`gh`) must be installed and authenticated
- Repository must have "Copilot" as a valid reviewer

## Example Output

```
========================================
Systematic PR Review - Kerrigan
========================================

Found 5 open PR(s)

Processing PR #30: Update status.json
  Status: Waiting for Copilot review

Processing PR #29: Add validation suite
  Copilot reviewed: APPROVED
  Status: Ready to merge!

Processing PR #28: Add hello-cli example
  Copilot reviewed: CHANGES_REQUESTED
  Action: Notify @copilot to address feedback
  Posted comment

========================================
Review complete!
========================================
```
