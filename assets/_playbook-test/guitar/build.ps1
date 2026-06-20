# assets/_playbook-test/guitar/build.ps1
# Regenerates all DXF exports from parametric Python sources (Windows / PowerShell).
#
# Usage:
#   pwsh assets/_playbook-test/guitar/build.ps1
#   (or .\build.ps1 from the guitar\ directory)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$GuitarDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir = Join-Path $GuitarDir "source"

Write-Host "=== Guitar playbook: building DXF exports ==="
Write-Host "Asset root: $GuitarDir"
Write-Host ""

python "$SourceDir\headstock.py"
python "$SourceDir\brass_logo.py"

Write-Host ""
Write-Host "Build complete. Exports in $GuitarDir\exports\"
