# assets/_playbook-test/guitar/smoke.ps1
# Builds DXF exports and runs all 5 acceptance-criteria assertions via pytest.
# Windows / PowerShell equivalent of smoke.sh.
#
# Usage:
#   pwsh assets/_playbook-test/guitar/smoke.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$GuitarDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot   = (Get-Item "$GuitarDir\..\..\..").FullName

Write-Host "=== Guitar playbook smoke test ==="
Write-Host "Asset root: $GuitarDir"
Write-Host ""

# Step 1: regenerate exports
Write-Host "[ Build ]"
& pwsh "$GuitarDir\build.ps1"
Write-Host ""

# Step 2: run pytest assertions
Write-Host "[ Assertions ]"
python -m pytest "$RepoRoot\tests\test_guitar_playbook.py" -v --tb=short
