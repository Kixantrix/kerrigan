#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Rerun action_required workflow runs for a pull request branch.

.DESCRIPTION
    Finds workflow runs on the PR branch and reruns runs with conclusion=action_required,
    skipping runs already queued or in progress.

.PARAMETER PrNumber
    Pull request number to process.

.EXAMPLE
    .\tools\pr-rerun-pending.ps1 270
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
    $pr = Invoke-GhJson -Args @("pr", "view", "$PrNumber", "--json", "headRefName")
    $branch = $pr.headRefName
    $runs = Invoke-GhJson -Args @("run", "list", "--branch", $branch, "--json", "status,conclusion,databaseId,name", "--limit", "100")

    $rerunTargets = $runs | Where-Object {
        $_.conclusion -eq "action_required" -and $_.status -ne "queued" -and $_.status -ne "in_progress"
    }

    if (-not $rerunTargets) {
        Write-Host "No action_required runs to rerun on branch '$branch'."
        exit 0
    }

    foreach ($run in $rerunTargets) {
        & gh run rerun $run.databaseId 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to rerun run $($run.databaseId)"
        }
        Write-Host "Reran run $($run.databaseId): $($run.name)"
    }

    exit 0
} catch {
    Write-Error "pr-rerun-pending failed: $_"
    exit 1
}
