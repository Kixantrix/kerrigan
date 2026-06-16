<#
.SYNOPSIS
  Fast-forward the local checkout to origin/<branch> (default: main), robustly.

.DESCRIPTION
  Wraps the `git fetch` + `git merge --ff-only` dance that the conductor ran by
  hand 10+ times during the dashboard session. Centralizes two recurring papercuts:
    - git writes progress to stderr, which PowerShell surfaces as a NativeCommandError
      and aborts chained `;` commands. We funnel stderr to the host explicitly.
    - `git pull --ff-only` can fail with "Cannot fast-forward to multiple branches"
      when refspecs are ambiguous; an explicit fetch + ff-merge avoids it.

  Prints the short HEAD before/after and the list of changed files, and leaves any
  local uncommitted changes untouched (it refuses to merge if the tree is dirty in a
  way that would block a fast-forward).

.PARAMETER Branch
  The branch to sync to. Defaults to 'main'.

.PARAMETER Remote
  The remote to fetch from. Defaults to 'origin'.

.EXAMPLE
  .\tools\sync-main.ps1
  Fetches origin and fast-forwards local main.

.EXAMPLE
  .\tools\sync-main.ps1 -Branch develop
#>
[CmdletBinding()]
param(
  [string]$Branch = 'main',
  [string]$Remote = 'origin'
)

$ErrorActionPreference = 'Continue'

function Invoke-Git {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GitArgs)
  # Run git and surface stderr as normal text so a progress line doesn't abort the script.
  & git @GitArgs 2>&1 | ForEach-Object { Write-Host $_ }
  return $LASTEXITCODE
}

$before = (& git rev-parse --short HEAD 2>$null)
Write-Host "Current HEAD: $before" -ForegroundColor Cyan

Write-Host "Fetching $Remote ..." -ForegroundColor Cyan
$code = Invoke-Git fetch $Remote
if ($code -ne 0) {
  Write-Host "[FAIL] git fetch $Remote exited $code" -ForegroundColor Red
  exit $code
}

# Make sure we're ON the target branch before fast-forwarding; otherwise a
# `merge --ff-only origin/<Branch>` tries to advance whatever branch is checked
# out (which fails if it has diverged, e.g. a squash-merged feature branch).
$current = (& git rev-parse --abbrev-ref HEAD 2>$null)
if ($current -ne $Branch) {
  Write-Host "Switching $current -> $Branch ..." -ForegroundColor Cyan
  $code = Invoke-Git checkout $Branch
  if ($code -ne 0) {
    Write-Host "[FAIL] git checkout $Branch exited $code (uncommitted changes blocking the switch?)." -ForegroundColor Red
    exit $code
  }
}

Write-Host "Fast-forwarding to $Remote/$Branch ..." -ForegroundColor Cyan
$code = Invoke-Git merge --ff-only "$Remote/$Branch"
if ($code -ne 0) {
  Write-Host "[FAIL] Could not fast-forward to $Remote/$Branch (diverged or dirty tree?). Resolve manually." -ForegroundColor Red
  exit $code
}

$after = (& git rev-parse --short HEAD 2>$null)
if ($before -eq $after) {
  Write-Host "[OK] Already up to date at $after" -ForegroundColor Green
}
else {
  Write-Host "[OK] $before -> $after" -ForegroundColor Green
  Write-Host "Changed files:" -ForegroundColor Cyan
  & git --no-pager diff --name-only "$before..$after" 2>&1 | ForEach-Object { Write-Host "  $_" }
}

# Surface any leftover working-tree changes so the conductor notices stray files.
$dirty = (& git status --porcelain 2>$null)
if ($dirty) {
  Write-Host "Working tree (uncommitted / untracked):" -ForegroundColor Yellow
  $dirty | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
}
