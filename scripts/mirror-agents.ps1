# scripts/mirror-agents.ps1
# Mirrors .github/agents/ into .claude/agents/ so Claude Code sees the same files.
# Windows: directory junction (no admin required for same-volume junctions).
# POSIX (macOS/Linux): symbolic link.
# Run from the repo root.

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot '.github' 'agents'
$target = Join-Path $repoRoot '.claude' 'agents'
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
        # Real directory (e.g. from a fresh git clone) — remove and replace with link
        Write-Host "Replacing existing directory with link: $target"
        Remove-Item -Recurse -Force $target
    }
}

if ($IsWindows -or $env:OS -eq 'Windows_NT') {
    New-Item -ItemType Junction -Path $target -Value $source | Out-Null
    Write-Host "Created junction: $target -> $source"
} else {
    New-Item -ItemType SymbolicLink -Path $target -Value $source | Out-Null
    Write-Host "Created symlink: $target -> $source"
}
