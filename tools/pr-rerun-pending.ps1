#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Rerun PR workflow runs stuck in action_required.

.DESCRIPTION
    Looks up workflow runs on the PR branch and reruns runs with
    conclusion=action_required, while skipping queued or in_progress runs.

.PARAMETER PrNumber
    Pull request number whose branch should be inspected.

.EXAMPLE
    .\tools\pr-rerun-pending.ps1 270
    Reruns action_required runs for PR #270's branch.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$PrNumber
)

$ErrorActionPreference = 'Stop'

$pr = gh pr view $PrNumber --json headRefName | ConvertFrom-Json
$branch = $pr.headRefName
$runs = gh run list --branch $branch --json status,conclusion,databaseId,name | ConvertFrom-Json
$rerun = @($runs | Where-Object { $_.conclusion -eq 'action_required' -and $_.status -ne 'in_progress' -and $_.status -ne 'queued' })

if ($rerun.Count -eq 0) {
    Write-Host "No action_required runs to rerun for branch '$branch'."
    exit 0
}

foreach ($run in $rerun) {
    gh run rerun $run.databaseId | Out-Null
    Write-Host ("Reran run {0} ({1})" -f $run.databaseId, $run.name)
}

exit 0
