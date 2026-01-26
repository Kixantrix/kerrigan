#!/usr/bin/env pwsh
#Requires -Version 5.1

<#
.SYNOPSIS
    Submit feedback from a satellite Kerrigan installation to the main Kerrigan repository.

.DESCRIPTION
    Collects feedback from satellite users interactively and submits it to the main
    Kerrigan repo. Supports creating GitHub issues directly or saving markdown files
    for manual submission.
    
    This enables satellite repos to report bugs, suggest enhancements, share patterns,
    and ask questions about Kerrigan components.

.PARAMETER Category
    Type of feedback: bug, enhancement, pattern, or question.

.PARAMETER SaveOnly
    Save feedback as markdown file without creating GitHub issue.

.PARAMETER DryRun
    Show what would be created without actually creating.

.PARAMETER MainRepo
    Main Kerrigan repository. Default: Kixantrix/kerrigan

.EXAMPLE
    ./feedback-to-kerrigan.ps1
    Interactive mode - prompts for all information

.EXAMPLE
    ./feedback-to-kerrigan.ps1 -Category bug
    Start with bug category pre-selected

.EXAMPLE
    ./feedback-to-kerrigan.ps1 -SaveOnly
    Save feedback as markdown file without creating issue

.EXAMPLE
    ./feedback-to-kerrigan.ps1 -DryRun
    Preview what would be created
#>

param(
    [ValidateSet('bug', 'enhancement', 'pattern', 'question')]
    [string]$Category,
    
    [switch]$SaveOnly,
    [switch]$DryRun,
    [string]$MainRepo = "Kixantrix/kerrigan"
)

$ErrorActionPreference = "Stop"

# Check PowerShell version
if ($PSVersionTable.PSVersion -lt [Version]"5.1") {
    Write-Error "This script requires PowerShell 5.1 or later"
    exit 1
}

# ASCII-only output (no Unicode)
$script:UseUnicode = $false

# Helper function for colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Detect Kerrigan version
function Get-KerriganVersion {
    try {
        # Try git describe first
        $gitVersion = git describe --tags --always 2>$null
        if ($LASTEXITCODE -eq 0 -and $gitVersion) {
            return $gitVersion
        }
        
        # Try git rev-parse
        $gitCommit = git rev-parse --short HEAD 2>$null
        if ($LASTEXITCODE -eq 0 -and $gitCommit) {
            return $gitCommit
        }
    } catch {
        # Git command failed, return unknown
    }
    
    return "unknown"
}

# Get repo information
function Get-RepoInfo {
    try {
        $repoUrl = git config --get remote.origin.url 2>$null
        if ($LASTEXITCODE -eq 0 -and $repoUrl) {
            # Clean up the URL
            $repoUrl = $repoUrl -replace "\.git$", ""
            
            # Extract repo name
            if ($repoUrl -match "/([^/]+/[^/]+)$") {
                $repoName = $Matches[1] -replace "\.git$", ""
                return @{
                    Name = $repoName.Split('/')[-1]
                    Url = $repoUrl
                }
            }
        }
    } catch {
        # Git command failed
    }
    
    return @{
        Name = "unknown"
        Url = "unknown"
    }
}

# Main script
Write-ColorOutput "`n========================================" "Green"
Write-ColorOutput "Satellite Feedback to Kerrigan" "Green"
Write-ColorOutput "========================================" "Green"
Write-ColorOutput ""

# Detect context
$kerriganVersion = Get-KerriganVersion
$repoInfo = Get-RepoInfo

Write-ColorOutput "Detected information:" "Cyan"
Write-ColorOutput "  Kerrigan version: $kerriganVersion" "Gray"
Write-ColorOutput "  Current repo: $($repoInfo.Name)" "Gray"
Write-ColorOutput "  Repo URL: $($repoInfo.Url)" "Gray"
Write-ColorOutput ""

# Collect feedback information
Write-ColorOutput "This script will help you submit feedback to the main Kerrigan repository." "White"
Write-ColorOutput "Your feedback helps improve Kerrigan for everyone!" "White"
Write-ColorOutput ""

# Category
if (-not $Category) {
    Write-ColorOutput "What type of feedback do you have?" "Yellow"
    Write-ColorOutput "  1. Bug - Something is broken" "White"
    Write-ColorOutput "  2. Enhancement - Improvement suggestion" "White"
    Write-ColorOutput "  3. Pattern - Successful technique to share" "White"
    Write-ColorOutput "  4. Question - Need clarification or help" "White"
    
    do {
        $categoryChoice = Read-Host "Enter number (1-4)"
    } while ($categoryChoice -notmatch "^[1-4]$")
    
    $Category = switch ($categoryChoice) {
        "1" { "bug" }
        "2" { "enhancement" }
        "3" { "pattern" }
        "4" { "question" }
    }
}

