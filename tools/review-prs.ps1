# Systematic PR Review Script
# Goes through all open PRs and manages Copilot reviews
param(
    [switch]$DryRun,
    [switch]$MarkReadyForReview
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Systematic PR Review - Kerrigan" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "DRY RUN MODE - No actions will be taken`n" -ForegroundColor Magenta
}

$prsJson = gh pr list --json number,title,isDraft --limit 50 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to list pull requests using the GitHub CLI ('gh').`n`nPossible causes:`n  - 'gh' is not installed or not available on PATH`n  - You are not authenticated (run 'gh auth login')`n  - There is a network or GitHub API issue`n`nDetails:`n$prsJson"
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
        $prViewResult = gh pr view $pr.number --json reviews,reviewRequests,mergeable,reviewDecision,url 2>$null
        
        if ($LASTEXITCODE -ne 0 -or -not $prViewResult) {
            Write-Host "  Warning: Unable to retrieve details for PR #$($pr.number). It may have been closed or become inaccessible. Skipping." -ForegroundColor Yellow
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
            } else {
                Write-Host "  Failed to add Copilot as reviewer (exit code $LASTEXITCODE)" -ForegroundColor Red
                if ($result) {
                    Write-Host "  gh output: $result" -ForegroundColor DarkRed
                }
            }
        } else {
            Write-Host "  [DRY RUN] Would add Copilot" -ForegroundColor Magenta
        }
        $copilotRequested = $true
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
                    $commentsJson = gh api repos/:owner/:repo/issues/$($pr.number)/comments 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        $comments = $commentsJson | ConvertFrom-Json
                        $existingNotification = $comments | Where-Object {
                            if ($_.body -eq $notificationBody -and $_.created_at) {
                                $parsedDate = [DateTime]::MinValue
                                if ([DateTime]::TryParse($_.created_at, [ref]$parsedDate)) {
                                    return $parsedDate -gt $recentWindow
                                }
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
                    gh pr comment $pr.number --body $notificationBody
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  Posted comment" -ForegroundColor Green
                    } else {
                        Write-Host "  Failed to post comment (exit code $LASTEXITCODE)" -ForegroundColor Red
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
