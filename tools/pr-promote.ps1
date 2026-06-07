#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Promote a draft PR into the merge queue sequence, gated by a pre-flight
    content check.

.DESCRIPTION
    Runs a MANDATORY pre-flight gate, then the four PR promotion steps in strict
    order, then a rerun nudge:

    0) Pre-flight gate (unless -SkipPreflight): inspect the PR's files + commits.
       If the PR has zero changed files, or its only commits are scaffold/merge
       commits (e.g. `Initial plan`), the cloud agent stalled and prematurely
       cleared `[WIP]`. REFUSE to promote (exit 2) rather than auto-merging an
       empty PR to main. (Guards the 2026-05-27 #294 empty-merge incident class.)
    1) Mark PR ready for review
    2) Update branch from main
    3) Request Copilot reviewer (unless skipped)
    4) Arm auto-merge with selected merge method
    5) Rerun action_required checks (unless -SkipRerun): bot-authored branches
       leave workflow runs in `action_required` after the synchronize push;
       this nudges them via tools/pr-rerun-pending.ps1.

    Dry run mode prints commands without executing them.

.PARAMETER PrNumber
    Pull request number to promote.

.PARAMETER DryRun
    Print planned commands without executing gh.

.PARAMETER MergeMethod
    Merge method for auto-merge: squash, merge, or rebase.

.PARAMETER SkipReviewer
    Skip requesting the Copilot reviewer.

.PARAMETER SkipPreflight
    Skip the pre-flight empty-PR gate. Use only when you have already verified
    the PR has real content by other means.

.PARAMETER SkipRerun
    Skip the trailing pr-rerun-pending nudge.

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
    [switch]$SkipReviewer,
    [switch]$SkipPreflight,
    [switch]$SkipRerun
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
        $global:LASTEXITCODE = 0
        # gh writes its success confirmations to stderr; under the script-scope
        # $ErrorActionPreference='Stop' a native stderr write is promoted to a
        # terminating error, which previously made successful steps (e.g.
        # marking the PR ready) report [FAIL] with the success text as the
        # message. Lower EAP for just the native call and rely on the explicit
        # $LASTEXITCODE check below to decide success/failure.
        $previousEap = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            & $Command
        } finally {
            $ErrorActionPreference = $previousEap
        }
        if ($LASTEXITCODE -ne 0) {
            throw ("Command exited with code {0}." -f $LASTEXITCODE)
        }
        Write-Host ("[OK] {0}" -f $Label)
        return $true
    } catch {
        Write-Host ("[FAIL] {0}: {1}" -f $Label, $_.Exception.Message)
        if ($ContinueOnFailure) {
            Write-Host ("[WARN] Continuing after step failure: {0}" -f $Label) -ForegroundColor Yellow
            return $true
        }
        return $false
    }
}

$repo = '(unknown)/(unknown)'
if ($DryRun) {
    Write-Host "[OK] [dry-run] gh repo view --json nameWithOwner --jq "".nameWithOwner"""
} else {
    $repoOutput = gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ("[FAIL] Resolve repository owner/name: {0}" -f ($repoOutput -join "`n"))
        exit 1
    }
    $repo = ($repoOutput -join "`n").Trim()
    if ([string]::IsNullOrWhiteSpace($repo)) {
        Write-Host "[FAIL] Resolve repository owner/name: empty response from gh repo view."
        exit 1
    }
    Write-Host "[OK] Resolved repository owner/name."
}

