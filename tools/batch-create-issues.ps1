<#
.SYNOPSIS
    Process all pending issue files from a directory and create GitHub issues.

.DESCRIPTION
    Reads markdown files from a staging directory, creates issues, and optionally
    moves processed files to a completed directory or deletes them.

.PARAMETER InputDir
    Directory containing markdown files to process. Default: ./temp-issues

.PARAMETER Pattern
    File pattern to match. Default: *.md

.PARAMETER AssignCopilot
    If set, assigns @copilot to all created issues.

.PARAMETER DeleteAfter
    Delete files after successful issue creation. Default: move to ./temp-issues/processed

.PARAMETER DryRun
    Show what would be created without actually creating.

.EXAMPLE
    ./batch-create-issues.ps1 -AssignCopilot

.EXAMPLE
    ./batch-create-issues.ps1 -InputDir "./my-issues" -DeleteAfter

.EXAMPLE
    ./batch-create-issues.ps1 -DryRun
#>

param(
    [string]$InputDir = "./temp-issues",
    [string]$Pattern = "*.md",
    [switch]$AssignCopilot,
    [switch]$DeleteAfter,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if input directory exists
if (-not (Test-Path $InputDir)) {
    Write-Host "No pending issues directory found: $InputDir" -ForegroundColor Yellow
    Write-Host "Create the directory and add markdown files to process." -ForegroundColor Gray
    exit 0
}

# Find all matching files
$files = Get-ChildItem -Path $InputDir -Filter $Pattern -File | Where-Object { $_.Name -ne "README.md" }

if ($files.Count -eq 0) {
    Write-Host "No issue files found in $InputDir" -ForegroundColor Yellow
    exit 0
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Batch Issue Creator" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Found $($files.Count) issue file(s) to process" -ForegroundColor Cyan
Write-Host "Assign Copilot: $AssignCopilot" -ForegroundColor Gray
Write-Host "Dry Run: $DryRun" -ForegroundColor Gray
Write-Host "----------------------------------------`n"

$created = 0
$failed = 0
$createdIssues = @()

foreach ($file in $files) {
    Write-Host "Processing: $($file.Name)" -ForegroundColor White
    
    # Build arguments for create-issue.ps1
    $args = @("-BodyFile", $file.FullName)
    
    if ($AssignCopilot) {
        $args += "-AssignCopilot"
    }
    
    if ($DryRun) {
        $args += "-DryRun"
    }
    
    try {
        # Call create-issue.ps1
        $output = & "$scriptDir\create-issue.ps1" @args 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Host $output
            $created++
            
            # Extract issue URL from output
            $issueUrl = $output | Select-String -Pattern "https://github.com/.+/issues/\d+" | Select-Object -First 1
            if ($issueUrl) {
                $createdIssues += @{
                    File = $file.Name
                    Url = $issueUrl.Matches[0].Value
                }
            }
            
            # Handle processed file
            if (-not $DryRun) {
                if ($DeleteAfter) {
                    Remove-Item $file.FullName -Force
                    Write-Host "  Deleted: $($file.Name)" -ForegroundColor Gray
                } else {
                    # Move to processed subdirectory
                    $processedDir = Join-Path $InputDir "processed"
                    if (-not (Test-Path $processedDir)) {
                        New-Item -ItemType Directory -Path $processedDir -Force | Out-Null
                    }
                    Move-Item $file.FullName -Destination $processedDir -Force
                    Write-Host "  Moved to: processed/$($file.Name)" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "  FAILED: $output" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        $failed++
    }
    
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Green
Write-Host "Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Created: $created" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "Failed: $failed" -ForegroundColor Red
}

if ($createdIssues.Count -gt 0) {
    Write-Host "`nCreated Issues:" -ForegroundColor Cyan
    foreach ($issue in $createdIssues) {
        Write-Host "  - $($issue.File): $($issue.Url)" -ForegroundColor White
    }
}
