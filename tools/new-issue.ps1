#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Create a single GitHub issue from a body file, avoiding the PowerShell heredoc footgun.

.DESCRIPTION
    Inline `gh issue create --body "@'...'@"` with multi-line PowerShell heredocs has fired
    `gh issue create` twice in this repo (issues #293+#295 / PRs #294+#296 incident,
    2026-05-27), creating duplicate issues and duplicate cloud-agent PRs.

    This wrapper always reads the body from a file written as UTF-8 (no BOM), passes it via
    --body-file, and ensures exactly one invocation. Use this in place of any inline
    `gh issue create --body "..."` with multi-line content.

.PARAMETER Title
    Issue title.

.PARAMETER BodyFile
    Path to a UTF-8 file containing the issue body. Required.

.PARAMETER Label
    Zero or more labels to apply.

.PARAMETER Assignee
    Optional assignee handle (e.g. 'copilot' or a username).

.PARAMETER Milestone
    Optional milestone name.

.PARAMETER DryRun
    Print the planned gh command without executing it.

.EXAMPLE
    .\tools\new-issue.ps1 -Title "Wire up X" -BodyFile .specify/briefings/x.md -Label agent:go -Assignee copilot

.EXAMPLE
    Set-Content -Encoding utf8 -NoNewline -Path body.md -Value $body
    .\tools\new-issue.ps1 -Title "Fix Y" -BodyFile body.md -Label agent:go,bug
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Title,
    [Parameter(Mandatory = $true)]
    [string]$BodyFile,
    [string[]]$Label,
    [string]$Assignee,
    [string]$Milestone,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $BodyFile)) {
    Write-Error "Body file not found: $BodyFile"
    exit 1
}

$args = @('issue', 'create', '--title', $Title, '--body-file', $BodyFile)
if ($Label) {
    foreach ($l in $Label) {
        $args += @('--label', $l)
    }
}
if ($Assignee) {
    $args += @('--assignee', $Assignee)
}
if ($Milestone) {
    $args += @('--milestone', $Milestone)
}

if ($DryRun) {
    Write-Host "[dry-run] gh $($args -join ' ')"
    exit 0
}

& gh @args
if ($LASTEXITCODE -ne 0) {
    Write-Error "gh issue create failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
