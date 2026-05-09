#!/usr/bin/env pwsh

$ErrorActionPreference = 'Stop'

<#
.SYNOPSIS
    Migrates legacy Kerrigan v1 issue labels to the v2 label set using gh.

.DESCRIPTION
    Mapping logic mirrors scripts/migrate-v1-to-v2.sh:
    - Remove legacy v1 labels:
      role:swe, role:architect, role:spec, role:testing, role:debugging,
      role:triage, agent:sprint, agent:triage, agent-ready
    - Only one label maps forward: agent-ready -> agent:go
    - The mapping happens only when the issue is OPEN and has no assignees.
    - All other legacy labels are removed with no replacement.
#>

$V1Labels = @(
    'role:swe',
    'role:architect',
    'role:spec',
    'role:testing',
    'role:debugging',
    'role:triage',
    'agent:sprint',
    'agent:triage',
    'agent-ready'
)

$dryRun = $false

function Show-Usage {
    Write-Output 'Usage: scripts/migrate-v1-to-v2.ps1 [--dry-run]'
    Write-Output ''
    Write-Output 'Migrates legacy Kerrigan v1 issue labels to the v2 label set using the GitHub CLI.'
}

for ($i = 0; $i -lt $args.Count; $i++) {
    switch ($args[$i]) {
        '--dry-run' {
            $dryRun = $true
        }
        '-h' {
            Show-Usage
            exit 0
        }
        '--help' {
            Show-Usage
            exit 0
        }
        default {
            Write-Error "Unknown argument: $($args[$i])"
            exit 1
        }
    }
}

$issueLines = & gh issue list `
    --state all `
    --limit 1000 `
    --json number,state,labels,assignees `
    --template '{{range .}}{{.number}}{{"\t"}}{{.state}}{{"\t"}}{{len .assignees}}{{"\t"}}{{range $i, $label := .labels}}{{if $i}},{{end}}{{$label.name}}{{end}}{{"\n"}}{{end}}'

if (-not $issueLines) {
    Write-Output 'No issues found.'
    exit 0
}

if ($issueLines -is [string]) {
    $issueLines = @($issueLines)
}

$changed = 0

foreach ($line in $issueLines) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $parts = $line -split "`t", 4
    $number = $parts[0]
    $state = $parts[1]
    $assigneeCount = $parts[2]
    $labelsCsv = if ($parts.Count -ge 4) { $parts[3] } else { '' }
    $labels = if ([string]::IsNullOrEmpty($labelsCsv)) { @() } else { $labelsCsv -split ',' }

    $removeLabels = @()
    foreach ($label in $V1Labels) {
        if ($labels -contains $label) {
            $removeLabels += $label
        }
    }

    if ($removeLabels.Count -eq 0) {
        continue
    }

    $addLabels = @()
    if (
        ($labels -contains 'agent-ready') -and
        $state -eq 'OPEN' -and
        $assigneeCount -eq '0' -and
        -not ($labels -contains 'agent:go')
    ) {
        $addLabels += 'agent:go'
    }

    $removeCsv = $removeLabels -join ','
    $addCsv = $addLabels -join ','

    if ($dryRun) {
        if ($addCsv) {
            Write-Output "DRY RUN #$number remove=$removeCsv add=$addCsv"
        } else {
            Write-Output "DRY RUN #$number remove=$removeCsv"
        }
    } else {
        $editArgs = @('issue', 'edit', $number, '--remove-label', $removeCsv)
        if ($addCsv) {
            $editArgs += @('--add-label', $addCsv)
        }
        & gh @editArgs | Out-Null

        if ($addCsv) {
            Write-Output "UPDATED #$number remove=$removeCsv add=$addCsv"
        } else {
            Write-Output "UPDATED #$number remove=$removeCsv"
        }
    }

    $changed++
}

if ($changed -eq 0) {
    Write-Output 'No legacy labels found.'
} else {
    Write-Output "Processed $changed issue(s)."
}
