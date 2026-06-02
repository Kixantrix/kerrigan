#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Kerrigan repo health smoke test (PowerShell / Windows mirror of smoke.sh).

.DESCRIPTION
    Runs read-only checks to verify the repo is in a healthy state:
      1. Python is importable
      2. Key validator scripts exist
      3. Kerrigan CLI package is loadable
      4. Key repository directories exist

    Exits 0 on success, exits 1 on failure.
    Idempotent and side-effect-free by default (read-only checks only).
    Optional dashboard build checks can be enabled with:
      KERRIGAN_SMOKE_DASHBOARD=1

.EXAMPLE
    pwsh scripts/smoke.ps1

.NOTES
    Requires PowerShell 5.1 or later and Python 3.
#>

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$pass = 0
$fail = 0

function Write-Pass([string]$msg) {
    Write-Output "  ✓ $msg"
    $script:pass++
}

function Write-Fail([string]$msg) {
    Write-Output "  ✗ $msg"
    $script:fail++
}

Write-Output "=== Kerrigan smoke test ==="
Write-Output "Repo root: $repoRoot"
Write-Output ""

# --- Check 1: Python importable ---
Write-Output "[ Python ]"
try {
    $result = python3 -c "import sys, pathlib, json, re" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "python3 importable (sys, pathlib, json, re)"
    } else {
        Write-Fail "python3 not importable or missing stdlib modules"
    }
} catch {
    Write-Fail "python3 not found on PATH"
}
Write-Output ""

# --- Check 2: Validators exist ---
Write-Output "[ Validators ]"
$validatorsDir = Join-Path $repoRoot 'tools' 'validators'
foreach ($v in @('agents_md.py', 'check_artifacts.py', 'check_dependencies.py', 'check_placeholders.py')) {
    $vPath = Join-Path $validatorsDir $v
    if (Test-Path -Path $vPath -PathType Leaf) {
        Write-Pass "validators/$v exists"
    } else {
        Write-Fail "validators/$v missing"
    }
}
Write-Output ""

# --- Check 3: Kerrigan CLI loadable ---
Write-Output "[ Kerrigan CLI ]"
$cliPkg = Join-Path $repoRoot 'tools' 'cli' 'kerrigan'
$cliCheck = @"
import sys
sys.path.insert(0, r'$cliPkg')
from kerrigan_cli import cli as _cli
"@
try {
    python3 -c $cliCheck 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "kerrigan_cli package loadable"
    } else {
        Write-Fail "kerrigan_cli package not loadable (check tools/cli/kerrigan)"
    }
} catch {
    Write-Fail "kerrigan_cli package not loadable (python3 error)"
}
Write-Output ""

# --- Check 4: Key directories exist ---
Write-Output "[ Key directories ]"
$keyDirs = @(
    'tools',
    'tools/validators',
    'tools/cli',
    'scripts',
    '.github/agents',
    'specs',
    'playbooks'
)
foreach ($dir in $keyDirs) {
    $dirPath = Join-Path $repoRoot $dir
    if (Test-Path -Path $dirPath -PathType Container) {
        Write-Pass "$dir/"
    } else {
        Write-Fail "$dir/ missing"
    }
}
Write-Output ""

# --- Check 5: Optional dashboard build + artifact ---
Write-Output "[ Dashboard build ]"
$dashboardDir = Join-Path $repoRoot 'apps' 'kerrigan-dashboard'
$runDashboardSmoke = $env:KERRIGAN_SMOKE_DASHBOARD
$skipDashboardBuild = $env:KERRIGAN_SMOKE_DASHBOARD_SKIP_BUILD

if ($runDashboardSmoke -ne '1') {
    Write-Pass "dashboard smoke skipped (set KERRIGAN_SMOKE_DASHBOARD=1 to enable)"
} elseif (-not (Test-Path -Path $dashboardDir -PathType Container)) {
    Write-Pass "dashboard smoke skipped (apps/kerrigan-dashboard not present)"
} else {
    $pnpmCmd = Get-Command pnpm -ErrorAction SilentlyContinue
    if (-not $pnpmCmd) {
        Write-Fail "pnpm is required for dashboard smoke checks"
    } else {
        if ($skipDashboardBuild -ne '1') {
            try {
                & $pnpmCmd.Source -C $dashboardDir tauri build
                if ($LASTEXITCODE -eq 0) {
                    Write-Pass "dashboard tauri build completed"
                } else {
                    Write-Fail "dashboard tauri build failed"
                }
            } catch {
                Write-Fail "dashboard tauri build failed"
            }
        } else {
            Write-Pass "dashboard tauri build skipped (KERRIGAN_SMOKE_DASHBOARD_SKIP_BUILD=1)"
        }

        $bundleDir = Join-Path $dashboardDir 'src-tauri' 'target' 'release' 'bundle'
        $patterns = switch ($IsWindows) {
            $true { @('*.msi', '*.exe') }
            $false {
                if ($IsMacOS) { @('*.dmg', '*.app') } else { @('*.AppImage', '*.deb', '*.rpm') }
            }
        }

        $artifacts = @()
        foreach ($pattern in $patterns) {
            $matches = Get-ChildItem -Path $bundleDir -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue
            if ($matches) { $artifacts += $matches.FullName }
        }

        if ($artifacts.Count -gt 0) {
            Write-Pass "dashboard artifact exists ($($artifacts.Count) found; first: $($artifacts[0]))"
        } else {
            Write-Fail "dashboard artifact missing under $bundleDir"
        }
    }
}
Write-Output ""

# --- Summary ---
$total = $pass + $fail
Write-Output "=== Results: $pass/$total passed ==="
if ($fail -gt 0) {
    Write-Output "SMOKE FAILED — $fail check(s) did not pass."
    exit 1
}
Write-Output "SMOKE PASSED"
exit 0
