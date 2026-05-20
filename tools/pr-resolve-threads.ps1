#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Resolve unresolved PR review threads.

.DESCRIPTION
    Finds unresolved review threads on a pull request, lists each one (path +
    comment preview), and resolves them with GraphQL resolveReviewThread.

.PARAMETER PrNumber
    Pull request number to process.

.PARAMETER DryRun
    Show unresolved threads that would be resolved without mutating GitHub state.

.PARAMETER Confirm
    Prompt before resolving threads. Enabled by default; use -Confirm:$false to skip.

.EXAMPLE
    .\tools\pr-resolve-threads.ps1 270
    Prompts, then resolves all unresolved review threads.

.EXAMPLE
    .\tools\pr-resolve-threads.ps1 270 -DryRun
    Shows unresolved threads without resolving them.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$PrNumber,
    [switch]$DryRun,
    [switch]$Confirm = $true
)

$ErrorActionPreference = 'Stop'

$repo = gh repo view --json nameWithOwner --jq '.nameWithOwner'
$owner, $name = $repo.Split('/')
$query = 'query($owner:String!, $name:String!, $number:Int!) { repository(owner:$owner, name:$name) { pullRequest(number:$number) { reviewThreads(first:100) { nodes { id isResolved comments(first:1) { nodes { path body } } } } } } }'
$data = gh api graphql -f query=$query -f owner=$owner -f name=$name -F number=$PrNumber | ConvertFrom-Json
$threads = @($data.data.repository.pullRequest.reviewThreads.nodes | Where-Object { -not $_.isResolved })

if ($threads.Count -eq 0) {
    Write-Host "No unresolved threads to resolve."
    exit 0
}

Write-Host "Unresolved threads on PR #$PrNumber:" -ForegroundColor Cyan
foreach ($thread in $threads) {
    $comment = $thread.comments.nodes | Select-Object -First 1
    $path = if ($null -ne $comment -and $comment.path) { $comment.path } else { '(unknown path)' }
    $body = if ($null -ne $comment -and $comment.body) { $comment.body } else { '' }
    $preview = ($body -replace "\s+", ' ').Trim()
    if ($preview.Length -gt 80) { $preview = $preview.Substring(0, 80) }
    Write-Host ("- {0}: {1}" -f $path, $preview)
}

if ($DryRun) {
    Write-Host "Dry run: would resolve $($threads.Count) thread(s)." -ForegroundColor Magenta
    exit 0
}

if ($Confirm) {
    $reply = Read-Host "Resolve $($threads.Count) thread(s)? [y/N]"
    if ($reply -notmatch '^[Yy]') {
        Write-Host "Cancelled."
        exit 0
    }
}

$mutation = 'mutation($threadId:ID!) { resolveReviewThread(input:{threadId:$threadId}) { thread { id isResolved } } }'
foreach ($thread in $threads) {
    gh api graphql -f query=$mutation -f threadId=$thread.id | Out-Null
    Write-Host "Resolved thread $($thread.id)"
}

exit 0
