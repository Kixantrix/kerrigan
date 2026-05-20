#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Resolve all unresolved review threads on a pull request.

.DESCRIPTION
    Lists unresolved threads, optionally prompts for confirmation, and resolves each
    unresolved thread using the GitHub GraphQL resolveReviewThread mutation.

.PARAMETER PrNumber
    Pull request number to process.

.PARAMETER DryRun
    Show unresolved threads that would be resolved, without mutating anything.

.PARAMETER Confirm
    Prompt for confirmation before resolving threads. Defaults to true.

.EXAMPLE
    .\tools\pr-resolve-threads.ps1 270

.EXAMPLE
    .\tools\pr-resolve-threads.ps1 270 -DryRun
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$PrNumber,
    [switch]$DryRun,
    [switch]$Confirm = $true
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
    $query = 'query($owner: String!, $name: String!, $number: Int!) { repository(owner: $owner, name: $name) { pullRequest(number: $number) { reviewThreads(first: 100) { nodes { id isResolved comments(first: 1) { nodes { body path } } } } } } }'
    $result = Invoke-GhJson -Args @("api", "graphql", "-f", "query=$query", "-f", "owner={owner}", "-f", "name={repo}", "-F", "number=$PrNumber")

    $threads = $result.data.repository.pullRequest.reviewThreads.nodes
    $unresolved = $threads | Where-Object { -not $_.isResolved }

    if (-not $unresolved) {
        Write-Host "No unresolved review threads on PR #$PrNumber."
        exit 0
    }

    Write-Host "Unresolved threads on PR #$PrNumber:"
    foreach ($thread in $unresolved) {
        $comment = $thread.comments.nodes | Select-Object -First 1
        $snippet = ""
        if ($null -ne $comment -and $null -ne $comment.body) {
            $snippet = $comment.body.Replace("`r", " ").Replace("`n", " ")
            if ($snippet.Length -gt 80) { $snippet = $snippet.Substring(0, 80) + "..." }
        }
        $path = if ($null -ne $comment -and $comment.path) { $comment.path } else { "(unknown path)" }
        Write-Host "- $path :: $snippet"
    }

    if ($DryRun) {
        Write-Host "Dry run enabled; no threads resolved."
        exit 0
    }

    if ($Confirm) {
        $answer = Read-Host "Resolve $($unresolved.Count) unresolved thread(s)? [y/N]"
        if ($answer -notmatch '^(y|yes)$') {
            Write-Host "Cancelled."
            exit 0
        }
    }

    $mutation = 'mutation($threadId: ID!) { resolveReviewThread(input: {threadId: $threadId}) { thread { id isResolved } } }'
    foreach ($thread in $unresolved) {
        Invoke-GhJson -Args @("api", "graphql", "-f", "query=$mutation", "-f", "threadId=$($thread.id)") | Out-Null
        Write-Host "Resolved thread $($thread.id)"
    }

    exit 0
} catch {
    Write-Error "pr-resolve-threads failed: $_"
    exit 1
}
