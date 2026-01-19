#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PR Triage Dashboard - Shows PRs needing attention and provides quick actions

.DESCRIPTION
    Main triage workflow script that displays:
    - PRs ready for review (not draft, CI status)
    - PRs with CI failures
    - PRs with merge conflicts
    - Stalled draft PRs (>24 hours without activity)
    - Merge-ready PRs (approved, CI passing)

.PARAMETER ShowAll
    Show all PRs regardless of status

.PARAMETER DryRun
    Show what would be done without taking any actions

.EXAMPLE
    .\tools\triage-prs.ps1
    Shows PRs needing attention

.EXAMPLE
    .\tools\triage-prs.ps1 -ShowAll
    Shows all open PRs with their status
#>

param(
    [switch]$ShowAll,
    [switch]$DryRun
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PR Triage Dashboard - Kerrigan" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No actions will be taken" -ForegroundColor Magenta
    Write-Host ""
}

# Fetch all open PRs with detailed information
Write-Host "Fetching open PRs..." -ForegroundColor Gray

$prsJson = gh pr list --json number,title,isDraft,updatedAt,createdAt,url,author,mergeable,reviewDecision --limit 100 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error @"
Failed to list pull requests using the GitHub CLI ('gh').

Possible causes:
  - 'gh' is not installed or not available on PATH
  - You are not authenticated (run 'gh auth login')
  - There is a network or GitHub API issue

Details:
$prsJson
"@
    exit 1
}

try {
    $prs = $prsJson | ConvertFrom-Json
} catch {
    Write-Error "Failed to parse pull request data returned by 'gh pr list'. Ensure you are using a compatible version of the GitHub CLI and try again. Details: $_"
    exit 1
}

if ($prs.Count -eq 0) {
    Write-Host "No open PRs found." -ForegroundColor Green
    exit 0
}

Write-Host "Found $($prs.Count) open PR(s)" -ForegroundColor Cyan
Write-Host ""

# Categorize PRs
$readyForReview = @()
$withCiFailures = @()
$withConflicts = @()
$stalledDrafts = @()
$mergeReady = @()
$withReviewFeedback = @()
$otherPrs = @()

$now = Get-Date

foreach ($pr in $prs) {
    # Get CI status for this PR
    # Note: This makes a separate API call per PR, which could hit rate limits with many PRs.
    # If you have >50 PRs, consider using the GitHub GraphQL API to batch requests.
    $checksJson = gh pr checks $pr.number --json name,state,conclusion 2>&1
    $ciStatus = "unknown"
    $ciPassing = $false
    
    if ($LASTEXITCODE -eq 0) {
        try {
            $checks = $checksJson | ConvertFrom-Json
            if ($checks.Count -gt 0) {
                # Check if all required checks pass
                $failedChecks = $checks | Where-Object { $_.conclusion -eq "failure" -or $_.state -eq "failure" }
                $pendingChecks = $checks | Where-Object { $_.state -eq "pending" -or $_.state -eq "in_progress" }
                
                if ($failedChecks.Count -gt 0) {
                    $ciStatus = "failing"
                } elseif ($pendingChecks.Count -gt 0) {
                    $ciStatus = "pending"
                } else {
                    $ciStatus = "passing"
                    $ciPassing = $true
                }
            } else {
                $ciStatus = "no-checks"
                $ciPassing = $true  # No checks means no failures
            }
        } catch {
            $ciStatus = "unknown"
        }
    }
    
    # Check for Copilot review comments (only for non-draft PRs)
    $reviewCommentCount = 0
    if (-not $pr.isDraft) {
        $commentsJson = gh api "/repos/{owner}/{repo}/pulls/$($pr.number)/comments" 2>&1
        if ($LASTEXITCODE -eq 0) {
            try {
                $comments = $commentsJson | ConvertFrom-Json
                # Filter for known Copilot bot usernames (exact matches)
                $copilotComments = $comments | Where-Object { 
                    $_.user.login -eq "github-copilot[bot]" -or $_.user.login -eq "github-actions[bot]"
                }
                $reviewCommentCount = $copilotComments.Count
            } catch {
                # Silently ignore parsing errors
            }
        }
    }
    
    # Parse timestamps
    $updatedAt = [DateTime]::Parse($pr.updatedAt)
    $createdAt = [DateTime]::Parse($pr.createdAt)
    $hoursSinceUpdate = ($now - $updatedAt).TotalHours
    
    # Add CI status, staleness, and review feedback to PR object
    $pr | Add-Member -NotePropertyName "ciStatus" -NotePropertyValue $ciStatus -Force
    $pr | Add-Member -NotePropertyName "hoursSinceUpdate" -NotePropertyValue $hoursSinceUpdate -Force
    $pr | Add-Member -NotePropertyName "reviewCommentCount" -NotePropertyValue $reviewCommentCount -Force
    
    # Categorize the PR
    if ($pr.isDraft) {
        if ($hoursSinceUpdate -gt 24) {
            $stalledDrafts += $pr
        }
    } elseif ($pr.mergeable -eq "CONFLICTING") {
        $withConflicts += $pr
    } elseif ($ciStatus -eq "failing") {
        $withCiFailures += $pr
    } elseif ($reviewCommentCount -gt 0) {
        $withReviewFeedback += $pr
    } elseif ($pr.reviewDecision -eq "APPROVED" -and $ciPassing -and $pr.mergeable -eq "MERGEABLE") {
        $mergeReady += $pr
    } elseif (-not $pr.isDraft) {
        $readyForReview += $pr
    } else {
        $otherPrs += $pr
    }
}

