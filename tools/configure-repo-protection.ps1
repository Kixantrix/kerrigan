#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Apply a repo's declared branch-protection + merge-queue shape from
    .github/repo-protection.json. DRY-RUN by default; mutates only with -Apply.

.DESCRIPTION
    Kerrigan picks a protection/merge-queue shape PER REPO via a declarative
    config (.github/repo-protection.json). This tool reads that config and brings
    the repo's GitHub settings into line with it:

      1. Required status checks + strict-up-to-date  (classic branch protection)
      2. Merge queue                                 (repository ruleset)

    Flexible: any repo can ship a different config (different required checks,
    queue off, strict on) and this tool applies whatever is declared. Optimized
    default lives in preset/kerrigan/repo-protection.json. Absent config => the
    tool refuses (nothing declared to apply).

    SAFETY: the default mode is a DRY-RUN that prints every planned API call and
    the exact JSON payloads. It mutates shared branch protection ONLY when you
    pass -Apply. Re-running is idempotent (converges to the declared state).

    The merge-queue rule is created/updated via the repository rulesets API. The
    dry-run prints the full ruleset payload so you can review the merge_queue
    parameters against your repo's GitHub plan before the first -Apply.

.PARAMETER Repo
    owner/name. Defaults to the current repo (gh repo view).

.PARAMETER ConfigPath
    Path to the declared config. Default: .github/repo-protection.json.

.PARAMETER Apply
    Actually perform the mutations. Without it, the tool only prints the plan.

.EXAMPLE
    .\tools\configure-repo-protection.ps1
    Dry-run: show what would change on the current repo.

.EXAMPLE
    .\tools\configure-repo-protection.ps1 -Repo Kixantrix/kerrigan -Apply
    Apply the declared protection + merge queue to the repo.
#>

param(
    [string]$Repo,
    [string]$ConfigPath = ".github/repo-protection.json",
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'

function Write-Plan([string]$msg) { Write-Host "[plan] $msg" -ForegroundColor Cyan }
function Write-Did([string]$msg) { Write-Host "[done] $msg" -ForegroundColor Green }

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    Write-Host "[skip] No $ConfigPath in this repo; nothing declared to apply." -ForegroundColor Yellow
    exit 0
}

$config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json

if (-not $Repo) {
    $Repo = (gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Repo)) {
        Write-Host "[fail] Could not resolve current repo; pass -Repo owner/name." -ForegroundColor Red
        exit 1
    }
}

$branch = if ($config.branch) { [string]$config.branch } else { 'main' }
$requiredChecks = @($config.required_checks)
$strict = [bool]$config.strict_status_checks
$mode = if ($Apply) { "APPLY" } else { "DRY-RUN" }

Write-Host "=== configure-repo-protection ($mode) ===" -ForegroundColor Cyan
Write-Host ("repo={0} branch={1}" -f $Repo, $branch)
Write-Host ""

# ---------------------------------------------------------------------------
# 1) Required status checks + strict (classic branch protection)
# ---------------------------------------------------------------------------
$rscPayload = [ordered]@{
    strict   = $strict
    contexts = $requiredChecks
} | ConvertTo-Json -Compress
Write-Plan "PATCH /repos/$Repo/branches/$branch/protection/required_status_checks"
Write-Host "       payload: $rscPayload"
if ($Apply) {
    $tmp = New-TemporaryFile
    Set-Content -LiteralPath $tmp -Value $rscPayload -Encoding ascii -NoNewline
    gh api --method PATCH "repos/$Repo/branches/$branch/protection/required_status_checks" --input $tmp 2>&1 | Out-Null
    Remove-Item $tmp -ErrorAction SilentlyContinue
    if ($LASTEXITCODE -ne 0) { Write-Host "[fail] required_status_checks PATCH failed." -ForegroundColor Red; exit 1 }
    Write-Did "required status checks set (strict=$strict; contexts=$($requiredChecks -join ', '))"
}
Write-Host ""

