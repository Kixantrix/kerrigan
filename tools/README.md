# PR and Issue Management Scripts

Scripts for managing pull requests and issues in the Kerrigan repository.

## Requirements

- **PowerShell 5.1 or later** - All scripts are compatible with both PowerShell 5.1 (Windows PowerShell) and PowerShell 7+ (PowerShell Core)
- **GitHub CLI (`gh`)** - Must be installed and authenticated (`gh auth login`)

### Installing PowerShell

- **Windows**: PowerShell 5.1 is pre-installed. For PowerShell 7+, see [PowerShell installation guide](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows)
- **macOS/Linux**: Install PowerShell 7+ from [PowerShell installation guide](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell)

## Scripts

### Upgrade Kerrigan (upgrade-kerrigan.ps1)

Upgrade Kerrigan components from the main repository to get latest improvements.

**Usage:**
```powershell
# Preview what would change
.\tools\upgrade-kerrigan.ps1 -DryRun

# Show detailed diff
.\tools\upgrade-kerrigan.ps1 -ShowDiff

# Upgrade specific components
.\tools\upgrade-kerrigan.ps1 -Components workflows,prompts

# Upgrade all components
.\tools\upgrade-kerrigan.ps1 -Components all
```

**See also**: [playbooks/upgrade-satellite.md](../playbooks/upgrade-satellite.md) for complete upgrade guide.

### PR Review Script (review-prs.ps1)

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

Run these scripts to manage your PRs and issues:

1. **Triage PRs**: `.\tools\triage-prs.ps1` - See what needs attention
2. **Review PRs**: `.\tools\review-prs.ps1` - Add Copilot as reviewer
3. **View Details**: `.\tools\show-prs.ps1` or `.\tools\show-issues.ps1` - Formatted tables

Run the review script periodically to:
- Ensure all PRs have Copilot assigned for review
- Check which PRs are ready to merge
- Ping @copilot on PRs with requested changes

## Parameters

- `-DryRun`: Show what would happen without making changes
- `-MarkReadyForReview`: Convert draft PRs to ready for review

### PR Triage Dashboard (triage-prs.ps1)

Main triage workflow script for viewing PRs by category and suggested actions.

**Usage:**
```powershell
.\tools\triage-prs.ps1              # Show PRs needing attention
.\tools\triage-prs.ps1 -ShowAll     # Show all PRs
.\tools\triage-prs.ps1 -DryRun      # Preview without actions
```

**Parameters:**
- `-ShowAll`: Show all PRs regardless of status
- `-DryRun`: Show what would be done without taking any actions

### Show PRs (show-prs.ps1)

Display open pull requests in a formatted table.

**Usage:**
```powershell
.\tools\show-prs.ps1                     # Show open PRs
.\tools\show-prs.ps1 -State all -Limit 50  # Show all PRs
```

**Parameters:**
- `-State`: PR state to filter by (open, closed, merged, all). Default: open
- `-Limit`: Maximum number of PRs to display. Default: 20

### Show Issues (show-issues.ps1)

Display open issues in a formatted table.

**Usage:**
```powershell
.\tools\show-issues.ps1                      # Show open issues
.\tools\show-issues.ps1 -State all -Limit 50   # Show all issues
```

**Parameters:**
- `-State`: Issue state to filter by (open, closed, all). Default: open
- `-Limit`: Maximum number of issues to display. Default: 20

### Create Issue (create-issue.ps1)

Create a GitHub issue from a markdown file or inline content. Supports YAML frontmatter for metadata.

**Usage:**
```powershell
# From inline content
.\tools\create-issue.ps1 -Title "Fix bug" -Body "Description" -Labels "bug,role:swe"

# From markdown file (title extracted from first # heading)
.\tools\create-issue.ps1 -BodyFile "./my-issue.md" -Labels "enhancement"

# Assign @copilot automatically
.\tools\create-issue.ps1 -BodyFile "./issue.md" -AssignCopilot

# Preview without creating
.\tools\create-issue.ps1 -BodyFile "./issue.md" -DryRun
```

