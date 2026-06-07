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
      isDraft + [WIP]  -> cloud marked the PR ready
      state            -> PR merged or closed
      set membership   -> a NEW open PR appeared (a dispatched issue's PR), or
                          a watched PR left the open set (merged/closed)

    mergeStateStatus is intentionally NOT tracked: it churns UNKNOWN->BEHIND
    whenever `main` moves (an unrelated merge), which is not work on this PR and
    would false-fire the watcher. The pr-driver pass you run on wake recomputes
    BEHIND/CLEAN itself.

    On any delta the script prints a summary and exits 0. On the safety
    timeout it exits 0 with a "no change" note so the agent can relaunch.
    Exit code is always 0 (informational); the wake-up is the completion event,
    not the code.

.PARAMETER Pr
    One or more PR numbers to watch. If omitted, watches ALL currently-open PRs
    and also fires when a brand-new open PR appears.

.PARAMETER Mine
    Watch only the PRs that belong to this conductor's work: PRs authored by the
    current gh user OR by the Copilot coding agent. The set is RE-DERIVED every
    poll cycle, so a newly-opened cloud PR auto-joins the watch and a merged one
    drops out -- no need to pass explicit numbers or relaunch with a new list.
    Ignored if -Pr is given (an explicit list wins).

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

.EXAMPLE
    .\tools\pr-watch.ps1 -Mine
    Watch my own + Copilot-authored open PRs, re-derived each cycle, so new
    cloud PRs auto-join and merged ones drop without relaunching with a new list.
#>

param(
    [Parameter(Position = 0)]
    [int[]]$Pr = @(),

    [switch]$Mine,

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
    param([int[]]$Restrict, [string[]]$OnlyAuthors)

    $fields = 'number,title,state,isDraft,headRefOid,reviewDecision,author'
    $raw = gh pr list --state open --json $fields 2>&1
    # A native command failure (e.g. a transient network error) is NOT a
    # terminating PowerShell error, so it would otherwise yield $null -> an
    # empty map -> the delta logic would read "every watched PR vanished" and
    # false-fire. Check the exit code and throw so the poll loop's catch treats
    # it as a transient failure and retries next cycle. (Learned 2026-06-03:
    # a wsarecv timeout made the watcher report both PRs as merged/closed.)
    # Capture 2>&1 so the actual gh error text (usually on stderr) rides along
    # in the thrown message instead of just a bare exit code.
    if ($LASTEXITCODE -ne 0) {
        throw "gh pr list failed (exit $LASTEXITCODE): $(($raw | Out-String).Trim())"
    }
    $list = ($raw | Out-String) | ConvertFrom-Json
    if ($null -eq $list) { $list = @() }

    $map = [ordered]@{}
    foreach ($p in $list) {
        if ($Restrict.Count -gt 0 -and ($Restrict -notcontains $p.number)) { continue }
        # -Mine restricts to PRs authored by the current user or the Copilot
        # coding agent. The set is recomputed each cycle (this function runs per
        # poll), so newly-opened cloud PRs join and merged ones drop on their own.
        if ($OnlyAuthors.Count -gt 0) {
            $login = if ($null -ne $p.author) { [string]$p.author.login } else { '' }
            # The Copilot coding agent's author.login varies by API surface
            # ('Copilot' from some endpoints, 'app/copilot-swe-agent' from
            # `gh pr list --json author`, 'copilot-swe-agent', etc.). The sentinel
            # 'Copilot' in the filter therefore matches ANY copilot-ish login
            # case-insensitively; other entries (real usernames) match exactly.
            # (Bug 2026-06-08: an exact 'Copilot' compare silently excluded every
            # cloud PR, so -Mine only ever tracked my own PRs.)
            $match = $false
            foreach ($a in $OnlyAuthors) {
                if ($a -eq 'Copilot') {
                    if ($login -match '(?i)copilot') { $match = $true; break }
                } elseif ($login -eq $a) {
                    $match = $true; break
                }
            }
            if (-not $match) { continue }
        }
        $wip = if ($p.title -match '\[WIP\]') { 'wip' } else { 'ready' }
        $draft = if ($p.isDraft) { 'draft' } else { 'open' }
        # mergeStateStatus is deliberately EXCLUDED from the signature: it churns
        # UNKNOWN->BEHIND every time `main` moves (an unrelated merge), which is
        # not cloud work on THIS PR and would false-fire the watcher. The real
        # "cloud did something" signals are commit push (headRefOid), review
        # (reviewDecision), draft->ready, merge (state), and new-PR membership.
        # When the watcher wakes on one of those, the pr-driver pass recomputes
        # BEHIND/CLEAN itself and acts. (Learned from the first live run.)
        # Order matters only for readability; the whole string is the signature.
        $sig = @(
            $p.state
            $draft
            $wip
            $p.headRefOid
            $p.reviewDecision
        ) -join '|'
        $map[[string]$p.number] = $sig
    }
    return $map
}

# ---------------------------------------------------------------------------
# Acquire a signature map, retrying transient gh failures until a deadline.
# Used for the baseline so a startup network blip does not kill the script
# (which would falsely wake the caller before any real change occurred).
# ---------------------------------------------------------------------------
function Get-PrSignatureMapWithRetry {
    param([int[]]$Restrict, [string[]]$OnlyAuthors, [datetime]$Deadline, [int]$RetrySeconds = 10)

    while ($true) {
        try {
            return Get-PrSignatureMap -Restrict $Restrict -OnlyAuthors $OnlyAuthors
        }
        catch {
            if ((Get-Date) -ge $Deadline) { throw }
            Write-Host ("[warn] baseline poll failed ({0}); retrying in {1}s." -f $_.Exception.Message, $RetrySeconds)
            Start-Sleep -Seconds $RetrySeconds
        }
    }
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
# Resolve the -Mine author filter (current gh user + the Copilot coding agent).
# Skipped when -Pr is given (an explicit list wins) or -Mine is not set.
# ---------------------------------------------------------------------------
$authorFilter = @()
if ($Mine -and $Pr.Count -eq 0) {
    $me = (gh api user --jq '.login' 2>&1)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($me | Out-String))) {
        Write-Host "[warn] -Mine: could not resolve current gh user; watching Copilot-authored PRs only."
        $authorFilter = @('Copilot')
    } else {
        $authorFilter = @(($me | Out-String).Trim(), 'Copilot')
    }
}

# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------
$deadline = (Get-Date).AddMinutes($MaxMinutes)
$baseline = Get-PrSignatureMapWithRetry -Restrict $Pr -OnlyAuthors $authorFilter -Deadline $deadline
$scope = if ($Pr.Count -gt 0) { "PRs $($Pr -join ', ')" } elseif ($authorFilter.Count -gt 0) { "my + Copilot open PRs ($($authorFilter -join ', '))" } else { "all open PRs" }

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
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds $IntervalSeconds

    try {
        $current = Get-PrSignatureMap -Restrict $Pr -OnlyAuthors $authorFilter
    }
    catch {
        Write-Host ("[warn] poll failed ({0}); retrying next cycle." -f $_.Exception.Message)
        continue
    }

    # A poll that returns zero PRs against a non-empty baseline is ambiguous: it
    # can be a transient API blip (exit 0, empty/partial body) OR a genuine
    # mass-merge where every watched PR really left the open set at once - which
    # is the COMMON single-PR-merge case we must not suppress. Disambiguate with
    # ONE immediate confirm re-poll instead of skipping forever: if the confirm
    # also returns zero, the emptiness is real and we let the delta logic fire
    # (so the merge wakes us); if the confirm returns PRs, the first read was a
    # blip and we use the confirm result.
    if ($current.Count -eq 0 -and $baseline.Count -gt 0) {
        Start-Sleep -Seconds 3
        try {
            $confirm = Get-PrSignatureMap -Restrict $Pr -OnlyAuthors $authorFilter
        }
        catch {
            Write-Host ("[warn] confirm re-poll failed ({0}); retrying next cycle." -f $_.Exception.Message)
            continue
        }
        if ($confirm.Count -gt 0) {
            Write-Host "[warn] empty poll was a transient blip; confirm re-poll recovered, continuing."
            $current = $confirm
        }
        else {
            Write-Host "[info] confirm re-poll also empty; treating as genuine - all watched PRs left the open set."
            # fall through with $current empty so the delta fires and we wake.
        }
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
