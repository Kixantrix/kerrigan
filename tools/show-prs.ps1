#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Display open pull requests with their status and details in a formatted table.

.DESCRIPTION
    Fetches all open PRs from the repository and displays them in an easy-to-read
    table format showing PR number, title, author, draft status, reviews, and mergeable state.

.PARAMETER State
    PR state to filter by. Default: open. Options: open, closed, merged, all

.PARAMETER Limit
    Maximum number of PRs to display. Default: 20

.EXAMPLE
    .\tools\show-prs.ps1
    Shows all open PRs

.EXAMPLE
    .\tools\show-prs.ps1 -State all -Limit 50
    Shows all PRs (open, closed, merged), up to 50

.NOTES
    Requires PowerShell 5.1 or later for compatibility.
#>

param(
    [ValidateSet('open', 'closed', 'merged', 'all')]
    [string]$State = 'open',
    
    [int]$Limit = 20
)

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5 -or ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -lt 1)) {
    Write-Error "This script requires PowerShell 5.1 or later. Current version: $($PSVersionTable.PSVersion)"
    exit 1
}

# Fetch PRs from GitHub
Write-Host "Fetching $State pull requests..." -ForegroundColor Cyan

$prs = gh pr list --state $State --limit $Limit --json number,title,author,isDraft,reviews,mergeable,createdAt,updatedAt,labels | ConvertFrom-Json

if ($prs.Count -eq 0) {
    Write-Host "`nNo $State pull requests found." -ForegroundColor Yellow
    exit 0
}

# Format PRs for display
$formatted = $prs | ForEach-Object {
    $reviewCount = $_.reviews.Count
    $isBot = $_.author.is_bot
    $authorName = $_.author.login
    
    # Status indicator (using ASCII for PowerShell 5.1 compatibility)
    $status = if ($_.isDraft) { '[DRAFT]' }
              elseif ($_.mergeable -eq 'CONFLICTING') { '[WARN]' }
              elseif ($_.mergeable -eq 'MERGEABLE' -and $reviewCount -gt 0) { '[OK]' }
              elseif ($_.mergeable -eq 'MERGEABLE') { '[READY]' }
              else { '[?]' }
    
    # Author indicator
    $author = if ($isBot) { "[BOT] $authorName" } else { $authorName }
    
    [PSCustomObject]@{
        ' ' = $status
        '#' = $_.number
        Title = $_.title
        Author = $author
        Draft = if ($_.isDraft) { 'Yes' } else { '-' }
        Reviews = if ($reviewCount -gt 0) { $reviewCount } else { '-' }
        Mergeable = switch ($_.mergeable) {
            'MERGEABLE' { 'Yes' }
            'CONFLICTING' { 'Conflict' }
            'UNKNOWN' { '?' }
            default { '-' }
        }
        Updated = (Get-Date $_.updatedAt).ToString('MMM dd HH:mm')
    }
}

# Display results
Write-Host "`n$($prs.Count) $State pull request(s) found:" -ForegroundColor Green
Write-Host ""

$formatted | Format-Table -AutoSize

# Summary
Write-Host "`nSummary:" -ForegroundColor Cyan

$drafts = ($prs | Where-Object { $_.isDraft }).Count
$readyForReview = $prs.Count - $drafts
$mergeable = ($prs | Where-Object { $_.mergeable -eq 'MERGEABLE' }).Count
$conflicts = ($prs | Where-Object { $_.mergeable -eq 'CONFLICTING' }).Count
$reviewed = ($prs | Where-Object { $_.reviews.Count -gt 0 }).Count
$botPRs = ($prs | Where-Object { $_.author.is_bot }).Count

Write-Host "  Draft: $drafts" -ForegroundColor Gray
Write-Host "  Ready for review: $readyForReview" -ForegroundColor Gray
Write-Host "  Mergeable: $mergeable" -ForegroundColor $(if ($mergeable -eq $prs.Count) { 'Green' } else { 'Gray' })
Write-Host "  Conflicts: $conflicts" -ForegroundColor $(if ($conflicts -gt 0) { 'Yellow' } else { 'Gray' })
Write-Host "  Reviewed: $reviewed" -ForegroundColor Gray
Write-Host "  Bot PRs: $botPRs" -ForegroundColor Gray

# Legend
Write-Host "`nStatus Legend:" -ForegroundColor Cyan
Write-Host "  [DRAFT]  Draft PR" -ForegroundColor Gray
Write-Host "  [READY]  Ready to review" -ForegroundColor Gray
Write-Host "  [OK]     Reviewed and mergeable" -ForegroundColor Gray
Write-Host "  [WARN]   Has conflicts" -ForegroundColor Gray
Write-Host "  [?]      Status unknown" -ForegroundColor Gray

Write-Host ""
