# assets/_playbook-test/voxel/smoke.ps1
# PowerShell equivalent of smoke.sh
#
# Acceptance criteria tested (one-to-one):
#   AC1  exports/ship.glb regenerates from source via build.ps1 (no GUI)
#   AC2  glTF validates (pygltflib loads without error)
#   AC3  mesh is manifold AND tri count ≤ budget
#   AC4  texture dimensions are power-of-two
#   AC5  re-running build.ps1 is deterministic (SHA-256 matches)
#
# Usage: .\smoke.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== voxel hero ship smoke ==="
Write-Host ""

# --- Step 1: (re-)build ---
Write-Host "[ step 1: build ]"
& "$ScriptDir\build.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ""

# --- Step 2: validate ---
Write-Host "[ step 2: validate ]"
python "$ScriptDir\validate.py" `
    --exports-dir "$ScriptDir\exports" `
    --source-dir  "$ScriptDir\source"  `
    --check-determinism
exit $LASTEXITCODE
