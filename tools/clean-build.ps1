#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Safely remove known build / cache artifacts from the repo.

.DESCRIPTION
    Deletes only a fixed allowlist of generated build and cache directories
    (and a few generated files) that live under the repository root. This is
    the reviewed, auto-approvable alternative to ad-hoc `rm` / `Remove-Item`:
    raw deletes still prompt for approval, but this tool encodes a safe target
    set so routine cleanup does not.

    Hard guarantees:
      - Refuses to run outside a git working tree.
      - Only ever deletes paths that resolve to INSIDE the repo root (a
        separator-aware containment check, so a sibling like `repo-backup` is
        never mistaken for being inside `repo`).
      - Targets a fixed allowlist of generated-artifact directory NAMES
        (node_modules, dist, .next, __pycache__, .pytest_cache, etc). Matching
        is by name only - it does not inspect git tracked-status - so if you
        deliberately track a directory with one of these names it would match.
        Run `-DryRun` first to review the target list.

.PARAMETER DryRun
    List what would be removed without deleting anything.

.EXAMPLE
    .\tools\clean-build.ps1
    Removes all known build/cache artifacts.

.EXAMPLE
    .\tools\clean-build.ps1 -DryRun
    Shows what would be removed.
#>

param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# Must be inside a git repo; resolve the root so we can sandbox deletions to it.
$repoRoot = (git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoRoot)) {
    Write-Error "Not inside a git working tree; refusing to delete anything."
    exit 1
}
$repoRoot = (Resolve-Path $repoRoot).Path

# Allowlist of generated artifact directory names. Matched anywhere in the tree.
$dirPatterns = @(
    'node_modules',
    'dist',
    'build',
    'out',
    '.next',
    '.turbo',
    'coverage',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.gradle'
)

# Allowlist of generated top-level scratch dirs (relative to repo root).
$relPaths = @(
    '.specify/tmp'
)

function Test-InsideRepo {
    param([string]$Path)
    $full = (Resolve-Path -LiteralPath $Path -ErrorAction SilentlyContinue)
    if (-not $full) { return $false }
    # Separator-aware containment: a bare StartsWith($repoRoot) prefix check
    # would treat siblings like `C:\repo-backup` as inside `C:\repo` (prefix
    # collision). Require the path to equal the root, or begin with the root
    # followed by a directory separator.
    $cmp = [System.StringComparison]::OrdinalIgnoreCase
    if ($full.Path.Equals($repoRoot, $cmp)) { return $true }
    $rootWithSep = $repoRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    return $full.Path.StartsWith($rootWithSep, $cmp)
}

$targets = New-Object System.Collections.Generic.List[string]

# Walk the tree ONCE and match directory names against a case-insensitive set,
# rather than running a full recursive Get-ChildItem per allowlisted name
# (which multiplied traversal cost by the number of patterns).
$nameSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($name in $dirPatterns) { [void]$nameSet.Add($name) }

Get-ChildItem -Path $repoRoot -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $nameSet.Contains($_.Name) } |
    ForEach-Object { $targets.Add($_.FullName) }

foreach ($rel in $relPaths) {
    $candidate = Join-Path $repoRoot $rel
    if (Test-Path -LiteralPath $candidate) { $targets.Add((Resolve-Path -LiteralPath $candidate).Path) }
}

$unique = $targets | Sort-Object -Unique
if (-not $unique -or $unique.Count -eq 0) {
    Write-Host "Nothing to clean."
    exit 0
}

$removed = 0
foreach ($t in $unique) {
    if (-not (Test-InsideRepo $t)) {
        Write-Warning "Skipping (outside repo): $t"
        continue
    }
    $rel = $t.Substring($repoRoot.Length).TrimStart('\', '/')
    if ($DryRun) {
        Write-Host "would remove: $rel"
        continue
    }
    Remove-Item -LiteralPath $t -Recurse -Force -ErrorAction Stop
    Write-Host "removed: $rel"
    $removed++
}

if ($DryRun) {
    Write-Host "(dry run) $($unique.Count) target(s) matched."
} else {
    Write-Host "Cleaned $removed target(s)."
}
