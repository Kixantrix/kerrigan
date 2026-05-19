#!/usr/bin/env pwsh

$ErrorActionPreference = 'Stop'

function Show-Usage {
    Write-Output 'Usage:'
    Write-Output '  scripts/worktree.ps1 new <task-id> [-Bootstrap]'
    Write-Output '  scripts/worktree.ps1 list'
    Write-Output '  scripts/worktree.ps1 remove <task-id> [-Force]'
    Write-Output '  scripts/worktree.ps1 prune'
    Write-Output '  scripts/worktree.ps1 -Help'
    Write-Output ''
    Write-Output 'Verbs:'
    Write-Output '  new       Create ../<repo>-worktrees/<task-id> on branch task/<task-id> from current HEAD.'
    Write-Output '  list      List active worktrees with branch and dirty state.'
    Write-Output '  remove    Remove worktree and delete task/<task-id> branch (warn if unmerged unless -Force).'
    Write-Output '  prune     Run git worktree prune.'
    Write-Output ''
    Write-Output 'Flags:'
    Write-Output '  -Bootstrap  (new) Run dependency install commands in the new worktree.'
    Write-Output '  -Force      (remove) Remove even if worktree is dirty and delete unmerged branch.'
}

function Write-ErrorExit {
    param([string]$Message)

    [Console]::Error.WriteLine("Error: $Message")
    exit 1
}

function Write-WarningStderr {
    param([string]$Message)

    [Console]::Error.WriteLine("Warning: $Message")
}

function Get-RepoRoot {
    $root = (& git rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
        Write-ErrorExit 'Not inside a git repository.'
    }

    return $root.Trim()
}

function Test-HeadAttached {
    & git symbolic-ref --quiet HEAD > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorExit 'HEAD is detached. Checkout a branch before creating a worktree.'
    }
}

function Get-WorktreeParent {
    param([string]$RepoRoot)

    $parent = Split-Path $RepoRoot -Parent
    $leaf = Split-Path $RepoRoot -Leaf
    return ($parent + '/' + $leaf + '-worktrees')
}

function Test-BranchExists {
    param([string]$Branch)

    & git show-ref --verify --quiet "refs/heads/$Branch"
    return ($LASTEXITCODE -eq 0)
}

function Warn-LongPathsIfNeeded {
    $value = (& git config --get core.longpaths 2>$null)
    if ($LASTEXITCODE -ne 0 -or $value.Trim() -ne 'true') {
        Write-WarningStderr 'git core.longpaths is not true. On Windows, run: git config core.longpaths true'
    }
}

function Invoke-Bootstrap {
    param([string]$WorktreePath)

    if (Test-Path (Join-Path $WorktreePath 'package.json') -PathType Leaf) {
        if (Test-Path (Join-Path $WorktreePath 'package-lock.json') -PathType Leaf) {
            Push-Location $WorktreePath
            try {
                & npm ci
            }
            finally {
                Pop-Location
            }
        }
        else {
            Push-Location $WorktreePath
            try {
                & npm install
            }
            finally {
                Pop-Location
            }
        }
    }

    if (Test-Path (Join-Path $WorktreePath 'requirements.txt') -PathType Leaf) {
        Push-Location $WorktreePath
        try {
            & python -m pip install -r requirements.txt
        }
        finally {
            Pop-Location
        }
    }

    if (Test-Path (Join-Path $WorktreePath 'pyproject.toml') -PathType Leaf) {
        Push-Location $WorktreePath
        try {
            & python -m pip install -e .
        }
        finally {
            Pop-Location
        }
    }
}

function Invoke-New {
    param(
        [string]$TaskId,
        [bool]$Bootstrap
    )

    if ([string]::IsNullOrWhiteSpace($TaskId)) {
        Write-ErrorExit 'Missing <task-id> for new.'
    }

    $repoRoot = Get-RepoRoot
    Test-HeadAttached
    Warn-LongPathsIfNeeded

    $branch = "task/$TaskId"
    $parent = Get-WorktreeParent -RepoRoot $repoRoot
    $target = Join-Path $parent $TaskId

    if (Test-BranchExists -Branch $branch) {
        Write-ErrorExit "Branch already exists: $branch"
    }

    if (Test-Path $target) {
        Write-ErrorExit "Target directory already exists: $target"
    }

    New-Item -Path $parent -ItemType Directory -Force | Out-Null
    & git worktree add -b $branch $target HEAD
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorExit 'git worktree add failed.'
    }

    $envPath = Join-Path $repoRoot '.env'
    if (Test-Path $envPath -PathType Leaf) {
        Copy-Item -Path $envPath -Destination (Join-Path $target '.env') -Force
    }

    if ($Bootstrap) {
        Invoke-Bootstrap -WorktreePath $target
    }

    Write-Output $target
}

