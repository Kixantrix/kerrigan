# Workflow Approval Configuration Guide

This guide helps you configure GitHub Actions to work smoothly with the PR review script's auto-merge and workflow approval features, based on [GitHub's documentation for approving runs from forks](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks).

## Understanding the Challenge

GitHub Actions requires manual approval for workflows from:
- **First-time contributors** (including bot accounts like `copilot-swe-agent`)
- **Fork-based pull requests**
- **PRs that modify workflow files** (`.github/workflows/*`)

This security feature prevents malicious workflow code from running automatically and potentially exposing secrets or abusing resources.

## Configuration Options

### Option 1: Repository Settings (Recommended for Most Cases)

Configure your repository to handle workflow approvals appropriately:

#### For Trusted Bot Accounts
**Navigate to**: `Settings → Actions → General → Fork pull request workflows`

**Recommended Setting**: "Require approval for first-time contributors who recently created a GitHub account"
- ✅ Allows established accounts (like `copilot-swe-agent`) to run without approval
- ✅ Still protects against newly created malicious accounts
- ⚠️ Requires human verification for truly new contributors

#### For Maximum Automation (Use with Caution)
**Setting**: "Require approval for all outside collaborators"
- ✅ Only requires approval from non-collaborators
- ⚠️ Less secure for public repositories
- 💡 Best for private repos or when combined with other protections

### Option 2: Add Bot as Collaborator (Best for Automation)

**Navigate to**: `Settings → Collaborators and teams → Add people`

**Add**: The bot account username (e.g., `copilot-swe-agent` if it's a valid GitHub user)
**Permission**: `Write` or `Triage` (minimum needed)

**Benefits**:
- ✅ Bot PRs run automatically without approval
- ✅ Script's `-ApproveWorkflows` becomes unnecessary for bot PRs
- ✅ Most seamless automation experience

**Limitations**:
- ⚠️ Requires bot account to be a real GitHub user
- ⚠️ Not possible if bot uses GitHub Apps authentication
- 💡 Check if your bot account can be added before choosing this option

### Option 3: GitHub App Token with Actions Permissions

**For**: Organizations using GitHub Apps for authentication

**Setup**:
1. Create a GitHub App with `actions:write` permission
2. Install app on repository
3. Use app token instead of personal access token for `gh` CLI
4. Script's `-ApproveWorkflows` flag will work programmatically

**Benefits**:
- ✅ Fine-grained access control
- ✅ Audit trail for workflow approvals
- ✅ Scales across multiple repositories

**Complexity**: Higher - requires app creation and maintenance

### Option 4: Protected Workflow Paths (Security-First Approach)

**Use When**: You want automation but need extra protection for workflow modifications

**Configuration**:
1. Use Option 1 or 2 for general workflow approvals
2. Add **manual review requirement** for PRs that touch `.github/workflows/`
3. Configure branch protection rules:
   - Require reviews for paths: `.github/workflows/*`
   - Require status checks before merging

**Implementation in Script**:
The review script can be enhanced to add discretion for workflow changes:

```powershell
# Check if PR modifies workflows
$modifiesWorkflows = $false
$files = gh pr view $pr.number --json files -q '.files[].path'
foreach ($file in $files) {
    if ($file -like ".github/workflows/*") {
        $modifiesWorkflows = $true
        break
    }
}

# Skip auto-merge for workflow changes
if ($modifiesWorkflows -and $AutoMerge) {
    Write-Host "  ⚠️  PR modifies workflows - skipping auto-merge" -ForegroundColor Yellow
    Write-Host "     Manual review required for security" -ForegroundColor Gray
    continue
}
```

## Recommendations by Use Case

### Solo Developer / Private Project
- **Configuration**: Option 2 (Add bot as collaborator) OR Option 1 with relaxed settings
- **Why**: Maximum automation with minimal overhead
- **Script Usage**: All features work seamlessly

### Small Team / Trusted Contributors
- **Configuration**: Option 1 with "Require approval for first-time contributors who recently created a GitHub account"
- **Protection**: Option 4 for workflow file changes
- **Script Usage**: Manual approval for first-time bots, then automatic

### Open Source / Public Repository
- **Configuration**: Option 1 with "Require approval for all outside collaborators"
- **Protection**: Option 4 (mandatory review for workflow changes)
- **Additional**: Consider requiring approval for PRs from users with < 30 days account age
- **Script Usage**: `-ApproveWorkflows` for trusted contributors, manual for others

### Enterprise / High Security
- **Configuration**: Option 3 (GitHub App) + Option 4 (workflow path protection)
- **Additional**: 
  - Enable secret scanning
  - Require signed commits
  - Audit all workflow approvals
- **Script Usage**: Programmatic approval via GitHub App only

## Setting Up the Script

### Minimal Setup (Manual Approvals)
```powershell
# Check what needs approval
.\tools\review-prs.ps1

# Approve in web UI, then merge approved PRs
.\tools\review-prs.ps1 -AutoMerge
```

### Automated Setup (After Repository Configuration)
```powershell
# Full automation (if bot is collaborator or repo settings allow)
.\tools\review-prs.ps1 -ApproveWorkflows -AutoMerge -GenerateNextIssues -UpdateStatus
```

### Safe Automation with Workflow Protection
```powershell
# Script could be enhanced to check for workflow modifications
# and skip auto-merge, requiring human review
.\tools\review-prs.ps1 -AutoMerge -GenerateNextIssues
# Add logic to detect .github/workflows/* changes and skip auto-merge
```

## Security Checklist

Before enabling full automation:

- [ ] Choose appropriate repository workflow approval setting for your security needs
- [ ] Decide if PRs modifying `.github/workflows/` should bypass auto-merge
- [ ] Enable branch protection rules for main branch
- [ ] Require status checks (CI, validators) before merge
- [ ] Consider requiring signed commits
- [ ] Set up secret scanning (if not already enabled)
- [ ] Document the approval process for your team
- [ ] Test with dry-run mode first: `-DryRun`

## Monitoring and Maintenance

### Regular Checks
- Review approved workflow runs periodically
- Audit PRs that were auto-merged
- Monitor for unusual patterns in bot activity

### Adjust as Needed
- Tighten security if you see abuse attempts
- Relax settings if legitimate contributions are blocked
- Keep GitHub Actions and dependencies updated

## Getting Help

If you need to configure this but are unsure:

1. **Start conservative**: Use Option 4 (workflow path protection) with manual reviews
2. **Test with dry-run**: Always use `-DryRun` first
3. **Monitor closely**: Check first 5-10 auto-merges carefully
4. **Adjust gradually**: Relax restrictions as you build confidence

For specific questions about your setup, consult:
- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Managing workflow runs](https://docs.github.com/en/actions/managing-workflow-runs)

## Human Configuration Required

The script **cannot** automatically configure these settings. A repository admin must:

1. **Choose and apply** the appropriate repository settings (Options 1-3)
2. **Set up branch protection** rules if using Option 4
3. **Add collaborators** if using Option 2
4. **Create and configure** GitHub App if using Option 3

Once configured, the script can work autonomously within those boundaries.
