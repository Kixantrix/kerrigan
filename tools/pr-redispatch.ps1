#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Re-dispatch review feedback to @copilot and re-arm auto-merge.

.DESCRIPTION
    Opens an editor with a pre-filled multi-line redispatch preamble, posts the
    resulting comment to the PR, and re-arms auto-merge with squash.

.PARAMETER PrNumber
    Pull request number to comment on.

.PARAMETER Body
    Optional comment body. If provided, editor interaction is skipped.

.EXAMPLE
    .\tools\pr-redispatch.ps1 270
    Opens editor, posts comment, then runs auto-merge command.

.EXAMPLE
    .\tools\pr-redispatch.ps1 270 -Body "@copilot please address remaining review feedback"
    Posts the provided body directly.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$PrNumber,
    [string]$Body
)

$ErrorActionPreference = 'Stop'

$commentBody = $Body
$tempFile = $null

if ([string]::IsNullOrWhiteSpace($commentBody)) {
    $defaultBody = "@copilot please address the following review feedback on this branch:`n`n"
    $tempFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.md'
    Set-Content -Path $tempFile -Value $defaultBody -Encoding UTF8

    $isWindows = $PSVersionTable.PSEdition -eq 'Desktop' -or $env:OS -eq 'Windows_NT'
    $editor = if ($env:EDITOR) { $env:EDITOR } elseif ($isWindows) { 'notepad' } else { 'vi' }

    & $editor $tempFile
    $commentBody = Get-Content -Path $tempFile -Raw
}

try {
    if (-not [string]::IsNullOrWhiteSpace($commentBody)) {
        if ($null -eq $tempFile) {
            $tempFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.md'
            Set-Content -Path $tempFile -Value $commentBody -Encoding UTF8
        }

        gh pr comment $PrNumber --body-file $tempFile
        gh pr merge $PrNumber --auto --squash
        Write-Host "Posted redispatch comment and re-armed auto-merge for PR #$PrNumber."
    } else {
        Write-Host "No comment body provided; nothing posted."
    }
} finally {
    if ($tempFile -and (Test-Path $tempFile)) {
        Remove-Item -Path $tempFile -Force
    }
}

exit 0
