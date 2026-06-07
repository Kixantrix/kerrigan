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

      1. One branch ruleset containing:
         - required_status_checks
         - merge_queue (when enabled)
      2. Classic required_status_checks cleared (to avoid ruleset conflicts)

    Flexible: any repo can ship a different config (different required checks,
    queue off, strict on) and this tool applies whatever is declared. Optimized
    default lives in preset/kerrigan/repo-protection.json. Absent config => the
    tool refuses (nothing declared to apply).

    SAFETY: the default mode is a DRY-RUN that prints every planned API call and
    the exact JSON payloads. It mutates shared branch protection ONLY when you
    pass -Apply. Re-running is idempotent (converges to the declared state).

    The checks + queue rules are created/updated together in a single repository
    ruleset. The dry-run prints the full payloads (ruleset + classic-clear plan)
    so you can review them before the first -Apply.

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
$protectionMode = if ($config.protection_mode) { [string]$config.protection_mode } else { 'ruleset' }
$mq = $config.merge_queue
$mqEnabled = ($null -ne $mq -and [bool]$mq.enabled)
$mode = if ($Apply) { "APPLY" } else { "DRY-RUN" }

# Guard: a missing / non-string-array required_checks would PATCH an EMPTY
# contexts list, silently CLEARING the branch's required checks. Refuse instead.
if ($requiredChecks.Count -eq 0 -or ($requiredChecks | Where-Object { $_ -isnot [string] -or [string]::IsNullOrWhiteSpace($_) })) {
    Write-Host "[fail] ${ConfigPath}: 'required_checks' must be a non-empty array of check-name strings (refusing to clear required checks)." -ForegroundColor Red
    exit 1
}

if ($protectionMode -ne 'ruleset') {
    Write-Host "[fail] ${ConfigPath}: unsupported protection_mode '$protectionMode' (only 'ruleset' is supported)." -ForegroundColor Red
    exit 1
}