# Display results by category

# 1. Merge-Ready PRs (highest priority)
if ($mergeReady.Count -gt 0) {
    Write-Host "[OK] MERGE READY ($($mergeReady.Count))" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    foreach ($pr in $mergeReady) {
        Write-Host "  #$($pr.number): $($pr.title)" -ForegroundColor White
        Write-Host "    Status: Approved, CI passing, no conflicts" -ForegroundColor Green
        Write-Host "    URL: $($pr.url)" -ForegroundColor Gray
        Write-Host "    Actions:" -ForegroundColor Yellow
        Write-Host "      gh pr merge $($pr.number) --squash  # Squash merge" -ForegroundColor Cyan
        Write-Host "      gh pr merge $($pr.number) --merge   # Regular merge" -ForegroundColor Cyan
        Write-Host ""
    }
}

# 2. PRs with CI Failures (high priority)
if ($withCiFailures.Count -gt 0) {
    Write-Host "[!!] CI FAILURES ($($withCiFailures.Count))" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    foreach ($pr in $withCiFailures) {
        Write-Host "  #$($pr.number): $($pr.title)" -ForegroundColor White
        Write-Host "    Author: $($pr.author.login)" -ForegroundColor Gray
        Write-Host "    URL: $($pr.url)" -ForegroundColor Gray
        Write-Host "    Actions:" -ForegroundColor Yellow
        Write-Host "      gh pr checks $($pr.number)  # View check details" -ForegroundColor Cyan
        Write-Host "      gh pr comment $($pr.number) --body 'CI is failing. Please review and fix.'  # Notify author" -ForegroundColor Cyan
        Write-Host ""
    }
}

# 3. PRs with Merge Conflicts
if ($withConflicts.Count -gt 0) {
    Write-Host "[WARN] MERGE CONFLICTS ($($withConflicts.Count))" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    foreach ($pr in $withConflicts) {
        Write-Host "  #$($pr.number): $($pr.title)" -ForegroundColor White
        Write-Host "    Author: $($pr.author.login)" -ForegroundColor Gray
        Write-Host "    URL: $($pr.url)" -ForegroundColor Gray
        Write-Host "    Actions:" -ForegroundColor Yellow
        Write-Host "      gh pr comment $($pr.number) --body 'This PR has merge conflicts. Please rebase on main.'  # Notify author" -ForegroundColor Cyan
        Write-Host ""
    }
}

# 4. PRs with Review Feedback
if ($withReviewFeedback.Count -gt 0) {
    Write-Host "[FEEDBACK] COPILOT REVIEW COMMENTS ($($withReviewFeedback.Count))" -ForegroundColor Magenta
    Write-Host "========================================" -ForegroundColor Magenta
    # Sort by review comment count (descending)
    $withReviewFeedback = $withReviewFeedback | Sort-Object -Property reviewCommentCount -Descending
    foreach ($pr in $withReviewFeedback) {
        Write-Host "  #$($pr.number): $($pr.title)" -ForegroundColor White
        Write-Host "    Author: $($pr.author.login)" -ForegroundColor Gray
        Write-Host "    Review comments: $($pr.reviewCommentCount) from Copilot reviewer" -ForegroundColor Gray
        Write-Host "    URL: $($pr.url)" -ForegroundColor Gray
        Write-Host "    Actions:" -ForegroundColor Yellow
        Write-Host "      gh pr view $($pr.number)  # View PR and review comments" -ForegroundColor Cyan
        Write-Host "      gh pr comment $($pr.number) --body '@copilot Please address review comments'  # Assign fixes" -ForegroundColor Cyan
        Write-Host ""
    }
    Write-Host "    Bulk action:" -ForegroundColor Yellow
    Write-Host "      .\tools\handle-reviews.ps1 --assign-fixes  # Assign all at once" -ForegroundColor Cyan
    Write-Host ""
}