function Invoke-List {
    $null = Get-RepoRoot

    $worktreePath = $null
    $worktreeBranch = ''
    $lines = & git worktree list --porcelain

    function Write-WorktreeRow {
        param(
            [string]$PathValue,
            [string]$BranchValue
        )

        if (-not $PathValue) {
            return
        }

        $status = (& git -C $PathValue status --porcelain 2>$null)
        $dirtyState = if ([string]::IsNullOrWhiteSpace(($status -join ''))) { 'clean' } else { 'dirty' }
        if ([string]::IsNullOrWhiteSpace($BranchValue)) {
            $BranchValue = 'detached'
        }
        Write-Output ("{0}`t{1}`t{2}" -f $PathValue, $BranchValue, $dirtyState)
    }

    foreach ($line in $lines) {
        if ($line.StartsWith('worktree ')) {
            $worktreePath = $line.Substring(9)
            $worktreeBranch = ''
            continue
        }

        if ($line.StartsWith('branch ')) {
            $worktreeBranch = $line.Substring(7)
            continue
        }

        if ($line -eq 'detached') {
            $worktreeBranch = 'detached'
            continue
        }

        if ([string]::IsNullOrWhiteSpace($line) -and $worktreePath) {
            Write-WorktreeRow -PathValue $worktreePath -BranchValue $worktreeBranch
            $worktreePath = $null
            $worktreeBranch = ''
        }
    }

    if ($worktreePath) {
        Write-WorktreeRow -PathValue $worktreePath -BranchValue $worktreeBranch
    }
}

function Invoke-Remove {
    param(
        [string]$TaskId,
        [bool]$Force
    )

    if ([string]::IsNullOrWhiteSpace($TaskId)) {
        Write-ErrorExit 'Missing <task-id> for remove.'
    }

    $repoRoot = Get-RepoRoot
    $parent = Get-WorktreeParent -RepoRoot $repoRoot
    $target = Join-Path $parent $TaskId
    $branch = "task/$TaskId"

    if (-not (Test-Path $target -PathType Container)) {
        Write-ErrorExit "Worktree directory does not exist: $target"
    }

    if ($Force) {
        & git worktree remove --force $target
    }
    else {
        & git worktree remove $target
    }

    if ($LASTEXITCODE -ne 0) {
        Write-ErrorExit 'git worktree remove failed.'
    }

    if (Test-BranchExists -Branch $branch) {
        & git merge-base --is-ancestor $branch HEAD > $null 2>&1
        $isMerged = ($LASTEXITCODE -eq 0)

        if ($isMerged) {
            & git branch -d $branch
            if ($LASTEXITCODE -ne 0) {
                Write-ErrorExit "Failed to delete merged branch: $branch"
            }
        }
        elseif ($Force) {
            & git branch -D $branch
            if ($LASTEXITCODE -ne 0) {
                Write-ErrorExit "Failed to force-delete branch: $branch"
            }
        }
        else {
            Write-WarningStderr "Branch $branch is unmerged; leaving branch in place (use -Force to delete)."
        }
    }
}

function Invoke-Prune {
    $null = Get-RepoRoot
    & git worktree prune
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorExit 'git worktree prune failed.'
    }
}

$verb = if ($args.Count -gt 0) { $args[0] } else { '' }

if ($verb -eq '-Help' -or $verb -eq '--help' -or $verb -eq '-h' -or [string]::IsNullOrWhiteSpace($verb)) {
    Show-Usage
    exit 0
}

switch ($verb) {
    'new' {
        $taskId = if ($args.Count -ge 2) { $args[1] } else { '' }
        $bootstrap = $false

        for ($i = 2; $i -lt $args.Count; $i++) {
            switch ($args[$i]) {
                '-Bootstrap' { $bootstrap = $true }
                '--bootstrap' { $bootstrap = $true }
                '-Help' { Show-Usage; exit 0 }
                '--help' { Show-Usage; exit 0 }
                default { Write-ErrorExit "Unknown argument for new: $($args[$i])" }
            }
        }

        Invoke-New -TaskId $taskId -Bootstrap $bootstrap
    }
    'list' {
        if ($args.Count -gt 1) {
            Write-ErrorExit 'list does not accept additional arguments.'
        }
        Invoke-List
    }
    'remove' {
        $taskId = if ($args.Count -ge 2) { $args[1] } else { '' }
        $force = $false

        for ($i = 2; $i -lt $args.Count; $i++) {
            switch ($args[$i]) {
                '-Force' { $force = $true }
                '--force' { $force = $true }
                '-Help' { Show-Usage; exit 0 }
                '--help' { Show-Usage; exit 0 }
                default { Write-ErrorExit "Unknown argument for remove: $($args[$i])" }
            }
        }

        Invoke-Remove -TaskId $taskId -Force $force
    }
    'prune' {
        if ($args.Count -gt 1) {
            Write-ErrorExit 'prune does not accept additional arguments.'
        }
        Invoke-Prune
    }
    default {
        Write-ErrorExit "Unknown verb: $verb"
    }
}
