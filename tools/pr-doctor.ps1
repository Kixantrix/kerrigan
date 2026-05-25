#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Diagnose pull request status in one command.

.DESCRIPTION
    Prints a six-section diagnostic for a PR in this order:
    1) PR state fields
    2) Last 5 commits
    3) Status checks (failures first)
    4) action_required workflow runs on the PR branch
    5) Resolved vs unresolved review thread counts
    6) Most recent review

.PARAMETER PrNumber
    Pull request number to inspect.

.EXAMPLE
    .\tools\pr-doctor.ps1 270
    Prints a one-shot diagnostic for PR #270.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$PrNumber
)

$ErrorActionPreference = 'Stop'

try {
    $pr = gh pr view $PrNumber --json state,isDraft,mergeable,mergeStateStatus,autoMergeRequest,headRefName,headRefOid,reviews | ConvertFrom-Json

    Write-Host "== PR STATE ==" -ForegroundColor Cyan
    Write-Host ("state: {0}" -f $pr.state)
    Write-Host ("isDraft: {0}" -f $pr.isDraft)
    Write-Host ("mergeable: {0}" -f $pr.mergeable)
    Write-Host ("mergeStateStatus: {0}" -f $pr.mergeStateStatus)
    $mergeMethod = if ($null -ne $pr.autoMergeRequest) { $pr.autoMergeRequest.mergeMethod } else { "none" }
    Write-Host ("autoMergeRequest.mergeMethod: {0}" -f $mergeMethod)

    Write-Host "`n== LAST 5 COMMITS ==" -ForegroundColor Cyan
    $commits = gh pr view $PrNumber --json commits --jq '.commits[-5:][] | "\(.oid[0:7]) \(.messageHeadline)"'
    if ([string]::IsNullOrWhiteSpace($commits)) {
        Write-Host "(none)"
    } else {
        $commits.TrimEnd() -split "`n" | ForEach-Object { Write-Host $_ }
    }

    Write-Host "`n== STATUS CHECKS ==" -ForegroundColor Cyan
    $repo = gh repo view --json nameWithOwner --jq '.nameWithOwner'
    $checks = gh api "repos/$repo/commits/$($pr.headRefOid)/check-runs?per_page=100" --jq '.check_runs[] | @json'
    $checkRows = @()
    if (-not [string]::IsNullOrWhiteSpace($checks)) {
        foreach ($line in ($checks.TrimEnd() -split "`n")) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                $checkRows += ($line | ConvertFrom-Json)
            }
        }
    }
    $priority = @{ failure = 0; cancelled = 0; timed_out = 0; startup_failure = 0; action_required = 0 }
    $sortedChecks = $checkRows | Sort-Object @{ Expression = { if ($priority.ContainsKey($_.conclusion)) { 0 } else { 1 } } }, name
    if ($sortedChecks.Count -eq 0) {
        Write-Host "(none)"
    } else {
        foreach ($c in $sortedChecks) {
            Write-Host ("{0} | conclusion={1} | status={2}" -f $c.name, $c.conclusion, $c.status)
        }
    }

    Write-Host "`n== ACTION_REQUIRED WORKFLOW RUNS ==" -ForegroundColor Cyan
    $runs = gh run list --branch $pr.headRefName --json status,conclusion,databaseId,name | ConvertFrom-Json
    $pending = @($runs | Where-Object { $_.conclusion -eq 'action_required' })
    if ($pending.Count -eq 0) {
        Write-Host "(none)"
    } else {
        foreach ($r in $pending) {
            Write-Host ("databaseId={0} | {1} | status={2} | conclusion={3}" -f $r.databaseId, $r.name, $r.status, $r.conclusion)
        }
    }

    Write-Host "`n== REVIEW THREAD COUNTS ==" -ForegroundColor Cyan
    $owner, $name = $repo.Split('/')
    $threadQuery = 'query($owner:String!, $name:String!, $number:Int!) { repository(owner:$owner, name:$name) { pullRequest(number:$number) { reviewThreads(first:100) { nodes { isResolved } } } } }'
    $threads = gh api graphql -f query=$threadQuery -f owner=$owner -f name=$name -F number=$PrNumber | ConvertFrom-Json
    $nodes = @($threads.data.repository.pullRequest.reviewThreads.nodes)
    $resolvedCount = @($nodes | Where-Object { $_.isResolved }).Count
    $unresolvedCount = @($nodes | Where-Object { -not $_.isResolved }).Count
    Write-Host ("resolved: {0}" -f $resolvedCount)
    Write-Host ("unresolved: {0}" -f $unresolvedCount)

    Write-Host "`n== MOST RECENT REVIEW ==" -ForegroundColor Cyan
    $latest = @($pr.reviews | Where-Object { $_.submittedAt } | Sort-Object submittedAt | Select-Object -Last 1)
    if ($latest.Count -eq 0) {
        Write-Host "(none)"
    } else {
        Write-Host ("author={0} | state={1} | submittedAt={2}" -f $latest[0].author.login, $latest[0].state, $latest[0].submittedAt)
    }

    exit 0
} catch {
    Write-Error $_
    exit 1
}
