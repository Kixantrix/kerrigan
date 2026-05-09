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
    Idempotent and side-effect-free (read-only checks only).

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

# --- Summary ---
$total = $pass + $fail
Write-Output "=== Results: $pass/$total passed ==="
if ($fail -gt 0) {
    Write-Output "SMOKE FAILED — $fail check(s) did not pass."
    exit 1
}
Write-Output "SMOKE PASSED"
exit 0
