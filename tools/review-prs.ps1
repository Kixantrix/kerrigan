# Systematic PR Review Script
# Manages PR reviews and CI workflow approvals with agentic capabilities
param(
    [switch]$DryRun,
    [switch]$MarkReadyForReview,
    [switch]$ApproveWorkflows,
    [switch]$AutoMerge,
    [switch]$GenerateNextIssues,
    [switch]$UpdateStatus
)

# Helper Functions
function Get-LinkedIssues {
    param([string]$prBody)
    
    $issues = @()
    if ($prBody) {
        # Match patterns like "Closes #123", "Fixes #456", "Resolves #789"
        $matches = [regex]::Matches($prBody, '(?:Close|Closes|Closed|Fix|Fixes|Fixed|Resolve|Resolves|Resolved)[\s:]+#(\d+)', 'IgnoreCase')
        foreach ($match in $matches) {
            $issues += $match.Groups[1].Value
        }
    }
    return $issues
}

function Test-PRReadyForMerge {
    param(
        [object]$prData,
        [array]$runs
    )
    
    $reasons = @()
    
    # Check if approved
    if ($prData.reviewDecision -ne "APPROVED") {
        $reasons += "Not approved (status: $($prData.reviewDecision))"
    }
    
    # Check if mergeable
    if ($prData.mergeable -ne "MERGEABLE") {
        $reasons += "Not mergeable (status: $($prData.mergeable))"
    }
    
    # Check CI status
    $completedRuns = $runs | Where-Object { $_.status -eq "completed" }
    $failedRuns = $completedRuns | Where-Object { $_.conclusion -in @("failure", "cancelled") }
    if ($failedRuns) {
        $reasons += "CI checks failed ($($failedRuns.Count) workflow(s))"
    }
    
    $pendingRuns = $runs | Where-Object { $_.status -in @("queued", "in_progress", "waiting") -or $_.conclusion -eq "action_required" }
    if ($pendingRuns) {
        $reasons += "CI checks pending ($($pendingRuns.Count) workflow(s))"
    }
    
    # Check for unresolved review comments
    if ($prData.reviews) {
        $unresolvedComments = $prData.reviews | Where-Object { $_.state -eq "CHANGES_REQUESTED" }
        if ($unresolvedComments) {
            $reasons += "Unresolved change requests"
        }
    }
    
    return @{
        Ready = ($reasons.Count -eq 0)
        Reasons = $reasons
    }
}

function Get-TasksFromFile {
    param([string]$filePath)
    
    if (-not (Test-Path $filePath)) {
        return @()
    }
    
    $content = Get-Content $filePath -Raw
    $tasks = @()
    
    # Parse tasks by milestone
    $milestonePattern = '##\s+Milestone\s+\d+:\s+([^\r\n]+)'
    $taskPattern = '-\s+\[([ x])\]\s+Task:\s+([^\r\n]+)'
    
    $lines = $content -split "`r?`n"
    $currentMilestone = ""
    
    foreach ($line in $lines) {
        if ($line -match $milestonePattern) {
            $currentMilestone = $matches[1].Trim()
        }
        elseif ($line -match $taskPattern) {
            $completed = $matches[1] -eq 'x'
            $taskName = $matches[2].Trim()
            
            $tasks += @{
                Milestone = $currentMilestone
                Name = $taskName
                Completed = $completed
            }
        }
    }
    
    return $tasks
}

