# scripts/mirror-agents.ps1
# Mirrors .github/agents/ into .claude/agents/ so Claude Code sees the same files.
# Uses directory junctions on Windows (no admin required for same-volume junctions).
# Run from the repo root.

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot '.github\agents'
$target = Join-Path $repoRoot '.claude\agents'
$claudeDir = Join-Path $repoRoot '.claude'

if (-not (Test-Path $source)) {
    Write-Error ".github/agents not found at $source"
    exit 1
}

if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Path $claudeDir | Out-Null
}

if (Test-Path $target) {
    $item = Get-Item $target -Force
    if ($item.LinkType -eq 'Junction' -or $item.LinkType -eq 'SymbolicLink') {
        Write-Host "Already linked: $target -> $($item.Target)"
        exit 0
    } else {
        Write-Error "Target exists and is not a link: $target. Move or delete it first."
        exit 1
    }
}

New-Item -ItemType Junction -Path $target -Value $source | Out-Null
Write-Host "Created junction: $target -> $source"