# Write text as UTF-8 WITHOUT a BOM. PowerShell 5.1's `Set-Content -Encoding utf8`
# adds a BOM (gh -> HTTP 400 "Problems parsing JSON"); writing as plain ASCII
# avoids the BOM but corrupts non-ASCII check/branch names. UTF-8-no-BOM is
# correct for both concerns.
function Write-Utf8NoBom([string]$Path, [string]$Content) {
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

Write-Host "=== configure-repo-protection ($mode) ===" -ForegroundColor Cyan
Write-Host ("repo={0} branch={1}" -f $Repo, $branch)
Write-Host ""

# ---------------------------------------------------------------------------
# 1) Build one branch ruleset: required_status_checks (+ merge_queue)
# ---------------------------------------------------------------------------
$rulesetName = "Kerrigan main protection"
$strictRequiredChecksPolicy = if ($mqEnabled) { $false } else { $strict }
$requiredStatusChecksRule = [ordered]@{
    type       = 'required_status_checks'
    parameters = [ordered]@{
        required_status_checks             = @($requiredChecks | ForEach-Object { [ordered]@{ context = [string]$_ } })
        strict_required_status_checks_policy = $strictRequiredChecksPolicy
    }
}

if ($mqEnabled) {
    $mergeMethod = if ($mq.merge_method) { ([string]$mq.merge_method).ToUpperInvariant() } else { 'SQUASH' }
    if (@('MERGE', 'REBASE', 'SQUASH') -notcontains $mergeMethod) {
        Write-Host "[fail] ${ConfigPath}: merge_queue.merge_method must be one of MERGE/REBASE/SQUASH." -ForegroundColor Red
        exit 1
    }
    $mqParams = [ordered]@{
        merge_method                      = $mergeMethod
        min_entries_to_merge              = if ($null -ne $mq.min_entries_to_merge) { [int]$mq.min_entries_to_merge } else { 1 }
        max_entries_to_merge              = if ($null -ne $mq.max_entries_to_merge) { [int]$mq.max_entries_to_merge } else { 5 }
        min_entries_to_merge_wait_minutes = if ($null -ne $mq.min_entries_to_merge_wait_minutes) { [int]$mq.min_entries_to_merge_wait_minutes } else { 5 }
        max_entries_to_build              = if ($null -ne $mq.max_entries_to_build) { [int]$mq.max_entries_to_build } else { 5 }
        check_response_timeout_minutes    = if ($null -ne $mq.check_response_timeout_minutes) { [int]$mq.check_response_timeout_minutes } else { 60 }
        grouping_strategy                 = if ($mq.grouping_strategy) { [string]$mq.grouping_strategy } else { 'ALLGREEN' }
    }
    $queueRule = [ordered]@{ type = 'merge_queue'; parameters = $mqParams }
    $rules = @($requiredStatusChecksRule, $queueRule)
} else {
    $rules = @($requiredStatusChecksRule)
}

$rulesetPayload = [ordered]@{
    name        = $rulesetName
    target      = 'branch'
    enforcement = 'active'
    conditions  = [ordered]@{ ref_name = [ordered]@{ include = @("refs/heads/$branch"); exclude = @() } }
    rules       = $rules
} | ConvertTo-Json -Depth 10

$clearClassicPayload = [ordered]@{
    strict   = $false
    contexts = @()
} | ConvertTo-Json -Compress
$restoreClassicPayload = [ordered]@{
    strict   = $strict
    contexts = $requiredChecks
} | ConvertTo-Json -Compress

Write-Plan "POST/PUT /repos/$Repo/rulesets  (idempotent by name '$rulesetName')"
Write-Host "       payload:"
$rulesetPayload.Split("`n") | ForEach-Object { Write-Host "         $_" }
Write-Host "       NOTE: required_status_checks and merge_queue are sent together in one ruleset."
if ($mqEnabled -and $strict) {
    Write-Host "       NOTE: strict_status_checks=true is ignored for queue mode; strict_required_status_checks_policy is set to false."
}
Write-Host ""
Write-Plan "PATCH /repos/$Repo/branches/$branch/protection/required_status_checks  (clear classic duplicate checks)"
Write-Host "       payload: $clearClassicPayload"
Write-Host ""

if ($Apply) {
    # Find an existing ruleset with our name (idempotent create-or-update).
    $existingId = $null
    $rulesets = gh api "repos/$Repo/rulesets" 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[fail] could not list existing rulesets for $Repo." -ForegroundColor Red
        exit 1
    }
    $existingId = ($rulesets | ConvertFrom-Json | Where-Object { $_.name -eq $rulesetName } | Select-Object -First 1).id

    $tmp = New-TemporaryFile
    Write-Utf8NoBom $tmp $clearClassicPayload
    gh api --method PATCH "repos/$Repo/branches/$branch/protection/required_status_checks" --input $tmp 2>&1 | Out-Null
    $clearRc = $LASTEXITCODE
    Remove-Item $tmp -ErrorAction SilentlyContinue
    if ($clearRc -ne 0) { Write-Host "[fail] classic required_status_checks clear failed (is branch protection enabled?)." -ForegroundColor Red; exit 1 }
    Write-Did "classic required status checks cleared (ruleset is now the single source of gating)."

    $tmp = New-TemporaryFile
    Write-Utf8NoBom $tmp $rulesetPayload
    if ($existingId) {
        gh api --method PUT "repos/$Repo/rulesets/$existingId" --input $tmp 2>&1 | Out-Null
    } else {
        gh api --method POST "repos/$Repo/rulesets" --input $tmp 2>&1 | Out-Null
    }
    $rulesetRc = $LASTEXITCODE
    Remove-Item $tmp -ErrorAction SilentlyContinue

    if ($rulesetRc -ne 0) {
        Write-Host "[fail] checks+queue ruleset write failed; attempting classic required_status_checks rollback." -ForegroundColor Red
        $tmp = New-TemporaryFile
        Write-Utf8NoBom $tmp $restoreClassicPayload
        gh api --method PATCH "repos/$Repo/branches/$branch/protection/required_status_checks" --input $tmp 2>&1 | Out-Null
        $rollbackRc = $LASTEXITCODE
        Remove-Item $tmp -ErrorAction SilentlyContinue
        if ($rollbackRc -eq 0) {
            Write-Host "[done] rollback restored classic required_status_checks payload." -ForegroundColor Yellow
        } else {
            Write-Host "[warn] rollback failed; re-run with corrected payload or restore manually." -ForegroundColor Yellow
        }
        exit 1
    }
    Write-Did "ruleset '$rulesetName' applied."
}

Write-Host ""
if ($Apply) {
    Write-Host "Applied. Re-run without -Apply any time to diff the declared state." -ForegroundColor Green
} else {
    Write-Host "Dry-run only. Re-run with -Apply to make these changes." -ForegroundColor Yellow
}
exit 0