Write-ColorOutput "`nCategory: $Category" "Cyan"
Write-ColorOutput ""

# Title
Write-ColorOutput "Enter a brief title for your feedback:" "Yellow"
$title = Read-Host "Title"
while ([string]::IsNullOrWhiteSpace($title)) {
    Write-ColorOutput "Title is required" "Red"
    $title = Read-Host "Title"
}

# Context
Write-ColorOutput "`nDescribe the context (what were you trying to do?):" "Yellow"
Write-ColorOutput "(Press Enter twice when done)" "Gray"
$contextLines = @()
do {
    $line = Read-Host
    if (-not [string]::IsNullOrWhiteSpace($line)) {
        $contextLines += $line
    } else {
        break
    }
} while ($true)
$context = $contextLines -join "`n"

# Feedback details
Write-ColorOutput "`nProvide detailed feedback:" "Yellow"
Write-ColorOutput "(What happened? What would be better? Press Enter twice when done)" "Gray"
$feedbackLines = @()
do {
    $line = Read-Host
    if (-not [string]::IsNullOrWhiteSpace($line)) {
        $feedbackLines += $line
    } else {
        break
    }
} while ($true)
$feedbackDetail = $feedbackLines -join "`n"

while ([string]::IsNullOrWhiteSpace($feedbackDetail)) {
    Write-ColorOutput "Feedback details are required" "Red"
    Write-ColorOutput "Provide detailed feedback (Press Enter twice when done):" "Yellow"
    $feedbackLines = @()
    do {
        $line = Read-Host
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            $feedbackLines += $line
        } else {
            break
        }
    } while ($true)
    $feedbackDetail = $feedbackLines -join "`n"
}

# Impact
Write-ColorOutput "`nWhat is the impact on your workflow?" "Yellow"
Write-ColorOutput "  1. Blocking - Cannot proceed without fix" "White"
Write-ColorOutput "  2. High - Significant friction or workaround needed" "White"
Write-ColorOutput "  3. Medium - Noticeable inconvenience" "White"
Write-ColorOutput "  4. Low - Minor improvement" "White"

do {
    $impactChoice = Read-Host "Enter number (1-4)"
} while ($impactChoice -notmatch "^[1-4]$")

$impactMapping = @{
    "1" = @{ Name = "Blocking"; Description = "Cannot proceed without fix" }
    "2" = @{ Name = "High"; Description = "Significant friction or workaround needed" }
    "3" = @{ Name = "Medium"; Description = "Noticeable inconvenience" }
    "4" = @{ Name = "Low"; Description = "Minor improvement" }
}

$impact = $impactMapping[$impactChoice].Name
$impactDescription = $impactMapping[$impactChoice].Description

# Suggested solution
Write-ColorOutput "`nDo you have a suggested solution? (optional)" "Yellow"
Write-ColorOutput "(Press Enter twice when done, or just Enter to skip)" "Gray"
$solutionLines = @()
do {
    $line = Read-Host
    if (-not [string]::IsNullOrWhiteSpace($line)) {
        $solutionLines += $line
    } else {
        break
    }
} while ($true)
$suggestedSolution = $solutionLines -join "`n"

# Privacy choice
Write-ColorOutput "`nWould you like to include your repo information?" "Yellow"
Write-ColorOutput "  1. Yes - Include repo name and URL (helps us understand context)" "White"
Write-ColorOutput "  2. Anonymous - Don't disclose repo information" "White"

do {
    $privacyChoice = Read-Host "Enter number (1-2)"
} while ($privacyChoice -notmatch "^[1-2]$")

$includeRepo = ($privacyChoice -eq "1")

# Build feedback content
$timestamp = Get-Date -Format "yyyy-MM-dd"

if ($includeRepo) {
    $satelliteRepo = $repoInfo.Name
    $satelliteUrl = $repoInfo.Url
} else {
    $satelliteRepo = "Anonymous"
    $satelliteUrl = "Not disclosed"
}

# Create markdown content
$feedbackContent = @"
## Satellite Information

**Satellite Repo**: $satelliteRepo  
**Repo URL**: $satelliteUrl  
**Kerrigan Version**: $kerriganVersion  
**Date**: $timestamp

## Category

**$Category**

## Context

$context

## Feedback

$feedbackDetail

## Impact

**$impact** - $impactDescription

"@

if (-not [string]::IsNullOrWhiteSpace($suggestedSolution)) {
    $feedbackContent += @"
## Suggested Solution

$suggestedSolution

"@
}

$feedbackContent += @"
## Additional Context

Submitted via feedback-to-kerrigan.ps1 from satellite installation.
"@

# Determine labels
$labels = @("satellite-feedback", $Category)
$labelString = $labels -join ","

