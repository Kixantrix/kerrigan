#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Display open issues with their labels and assignments in a formatted table.

.DESCRIPTION
    Fetches all open issues from the repository and displays them in an easy-to-read
    table format showing issue number, title, labels, and assignee.

.PARAMETER State
    Issue state to filter by. Default: open. Options: open, closed, all

.PARAMETER Limit
    Maximum number of issues to display. Default: 20

.EXAMPLE
    .\tools\show-issues.ps1
    Shows all open issues

.EXAMPLE
    .\tools\show-issues.ps1 -State all -Limit 50
    Shows all issues (open and closed), up to 50

.NOTES
    Requires PowerShell 5.1 or later for compatibility.
#>

param(
    [ValidateSet('open', 'closed', 'all')]
    [string]$State = 'open',
    
    [int]$Limit = 20
)

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error "This script requires PowerShell 5.1 or later. Current version: $($PSVersionTable.PSVersion)"
    exit 1
}

# Fetch issues from GitHub
Write-Host "Fetching $State issues..." -ForegroundColor Cyan

$issues = gh issue list --state $State --limit $Limit --json number,title,labels,assignees,createdAt,updatedAt | ConvertFrom-Json

if ($issues.Count -eq 0) {
    Write-Host "`nNo $State issues found." -ForegroundColor Yellow
    exit 0
}

# Format issues for display
$formatted = $issues | ForEach-Object {
    $labelNames = ($_.labels.name | Sort-Object) -join ', '
    $assigneeName = if ($_.assignees -and $_.assignees.Count -gt 0) { 
        $_.assignees[0].login 
    } else { 
        '-' 
    }
    
    # Priority indicator (using ASCII for PowerShell 5.1 compatibility)
    $priority = if ($_.labels.name -contains 'agent:go') { '[GO]' }
                elseif ($_.labels.name -contains 'agent:sprint') { '[SPRINT]' }
                else { ' ' }
    
    [PSCustomObject]@{
        ' ' = $priority
        '#' = $_.number
        Title = $_.title
        Labels = if ($labelNames) { $labelNames } else { '-' }
        Assignee = $assigneeName
        Updated = (Get-Date $_.updatedAt).ToString('MMM dd')
    }
}

# Display results
Write-Host "`n$($issues.Count) $State issue(s) found:" -ForegroundColor Green
Write-Host ""

$formatted | Format-Table -AutoSize -Wrap

# Summary by label
Write-Host "`nSummary:" -ForegroundColor Cyan
$allLabels = $issues | ForEach-Object { $_.labels.name } | Group-Object | Sort-Object Count -Descending | Select-Object -First 10
if ($allLabels) {
    $allLabels | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Count)" -ForegroundColor Gray
    }
}

# Assignment summary
Write-Host "`nAssignments:" -ForegroundColor Cyan
$assigned = $issues | Where-Object { $_.assignees.Count -gt 0 }
$unassigned = $issues.Count - $assigned.Count
Write-Host "  Assigned: $($assigned.Count)" -ForegroundColor Gray
Write-Host "  Unassigned: $unassigned" -ForegroundColor Gray

# Agent work indicators
$agentGo = ($issues | Where-Object { $_.labels.name -contains 'agent:go' }).Count
$agentSprint = ($issues | Where-Object { $_.labels.name -contains 'agent:sprint' }).Count
if ($agentGo -gt 0 -or $agentSprint -gt 0) {
    Write-Host "`nAgent Work:" -ForegroundColor Cyan
    if ($agentGo -gt 0) {
        Write-Host "  [GO] agent:go: $agentGo" -ForegroundColor Green
    }
    if ($agentSprint -gt 0) {
        Write-Host "  [SPRINT] agent:sprint: $agentSprint" -ForegroundColor Yellow
    }
}

Write-Host ""
