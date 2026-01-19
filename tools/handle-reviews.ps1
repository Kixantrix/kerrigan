#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Handle Copilot PR Reviewer Feedback - Detect and assign fixes for review comments

.DESCRIPTION
    This script checks all open PRs for comments from Copilot pull-request-reviewer
    and optionally assigns the agent to address the feedback.
    
    Shows:
    - PRs with review feedback and comment counts
    - Feedback categorized by severity
    - Actions to assign fixes

.PARAMETER AssignFixes
    Automatically comment on PRs to assign @copilot to address feedback

.PARAMETER Threshold
    Only process PRs with at least this many review comments (default: 1)

.PARAMETER DryRun
    Show what would be done without taking any actions

.EXAMPLE
    .\tools\handle-reviews.ps1
    Shows PRs with Copilot review feedback

.EXAMPLE
    .\tools\handle-reviews.ps1 -AssignFixes
    Comment on all PRs with feedback to assign fixes

.EXAMPLE
    .\tools\handle-reviews.ps1 -Threshold 5
    Only show PRs with 5+ review comments
#>

param(
    [switch]$AssignFixes,
    [int]$Threshold = 1,
    [switch]$DryRun
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Copilot PR Reviewer Feedback Handler" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No actions will be taken" -ForegroundColor Magenta
    Write-Host ""
}

# Fetch all open PRs
Write-Host "Fetching open PRs..." -ForegroundColor Gray

$prsJson = gh pr list --json number,title,url,author,isDraft --limit 100 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to list pull requests. Ensure 'gh' is installed and authenticated."
    exit 1
}

try {
    $prs = $prsJson | ConvertFrom-Json
} catch {
    Write-Error "Failed to parse pull request data: $_"
    exit 1
}

if ($prs.Count -eq 0) {
    Write-Host "No open PRs found." -ForegroundColor Green
    exit 0
}

Write-Host "Found $($prs.Count) open PR(s)" -ForegroundColor Cyan
Write-Host ""

# Check each PR for Copilot review comments
$prsWithFeedback = @()

foreach ($pr in $prs) {
    # Get review comments for this PR
    # Note: This gets review comments (comments on code), not general PR comments
    $commentsJson = gh api "/repos/{owner}/{repo}/pulls/$($pr.number)/comments" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        try {
            $comments = $commentsJson | ConvertFrom-Json
            
            # Filter for known Copilot bot usernames (exact matches)
            $copilotComments = $comments | Where-Object { 
                $_.user.login -eq "Copilot" -or $_.user.login -eq "github-actions[bot]"
            }
            
            if ($copilotComments.Count -ge $Threshold) {
                $pr | Add-Member -NotePropertyName "commentCount" -NotePropertyValue $copilotComments.Count -Force
                $prsWithFeedback += $pr
            }
        } catch {
            Write-Host "  ⚠️  Failed to parse comments for PR #$($pr.number): $_" -ForegroundColor Yellow
        }
    }
}

# Display results
if ($prsWithFeedback.Count -eq 0) {
    Write-Host "No PRs with Copilot review feedback found (threshold: $Threshold)" -ForegroundColor Green
    exit 0
}

Write-Host "[FEEDBACK] PRs WITH REVIEW FEEDBACK ($($prsWithFeedback.Count))" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

# Sort by comment count (descending)
$prsWithFeedback = $prsWithFeedback | Sort-Object -Property commentCount -Descending

foreach ($pr in $prsWithFeedback) {
    Write-Host "  #$($pr.number): $($pr.title)" -ForegroundColor White
    Write-Host "    Comments: $($pr.commentCount) from Copilot reviewer" -ForegroundColor Gray
    Write-Host "    Author: $($pr.author.login)" -ForegroundColor Gray
    Write-Host "    Status: $(if ($pr.isDraft) { 'Draft' } else { 'Ready for review' })" -ForegroundColor Gray
    Write-Host "    URL: $($pr.url)" -ForegroundColor Gray
    
    if ($AssignFixes) {
        Write-Host "    Action: Assigning @copilot to address feedback..." -ForegroundColor Cyan
        
        if (-not $DryRun) {
            try {
                gh pr comment $pr.number --body "@copilot Please address all review comments." 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    ✅ Comment added successfully" -ForegroundColor Green
                } else {
                    Write-Host "    ❌ Failed to add comment" -ForegroundColor Red
                }
            } catch {
                Write-Host "    ❌ Error: $_" -ForegroundColor Red
            }
        } else {
            Write-Host "    [DRY RUN] Would comment: '@copilot Please address all review comments'" -ForegroundColor Magenta
        }
    } else {
        Write-Host "    Suggested action:" -ForegroundColor Yellow
        Write-Host "      gh pr comment $($pr.number) --body '@copilot Please address all review comments'" -ForegroundColor Cyan
    }
    Write-Host ""
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total PRs with feedback: $($prsWithFeedback.Count)" -ForegroundColor White
Write-Host "Comment threshold: $Threshold" -ForegroundColor Gray

if ($AssignFixes -and -not $DryRun) {
    Write-Host "Status: Assigned fixes to all PRs" -ForegroundColor Green
} elseif ($AssignFixes -and $DryRun) {
    Write-Host "Status: Dry run - no actions taken" -ForegroundColor Magenta
} else {
    Write-Host "Status: Report only - use -AssignFixes to assign" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "SUGGESTED NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Review the feedback on each PR" -ForegroundColor White
Write-Host "  2. Run with -AssignFixes to assign @copilot to address feedback" -ForegroundColor White
Write-Host "  3. Monitor PRs for updates and re-review when fixed" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
