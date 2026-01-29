#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Suggests wave groupings for open issues based on predicted file overlap.

.DESCRIPTION
    Analyzes open issues with agent:go label to predict which files they will modify.
    Groups issues into waves to minimize merge conflicts.
    
    Prediction strategies:
    1. Scan issue descriptions for file/directory mentions
    2. Check linked specs for "Files to Modify" sections
    3. Use role labels to predict common file patterns
    4. Apply historical patterns

.PARAMETER DryRun
    Show wave suggestions without applying labels (default: true)

.PARAMETER Apply
    Apply suggested wave labels to issues

.EXAMPLE
    ./tools/suggest-waves.ps1
    Shows wave suggestions without applying labels

.EXAMPLE
    ./tools/suggest-waves.ps1 -Apply
    Applies suggested wave labels to issues

.NOTES
    This is a helper script. Manual review of suggestions is recommended.
    See playbooks/triage.md for wave-based assignment guidance.
#>

param(
    [switch]$Apply = $false
)

# Color helpers
function Write-Header($text) { Write-Host $text -ForegroundColor Cyan }
function Write-Wave($text) { Write-Host $text -ForegroundColor Blue }
function Write-Issue($text) { Write-Host $text -ForegroundColor White }
function Write-Files($text) { Write-Host $text -ForegroundColor Gray }
function Write-Success($text) { Write-Host $text -ForegroundColor Green }
function Write-Warning($text) { Write-Host $text -ForegroundColor Yellow }

Write-Header "=== Wave Assignment Suggestion Tool ==="
Write-Host ""

# Get open issues with agent:go label
Write-Host "Fetching open issues with agent:go label..."
$issues = gh issue list --label "agent:go" --state open --json number,title,labels,body | ConvertFrom-Json

if ($issues.Count -eq 0) {
    Write-Warning "No open issues with agent:go label found."
    exit 0
}

Write-Success "Found $($issues.Count) issue(s) to analyze"
Write-Host ""

# Function to predict files from issue
function Get-PredictedFiles {
    param($issue)
    
    $files = @()
    $text = "$($issue.title) $($issue.body)"
    
    # Common file patterns
    $patterns = @{
        'workflow|ci\.yml|github.*workflow' = @('.github/workflows/*.yml', '.github/test-mapping.yml')
        'triage|playbooks/triage' = @('playbooks/triage.md', '.github/agents/role.triage.md')
        'label|github.*label' = @('docs/github-labels.md')
        'validator|tools/validator' = @('tools/validators/*.py')
        'documentation|docs/' = @('docs/*.md')
        'playbook|playbooks/' = @('playbooks/*.md')
        'agent.*prompt|\.github/agents' = @('.github/agents/*.md')
        'test.*mapping' = @('.github/test-mapping.yml')
        'readme' = @('README.md')
        'script|tools/' = @('tools/*.ps1', 'tools/*.py', 'tools/*.sh')
    }
    
    # Check patterns
    foreach ($pattern in $patterns.Keys) {
        if ($text -match $pattern) {
            $files += $patterns[$pattern]
        }
    }
    
    # Role-based predictions
    $roleLabels = $issue.labels | Where-Object { $_.name -match '^role:' }
    foreach ($roleLabel in $roleLabels) {
        switch ($roleLabel.name) {
            'role:triage' { 
                $files += @('playbooks/triage.md', '.github/agents/role.triage.md')
            }
            'role:swe' {
                # SWE touches varied files, hard to predict
            }
            'role:architect' {
                $files += @('docs/architecture.md')
            }
            'role:testing' {
                $files += @('tests/*.py')
            }
        }
    }
    
    # Extract explicit file mentions (simple heuristic)
    $fileMatches = [regex]::Matches($text, '([`"]?[\w\-\.]+/[\w\-\.]+\.[\w]+[`"]?)')
    foreach ($match in $fileMatches) {
        $potentialFile = $match.Value -replace '[`"]', ''
        if ($potentialFile -match '\.(md|yml|yaml|py|ps1|sh|json)$') {
            $files += $potentialFile
        }
    }
    
    return $files | Select-Object -Unique
}

