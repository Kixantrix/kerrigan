#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Create a single GitHub pull request from a body file, avoiding the PowerShell heredoc footgun.

.DESCRIPTION
    Inline `gh pr create --body "@'...'@"` with multi-line PowerShell heredocs is fragile:
    the body is interpolated by PowerShell (so `$` and backticks misparse), and body text
    that happens to contain tokens like `rm` / `Remove-Item` trips terminal auto-approval
    deny rules because the whole command line is scanned. It can also double-fire.

    This wrapper always reads the body from a file (write it as UTF-8 / no BOM), passes it via
    --body-file, and runs exactly one `gh pr create`. Use this in place of any inline
    `gh pr create --body "..."` with multi-line content.

.PARAMETER Title
    Pull request title.

.PARAMETER BodyFile
    Path to a UTF-8 file containing the PR body. Required.

.PARAMETER Base
    Base branch to merge into. Defaults to 'main'.

.PARAMETER Head
    Head branch. Defaults to the current branch.

.PARAMETER Label
    Zero or more labels to apply.

.PARAMETER Draft
    Open the PR as a draft.

.PARAMETER DryRun
    Print the planned gh command without executing it.

.EXAMPLE
    .\tools\new-pr.ps1 -Title "Add approval rules" -BodyFile .specify/tmp/pr.md

.EXAMPLE
    Set-Content -Encoding utf8 -NoNewline -Path body.md -Value $body
    .\tools\new-pr.ps1 -Title "Fix Y" -BodyFile body.md -Base main -Draft
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Title,
    [Parameter(Mandatory = $true)]
    [string]$BodyFile,
    [string]$Base = 'main',
    [string]$Head,
    [string[]]$Label,
    [switch]$Draft,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $BodyFile -PathType Leaf)) {
    Write-Error "Body file not found or is not a file: $BodyFile"
    exit 1
}
$BodyFile = (Resolve-Path -LiteralPath $BodyFile).Path

if (-not $Head) {
    $Head = (git rev-parse --abbrev-ref HEAD 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Head)) {
        Write-Error "Could not determine current branch; pass -Head explicitly."
        exit 1
    }
    $Head = $Head.Trim()
    # Detached HEAD resolves to the literal 'HEAD', which gh would reject with a
    # confusing error; require an explicit branch instead.
    if ($Head -eq 'HEAD') {
        Write-Error "Detached HEAD state; pass -Head explicitly with a branch name."
        exit 1
    }
}

$ghArgs = @('pr', 'create', '--title', $Title, '--body-file', $BodyFile, '--base', $Base, '--head', $Head)
if ($Draft) {
    $ghArgs += '--draft'
}
if ($Label) {
    foreach ($l in $Label) {
        $ghArgs += @('--label', $l)
    }
}

if ($DryRun) {
    Write-Host "[dry-run] gh $($ghArgs -join ' ')"
    exit 0
}

& gh @ghArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "gh pr create failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