function Find-NextTasks {
    param(
        [array]$allTasks,
        [string]$completedTaskName
    )
    
    # Find the completed task - try exact match first, then substring match
    $taskIndex = -1
    
    # First try: exact match (case-insensitive)
    for ($i = 0; $i -lt $allTasks.Count; $i++) {
        if ($allTasks[$i].Name -eq $completedTaskName) {
            $taskIndex = $i
            break
        }
    }
    
    # Second try: substring match if exact match fails
    if ($taskIndex -eq -1) {
        # Normalize both strings for comparison: remove punctuation
        $normalizedSearch = $completedTaskName -replace '[^\w\s]', '' -replace '\s+', ' '
        
        for ($i = 0; $i -lt $allTasks.Count; $i++) {
            $normalizedTask = $allTasks[$i].Name -replace '[^\w\s]', '' -replace '\s+', ' '
            
            # Match if the normalized search term appears in the normalized task name
            if ($normalizedTask -match [regex]::Escape($normalizedSearch)) {
                $taskIndex = $i
                break
            }
        }
    }
    
    if ($taskIndex -eq -1) {
        return @()
    }
    
    $currentMilestone = $allTasks[$taskIndex].Milestone
    $nextTasks = @()
    
    # Find next incomplete tasks in the same milestone
    for ($i = $taskIndex + 1; $i -lt $allTasks.Count; $i++) {
        if ($allTasks[$i].Milestone -ne $currentMilestone) {
            break
        }
        if (-not $allTasks[$i].Completed) {
            $nextTasks += $allTasks[$i]
            # Only return first incomplete task to avoid creating too many issues
            break
        }
    }
    
    return $nextTasks
}

