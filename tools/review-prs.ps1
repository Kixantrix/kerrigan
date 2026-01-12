# Systematic PR Review Script
# Manages PR reviews and CI workflow approvals
param(
    [switch]$DryRun,
    [switch]$MarkReadyForReview,
    [switch]$ApproveWorkflows
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Systematic PR Review - Kerrigan" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "DRY RUN MODE - No actions will be taken`n" -ForegroundColor Magenta
}

if ($ApproveWorkflows) {
    Write-Host "WORKFLOW APPROVAL MODE: Will approve pending CI runs`n" -ForegroundColor Yellow
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
    
    $prData = gh pr view $pr.number --json reviews,reviewRequests,mergeable,reviewDecision,url,headRefName | ConvertFrom-Json
    
    # Check for workflow runs that need approval
    $runs = gh run list --branch $prData.headRefName --json databaseId,status,conclusion,workflowName --limit 10 | ConvertFrom-Json
    $needsApproval = $runs | Where-Object { $_.conclusion -eq "action_required" -or ($_.status -eq "waiting") }
    
    if ($needsApproval) {
        Write-Host "  Found $($needsApproval.Count) workflow(s) needing approval:" -ForegroundColor Yellow
        foreach ($run in $needsApproval) {
            Write-Host "    - $($run.workflowName) (run $($run.databaseId))" -ForegroundColor Gray
        }
        
        if ($ApproveWorkflows) {
            foreach ($run in $needsApproval) {
                Write-Host "    Approving $($run.workflowName)..." -ForegroundColor Yellow
                if (-not $DryRun) {
                    $result = gh api "repos/Kixantrix/kerrigan/actions/runs/$($run.databaseId)/approve" -X POST 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "     Approved" -ForegroundColor Green
                    } else {
                        Write-Host "     Failed to approve (may need web approval)" -ForegroundColor Red
                    }
                } else {
                    Write-Host "    [DRY RUN] Would approve" -ForegroundColor Magenta
                }
            }
        } else {
            Write-Host "  Use -ApproveWorkflows to approve these runs" -ForegroundColor Cyan
        }
    } else {
        $completedRuns = $runs | Where-Object { $_.status -eq "completed" }
        if ($completedRuns) {
            $successRuns = $completedRuns | Where-Object { $_.conclusion -eq "success" }
            if ($successRuns) {
                Write-Host "  CI: $($successRuns.Count) workflow(s) passing" -ForegroundColor Green
            }
            $failedRuns = $completedRuns | Where-Object { $_.conclusion -in @("failure", "cancelled") }
            if ($failedRuns) {
                Write-Host "  CI: $($failedRuns.Count) workflow(s) failed" -ForegroundColor Red
            }
        }
    }
    
    # Check review status
    if ($prData.reviewDecision) {
        Write-Host "  Review: $($prData.reviewDecision)" -ForegroundColor Green
        
        if ($prData.reviewDecision -eq "APPROVED") {
            if ($prData.mergeable -eq "MERGEABLE") {
                Write-Host "   Ready to merge!" -ForegroundColor Green
            } else {
                Write-Host "   Has merge conflicts or checks pending" -ForegroundColor Yellow
            }
        }
        
        if ($prData.reviewDecision -eq "CHANGES_REQUESTED") {
            Write-Host "   Changes requested" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Review: Awaiting review" -ForegroundColor Gray
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Review complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
