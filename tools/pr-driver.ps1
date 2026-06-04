#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Auto-advance a PR through its mechanical lifecycle; escalate only decisions.

.DESCRIPTION
    Runs one pass of the PR driver loop for the given PR number.  Mechanical
    steps (promote, update-branch, rerun CI, resolve converged threads, wait)
    are executed automatically.  Genuine decision points (empty PR, CI red,
    review classification, conflicts, stuck) are reported back and the script
    exits with code 2 so callers can surface them.

    The decision logic lives in tools/pr_driver_decide.py (pure Python, no
    network) so it can be unit-tested without GitHub access.

    Composed helpers (never reimplemented here):
      tools/pr-promote.ps1          — promote/update-branch/review-request/arm
      tools/pr-rerun-pending.ps1    — rerun action_required workflow runs
      tools/pr_reply_resolve.py     — reply + resolve one review thread
      tools/pr-redispatch.ps1       — post re-dispatch comment + re-arm

    Safety rails (hard-coded, never overridden by flags):
      • Never auto-close a PR.
      • Never push code to a PR branch.
      • Never gh pr merge --admin / never bypass branch protection.
      • Never auto-dispatch new issues; only emit dependent-unblocked notes.
      • AUTO_RESOLVE_CONVERGED is gated behind -AutoResolveConverged.

.PARAMETER PrNumber
    Pull request number to drive.

.PARAMETER AutoResolveConverged
    When set, automatically resolve review threads that predate the last commit
    and whose post-fix re-review added zero new inline comments.
    Without this flag the script reports the intent (dry-run style) but does
    not actually resolve.

.PARAMETER MaxPasses
    Maximum number of loop passes before the driver escalates as stuck.
    Defaults to 10.

.PARAMETER DryRun
    Print what would happen without executing any side-effecting gh calls.

.PARAMETER PassCount
    Current consecutive pass count with no state change (used for stuck
    detection). Defaults to 0.

.EXAMPLE
    .\tools\pr-driver.ps1 270
    Runs one pass of the driver loop for PR #270.

.EXAMPLE
    .\tools\pr-driver.ps1 270 -AutoResolveConverged -DryRun
    Shows what the driver would do for PR #270 (with converged-thread resolution
    enabled) without making any changes.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$PrNumber,

    [switch]$AutoResolveConverged,

    [int]$MaxPasses = 10,

    [switch]$DryRun,

    [int]$PassCount = 0
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ---------------------------------------------------------------------------
# Helper: run gh with optional dry-run short-circuit
# ---------------------------------------------------------------------------
function Invoke-Gh {
    param([string[]]$Args, [string]$Label = "gh")
    if ($DryRun) {
        Write-Host "[dry-run] gh $Args"
        return
    }
    $result = & gh @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ("gh $Args exited ${LASTEXITCODE}: $result")
    }
}

# ---------------------------------------------------------------------------
# Step 1: Gather raw PR state via gh
# ---------------------------------------------------------------------------
Write-Host "=== pr-driver pass for PR #$PrNumber ===" -ForegroundColor Cyan

$repo = (gh repo view --json nameWithOwner --jq '.nameWithOwner').Trim()
$owner, $repoName = $repo.Split('/')

# Core PR fields
# NOTE: keep the --json field list on ONE line. A backtick line-continuation
# inside a comma list splits it into two argv tokens, so trailing fields
# (headRefOid, files, commits, reviews) silently never get requested.
$prFields = 'state,isDraft,title,mergeable,mergeStateStatus,autoMergeRequest,headRefName,headRefOid,files,commits,reviews'
$prJson = gh pr view $PrNumber --json $prFields | ConvertFrom-Json

# Check-runs
$checkRunsRaw = gh api "repos/$repo/commits/$($prJson.headRefOid)/check-runs?per_page=100" `
    --jq '.check_runs[] | @json'

$checkRuns = @()
if (-not [string]::IsNullOrWhiteSpace($checkRunsRaw)) {
    foreach ($line in ($checkRunsRaw.TrimEnd() -split "`n")) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            $checkRuns += ($line | ConvertFrom-Json)
        }
    }
}

