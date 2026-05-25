#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Promote a draft PR into the merge queue sequence.

.DESCRIPTION
    Runs the four PR promotion steps in strict order:
    1) Mark PR ready for review
    2) Update branch from main
    3) Request Copilot reviewer (unless skipped)
    4) Arm auto-merge with selected merge method

    Dry run mode prints commands without executing them.

.PARAMETER PrNumber
    Pull request number to promote.

.PARAMETER DryRun
    Print planned commands without executing gh.

.PARAMETER MergeMethod
    Merge method for auto-merge: squash, merge, or rebase.

.PARAMETER SkipReviewer
    Skip requesting the Copilot reviewer.

.EXAMPLE
    .\tools\pr-promote.ps1 282
    Promotes PR #282 through ready, update-branch, reviewer request, and auto-merge.

.EXAMPLE
    .\tools\pr-promote.ps1 282 -DryRun -MergeMethod merge
    Prints the exact promotion commands without executing them.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$PrNumber,
    [switch]$DryRun,
    [ValidateSet('squash', 'merge', 'rebase')]
    [string]$MergeMethod = 'squash',
    [switch]$SkipReviewer
)

$ErrorActionPreference = 'Stop'

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,
        [switch]$ContinueOnFailure
    )

    try {
        & $Command
        Write-Host ("✓ {0}" -f $Label)
        return $true
    } catch {
        Write-Host ("✗ {0}: {1}" -f $Label, $_.Exception.Message)
        if ($ContinueOnFailure) {
            Write-Host ("✓ Continuing after step failure: {0}" -f $Label) -ForegroundColor Yellow
            return $true
        }
        return $false
    }
}

$repo = '(unknown)/(unknown)'
if ($DryRun) {
    Write-Host "✓ [dry-run] gh repo view --json nameWithOwner -q .nameWithOwner"
} else {
    try {
        $repo = gh repo view --json nameWithOwner -q .nameWithOwner
        Write-Host "✓ Resolved repository owner/name."
    } catch {
        Write-Host ("✗ Resolve repository owner/name: {0}" -f $_.Exception.Message)
        exit 1
    }
}

if (-not (Invoke-Step -Label "Ready PR #$PrNumber" -ContinueOnFailure -Command {
    if ($DryRun) {
        Write-Host "✓ [dry-run] gh pr ready $PrNumber"
    } else {
        gh pr ready $PrNumber | Out-Null
    }
})) {
    exit 1
}

if (-not (Invoke-Step -Label "Update branch for PR #$PrNumber" -Command {
    if ($DryRun) {
        Write-Host "✓ [dry-run] gh pr update-branch $PrNumber"
    } else {
        gh pr update-branch $PrNumber | Out-Null
    }
})) {
    exit 1
}

if ($SkipReviewer) {
    Write-Host "✓ Skip reviewer request (requested by -SkipReviewer)."
} else {
    if (-not (Invoke-Step -Label "Request Copilot reviewer for PR #$PrNumber" -Command {
        if ($DryRun) {
            Write-Host "✓ [dry-run] gh api --method POST repos/$repo/pulls/$PrNumber/requested_reviewers -f ""reviewers[]=copilot-pull-request-reviewer[bot]"""
        } else {
            $reviewerOutput = gh api --method POST "repos/$repo/pulls/$PrNumber/requested_reviewers" -f "reviewers[]=copilot-pull-request-reviewer[bot]" 2>&1
            if ($LASTEXITCODE -ne 0 -and ($reviewerOutput -join "`n") -notmatch '422') {
                throw ($reviewerOutput -join "`n")
            }
        }
    })) {
        exit 1
    }
}

if (-not (Invoke-Step -Label "Arm auto-merge ($MergeMethod) for PR #$PrNumber" -Command {
    if ($DryRun) {
        Write-Host "✓ [dry-run] gh pr merge $PrNumber --auto --$MergeMethod"
    } else {
        gh pr merge $PrNumber --auto --$MergeMethod | Out-Null
    }
})) {
    exit 1
}

exit 0
