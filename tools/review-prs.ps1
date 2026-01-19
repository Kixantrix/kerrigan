#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Systematic PR Review Script - Goes through all open PRs and manages Copilot reviews

.DESCRIPTION
    This script manages Copilot reviews on all open pull requests by:
    - Adding Copilot as a reviewer if not already assigned
    - Checking review status and reporting on PRs ready to merge
    - Posting comments to notify @copilot when changes are requested

.PARAMETER DryRun
    Show what would happen without making changes

.PARAMETER MarkReadyForReview
    Convert draft PRs to ready for review

.EXAMPLE
    .\tools\review-prs.ps1
    Add Copilot as reviewer to PRs without review

.EXAMPLE
    .\tools\review-prs.ps1 -DryRun
    Preview what would be done without making changes

.EXAMPLE
    .\tools\review-prs.ps1 -MarkReadyForReview
    Mark draft PRs as ready and add Copilot as reviewer

.NOTES
    Requires PowerShell 5.1 or later for compatibility.
#>
param(
    [switch]$DryRun,
    [switch]$MarkReadyForReview
)

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error "This script requires PowerShell 5.1 or later. Current version: $($PSVersionTable.PSVersion)"
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Systematic PR Review - Kerrigan" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "DRY RUN MODE - No actions will be taken`n" -ForegroundColor Magenta
}

$prsJson = gh pr list --json number,title,isDraft --limit 50 2>&1
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

Write-Host "Found $($prs.Count) open PR(s)`n" -ForegroundColor Cyan

foreach ($pr in $prs) {
    Write-Host "`nProcessing PR #$($pr.number): $($pr.title)" -ForegroundColor White
    
    if ($pr.isDraft) {
        if ($MarkReadyForReview) {
            Write-Host "  Action: Mark as ready for review" -ForegroundColor Yellow
            if (-not $DryRun) {
                gh pr ready $pr.number
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "  Failed to mark as ready for review (gh pr ready exited with code $LASTEXITCODE)" -ForegroundColor Red
                } else {
                    Write-Host "  Marked as ready for review" -ForegroundColor Green
                }
            } else {
                Write-Host "  [DRY RUN] Would mark as ready" -ForegroundColor Magenta
            }
        } else {
            Write-Host "  Status: Draft PR (use -MarkReadyForReview to change)" -ForegroundColor Gray
            continue
        }
    }
    
    try {
        $prViewResult = gh pr view $pr.number --json reviews,reviewRequests,mergeable,reviewDecision,url 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Warning: Unable to retrieve details for PR #$($pr.number). It may have been closed or become inaccessible. Skipping." -ForegroundColor Yellow
            if ($prViewResult) {
                Write-Host "  gh output: $prViewResult" -ForegroundColor DarkYellow
            }
            continue
        }
        
        if (-not $prViewResult) {
            Write-Host "  Warning: No data returned for PR #$($pr.number). Skipping." -ForegroundColor Yellow
            continue
        }
        
        $prData = $prViewResult | ConvertFrom-Json
    }
    catch {
        Write-Host "  Warning: Failed to parse PR details for PR #$($pr.number). Skipping this PR." -ForegroundColor Yellow
        continue
    }
    
    $copilotReview = $prData.reviews | Where-Object { $_.author.login -eq "Copilot" } | Select-Object -Last 1
    $copilotRequested = $prData.reviewRequests | Where-Object { $_.login -eq "Copilot" }
    
    if (-not $copilotReview -and -not $copilotRequested) {
        Write-Host "  Action: Add Copilot as reviewer" -ForegroundColor Yellow
        if (-not $DryRun) {
            $result = gh pr edit $pr.number --add-reviewer "Copilot" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Added Copilot as reviewer" -ForegroundColor Green
                # Mark as requested so we can report the correct status
                $copilotRequested = [PSCustomObject]@{ login = "Copilot" }
            } else {
                Write-Host "  Failed to add Copilot as reviewer (exit code $LASTEXITCODE)" -ForegroundColor Red
                if ($result) {
                    Write-Host "  gh output: $result" -ForegroundColor DarkRed
                }
            }
        } else {
            Write-Host "  [DRY RUN] Would add Copilot" -ForegroundColor Magenta
            # In dry-run mode, don't mark as requested
        }
    }
    
    if ($copilotRequested) {
        Write-Host "  Status: Waiting for Copilot review" -ForegroundColor Yellow
        continue
    }
    
    # Use reviewDecision for accurate overall review state
    if ($prData.reviewDecision) {
        Write-Host "  Review decision: $($prData.reviewDecision)" -ForegroundColor Green
        
        if ($prData.reviewDecision -eq "APPROVED") {
            if ($prData.mergeable -eq "MERGEABLE") {
                Write-Host "  Status: Ready to merge!" -ForegroundColor Green
            } else {
                Write-Host "  Status: Has merge conflicts" -ForegroundColor Yellow
            }
        }
        
        if ($prData.reviewDecision -eq "CHANGES_REQUESTED") {
            Write-Host "  Action: Notify @copilot to address feedback" -ForegroundColor Yellow
            $notificationBody = "@copilot Please address the requested changes."
            if (-not $DryRun) {
                # Check for a recent similar comment to avoid duplicate notifications
                $shouldPostComment = $true
                try {
                    $recentWindow = (Get-Date).AddDays(-1)
                    $commentsJson = gh pr view $pr.number --json comments 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        $prComments = ($commentsJson | ConvertFrom-Json).comments
                        $existingNotification = $prComments | Where-Object {
                            if ($_.body.Trim() -eq $notificationBody.Trim() -and $_.createdAt) {
                                $parsedDate = $null
                                # Use TryParse for robust date parsing (GitHub API returns ISO 8601 format)
                                if ([DateTime]::TryParse($_.createdAt, [ref]$parsedDate)) {
                                    return $parsedDate -gt $recentWindow
                                }
                                # Silently ignore date parsing failures - invalid dates are treated as non-matches
                            }
                            return $false
                        } | Select-Object -First 1

                        if ($existingNotification) {
                            Write-Host "  Skipping comment: similar notification already posted recently" -ForegroundColor Gray
                            $shouldPostComment = $false
                        }
                    }
                } catch {
                    Write-Host "  Warning: Unable to check for existing comments. Proceeding with comment." -ForegroundColor Yellow
                }
                
                if ($shouldPostComment) {
                    $result = gh pr comment $pr.number --body $notificationBody 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  Posted comment" -ForegroundColor Green
                    } else {
                        Write-Host "  Failed to post comment (exit code $LASTEXITCODE)" -ForegroundColor Red
                        if ($result) {
                            Write-Host "  gh output: $result" -ForegroundColor DarkRed
                        }
                    }
                }
            } else {
                Write-Host "  [DRY RUN] Would post comment" -ForegroundColor Magenta
            }
        }
    } elseif ($copilotReview) {
        Write-Host "  Copilot reviewed: $($copilotReview.state)" -ForegroundColor Green
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Review complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