function Update-ProjectStatus {
    param(
        [string]$statusPath,
        [string]$milestone,
        [bool]$dryRun
    )
    
    if (-not (Test-Path $statusPath)) {
        Write-Host "  ⚠️  status.json not found at $statusPath" -ForegroundColor Yellow
        return
    }
    
    try {
        $status = Get-Content $statusPath -Raw | ConvertFrom-Json
    } catch {
        Write-Host "  ❌ Failed to parse status.json: $_" -ForegroundColor Red
        return
    }
    
    # Update last_updated timestamp
    $status.last_updated = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    
    # Update notes about milestone
    if ($milestone) {
        $status.notes = "Progress on $milestone - Updated by auto-merge script"
    }
    
    if (-not $dryRun) {
        try {
            $status | ConvertTo-Json -Depth 10 | Set-Content $statusPath -ErrorAction Stop
            Write-Host "  ✅ Updated status.json" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Failed to write status.json: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  [DRY RUN] Would update status.json" -ForegroundColor Magenta
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Systematic PR Review - Kerrigan" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "DRY RUN MODE - No actions will be taken`n" -ForegroundColor Magenta
}

if ($ApproveWorkflows) {
    Write-Host "WORKFLOW APPROVAL MODE: Will approve pending CI runs`n" -ForegroundColor Yellow
}

if ($AutoMerge) {
    Write-Host "AUTO-MERGE MODE: Will merge approved PRs`n" -ForegroundColor Yellow
    if (-not $DryRun) {
        Write-Host "⚠️  This will automatically merge qualifying PRs!`n" -ForegroundColor Red
    }
}

if ($GenerateNextIssues) {
    Write-Host "ISSUE GENERATION MODE: Will create next-step issues`n" -ForegroundColor Yellow
}

if ($UpdateStatus) {
    Write-Host "STATUS UPDATE MODE: Will update status.json`n" -ForegroundColor Yellow
}

$prs = gh pr list --json number,title,isDraft --limit 50 | ConvertFrom-Json

if ($prs.Count -eq 0) {
    Write-Host "No open PRs found." -ForegroundColor Green
    exit 0
}

Write-Host "Found $($prs.Count) open PR(s)`n" -ForegroundColor Cyan

$mergedPRs = @()

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
    
    $prData = gh pr view $pr.number --json reviews,reviewRequests,mergeable,reviewDecision,url,headRefName,body,closingIssuesReferences | ConvertFrom-Json
    
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
                
                # Auto-merge logic
                if ($AutoMerge) {
                    Write-Host "`n  🤖 Evaluating for auto-merge..." -ForegroundColor Cyan
                    
                    # Check if PR modifies workflow files (security consideration)
                    $prFiles = gh pr view $pr.number --json files -q '.files[].path' 2>&1
                    $modifiesWorkflows = $false
                    
                    if ($LASTEXITCODE -eq 0) {
                        foreach ($file in $prFiles) {
                            if ($file -like ".github/workflows/*") {
                                $modifiesWorkflows = $true
                                break
                            }
                        }
                    }
                    
                    if ($modifiesWorkflows) {
                        Write-Host "  ⚠️  PR modifies workflow files - auto-merge disabled for security" -ForegroundColor Yellow
                        Write-Host "     Manual review required for: .github/workflows/*" -ForegroundColor Gray
                        Write-Host "     This prevents potential workflow abuse or malicious code execution" -ForegroundColor Gray
                    } else {
                        $mergeCheck = Test-PRReadyForMerge -prData $prData -runs $runs
                        
                        if ($mergeCheck.Ready) {
                            Write-Host "  ✅ All merge criteria met!" -ForegroundColor Green
                        
                        if (-not $DryRun) {
                            # Get linked issues (handle null body)
                            $linkedIssues = @()
                            if ($null -ne $prData.body -and $prData.body -ne "") {
                                $linkedIssues = Get-LinkedIssues -prBody $prData.body
                            }
                            
                            # Merge the PR
                            Write-Host "  🔀 Merging PR #$($pr.number)..." -ForegroundColor Yellow
                            $mergeResult = gh pr merge $pr.number --squash --delete-branch 2>&1
                            
                            if ($LASTEXITCODE -eq 0) {
                                Write-Host "  ✅ PR merged successfully!" -ForegroundColor Green
                                
                                # Post merge notification comment
                                $comment = "✅ **Auto-merged** by Kerrigan PR review script`n`n"
                                $comment += "- Review: Approved ✓`n"
                                $comment += "- CI: Passing ✓`n"
                                $comment += "- Merge conflicts: None ✓`n"
                                
                                if ($linkedIssues.Count -gt 0) {
                                    $comment += "`n**Linked issues**: #$($linkedIssues -join ', #')"
                                }
                                
                                gh pr comment $pr.number --body $comment
                                
                                # Track merged PR for later processing
                                $mergedPRs += @{
                                    Number = $pr.number
                                    Title = $pr.title
                                    LinkedIssues = $linkedIssues
                                    Body = $prData.body
                                }
                                
                                Write-Host "  📝 Posted merge notification" -ForegroundColor Green
                            } else {
                                Write-Host "  ❌ Failed to merge: $mergeResult" -ForegroundColor Red
                            }
                        } else {
                            Write-Host "  [DRY RUN] Would merge PR #$($pr.number)" -ForegroundColor Magenta
                            
                            # Track for dry-run issue generation (handle null body)
                            $linkedIssues = @()
                            if ($null -ne $prData.body -and $prData.body -ne "") {
                                $linkedIssues = Get-LinkedIssues -prBody $prData.body
                            }
                            $mergedPRs += @{
                                Number = $pr.number
                                Title = $pr.title
                                LinkedIssues = $linkedIssues
                                Body = $prData.body
                            }
                        }
                        } else {
                            Write-Host "  ⚠️  Cannot auto-merge:" -ForegroundColor Yellow
                            foreach ($reason in $mergeCheck.Reasons) {
                                Write-Host "    - $reason" -ForegroundColor Gray
                            }
                        }
                    }
                }
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

# Process merged PRs for next-step issue generation
if ($GenerateNextIssues -and $mergedPRs.Count -gt 0) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Generating Next-Step Issues" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Load tasks from kerrigan project
    $tasksPath = "specs/projects/kerrigan/tasks.md"
    if (Test-Path $tasksPath) {
        $allTasks = Get-TasksFromFile -filePath $tasksPath
        Write-Host "📋 Loaded $($allTasks.Count) tasks from $tasksPath`n" -ForegroundColor Cyan
        
        foreach ($mergedPR in $mergedPRs) {
            Write-Host "`nProcessing merged PR #$($mergedPR.Number): $($mergedPR.Title)" -ForegroundColor White
            
            # Try to determine which task was completed
            $nextTasks = Find-NextTasks -allTasks $allTasks -completedTaskName $mergedPR.Title
            
            if ($nextTasks.Count -gt 0) {
                foreach ($task in $nextTasks) {
                    Write-Host "  📝 Next task identified: $($task.Name)" -ForegroundColor Green
                    Write-Host "     Milestone: $($task.Milestone)" -ForegroundColor Gray
                    
                    # Create issue for next task
                    $issueTitle = $task.Name
                    $issueBody = "## Next Step After PR #$($mergedPR.Number)`n`n"
                    $issueBody += "This task is the next logical step following the completion of:`n"
                    $issueBody += "- **Merged PR**: #$($mergedPR.Number) - $($mergedPR.Title)`n`n"
                    $issueBody += "**Milestone**: $($task.Milestone)`n`n"
                    $issueBody += "**Task**: $($task.Name)`n`n"
                    $issueBody += "---`n`n"
                    $issueBody += "*Auto-generated by the PR review script's next-step issue generation.*"
                    
                    if (-not $DryRun) {
                        # Check if issue already exists - use label filtering instead of title search
                        # to avoid issues with special characters
                        try {
                            $existingIssues = gh issue list --label "kerrigan" --state open --json number,title --limit 50 | ConvertFrom-Json
                            # Normalize titles for comparison to avoid case and punctuation issues
                            $normalizedIssueTitle = $issueTitle -replace '[^\w\s]', '' -replace '\s+', ' '
                            $alreadyExists = $existingIssues | Where-Object { 
                                $normalizedExisting = $_.title -replace '[^\w\s]', '' -replace '\s+', ' '
                                $normalizedExisting -eq $normalizedIssueTitle
                            }
                            
                            if (-not $alreadyExists) {
                                Write-Host "  📤 Creating issue: $issueTitle" -ForegroundColor Yellow
                                $newIssue = gh issue create --title $issueTitle --body $issueBody --label "kerrigan,agent:go" 2>&1
                                
                                if ($LASTEXITCODE -eq 0) {
                                    Write-Host "  ✅ Created issue: $newIssue" -ForegroundColor Green
                                } else {
                                    Write-Host "  ❌ Failed to create issue: $newIssue" -ForegroundColor Red
                                }
                            } else {
                                Write-Host "  ⏭️  Issue already exists: #$($alreadyExists.number)" -ForegroundColor Gray
                            }
                        } catch {
                            Write-Host "  ⚠️  Error checking/creating issue: $_" -ForegroundColor Yellow
                        }
                    } else {
                        Write-Host "  [DRY RUN] Would create issue: $issueTitle" -ForegroundColor Magenta
                    }
                }
            } else {
                Write-Host "  ℹ️  No clear next task identified" -ForegroundColor Gray
            }
            
            # Update status if requested
            if ($UpdateStatus) {
                $statusPath = "specs/projects/kerrigan/status.json"
                if (Test-Path $statusPath) {
                    Write-Host "  📊 Updating project status..." -ForegroundColor Cyan
                    
                    # Determine milestone from task name using same normalization as Find-NextTasks
                    $milestone = ""
                    $normalizedPRTitle = $mergedPR.Title -replace '[^\w\s]', '' -replace '\s+', ' '
                    
                    foreach ($task in $allTasks) {
                        # Try exact match first
                        if ($task.Name -eq $mergedPR.Title) {
                            $milestone = $task.Milestone
                            break
                        }
                        
                        # Then try normalized match
                        $normalizedTaskName = $task.Name -replace '[^\w\s]', '' -replace '\s+', ' '
                        if ($normalizedTaskName -match [regex]::Escape($normalizedPRTitle)) {
                            $milestone = $task.Milestone
                            break
                        }
                    }
                    
                    Update-ProjectStatus -statusPath $statusPath -milestone $milestone -dryRun $DryRun
                }
            }
        }
    } else {
        Write-Host "⚠️  Tasks file not found: $tasksPath" -ForegroundColor Yellow
        Write-Host "   Cannot generate next-step issues without task definitions" -ForegroundColor Gray
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Review complete!" -ForegroundColor Green

if ($mergedPRs.Count -gt 0) {
    Write-Host "✅ Merged $($mergedPRs.Count) PR(s)" -ForegroundColor Green
}

Write-Host "========================================`n" -ForegroundColor Cyan
