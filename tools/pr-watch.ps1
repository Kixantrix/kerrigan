#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Block until cloud work produces an actionable change on the watched PRs,
    then exit so the calling agent is woken to run a pr-driver pass.

.DESCRIPTION
    The kerrigan conductor is not notified when a cloud agent pushes a commit,
    Copilot posts a re-review, CI completes, or a new cloud PR opens. The only
    event that wakes a local agent is a TERMINAL COMMAND COMPLETING.

    pr-watch bridges that gap: it polls a lightweight signature of the open PRs
    on an interval (internally, with Start-Sleep - that is fine for a tool; the
    agent itself never sleep-polls), and EXITS the moment any signature changes
    in a way worth acting on. Launch it async; its exit is your trigger.

    The signature comes from a single `gh pr list --json` call per cycle, so a
    watch cycle is one API round-trip regardless of how many PRs are open. The
    tracked fields each map to a real "go look" event:

      headRefOid       -> cloud pushed a new commit (e.g. a re-dispatched fix)
      reviewDecision   -> a new review landed (APPROVED / CHANGES_REQUESTED)
      mergeStateStatus -> CI/threads moved (BEHIND / BLOCKED / UNSTABLE / CLEAN)
      isDraft + [WIP]  -> cloud marked the PR ready
      state            -> PR merged or closed
      set membership   -> a NEW open PR appeared (a dispatched issue's PR), or
                          a watched PR left the open set (merged/closed)

    On any delta the script prints a summary and exits 0. On the safety
    timeout it exits 0 with a "no change" note so the agent can relaunch.
    Exit code is always 0 (informational); the wake-up is the completion event,
    not the code.

.PARAMETER Pr
    One or more PR numbers to watch. If omitted, watches ALL currently-open PRs
    and also fires when a brand-new open PR appears.

.PARAMETER IntervalSeconds
    Seconds between poll cycles. Default 90.

.PARAMETER MaxMinutes
    Safety cap. After this many minutes with no actionable change, exit 0 with a
    "no change" note (relaunch to keep watching). Default 45.

.PARAMETER Once
    Take a single signature snapshot, print it, and exit without looping. Used
    for testing and to capture a baseline.

.EXAMPLE
    .\tools\pr-watch.ps1
    Watch every open PR; exit when any of them changes or a new PR opens.

.EXAMPLE
    .\tools\pr-watch.ps1 -Pr 310,320
    Watch only #310 and #320; exit on the first actionable change to either.
#>

param(
    [Parameter(Position = 0)]
    [int[]]$Pr = @(),

    [int]$IntervalSeconds = 90,

    [int]$MaxMinutes = 45,

    [switch]$Once
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Capture a signature map { prNumber -> signatureString } for the open PRs.
# One `gh pr list` call. When -Pr is given, restrict to that set.
# ---------------------------------------------------------------------------
function Get-PrSignatureMap {
    param([int[]]$Restrict)

    $fields = 'number,title,state,isDraft,headRefOid,mergeStateStatus,reviewDecision'
    $list = gh pr list --state open --json $fields | ConvertFrom-Json
    if ($null -eq $list) { $list = @() }

    $map = [ordered]@{}
    foreach ($p in $list) {
        if ($Restrict.Count -gt 0 -and ($Restrict -notcontains $p.number)) { continue }
        $wip = if ($p.title -match '\[WIP\]') { 'wip' } else { 'ready' }
        $draft = if ($p.isDraft) { 'draft' } else { 'open' }
        # Order matters only for readability; the whole string is the signature.
        $sig = @(
            $p.state
            $draft
            $wip
            $p.headRefOid
            $p.mergeStateStatus
            $p.reviewDecision
        ) -join '|'
        $map[[string]$p.number] = $sig
    }
    return $map
}

# ---------------------------------------------------------------------------
# Diff two signature maps. Returns a list of human-readable change strings.
# Covers: new PR, removed PR (merged/closed), and changed signature.
# ---------------------------------------------------------------------------
function Get-SignatureDelta {
    param($Baseline, $Current)

    $changes = @()

    foreach ($num in $Current.Keys) {
        if (-not $Baseline.Contains($num)) {
            $changes += "PR #${num}: NEW open PR ($($Current[$num]))"
        }
        elseif ($Baseline[$num] -ne $Current[$num]) {
            $changes += "PR #${num}: changed`n    was: $($Baseline[$num])`n    now: $($Current[$num])"
        }
    }
    foreach ($num in $Baseline.Keys) {
        if (-not $Current.Contains($num)) {
            $changes += "PR #${num}: left the open set (merged or closed)"
        }
    }
    return $changes
}

# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------
$baseline = Get-PrSignatureMap -Restrict $Pr
$scope = if ($Pr.Count -gt 0) { "PRs $($Pr -join ', ')" } else { "all open PRs" }

Write-Host "=== pr-watch: $scope ===" -ForegroundColor Cyan
Write-Host ("Baseline ({0} PR(s)) at {1}:" -f $baseline.Count, (Get-Date -Format 'HH:mm:ss'))
foreach ($num in $baseline.Keys) {
    Write-Host ("  #{0}  {1}" -f $num, $baseline[$num])
}

if ($Once) {
    Write-Host "[once] snapshot only; not looping."
    exit 0
}

Write-Host ("Polling every {0}s, max {1} min. Will exit on first actionable change." -f $IntervalSeconds, $MaxMinutes)

# ---------------------------------------------------------------------------
# Poll loop
# ---------------------------------------------------------------------------
$deadline = (Get-Date).AddMinutes($MaxMinutes)

while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds $IntervalSeconds

    try {
        $current = Get-PrSignatureMap -Restrict $Pr
    }
    catch {
        Write-Host ("[warn] poll failed ({0}); retrying next cycle." -f $_.Exception.Message)
        continue
    }

    $delta = Get-SignatureDelta -Baseline $baseline -Current $current
    if ($delta.Count -gt 0) {
        Write-Host ""
        Write-Host ("=== ACTIONABLE CHANGE at {0} ===" -f (Get-Date -Format 'HH:mm:ss')) -ForegroundColor Green
        foreach ($c in $delta) { Write-Host "  $c" }
        Write-Host ""
        Write-Host "Run a pr-driver pass on the affected PR(s)."
        exit 0
    }
}

Write-Host ""
Write-Host ("=== no actionable change after {0} min - relaunch to keep watching ===" -f $MaxMinutes) -ForegroundColor Yellow
exit 0