# Preview
Write-ColorOutput "`n========================================" "Green"
Write-ColorOutput "Feedback Preview" "Green"
Write-ColorOutput "========================================" "Green"
Write-ColorOutput "Title: $title" "White"
Write-ColorOutput "Labels: $labelString" "Yellow"
Write-ColorOutput "Category: $Category" "Cyan"
Write-ColorOutput "Impact: $impact" "Magenta"
Write-ColorOutput ""
Write-ColorOutput "Content preview (first 500 chars):" "Gray"
Write-ColorOutput ($feedbackContent.Substring(0, [Math]::Min(500, $feedbackContent.Length))) "Gray"
Write-ColorOutput ""

if ($DryRun) {
    Write-ColorOutput "[DRY RUN] Would create feedback with above settings" "Cyan"
    exit 0
}

# Save to file option
if ($SaveOnly) {
    # Sanitize title for filename - replace non-alphanumeric with single dash
    $sanitizedTitle = $title -replace '[^a-zA-Z0-9]+', '-' -replace '^-+|-+$', ''
    $filename = "satellite-feedback-$timestamp-$sanitizedTitle.md"
    $filepath = Join-Path $PWD $filename
    
    $fileContent = @"
---
title: $title
labels: $labelString
---

$feedbackContent
"@
    
    $fileContent | Set-Content -Path $filepath -Encoding UTF8
    Write-ColorOutput "`nSaved feedback to: $filepath" "Green"
    Write-ColorOutput ""
    Write-ColorOutput "To submit this feedback:" "Yellow"
    Write-ColorOutput "  1. Fork the main Kerrigan repo: https://github.com/$MainRepo" "White"
    Write-ColorOutput "  2. Add this file to feedback/satellite/" "White"
    Write-ColorOutput "  3. Create a PR to the main repo" "White"
    Write-ColorOutput "  OR" "White"
    Write-ColorOutput "  Create a GitHub issue at https://github.com/$MainRepo/issues/new" "White"
    Write-ColorOutput "  and paste the contents of this file" "White"
    exit 0
}

# Create GitHub issue
Write-ColorOutput "Ready to submit feedback to $MainRepo" "Yellow"
Write-ColorOutput ""

# Check if gh CLI is available
$ghAvailable = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghAvailable) {
    Write-ColorOutput "GitHub CLI (gh) not found. Cannot create issue automatically." "Red"
    Write-ColorOutput ""
    Write-ColorOutput "Options:" "Yellow"
    Write-ColorOutput "  1. Install GitHub CLI: https://cli.github.com/" "White"
    Write-ColorOutput "  2. Re-run with -SaveOnly to save as markdown file" "White"
    Write-ColorOutput "  3. Manually create an issue at https://github.com/$MainRepo/issues/new" "White"
    exit 1
}

$createIssue = Read-Host "Create GitHub issue in $MainRepo? (y/n)"
if ($createIssue -ne "y") {
    Write-ColorOutput "Cancelled. Re-run with -SaveOnly to save as file instead." "Yellow"
    exit 0
}

# Create temp file for body
$tempFile = [System.IO.Path]::GetTempFileName()
try {
    $feedbackContent | Set-Content -Path $tempFile -Encoding UTF8
    
    # Create issue in main Kerrigan repo
    Write-ColorOutput "`nCreating issue in $MainRepo..." "Cyan"
    
    $ghArgs = @(
        "issue", "create",
        "--repo", $MainRepo,
        "--title", $title,
        "--body-file", $tempFile,
        "--label", $labelString
    )
    
    try {
        $result = & gh @ghArgs 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "Failed to create issue: $result" "Red"
            Write-ColorOutput ""
            Write-ColorOutput "You can try:" "Yellow"
            Write-ColorOutput "  1. Check you're authenticated with: gh auth status" "White"
            Write-ColorOutput "  2. Re-run with -SaveOnly to save as file instead" "White"
            exit 1
        }
        
        # Extract issue URL
        $issueUrl = $result | Select-Object -Last 1
        
        Write-ColorOutput "`n========================================" "Green"
        Write-ColorOutput "Success!" "Green"
        Write-ColorOutput "========================================" "Green"
        Write-ColorOutput "Feedback submitted successfully!" "Green"
        Write-ColorOutput ""
        Write-ColorOutput "Issue created: $issueUrl" "Cyan"
        Write-ColorOutput ""
        Write-ColorOutput "Thank you for contributing to Kerrigan!" "White"
        Write-ColorOutput "Your feedback helps improve the framework for everyone." "White"
    } catch {
        Write-ColorOutput "Error creating issue: $($_.Exception.Message)" "Red"
        Write-ColorOutput ""
        Write-ColorOutput "You can try:" "Yellow"
        Write-ColorOutput "  1. Check you're authenticated with: gh auth status" "White"
        Write-ColorOutput "  2. Re-run with -SaveOnly to save as file instead" "White"
        exit 1
    }
    
} finally {
    # Cleanup temp file
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
    }
}