# 5. Stalled Draft PRs (>24 hours)
if ($stalledDrafts.Count -gt 0) {
    Write-Host "[PAUSE] STALLED DRAFTS ($($stalledDrafts.Count))" -ForegroundColor Magenta
    Write-Host "========================================" -ForegroundColor Magenta
    foreach ($pr in $stalledDrafts) {
        $hours = [Math]::Floor($pr.hoursSinceUpdate)
        Write-Host "  #$($pr.number): $($pr.title)" -ForegroundColor White
        Write-Host "    Author: $($pr.author.login)" -ForegroundColor Gray
        Write-Host "    Last updated: $hours hours ago" -ForegroundColor Gray
        Write-Host "    URL: $($pr.url)" -ForegroundColor Gray
        Write-Host "    Actions:" -ForegroundColor Yellow
        Write-Host "      gh pr comment $($pr.number) --body '@copilot Please continue work on this PR.'  # Restart agent" -ForegroundColor Cyan
        Write-Host ""
    }
}

# 6. Ready for Review PRs
if ($readyForReview.Count -gt 0) {
    Write-Host "[REVIEW] READY FOR REVIEW ($($readyForReview.Count))" -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
    foreach ($pr in $readyForReview) {
        Write-Host "  #$($pr.number): $($pr.title)" -ForegroundColor White
        Write-Host "    Author: $($pr.author.login)" -ForegroundColor Gray
        $ciColor = "Red"
        if ($pr.ciStatus -eq "passing") { $ciColor = "Green" }
        elseif ($pr.ciStatus -eq "pending") { $ciColor = "Yellow" }
        Write-Host "    CI Status: $($pr.ciStatus)" -ForegroundColor $ciColor
        Write-Host "    Review Decision: $($pr.reviewDecision)" -ForegroundColor Gray
        Write-Host "    URL: $($pr.url)" -ForegroundColor Gray
        Write-Host "    Actions:" -ForegroundColor Yellow
        Write-Host "      gh pr view $($pr.number)  # View PR details" -ForegroundColor Cyan
        Write-Host "      gh pr diff $($pr.number)  # View changes" -ForegroundColor Cyan
        Write-Host "      gh pr review $($pr.number) --approve  # Approve PR" -ForegroundColor Cyan
        Write-Host "      gh pr review $($pr.number) --request-changes  # Request changes" -ForegroundColor Cyan
        Write-Host ""
    }
}

# 7. Other PRs (if ShowAll flag is set)
if ($ShowAll -and $otherPrs.Count -gt 0) {
    Write-Host "[OTHER] OTHER PRs ($($otherPrs.Count))" -ForegroundColor Gray
    Write-Host "========================================" -ForegroundColor Gray
    foreach ($pr in $otherPrs) {
        Write-Host "  #$($pr.number): $($pr.title)" -ForegroundColor White
        Write-Host "    Status: Draft=$($pr.isDraft), CI=$($pr.ciStatus)" -ForegroundColor Gray
        Write-Host "    URL: $($pr.url)" -ForegroundColor Gray
        Write-Host ""
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total PRs: $($prs.Count)" -ForegroundColor White
Write-Host "  [OK] Merge ready: $($mergeReady.Count)" -ForegroundColor Green
Write-Host "  [!!] CI failures: $($withCiFailures.Count)" -ForegroundColor Red
Write-Host "  [WARN] Merge conflicts: $($withConflicts.Count)" -ForegroundColor Yellow
Write-Host "  [FEEDBACK] Review comments: $($withReviewFeedback.Count)" -ForegroundColor Magenta
Write-Host "  [PAUSE] Stalled drafts: $($stalledDrafts.Count)" -ForegroundColor Magenta
Write-Host "  [REVIEW] Ready for review: $($readyForReview.Count)" -ForegroundColor Blue
Write-Host "  [OTHER] Other: $($otherPrs.Count)" -ForegroundColor Gray
Write-Host ""

# Quick action suggestions
Write-Host "SUGGESTED NEXT STEPS:" -ForegroundColor Cyan
if ($mergeReady.Count -gt 0) {
    Write-Host "  1. Merge ready PRs (highest priority)" -ForegroundColor Green
}
if ($withCiFailures.Count -gt 0) {
    Write-Host "  2. Investigate and fix CI failures" -ForegroundColor Red
}
if ($withConflicts.Count -gt 0) {
    Write-Host "  3. Notify authors about merge conflicts" -ForegroundColor Yellow
}
if ($withReviewFeedback.Count -gt 0) {
    Write-Host "  4. Assign fixes for Copilot review feedback" -ForegroundColor Magenta
}
if ($stalledDrafts.Count -gt 0) {
    Write-Host "  5. Restart stalled draft PRs" -ForegroundColor Magenta
}
if ($readyForReview.Count -gt 0) {
    Write-Host "  6. Review and approve ready PRs" -ForegroundColor Blue
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
