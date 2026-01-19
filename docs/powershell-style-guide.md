# PowerShell Style Guide

This document provides guidelines for writing PowerShell scripts in Kerrigan to ensure cross-version compatibility and maintainability.

## Version Requirements

### Minimum Version
- **Require PowerShell 5.1** as the minimum version
- Add `#Requires -Version 5.1` at the top of every script
- Include version requirements in `.NOTES` section of script documentation

### Recommended Version
- **PowerShell 7+** is recommended for best compatibility and features
- Scripts should include a warning when running on PowerShell 5.1

### Version Check Template
```powershell
#Requires -Version 5.1

# Check PowerShell version and warn if using 5.1 (Unicode limitations)
if ($PSVersionTable.PSVersion.Major -eq 5) {
    Write-Warning "PowerShell 5.1 detected. For best compatibility, consider upgrading to PowerShell 7+"
}
```

## Character Encoding and Unicode

### ASCII vs Unicode
PowerShell 5.1 has known issues with multi-byte Unicode characters (emojis, box-drawing characters) in string literals.

**DO:**
- Use ASCII characters for status indicators: `[OK]`, `[!!]`, `[WARN]`, `[INFO]`
- Use standard ASCII box characters: `=`, `-`, `|`, `+`
- Use ASCII alternatives in string literals and script content

**DON'T:**
- Avoid Unicode emojis in string literals (green circle, red circle, warning sign, pause button, clipboard, memo)
- Avoid Unicode box-drawing characters in string literals (heavy horizontal line, vertical line, corners)
- Don't use multi-byte UTF-8 characters in script source code

### Output vs Script Content
It's acceptable to use Unicode in **output only** (via `Write-Host`, `Write-Output`) if the script will primarily run on PowerShell 7+, but script source code should remain ASCII-compatible.

```powershell
# Good: ASCII in script
$status = "[OK]"
Write-Host "Status: $status" -ForegroundColor Green

# Acceptable for output on PS7+ (but document the requirement)
if ($PSVersionTable.PSVersion.Major -ge 7) {
    Write-Host "Status: ✅" -ForegroundColor Green
}

# Bad: Unicode in script content (breaks PS5.1 parser)
$status = "🟢"  # Will cause parse errors in PS5.1
```

## Script Documentation

### Comment-Based Help
Every script should include comprehensive comment-based help:

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Brief description of what the script does

.DESCRIPTION
    Detailed description of the script's functionality and purpose

.PARAMETER ParameterName
    Description of each parameter

.EXAMPLE
    .\script-name.ps1
    Example of how to use the script

.EXAMPLE
    .\script-name.ps1 -Parameter Value
    Another example with parameters

.NOTES
    Requires PowerShell 5.1 or later
    For best results, use PowerShell 7+
#>
```

### Shebang Line
Always include the shebang for cross-platform compatibility:
```powershell
#!/usr/bin/env pwsh
```

## Error Handling

### Graceful Failures
Check for prerequisites and provide helpful error messages:

```powershell
# Check for required tools
$ghExists = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghExists) {
    Write-Error @"
GitHub CLI (gh) is not installed or not available on PATH.

Install it from: https://cli.github.com/

After installation, authenticate with: gh auth login
"@
    exit 1
}

# Check for authentication
$ghAuthStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "GitHub CLI is not authenticated. Run: gh auth login"
    exit 1
}
```

### Try-Catch for Parsing
Wrap JSON parsing and external commands in try-catch blocks:

```powershell
try {
    $data = $jsonOutput | ConvertFrom-Json
} catch {
    Write-Error "Failed to parse JSON data: $_"
    exit 1
}
```

## Style Conventions

### Naming
- Use **PascalCase** for function names and parameters
- Use **camelCase** for local variables
- Use **kebab-case** for script file names

### Formatting
- Indent with **4 spaces** (no tabs)
- Use spaces around operators: `$x -eq 5` not `$x-eq5`
- Place opening braces on the same line
- Use blank lines to separate logical sections

### Example
```powershell
param(
    [switch]$DryRun,
    [int]$Limit = 20
)

$itemCount = 0

foreach ($item in $items) {
    if ($DryRun) {
        Write-Host "Would process: $($item.name)"
    } else {
        Process-Item $item
        $itemCount++
    }
}

Write-Host "Processed $itemCount items"
```

## Common Patterns

### Parameter Validation
Use `ValidateSet` for enum-like parameters:
```powershell
param(
    [ValidateSet('open', 'closed', 'all')]
    [string]$State = 'open'
)
```

### Switch Parameters
Use switch parameters for boolean flags:
```powershell
param(
    [switch]$DryRun,
    [switch]$Verbose
)

if ($DryRun) {
    Write-Host "DRY RUN MODE - No actions will be taken" -ForegroundColor Magenta
}
```

### GitHub CLI Integration
```powershell
# Fetch data with error handling
$jsonOutput = gh pr list --json number,title,state --limit 50 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to fetch PRs: $jsonOutput"
    exit 1
}

$prs = $jsonOutput | ConvertFrom-Json
```

## Testing

### Manual Testing Checklist
Before committing PowerShell scripts:

1. ✅ Test on PowerShell 5.1 (if available)
2. ✅ Test on PowerShell 7+
3. ✅ Test with `gh` CLI installed and authenticated
4. ✅ Test with `gh` CLI not installed (error handling)
5. ✅ Test with `-DryRun` flag (if applicable)
6. ✅ Verify no Unicode parsing errors
7. ✅ Check error messages are helpful

### Testing Platforms
- **Windows**: PowerShell 5.1 (default) and PowerShell 7+
- **macOS**: PowerShell 7+ (install via Homebrew)
- **Linux**: PowerShell 7+ (install via package manager)

## References

### Installation
- **PowerShell 7+**: https://github.com/PowerShell/PowerShell#get-powershell
- **GitHub CLI**: https://cli.github.com/

### Documentation
- **PowerShell Docs**: https://docs.microsoft.com/en-us/powershell/
- **Comment-Based Help**: https://docs.microsoft.com/en-us/powershell/scripting/developer/help/writing-comment-based-help-topics
- **PowerShell Style Guide**: https://poshcode.gitbooks.io/powershell-practice-and-style/

## Related Feedback

This style guide addresses issues reported in:
- Feedback: `2026-01-17-71-powershell-unicode-compatibility.yaml`
- Issue: PowerShell 5.1 cannot parse Unicode emojis and box-drawing characters
