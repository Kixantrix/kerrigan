#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Diagnose a pull request's merge/review state in one command.

.DESCRIPTION
    Prints key PR state, recent commits, status checks, action_required workflow runs,
    review thread counts, and most recent review so stalled PR loops are visible quickly.

.PARAMETER PrNumber
    Pull request number to inspect.

.EXAMPLE
    .\tools\pr-doctor.ps1 270
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$PrNumber
)

$ErrorActionPreference = "Stop"

function Invoke-GhJson {
    param([string[]]$Args)
    $output = & gh @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ($output | Out-String)
    }
    return ($output | ConvertFrom-Json)
}

try {
    $pr = Invoke-GhJson -Args @("pr", "view", "$PrNumber", "--json", "state,isDraft,mergeable,mergeStateStatus,autoMergeRequest,headRefName")
    $checks = Invoke-GhJson -Args @("pr", "checks", "$PrNumber", "--json", "name,conclusion,status")
    $runs = Invoke-GhJson -Args @("run", "list", "--branch", $pr.headRefName, "--json", "status,conclusion,databaseId,name", "--limit", "50")
    $commits = Invoke-GhJson -Args @("api", "repos/{owner}/{repo}/commits?sha=$($pr.headRefName)&per_page=5")

    $query = 'query($owner: String!, $name: String!, $number: Int!) { repository(owner: $owner, name: $name) { pullRequest(number: $number) { reviewThreads(first: 100) { nodes { isResolved } } reviews(last: 1) { nodes { author { login } state submittedAt } } } } }'
    $graph = Invoke-GhJson -Args @("api", "graphql", "-f", "query=$query", "-f", "owner={owner}", "-f", "name={repo}", "-F", "number=$PrNumber")

    Write-Host "== PR state =="
    Write-Host "state=$($pr.state)"
    Write-Host "isDraft=$($pr.isDraft)"
    Write-Host "mergeable=$($pr.mergeable)"
    Write-Host "mergeStateStatus=$($pr.mergeStateStatus)"
    Write-Host "autoMergeRequest.mergeMethod=$($pr.autoMergeRequest.mergeMethod)"

    Write-Host "`n== Last 5 commits =="
    foreach ($c in $commits) {
        $shortSha = $c.sha.Substring(0, 7)
        Write-Host "$shortSha $($c.commit.message.Split("`n")[0])"
    }

    Write-Host "`n== Status checks (failures first) =="
    $rank = @{ failure = 0; timed_out = 1; cancelled = 2; action_required = 3; startup_failure = 4; stale = 5; skipped = 6; neutral = 7; success = 8; "" = 9 }
    $sortedChecks = $checks | Sort-Object -Property @{ Expression = { if ($rank.ContainsKey($_.conclusion)) { $rank[$_.conclusion] } else { 9 } } }, @{ Expression = "name" }
    foreach ($check in $sortedChecks) {
        Write-Host "$($check.name) | conclusion=$($check.conclusion) | status=$($check.status)"
    }

    Write-Host "`n== action_required workflow runs =="
    $actionRequiredRuns = $runs | Where-Object { $_.conclusion -eq "action_required" }
    if (-not $actionRequiredRuns) {
        Write-Host "none"
    } else {
        foreach ($run in $actionRequiredRuns) {
            Write-Host "$($run.name) | databaseId=$($run.databaseId) | status=$($run.status)"
        }
    }

    Write-Host "`n== Review threads =="
    $threads = $graph.data.repository.pullRequest.reviewThreads.nodes
    $resolvedCount = ($threads | Where-Object { $_.isResolved }).Count
    $unresolvedCount = ($threads | Where-Object { -not $_.isResolved }).Count
    Write-Host "resolved=$resolvedCount unresolved=$unresolvedCount"

    Write-Host "`n== Most recent review =="
    $lastReview = $graph.data.repository.pullRequest.reviews.nodes | Select-Object -First 1
    if ($null -eq $lastReview) {
        Write-Host "none"
    } else {
        Write-Host "author=$($lastReview.author.login) state=$($lastReview.state) submittedAt=$($lastReview.submittedAt)"
    }

    exit 0
} catch {
    Write-Error "pr-doctor failed: $_"
    exit 1
}