# ---------------------------------------------------------------------------
# 2) Merge queue (repository ruleset)
# ---------------------------------------------------------------------------
$mq = $config.merge_queue
if ($null -ne $mq -and [bool]$mq.enabled) {
    $rulesetName = "Kerrigan merge queue"
    $mqParams = [ordered]@{
        merge_method                      = if ($mq.merge_method) { [string]$mq.merge_method } else { 'SQUASH' }
        min_entries_to_merge              = if ($null -ne $mq.min_entries_to_merge) { [int]$mq.min_entries_to_merge } else { 1 }
        max_entries_to_merge              = if ($null -ne $mq.max_entries_to_merge) { [int]$mq.max_entries_to_merge } else { 5 }
        min_entries_to_merge_wait_minutes = if ($null -ne $mq.min_entries_to_merge_wait_minutes) { [int]$mq.min_entries_to_merge_wait_minutes } else { 5 }
        max_entries_to_build              = if ($null -ne $mq.max_entries_to_build) { [int]$mq.max_entries_to_build } else { 5 }
        check_response_timeout_minutes    = if ($null -ne $mq.check_response_timeout_minutes) { [int]$mq.check_response_timeout_minutes } else { 60 }
        grouping_strategy                 = if ($mq.grouping_strategy) { [string]$mq.grouping_strategy } else { 'ALLGREEN' }
    }
    $rulesetPayload = [ordered]@{
        name        = $rulesetName
        target      = 'branch'
        enforcement = 'active'
        conditions  = [ordered]@{ ref_name = [ordered]@{ include = @("refs/heads/$branch"); exclude = @() } }
        rules       = @([ordered]@{ type = 'merge_queue'; parameters = $mqParams })
    } | ConvertTo-Json -Depth 8

    # Find an existing ruleset with our name (idempotent create-or-update).
    $existingId = $null
    $rulesets = gh api "repos/$Repo/rulesets" 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        $existingId = ($rulesets | ConvertFrom-Json | Where-Object { $_.name -eq $rulesetName } | Select-Object -First 1).id
    }

    if ($existingId) {
        Write-Plan "PUT /repos/$Repo/rulesets/$existingId  (update '$rulesetName')"
    } else {
        Write-Plan "POST /repos/$Repo/rulesets  (create '$rulesetName')"
    }
    Write-Host "       payload:"
    $rulesetPayload.Split("`n") | ForEach-Object { Write-Host "         $_" }
    Write-Host "       NOTE: review the merge_queue parameters above against your repo's GitHub plan before the first apply."

    if ($Apply) {
        $tmp = New-TemporaryFile
        # ASCII (no BOM): PowerShell 5.1's -Encoding utf8 writes a BOM, which gh
        # rejects with HTTP 400 "Problems parsing JSON". The payload is ASCII.
        Set-Content -LiteralPath $tmp -Value $rulesetPayload -Encoding ascii -NoNewline
        if ($existingId) {
            gh api --method PUT "repos/$Repo/rulesets/$existingId" --input $tmp 2>&1 | Out-Null
        } else {
            gh api --method POST "repos/$Repo/rulesets" --input $tmp 2>&1 | Out-Null
        }
        $rc = $LASTEXITCODE
        Remove-Item $tmp -ErrorAction SilentlyContinue
        if ($rc -ne 0) { Write-Host "[fail] merge-queue ruleset write failed (review merge_queue params)." -ForegroundColor Red; exit 1 }
        Write-Did "merge queue ruleset '$rulesetName' applied."
    }
} else {
    Write-Plan "merge queue: not enabled in config; leaving rulesets untouched."
}

Write-Host ""
if ($Apply) {
    Write-Host "Applied. Re-run without -Apply any time to diff the declared state." -ForegroundColor Green
} else {
    Write-Host "Dry-run only. Re-run with -Apply to make these changes." -ForegroundColor Yellow
}
exit 0
