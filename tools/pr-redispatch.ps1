#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Post a re-dispatch comment and re-arm PR auto-merge.

.DESCRIPTION
    Opens an editor for a multiline re-dispatch comment body (or uses -Body), posts it
    with gh pr comment --body-file, then re-arms auto-merge using gh pr merge --auto --squash.

.PARAMETER PrNumber
    Pull request number to comment on and re-arm.

.PARAMETER Body
    Comment body to post directly, bypassing editor.

.EXAMPLE
    .\tools\pr-redispatch.ps1 270

.EXAMPLE
    .\tools\pr-redispatch.ps1 270 -Body "@copilot please address the remaining review feedback"
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$PrNumber,
    [string]$Body
)

$ErrorActionPreference = "Stop"
$defaultEditor = if ($IsWindows -or $env:OS -eq "Windows_NT") { "notepad" } else { "vi" }
$editor = if ($env:EDITOR) { $env:EDITOR } else { $defaultEditor }
$preamble = "@copilot please address the following review feedback on this branch:`n`n"
$tempPath = Join-Path ([System.IO.Path]::GetTempPath()) ("pr_redispatch_{0}.md" -f [System.Guid]::NewGuid().ToString("N"))

try {
    if ($PSBoundParameters.ContainsKey("Body")) {
        $finalBody = $Body
    } else {
        Set-Content -Path $tempPath -Value $preamble -Encoding UTF8
        & $editor $tempPath
        if ($LASTEXITCODE -ne 0) {
            throw "Editor exited with code $LASTEXITCODE"
        }
        $finalBody = Get-Content -Path $tempPath -Raw -Encoding UTF8
    }

    if ([string]::IsNullOrWhiteSpace($finalBody)) {
        Write-Host "Comment body is empty. Nothing posted."
        exit 0
    }

    Set-Content -Path $tempPath -Value $finalBody -Encoding UTF8
    & gh pr comment $PrNumber --body-file $tempPath 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to post PR comment"
    }

    & gh pr merge $PrNumber --auto --squash 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to re-arm auto-merge"
    }

    Write-Host "Posted re-dispatch comment and re-armed auto-merge for PR #$PrNumber."
    exit 0
} catch {
    Write-Error "pr-redispatch failed: $_"
    exit 1
} finally {
    if (Test-Path $tempPath) {
        Remove-Item -Path $tempPath -Force -ErrorAction SilentlyContinue
    }
}
