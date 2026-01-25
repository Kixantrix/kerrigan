<#
.SYNOPSIS
    Upgrade Kerrigan components from upstream repository.

.DESCRIPTION
    Fetches latest changes from the main Kerrigan repository and allows selective
    component upgrades. Preserves project-specific customizations and updates the
    version manifest.

.PARAMETER Components
    Comma-separated list of components to upgrade.
    Available: workflows, prompts, validators, skills, playbooks, tools, all
    Default: all

.PARAMETER UpstreamRepo
    URL of the upstream Kerrigan repository.
    Default: https://github.com/Kixantrix/kerrigan

.PARAMETER UpstreamBranch
    Branch to fetch from upstream.
    Default: main

.PARAMETER ShowDiff
    Show diff of what would change without applying.

.PARAMETER DryRun
    Show what would be upgraded without applying changes.

.PARAMETER Force
    Force upgrade even if there are uncommitted changes.

.EXAMPLE
    ./upgrade-kerrigan.ps1 -ShowDiff
    Show what would change in all components

.EXAMPLE
    ./upgrade-kerrigan.ps1 -Components workflows,prompts
    Upgrade only workflows and prompts

.EXAMPLE
    ./upgrade-kerrigan.ps1 -DryRun
    See what would be upgraded without making changes

.EXAMPLE
    ./upgrade-kerrigan.ps1 -Components all
    Upgrade all components
#>

param(
    [string]$Components = "all",
    [string]$UpstreamRepo = "https://github.com/Kixantrix/kerrigan",
    [string]$UpstreamBranch = "main",
    [switch]$ShowDiff,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Component path mapping
$ComponentPaths = @{
    "workflows" = @(".github/workflows")
    "prompts" = @(".github/agents")
    "validators" = @("tools/validators")
    "skills" = @("skills")
    "playbooks" = @("playbooks")
    "tools" = @("tools")
}

# Excluded files from upgrade (project-specific customizations)
$ExcludePatterns = @(
    "kerrigan-version.json",
    "**/TEMPLATE.yaml",
    ".github/workflows/custom-*.yml"
)

function Get-CurrentVersion {
    $versionFile = "kerrigan-version.json"
    if (Test-Path $versionFile) {
        $versionData = Get-Content $versionFile -Raw | ConvertFrom-Json
        return $versionData
    }
    return $null
}

function Write-Banner {
    param([string]$Text)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Test-GitRepository {
    $gitDir = ".git"
    if (-not (Test-Path $gitDir)) {
        Write-Error "Not a git repository. Please run this from the root of your Kerrigan installation."
        exit 1
    }
}

function Test-CleanWorkingDirectory {
    $status = git status --porcelain
    if ($status -and -not $Force) {
        Write-Error "Working directory has uncommitted changes. Commit or stash them first, or use -Force to override."
        Write-Host "`nUncommitted changes:" -ForegroundColor Yellow
        Write-Host $status
        exit 1
    }
}

function Add-UpstreamRemote {
    param([string]$Repo)
    
    # Check if upstream remote exists
    $remotes = git remote
    if ($remotes -notcontains "kerrigan-upstream") {
        Write-Host "Adding upstream remote: $Repo" -ForegroundColor Cyan
        git remote add kerrigan-upstream $Repo
    } else {
        Write-Host "Updating upstream remote URL: $Repo" -ForegroundColor Cyan
        git remote set-url kerrigan-upstream $Repo
    }
}

function Get-UpstreamChanges {
    param([string]$Branch)
    
    Write-Host "Fetching changes from upstream/$Branch..." -ForegroundColor Cyan
    git fetch kerrigan-upstream $Branch --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to fetch from upstream"
        exit 1
    }
}

function Get-ComponentList {
    param([string]$ComponentsArg)
    
    if ($ComponentsArg -eq "all") {
        return $ComponentPaths.Keys
    }
    
    $components = $ComponentsArg -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ }
    
    # Validate components
    foreach ($component in $components) {
        if ($component -notin $ComponentPaths.Keys) {
            Write-Error "Unknown component: $component`nAvailable: $($ComponentPaths.Keys -join ', ')"
            exit 1
        }
    }
    
    return $components
}

function Show-ComponentDiff {
    param(
        [string]$Component,
        [string[]]$Paths,
        [string]$UpstreamRef
    )
    
    Write-Host "`n--- Component: $Component ---" -ForegroundColor Yellow
    
    $hasDiff = $false
    foreach ($path in $Paths) {
        if (Test-Path $path) {
            # Show diff for this path
            $diff = git diff HEAD..$UpstreamRef -- $path
            if ($diff) {
                $hasDiff = $true
                Write-Host "`nChanges in $path`:" -ForegroundColor Cyan
                Write-Host $diff
            }
        } else {
            Write-Host "Path $path does not exist in current installation" -ForegroundColor Gray
        }
    }
    
    if (-not $hasDiff) {
        Write-Host "No changes" -ForegroundColor Green
    }
    
    return $hasDiff
}

function Update-Component {
    param(
        [string]$Component,
        [string[]]$Paths,
        [string]$UpstreamRef
    )
    
    Write-Host "Updating component: $Component" -ForegroundColor Cyan
    
    foreach ($path in $Paths) {
        if (Test-Path $path) {
            Write-Host "  Checking out $path from upstream..." -ForegroundColor Gray
            git checkout $UpstreamRef -- $path
            
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Failed to checkout $path"
            }
        } else {
            Write-Host "  Path $path does not exist, skipping" -ForegroundColor Gray
        }
    }
}

