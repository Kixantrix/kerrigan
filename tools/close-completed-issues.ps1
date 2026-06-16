<#
.SYNOPSIS
  Close GitHub issues whose work is already merged, so the queue doesn't pile up.

.DESCRIPTION
  Dispatched cloud issues frequently are NOT auto-closed when their PR merges,
  because the Copilot-authored PR doesn't carry a "Closes #N" line. This tool
  finds open issues (default label 'agent:go') that have a MERGED connected or
  cross-referencing pull request and closes them with a comment citing the PR.

  Safe by default: runs read-only (dry-run) and just reports what it WOULD close.
  Pass -Apply to actually close them.

  Avoids the PowerShell papercuts that made the hand-rolled version a multi-line
  manual-approval chore: every gh call is isolated and stderr is swallowed, so a
  success-on-stderr line doesn't abort the loop.

.PARAMETER Label
  Issue label to filter by. Default 'agent:go'. Pass '' to scan all open issues.

.PARAMETER Apply
  Actually close the completed issues. Without it, dry-run (report only).

.PARAMETER Limit
  Max issues to scan. Default 100.

.EXAMPLE
  .\tools\close-completed-issues.ps1
  Dry-run: lists agent:go issues whose PR already merged.

.EXAMPLE
  .\tools\close-completed-issues.ps1 -Apply
  Closes those completed issues.
#>
[CmdletBinding()]
param(
  [string]$Label = 'agent:go',
  [switch]$Apply,
  [int]$Limit = 100
)

$ErrorActionPreference = 'Continue'

function Get-GhJson {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GhArgs)
  $out = & gh @GhArgs 2>$null
  if ($LASTEXITCODE -ne 0) { return $null }
  if (-not $out) { return $null }
  return ($out | ConvertFrom-Json)
}

# Resolve owner/repo from the current checkout.
$repoInfo = Get-GhJson repo view --json 'owner,name'
if (-not $repoInfo) {
  Write-Host "[FAIL] Could not resolve repo (is gh authenticated and cwd a repo?)." -ForegroundColor Red
  exit 1
}
$owner = $repoInfo.owner.login
$repo = $repoInfo.name

# List candidate open issues.
$listArgs = @('issue', 'list', '--state', 'open', '--limit', "$Limit", '--json', 'number,title')
if ($Label -ne '') { $listArgs += @('--label', $Label) }
$issues = Get-GhJson @listArgs
if (-not $issues) {
  Write-Host "No open issues$(if ($Label) { " with label '$Label'" })."
  exit 0
}

# GraphQL: for an issue, find connected / cross-referencing PRs and their merged state.
$query = @'
query($owner:String!, $repo:String!, $num:Int!){
  repository(owner:$owner, name:$repo){
    issue(number:$num){
      timelineItems(first:60, itemTypes:[CROSS_REFERENCED_EVENT, CONNECTED_EVENT]){
        nodes{
          __typename
          ... on CrossReferencedEvent { source { __typename ... on PullRequest { number merged } } }
          ... on ConnectedEvent { subject { __typename ... on PullRequest { number merged } } }
        }
      }
    }
  }
}
'@

$toClose = @()
foreach ($iss in $issues) {
  $raw = & gh api graphql -f query=$query -F owner=$owner -F repo=$repo -F num=$iss.number 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $raw) { continue }
  $data = $raw | ConvertFrom-Json
  $nodes = $data.data.repository.issue.timelineItems.nodes
  $mergedPr = $null
  foreach ($n in $nodes) {
    $pr = $null
    if ($n.__typename -eq 'CrossReferencedEvent') { $pr = $n.source }
    elseif ($n.__typename -eq 'ConnectedEvent') { $pr = $n.subject }
    if ($pr -and $pr.__typename -eq 'PullRequest' -and $pr.merged) { $mergedPr = $pr.number; break }
  }
  if ($mergedPr) {
    $toClose += [pscustomobject]@{ Issue = $iss.number; PR = $mergedPr; Title = $iss.title }
  }
}

if ($toClose.Count -eq 0) {
  Write-Host "[OK] No completed-but-open issues found$(if ($Label) { " (label '$Label')" })." -ForegroundColor Green
  exit 0
}

Write-Host ("Found {0} completed issue(s):" -f $toClose.Count) -ForegroundColor Cyan
$toClose | ForEach-Object { Write-Host ("  #{0}  (merged via #{1})  {2}" -f $_.Issue, $_.PR, $_.Title) }

if (-not $Apply) {
  Write-Host "`nDry-run. Re-run with -Apply to close them." -ForegroundColor Yellow
  exit 0
}

foreach ($c in $toClose) {
  & gh issue close $c.Issue --reason completed --comment ("Completed via #{0} (merged). Auto-closed by tools/close-completed-issues.ps1." -f $c.PR) 2>$null
  if ($LASTEXITCODE -eq 0) { Write-Host ("[OK] closed #{0} (via #{1})" -f $c.Issue, $c.PR) -ForegroundColor Green }
  else { Write-Host ("[FAIL] could not close #{0}" -f $c.Issue) -ForegroundColor Red }
}
