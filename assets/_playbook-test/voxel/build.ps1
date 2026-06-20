# assets/_playbook-test/voxel/build.ps1
# Re-generate exports/ship.vox and exports/ship.glb from source/gen_ship.py.
# PowerShell equivalent of build.sh.  No GUI required.  Deterministic.
#
# Usage: .\build.ps1 [-OutputDir <path>]

param(
    [string]$OutputDir = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Generator = Join-Path $ScriptDir "source\gen_ship.py"
if (-not $OutputDir) { $OutputDir = Join-Path $ScriptDir "exports" }

Write-Host "=== voxel hero ship build ==="
Write-Host "generator : $Generator"
Write-Host "output-dir: $OutputDir"
Write-Host ""

python $Generator --output-dir $OutputDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "build complete."
$vox = Get-Item (Join-Path $OutputDir "ship.vox")
$glb = Get-Item (Join-Path $OutputDir "ship.glb")
Write-Host "  ship.vox : $($vox.Length) bytes"
Write-Host "  ship.glb : $($glb.Length) bytes"
