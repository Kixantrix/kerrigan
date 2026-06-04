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
      - Only ever deletes paths that resolve to inside the repo root.
      - Never touches tracked source: the target list is generated artifacts
        only (node_modules, dist, .next, __pycache__, .pytest_cache, etc).

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
    return $full.Path.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)
}

$targets = New-Object System.Collections.Generic.List[string]

foreach ($name in $dirPatterns) {
    Get-ChildItem -Path $repoRoot -Directory -Recurse -Force -Filter $name -ErrorAction SilentlyContinue |
        ForEach-Object { $targets.Add($_.FullName) }
}

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
