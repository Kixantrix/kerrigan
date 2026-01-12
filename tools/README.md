# PR Review Script

Systematic script for managing Copilot reviews on open pull requests.

## Usage

### Check PR status
```powershell
.\tools\review-prs.ps1 -DryRun
```

### Mark draft PRs as ready and add Copilot as reviewer
```powershell
.\tools\review-prs.ps1 -MarkReadyForReview
```

### Add Copilot as reviewer to PRs without review
```powershell
.\tools\review-prs.ps1
```

## What it does

1. **Finds all open PRs** (lists drafts but doesn't modify them by default)
2. **Marks PRs ready** (with `-MarkReadyForReview` flag)
3. **Adds Copilot as reviewer** if not already reviewing
4. **Checks review status** and reports:
   - Pending reviews
   - Approved PRs (ready to merge)
   - PRs with requested changes
5. **Posts comments** to notify @copilot when changes are requested

## Workflow

Run this script periodically to:
- Ensure all PRs have Copilot assigned for review
- Check which PRs are ready to merge
- Ping @copilot on PRs with requested changes

## Parameters

- `-DryRun`: Show what would happen without making changes
- `-MarkReadyForReview`: Convert draft PRs to ready for review

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
