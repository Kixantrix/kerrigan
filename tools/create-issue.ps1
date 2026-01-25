<#
.SYNOPSIS
    Create a GitHub issue from a markdown file or inline content.

.DESCRIPTION
    Creates issues with proper labeling and optional @copilot assignment.
    Supports reading from markdown files with YAML frontmatter for metadata.

.PARAMETER Title
    Issue title. If not provided, extracted from first # heading in body.

.PARAMETER Body
    Issue body text. Mutually exclusive with BodyFile.

.PARAMETER BodyFile
    Path to markdown file containing issue body. Mutually exclusive with Body.

.PARAMETER Labels
    Comma-separated list of labels to apply.

.PARAMETER AssignCopilot
    If set, assigns @copilot and adds agent:go label.

.PARAMETER DryRun
    Show what would be created without actually creating.

.EXAMPLE
    ./create-issue.ps1 -Title "Fix bug" -Body "Description here" -Labels "bug,role:swe" -AssignCopilot

.EXAMPLE
    ./create-issue.ps1 -BodyFile "./temp-issue.md" -AssignCopilot

.EXAMPLE
    ./create-issue.ps1 -BodyFile "./issue.md" -DryRun
#>

param(
    [string]$Title,
    [string]$Body,
    [string]$BodyFile,
    [string]$Labels = "",
    [switch]$AssignCopilot,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Validate parameters
if ($Body -and $BodyFile) {
    Write-Error "Cannot specify both -Body and -BodyFile"
    exit 1
}

if (-not $Body -and -not $BodyFile) {
    Write-Error "Must specify either -Body or -BodyFile"
    exit 1
}

# Read body from file if specified
if ($BodyFile) {
    if (-not (Test-Path $BodyFile)) {
        Write-Error "File not found: $BodyFile"
        exit 1
    }
    $Body = Get-Content -Path $BodyFile -Raw
}

# Parse YAML frontmatter if present
$frontmatter = @{}
if ($Body -match "^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$") {
    $yamlContent = $Matches[1]
    $Body = $Matches[2]
    
    # Simple YAML parsing for common fields
    foreach ($line in $yamlContent -split "`n") {
        if ($line -match "^\s*(\w+):\s*(.+)\s*$") {
            $key = $Matches[1].Trim()
            $value = $Matches[2].Trim()
            # Remove quotes if present
            $value = $value -replace "^[`"']|[`"']$", ""
            $frontmatter[$key] = $value
        }
    }
    
    # Use frontmatter values if not provided via parameters
    if (-not $Title -and $frontmatter.ContainsKey("title")) {
        $Title = $frontmatter["title"]
    }
    if (-not $Labels -and $frontmatter.ContainsKey("labels")) {
        $Labels = $frontmatter["labels"]
    }
}

# Extract title from first heading if not provided
if (-not $Title) {
    if ($Body -match "^#\s+(.+)$" -or $Body -match "\n#\s+(.+)$") {
        $Title = $Matches[1].Trim()
        Write-Host "Extracted title: $Title" -ForegroundColor Cyan
    } else {
        Write-Error "No title provided and could not extract from body"
        exit 1
    }
}

# Build label list
$labelList = @()
if ($Labels) {
    $labelList = $Labels -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}

# Add agent:go if assigning Copilot
if ($AssignCopilot -and "agent:go" -notin $labelList) {
    $labelList += "agent:go"
}

# Display what will be created
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Creating Issue" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Title: $Title" -ForegroundColor White
Write-Host "Labels: $($labelList -join ', ')" -ForegroundColor Yellow
if ($AssignCopilot) {
    Write-Host "Assignee: @copilot" -ForegroundColor Magenta
}
Write-Host "Body length: $($Body.Length) characters" -ForegroundColor Gray
Write-Host "----------------------------------------"

if ($DryRun) {
    Write-Host "`n[DRY RUN] Would create issue with above settings" -ForegroundColor Cyan
    Write-Host "`nBody preview (first 500 chars):" -ForegroundColor Gray
    Write-Host ($Body.Substring(0, [Math]::Min(500, $Body.Length))) -ForegroundColor Gray
    exit 0
}

# Create temp file for body (avoids escaping issues)
$tempFile = [System.IO.Path]::GetTempFileName()
try {
    $Body | Set-Content -Path $tempFile -Encoding UTF8
    
    # Build gh command
    $ghArgs = @("issue", "create", "--title", $Title, "--body-file", $tempFile)
    
    if ($labelList.Count -gt 0) {
        $ghArgs += "--label"
        $ghArgs += ($labelList -join ",")
    }
    
    # Create issue
    Write-Host "`nCreating issue..." -ForegroundColor Cyan
    $result = & gh @ghArgs 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create issue: $result"
        exit 1
    }
    
    # Extract issue URL and number
    $issueUrl = $result | Select-Object -Last 1
    Write-Host "Created: $issueUrl" -ForegroundColor Green
    
    # Assign @copilot if requested
    if ($AssignCopilot) {
        # Extract issue number from URL
        if ($issueUrl -match "/issues/(\d+)$") {
            $issueNumber = $Matches[1]
            Write-Host "Assigning @copilot to issue #$issueNumber..." -ForegroundColor Cyan
            
            $assignResult = & gh issue edit $issueNumber --add-assignee "@copilot" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ @copilot assigned successfully" -ForegroundColor Green
            } else {
                Write-Warning "Failed to assign @copilot: $assignResult"
            }
        }
    }
    
    Write-Host "`n✓ Issue created successfully!" -ForegroundColor Green
    Write-Host $issueUrl
    
} finally {
    # Cleanup temp file
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
    }
}
