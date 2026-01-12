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

$prs = gh pr list --json number,title,isDraft --limit 50 | ConvertFrom-Json

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
                Write-Host "  Marked as ready for review" -ForegroundColor Green
            } else {
                Write-Host "  [DRY RUN] Would mark as ready" -ForegroundColor Magenta
            }
        } else {
            Write-Host "  Status: Draft PR (use -MarkReadyForReview to change)" -ForegroundColor Gray
            continue
        }
    }
    
    $prData = gh pr view $pr.number --json reviews,reviewRequests,mergeable,reviewDecision,url | ConvertFrom-Json
    
    $copilotReview = $prData.reviews | Where-Object { $_.author.login -eq "Copilot" } | Select-Object -Last 1
    $copilotRequested = $prData.reviewRequests | Where-Object { $_.login -eq "Copilot" }
    
    if (-not $copilotReview -and -not $copilotRequested) {
        Write-Host "  Action: Add Copilot as reviewer" -ForegroundColor Yellow
        if (-not $DryRun) {
            gh pr edit $pr.number --add-reviewer "Copilot"
            Write-Host "  Added Copilot as reviewer" -ForegroundColor Green
        } else {
            Write-Host "  [DRY RUN] Would add Copilot" -ForegroundColor Magenta
        }
        continue
    }
    
    if ($copilotRequested) {
        Write-Host "  Status: Waiting for Copilot review" -ForegroundColor Yellow
        continue
    }
    
    if ($copilotReview) {
        Write-Host "  Copilot reviewed: $($copilotReview.state)" -ForegroundColor Green
        
        if ($copilotReview.state -eq "APPROVED") {
            if ($prData.mergeable -eq "MERGEABLE") {
                Write-Host "  Status: Ready to merge!" -ForegroundColor Green
            } else {
                Write-Host "  Status: Has merge conflicts" -ForegroundColor Yellow
            }
        }
        
        if ($copilotReview.state -eq "CHANGES_REQUESTED") {
            Write-Host "  Action: Notify @copilot to address feedback" -ForegroundColor Yellow
            if (-not $DryRun) {
                gh pr comment $pr.number --body "@copilot Please address the requested changes."
                Write-Host "  Posted comment" -ForegroundColor Green
            } else {
                Write-Host "  [DRY RUN] Would post comment" -ForegroundColor Magenta
            }
        }
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Review complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