# Analyze each issue
$issueData = @()
foreach ($issue in $issues) {
    $predictedFiles = Get-PredictedFiles $issue
    
    $issueData += @{
        Number = $issue.number
        Title = $issue.title
        Files = $predictedFiles
        Labels = $issue.labels.name
    }
}

# Display analysis
Write-Header "File Overlap Analysis:"
Write-Host ""

foreach ($data in $issueData) {
    Write-Issue "Issue #$($data.Number): $($data.Title)"
    if ($data.Files.Count -gt 0) {
        Write-Files "  Predicted files: $($data.Files -join ', ')"
    } else {
        Write-Files "  Predicted files: (unable to predict - review manually)"
    }
    Write-Host ""
}

# Detect overlaps and suggest waves
Write-Header "Wave Grouping Suggestions:"
Write-Host ""

$waveAssignments = @{}
$currentWave = 1
$assignedIssues = @()

# Simple wave assignment algorithm:
# - Wave 1: Issues with no overlaps or unpredictable files
# - Wave 2+: Issues with overlaps, assigned to later waves

while ($assignedIssues.Count -lt $issueData.Count) {
    $waveIssues = @()
    $waveFiles = @()
    
    foreach ($data in $issueData) {
        if ($assignedIssues -contains $data.Number) {
            continue
        }
        
        # If no predicted files, safe to put in current wave
        if ($data.Files.Count -eq 0) {
            $waveIssues += $data.Number
            $assignedIssues += $data.Number
            continue
        }
        
        # Check for file overlap with current wave
        $hasOverlap = $false
        foreach ($file in $data.Files) {
            foreach ($waveFile in $waveFiles) {
                # Simple overlap check (could be more sophisticated)
                if ($file -eq $waveFile) {
                    $hasOverlap = $true
                    break
                }
            }
            if ($hasOverlap) { break }
        }
        
        if (-not $hasOverlap) {
            $waveIssues += $data.Number
            $waveFiles += $data.Files
            $assignedIssues += $data.Number
        }
    }
    
    if ($waveIssues.Count -eq 0) {
        # No more non-overlapping issues, put remaining in next wave
        foreach ($data in $issueData) {
            if ($assignedIssues -notcontains $data.Number) {
                $waveIssues += $data.Number
                $assignedIssues += $data.Number
            }
        }
    }
    
    $waveAssignments[$currentWave] = $waveIssues
    $currentWave++
    
    if ($currentWave -gt 10) {
        Write-Warning "Too many waves detected. Manual review recommended."
        break
    }
}

# Display wave suggestions
foreach ($wave in $waveAssignments.Keys | Sort-Object) {
    Write-Wave "Wave $wave ($($waveAssignments[$wave].Count) issue(s)):"
    foreach ($issueNum in $waveAssignments[$wave]) {
        $data = $issueData | Where-Object { $_.Number -eq $issueNum } | Select-Object -First 1
        Write-Issue "  #$issueNum - $($data.Title)"
    }
    Write-Host ""
}

# Apply labels if requested
if ($Apply) {
    Write-Header "Applying wave labels..."
    
    foreach ($wave in $waveAssignments.Keys | Sort-Object) {
        foreach ($issueNum in $waveAssignments[$wave]) {
            try {
                gh issue edit $issueNum --add-label "wave:$wave"
                Write-Success "  ✓ Added wave:$wave to issue #$issueNum"
            } catch {
                $errorMsg = $_.Exception.Message
                Write-Warning "  ✗ Failed to label issue #${issueNum}: $errorMsg"
            }
        }
    }
    
    Write-Host ""
    Write-Success "Wave labels applied!"
} else {
    Write-Host ""
    Write-Warning "Dry run mode. Review suggestions above."
    Write-Host "To apply these wave labels, run: ./tools/suggest-waves.ps1 -Apply"
}

Write-Host ""
Write-Header "Next Steps:"
Write-Host "1. Review wave suggestions above"
Write-Host "2. Manually adjust wave labels if needed: gh issue edit <number> --add-label 'wave:N'"
Write-Host "3. Assign only wave:1 issues: gh issue edit <number> --add-assignee '@copilot'"
Write-Host "4. Monitor wave:1 PRs through merge"
Write-Host "5. After wave:1 merges, assign wave:2"
Write-Host ""
Write-Host "See playbooks/triage.md#wave-based-assignment for detailed guidance."