**Parameters:**
- `-Title`: Issue title (optional if body has # heading)
- `-Body`: Issue body text
- `-BodyFile`: Path to markdown file with issue body
- `-Labels`: Comma-separated labels
- `-AssignCopilot`: Assign @copilot and add agent:go label
- `-DryRun`: Preview without creating

**Frontmatter support:**
```markdown
---
title: My Issue Title
labels: bug,role:swe,kerrigan
---
Issue body starts here...
```

### Batch Create Issues (batch-create-issues.ps1)

Process multiple markdown files from a staging directory and create issues.

**Usage:**
```powershell
# Process all .md files in ./temp-issues/
.\tools\batch-create-issues.ps1 -AssignCopilot

# Custom input directory
.\tools\batch-create-issues.ps1 -InputDir "./my-issues" -AssignCopilot

# Preview without creating
.\tools\batch-create-issues.ps1 -DryRun

# Delete files after creation (default: move to processed/)
.\tools\batch-create-issues.ps1 -DeleteAfter
```

**Parameters:**
- `-InputDir`: Directory with markdown files (default: ./temp-issues)
- `-Pattern`: File pattern to match (default: *.md)
- `-AssignCopilot`: Assign @copilot to all issues
- `-DeleteAfter`: Delete files after creation (default: move to processed/)
- `-DryRun`: Preview without creating

### Satellite Feedback Script (feedback-to-kerrigan.ps1)

Submit feedback from a satellite Kerrigan installation (your repo using Kerrigan) to the main repository. Helps improve Kerrigan for everyone!

**Usage:**
```powershell
# Interactive mode (recommended)
.\tools\feedback-to-kerrigan.ps1

# Pre-select category
.\tools\feedback-to-kerrigan.ps1 -Category bug

# Save as file without creating issue
.\tools\feedback-to-kerrigan.ps1 -SaveOnly

# Preview what would be created
.\tools\feedback-to-kerrigan.ps1 -DryRun
```

**Parameters:**
- `-Category`: Type of feedback (bug, enhancement, pattern, question)
- `-SaveOnly`: Save as markdown file without creating GitHub issue
- `-DryRun`: Preview without creating
- `-MainRepo`: Target repository (default: Kixantrix/kerrigan)

**What it does:**
1. Collects feedback from you interactively
2. Auto-detects your Kerrigan version
3. Categorizes feedback (bug, enhancement, pattern, question)
4. Creates GitHub issue in main Kerrigan repo (with your permission)
5. Or saves as markdown file for manual submission

**Privacy:** You can submit feedback anonymously or include your repo information.

See [feedback/satellite/README.md](../feedback/satellite/README.md) for more about the satellite feedback system.

## Style Guidelines

All PowerShell scripts follow the [PowerShell Style Guide](../docs/powershell-style-guide.md) which ensures:
- Compatibility with PowerShell 5.1 and later
- ASCII-only characters (no Unicode emojis or box-drawing characters)
- Clear version requirements and error messages

## Troubleshooting

### "string terminator missing" error

If you encounter this error on PowerShell 5.1, the script may contain Unicode characters. All scripts in this repository have been updated to use ASCII-only characters for compatibility.

### PowerShell version check fails

If the script reports an incompatible PowerShell version:
- On Windows: Update to PowerShell 5.1 or later
- On macOS/Linux: Install PowerShell 7+
- Check your version: `$PSVersionTable.PSVersion`

### GitHub CLI errors

If you see errors about `gh` command:
- Install GitHub CLI: https://cli.github.com/
- Authenticate: `gh auth login`
- Verify: `gh auth status`

## Related Documentation

- [PowerShell Style Guide](../docs/powershell-style-guide.md) - Coding standards for PowerShell scripts
- [Automation Limits](../docs/automation-limits.md) - What can be automated
- [PR Review Playbook](../playbooks/pr-review.md) - Human review guidelines

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