# Workflow runs (action_required)
$runs = gh run list --branch $prJson.headRefName --json status,conclusion,databaseId,name `
    | ConvertFrom-Json
$actionRequiredRuns = @($runs | Where-Object { $_.conclusion -eq 'action_required' })

# Review threads via GraphQL
$threadQuery = @'
query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      reviewThreads(first:100) {
        nodes {
          id
          isResolved
          comments(first:20) {
            nodes {
              databaseId
              path
              line
              body
              createdAt
            }
          }
        }
      }
    }
  }
}
'@
$threadsResult = gh api graphql `
    -f "query=$threadQuery" `
    -f "owner=$owner" `
    -f "name=$repoName" `
    -F "number=$PrNumber" | ConvertFrom-Json
$allThreads = @($threadsResult.data.repository.pullRequest.reviewThreads.nodes)
$unresolvedThreads = @($allThreads | Where-Object { -not $_.isResolved })

# Latest review timestamp
$latestReview = @($prJson.reviews | Where-Object { $_.submittedAt } |
    Sort-Object submittedAt | Select-Object -Last 1)
$latestReviewAt = if ($latestReview.Count -gt 0) { $latestReview[0].submittedAt } else { $null }

# Latest commit timestamp (from the list of commits in the PR)
$allCommits = @($prJson.commits)
$latestCommitAt = $null
if ($allCommits.Count -gt 0) {
    # commits list objects have `committedDate` or we fall back to sorting by oid
    $lastCommit = $allCommits[-1]
    $latestCommitAt = if ($lastCommit.PSObject.Properties['committedDate']) {
        $lastCommit.committedDate
    } else {
        $null
    }
}

# Count new inline comments from the latest review
# (reviews with state=COMMENTED that were submitted after the last commit)
$latestReviewNewInline = 0
if ($null -ne $latestReviewAt -and $null -ne $latestCommitAt) {
    $revDt = [DateTimeOffset]::Parse($latestReviewAt)
    $commitDt = [DateTimeOffset]::Parse($latestCommitAt)
    if ($revDt -gt $commitDt) {
        # Count unresolved threads whose first comment postdates latestCommitAt
        foreach ($t in $unresolvedThreads) {
            $firstComment = @($t.comments.nodes)[0]
            if ($null -ne $firstComment) {
                $cDt = [DateTimeOffset]::Parse($firstComment.createdAt)
                if ($cDt -gt $commitDt) {
                    $latestReviewNewInline++
                }
            }
        }
    }
}

# ---------------------------------------------------------------------------
# Step 2: Build state dict as JSON and call the pure Python decision function
# ---------------------------------------------------------------------------
$stateDict = [ordered]@{
    title                          = $prJson.title
    state                          = $prJson.state
    files                          = $prJson.files.Count
    commits                        = @($prJson.commits | ForEach-Object { $_.messageHeadline })
    isDraft                        = [bool]$prJson.isDraft
    mergeable                      = $prJson.mergeable
    mergeStateStatus               = $prJson.mergeStateStatus
    autoMergeArmed                 = ($null -ne $prJson.autoMergeRequest)
    checkConclusions               = @($checkRuns | ForEach-Object { $_.conclusion })
    checkNames                     = @($checkRuns | ForEach-Object { $_.name })
    checkStatuses                  = @($checkRuns | ForEach-Object { $_.status })
    actionRequiredRuns             = $actionRequiredRuns.Count
    unresolvedThreads              = @($unresolvedThreads | ForEach-Object {
        [ordered]@{
            id        = $_.id
            createdAt = $_.createdAt
            comments  = @($_.comments.nodes | ForEach-Object {
                [ordered]@{
                    databaseId = $_.databaseId
                    path       = $_.path
                    line       = $_.line
                    body       = $_.body
                    createdAt  = $_.createdAt
                }
            })
        }
    })
    latestReviewAt                 = $latestReviewAt
    latestCommitAt                 = $latestCommitAt
    latestReviewNewInlineComments  = $latestReviewNewInline
    passCount                      = $PassCount
}

$stateJson = $stateDict | ConvertTo-Json -Depth 10 -Compress

$decideScript = Join-Path $ScriptDir "pr_driver_decide.py"
$actionJson = $stateJson | python $decideScript --json-stdin 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "pr_driver_decide.py failed: $actionJson"
    exit 1
}
$decision = $actionJson | ConvertFrom-Json

$action = $decision.action
$reason = $decision.reason

Write-Host ("Action: {0}" -f $action) -ForegroundColor Yellow
Write-Host ("Reason: {0}" -f $reason)

# ---------------------------------------------------------------------------
# Step 3: Execute the action
# ---------------------------------------------------------------------------
switch ($action) {

    "SKIP" {
        Write-Host "[SKIP] $reason"
        exit 0
    }

    "AUTO_DONE" {
        Write-Host "[DONE] PR #$PrNumber is merged."
        exit 0
    }

    "AUTO_PROMOTE" {
        Write-Host "[AUTO] Promoting PR #$PrNumber via pr-promote.ps1"
        if ($DryRun) {
            Write-Host "[dry-run] pwsh $ScriptDir/pr-promote.ps1 $PrNumber"
        } else {
            & "$ScriptDir/pr-promote.ps1" $PrNumber
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        exit 0
    }

    "AUTO_UPDATE_BRANCH" {
        Write-Host "[AUTO] Updating branch for PR #$PrNumber (BEHIND)"
        if ($DryRun) {
            Write-Host "[dry-run] gh pr update-branch $PrNumber"
            Write-Host "[dry-run] gh pr merge $PrNumber --auto --squash"
        } else {
            gh pr update-branch $PrNumber 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Error "gh pr update-branch failed for PR #$PrNumber"
                exit 1
            }
            # Re-arm auto-merge after branch update (branch update can drop it)
            gh pr merge $PrNumber --auto --squash 2>&1 | Out-Null
        }
        exit 0
    }

    "AUTO_RERUN_CI" {
        Write-Host "[AUTO] Rerunning action_required CI for PR #$PrNumber"
        if ($DryRun) {
            Write-Host "[dry-run] pwsh $ScriptDir/pr-rerun-pending.ps1 $PrNumber"
        } else {
            & "$ScriptDir/pr-rerun-pending.ps1" $PrNumber
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        exit 0
    }

    "AUTO_WAIT" {
        Write-Host "[WAIT] $reason"
        exit 0
    }

    "AUTO_RESOLVE_CONVERGED" {
        $threadIds = @($decision.thread_ids)
        if ($AutoResolveConverged) {
            Write-Host ("[AUTO] Resolving {0} converged thread(s) for PR #{1}" -f $threadIds.Count, $PrNumber)
            foreach ($tid in $threadIds) {
                if ($DryRun) {
                    Write-Host "[dry-run] python $ScriptDir/pr_reply_resolve.py (resolve thread $tid)"
                } else {
                    # Resolve the thread directly via GraphQL (no reply needed for converged threads)
                    $mutation = 'mutation($threadId: ID!) { resolveReviewThread(input: {threadId: $threadId}) { thread { id isResolved } } }'
                    gh api graphql -f "query=$mutation" -f "threadId=$tid" | Out-Null
                    Write-Host ("  Resolved thread {0}" -f $tid)
                }
            }
        } else {
            Write-Host ("[DRY-RUN-INTENT] Would resolve {0} converged thread(s) for PR #{1}:" -f $threadIds.Count, $PrNumber)
            foreach ($tid in $threadIds) {
                Write-Host ("  would resolve thread {0} because re-review after last commit added 0 new inline comments" -f $tid)
            }
            Write-Host "  Re-run with -AutoResolveConverged to actually resolve."
        }
        exit 0
    }

    "ESCALATE" {
        $escalateType = $decision.escalate_type
        Write-Host ("[ESCALATE] type={0}" -f $escalateType) -ForegroundColor Red
        Write-Host ("  Reason: {0}" -f $reason)

        switch ($escalateType) {
            "review-classify" {
                $threads = @($decision.threads)
                Write-Host ("  Unresolved threads ({0}):" -f $threads.Count)
                foreach ($t in $threads) {
                    $loc = if ($t.path) { "{0}:{1}" -f $t.path, $t.line } else { "(no location)" }
                    $preview = if ($t.body -and $t.body.Length -gt 120) { $t.body.Substring(0, 120) + "..." } elseif ($t.body) { $t.body } else { "(no body)" }
                    Write-Host ("    [{0}] {1}" -f $loc, $preview)
                }
            }
            "stuck" {
                Write-Host ("  PR #$PrNumber has had no state change across {0} passes." -f $PassCount)
            }
        }

        # Exit code 2 signals ESCALATE to callers / loop drivers
        exit 2
    }

    default {
        Write-Error "Unrecognised action: $action"
        exit 1
    }
}