# ---------------------------------------------------------------------------
# Pre-flight gate: refuse empty / scaffold-only PRs. A cloud agent that stalls
# can clear [WIP] with nothing (or only an `Initial plan` commit) on the branch;
# promoting that auto-merges an empty PR to main (the #294 incident class).
# ---------------------------------------------------------------------------
if ($SkipPreflight) {
    Write-Host "[SKIP] Pre-flight empty-PR gate (requested by -SkipPreflight)."
} elseif ($DryRun) {
    Write-Host "[OK] [dry-run] gh pr view $PrNumber --json files,commits  (pre-flight empty-PR gate)"
} else {
    $preflightRaw = gh pr view $PrNumber --json files,commits 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ("[FAIL] Pre-flight: gh pr view #{0}: {1}" -f $PrNumber, (($preflightRaw | Out-String).Trim()))
        exit 1
    }
    $preflight = ($preflightRaw | Out-String) | ConvertFrom-Json
    $fileCount = @($preflight.files).Count
    $headlines = @($preflight.commits | ForEach-Object { ([string]$_.messageHeadline).Trim() } | Where-Object { $_ -ne '' })
    # A commit is "substantive" if it is not a scaffold (`Initial plan`) or a
    # merge commit. A PR with no substantive commit has nothing to merge.
    $substantive = @($headlines | Where-Object { $_ -notmatch '^(Initial plan|Merge )' })
    if ($fileCount -eq 0 -or $substantive.Count -eq 0) {
        Write-Host ("[BLOCK] Pre-flight refused PR #{0}: files={1}, substantive commits={2}." -f $PrNumber, $fileCount, $substantive.Count) -ForegroundColor Red
        Write-Host "        The cloud agent likely stalled and cleared [WIP] prematurely."
        Write-Host "        Close the PR and reopen the issue, or re-dispatch. (Use -SkipPreflight to override.)"
        exit 2
    }
    Write-Host ("[OK] Pre-flight: PR #{0} has {1} file(s) and {2} substantive commit(s)." -f $PrNumber, $fileCount, $substantive.Count)
}

if (-not (Invoke-Step -Label "Ready PR #$PrNumber" -ContinueOnFailure -Command {
    if ($DryRun) {
        Write-Host "[OK] [dry-run] gh pr ready $PrNumber"
    } else {
        # gh writes its success confirmation to stderr; redirect so $ErrorActionPreference='Stop' doesn't treat it as a failure.
        gh pr ready $PrNumber 2>&1 | Out-Null
    }
})) {
    exit 1
}

if (-not (Invoke-Step -Label "Update branch for PR #$PrNumber" -Command {
    if ($DryRun) {
        Write-Host "[OK] [dry-run] gh pr update-branch $PrNumber"
    } else {
        gh pr update-branch $PrNumber 2>&1 | Out-Null
    }
})) {
    exit 1
}

if ($SkipReviewer) {
    Write-Host "[SKIP] Skip reviewer request (requested by -SkipReviewer)."
} else {
    if (-not (Invoke-Step -Label "Request Copilot reviewer for PR #$PrNumber" -Command {
        if ($DryRun) {
            Write-Host "[OK] [dry-run] gh api --method POST repos/$repo/pulls/$PrNumber/requested_reviewers -f ""reviewers[]=copilot-pull-request-reviewer[bot]"""
        } else {
            $reviewerOutput = gh api --method POST "repos/$repo/pulls/$PrNumber/requested_reviewers" -f "reviewers[]=copilot-pull-request-reviewer[bot]" 2>&1
            if ($LASTEXITCODE -ne 0 -and ($reviewerOutput -join "`n") -notmatch '422') {
                throw ($reviewerOutput -join "`n")
            }
            if ($LASTEXITCODE -ne 0 -and ($reviewerOutput -join "`n") -match '422') {
                $global:LASTEXITCODE = 0
            }
        }
    })) {
        exit 1
    }
}

if (-not (Invoke-Step -Label "Arm auto-merge ($MergeMethod) for PR #$PrNumber" -Command {
    if ($DryRun) {
        Write-Host "[OK] [dry-run] gh pr merge $PrNumber --auto --$MergeMethod"
    } else {
        gh pr merge $PrNumber --auto --$MergeMethod | Out-Null
    }
})) {
    exit 1
}

# ---------------------------------------------------------------------------
# Rerun nudge: bot-authored branches leave required-check workflow runs in
# `action_required` after the synchronize push from update-branch. Auto-merge
# will never fire while they sit pending, so kick them. Best-effort: the merge
# is already armed, so a rerun failure must not fail the promotion.
# ---------------------------------------------------------------------------
if ($SkipRerun) {
    Write-Host "[SKIP] Rerun action_required checks (requested by -SkipRerun)."
} elseif ($DryRun) {
    Write-Host "[OK] [dry-run] tools/pr-rerun-pending.ps1 $PrNumber"
} else {
    $rerunScript = Join-Path $PSScriptRoot 'pr-rerun-pending.ps1'
    if (Test-Path -LiteralPath $rerunScript) {
        try {
            & $rerunScript $PrNumber
            Write-Host "[OK] Reran action_required checks."
        } catch {
            Write-Host ("[WARN] Rerun nudge failed (auto-merge still armed): {0}" -f $_.Exception.Message) -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARN] pr-rerun-pending.ps1 not found; skipping rerun nudge."
    }
}

exit 0