function Update-VersionManifest {
    param(
        [string[]]$UpdatedComponents,
        [string]$UpstreamVersion
    )
    
    $versionFile = "kerrigan-version.json"
    $versionData = Get-CurrentVersion
    
    if (-not $versionData) {
        Write-Warning "Version manifest not found. Creating new one."
        $versionData = @{
            "version" = $UpstreamVersion
            "installed" = (Get-Date -Format "yyyy-MM-dd")
            "components" = @{}
            "upstream" = @{
                "repository" = $UpstreamRepo
                "branch" = $UpstreamBranch
            }
        }
    }
    
    # Update component versions
    foreach ($component in $UpdatedComponents) {
        $versionData.components[$component] = $UpstreamVersion
    }
    
    # Update main version and last updated
    $versionData.version = $UpstreamVersion
    $versionData | Add-Member -NotePropertyName "last_updated" -NotePropertyValue (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ") -Force
    
    # Save back to file
    $versionData | ConvertTo-Json -Depth 10 | Set-Content $versionFile -Encoding UTF8
    
    Write-Host "✓ Updated version manifest" -ForegroundColor Green
}

function Get-UpstreamVersion {
    param([string]$UpstreamRef)
    
    # Try to read version from upstream's kerrigan-version.json
    try {
        $content = git show "${UpstreamRef}:kerrigan-version.json" 2>$null
        if ($content) {
            $versionData = $content | ConvertFrom-Json
            return $versionData.version
        }
    } catch {
        # Fallback to reading from CHANGELOG.md
        try {
            $changelog = git show "${UpstreamRef}:CHANGELOG.md" 2>$null
            if ($changelog -match "## \[(\d+\.\d+\.\d+)\]") {
                return $Matches[1]
            }
        } catch {
            # Ignore
        }
    }
    
    return "unknown"
}

# Main execution
Write-Banner "Kerrigan Upgrade Tool"

# Verify we're in a git repository
Test-GitRepository

# Show current version
$currentVersion = Get-CurrentVersion
if ($currentVersion) {
    Write-Host "Current version: $($currentVersion.version)" -ForegroundColor White
    Write-Host "Installed: $($currentVersion.installed)" -ForegroundColor Gray
    Write-Host "Components:"
    foreach ($comp in $currentVersion.components.PSObject.Properties) {
        Write-Host "  - $($comp.Name): $($comp.Value)" -ForegroundColor Gray
    }
} else {
    Write-Warning "No version manifest found (kerrigan-version.json)"
    Write-Host "This might be a fresh installation or an older version."
}

# Check for clean working directory
if (-not $DryRun -and -not $ShowDiff) {
    Test-CleanWorkingDirectory
}

# Add/update upstream remote
Add-UpstreamRemote -Repo $UpstreamRepo

# Fetch upstream changes
Get-UpstreamChanges -Branch $UpstreamBranch

# Get upstream version
$upstreamRef = "kerrigan-upstream/$UpstreamBranch"
$upstreamVersion = Get-UpstreamVersion -UpstreamRef $upstreamRef
Write-Host "`nUpstream version: $upstreamVersion" -ForegroundColor White

# Parse components to upgrade
$componentsToUpgrade = Get-ComponentList -ComponentsArg $Components

Write-Host "`nComponents to check: $($componentsToUpgrade -join ', ')" -ForegroundColor Yellow

# Show diffs or apply upgrades
$hasChanges = $false
$changedComponents = @()

foreach ($component in $componentsToUpgrade) {
    $paths = $ComponentPaths[$component]
    
    if ($ShowDiff -or $DryRun) {
        $diffFound = Show-ComponentDiff -Component $component -Paths $paths -UpstreamRef $upstreamRef
        if ($diffFound) {
            $hasChanges = $true
            $changedComponents += $component
        }
    } else {
        $diffOutput = git diff --name-only HEAD..$upstreamRef -- $paths
        if ($diffOutput) {
            $hasChanges = $true
            $changedComponents += $component
            Update-Component -Component $component -Paths $paths -UpstreamRef $upstreamRef
        } else {
            Write-Host "Component $component is up to date" -ForegroundColor Green
        }
    }
}

if ($DryRun -or $ShowDiff) {
    if ($hasChanges) {
        Write-Host "`n✓ Changes found in: $($changedComponents -join ', ')" -ForegroundColor Yellow
        if ($DryRun) {
            Write-Host "`n[DRY RUN] No changes applied. Run without -DryRun to upgrade." -ForegroundColor Cyan
        }
    } else {
        Write-Host "`n✓ All components are up to date" -ForegroundColor Green
    }
} else {
    if ($hasChanges) {
        Write-Host "`n✓ Updated components: $($changedComponents -join ', ')" -ForegroundColor Green
        
        # Update version manifest
        Update-VersionManifest -UpdatedComponents $changedComponents -UpstreamVersion $upstreamVersion
        
        Write-Host "`nNext steps:" -ForegroundColor Yellow
        Write-Host "1. Review the changes: git diff" -ForegroundColor White
        Write-Host "2. Test your project to ensure compatibility" -ForegroundColor White
        Write-Host "3. Commit the changes: git add . && git commit -m 'Upgrade Kerrigan to $upstreamVersion'" -ForegroundColor White
        Write-Host "4. Check CHANGELOG.md for any breaking changes" -ForegroundColor White
    } else {
        Write-Host "`n✓ All components are up to date" -ForegroundColor Green
    }
}

Write-Host ""
