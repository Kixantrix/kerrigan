# PowerShell Style Guide

This guide defines coding standards for PowerShell scripts in the Kerrigan repository to ensure cross-version compatibility and maintainability.

## Version Requirements

**All PowerShell scripts MUST support PowerShell 5.1 or later.**

PowerShell 5.1 is the default version on Windows systems and is still widely used. While PowerShell 7+ offers many improvements, we maintain compatibility with 5.1 to ensure our scripts work in all environments.

### Version Declaration

Every PowerShell script MUST include:

1. **#Requires directive** at the top of the file:
   ```powershell
   #Requires -Version 5.1
   ```

2. **Version check** at the beginning of script execution:
   ```powershell
   # Check PowerShell version
   if ($PSVersionTable.PSVersion.Major -lt 5 -or ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -lt 1)) {
       Write-Error "This script requires PowerShell 5.1 or later. Current version: $($PSVersionTable.PSVersion)"
       exit 1
   }
   ```

3. **Documentation** in the `.NOTES` section:
   ```powershell
   .NOTES
       Requires PowerShell 5.1 or later for compatibility.
   ```

## Character Encoding and Unicode

### The Problem

PowerShell 5.1 has limited support for multi-byte UTF-8 characters, particularly:
- Unicode emojis (🟢🔴⚠️⏸️📋📝)
- Special box-drawing characters (━)
- Other non-ASCII Unicode characters

These characters can cause parsing errors with cryptic error messages like "string terminator missing" that point to incorrect line numbers.

### The Solution

**Use ASCII characters for all code elements (string literals, variable names, etc.)**

#### Status Indicators

Instead of emojis, use ASCII alternatives:

| ❌ Don't Use | ✅ Use Instead | Meaning |
|-------------|----------------|---------|
| 🟢 | `[OK]` or `[READY]` | Success, ready |
| ✅ | `[OK]` | Approved, checked |
| 🔴 | `[!!]` or `[FAIL]` | Error, failure |
| ⚠️ | `[WARN]` | Warning |
| ⏸️ | `[PAUSE]` | Paused, stalled |
| 📋 | `[REVIEW]` | Needs review |
| 📝 | `[DRAFT]` | Draft status |
| 🤖 | `[BOT]` | Bot user |
| ❓ | `[?]` | Unknown |
| ⚪🟡 | `[GO]` `[SPRINT]` | Priority indicators |

#### Box Drawing and Separators

Instead of Unicode box-drawing characters, use ASCII:

| ❌ Don't Use | ✅ Use Instead |
|-------------|----------------|
| ━ | `=` |
| ─ | `-` |
| │ | `\|` |
| ┌┐└┘ | `+` at corners |

Example:
```powershell
# Bad (PowerShell 5.1 incompatible)
Write-Host "━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Good (PowerShell 5.1 compatible)
Write-Host "========================================" -ForegroundColor Cyan
```

### Where Unicode IS Acceptable

Unicode characters are safe to use in:
- **Output only** (via `Write-Host`, `Write-Output`, etc.)
- **Comments** (though ASCII is still preferred for clarity)
- **String literals** used exclusively for display (not parsed)

However, for consistency and to avoid confusion, **we recommend using ASCII throughout**.

## Color Coding

Use PowerShell's built-in color support for visual distinction:

```powershell
Write-Host "  [OK] Success message" -ForegroundColor Green
Write-Host "  [!!] Error message" -ForegroundColor Red
Write-Host "  [WARN] Warning message" -ForegroundColor Yellow
Write-Host "  [REVIEW] Info message" -ForegroundColor Blue
Write-Host "  [PAUSE] Neutral message" -ForegroundColor Magenta
```

## Script Header Template

Use this template for all PowerShell scripts:

```powershell
#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Brief description of what the script does

.DESCRIPTION
    Detailed description of the script's functionality

.PARAMETER ParameterName
    Description of the parameter

.EXAMPLE
    .\script-name.ps1
    Description of what this example does

.NOTES
    Requires PowerShell 5.1 or later for compatibility.
#>

param(
    # Parameters here
)

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5 -or ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -lt 1)) {
    Write-Error "This script requires PowerShell 5.1 or later. Current version: $($PSVersionTable.PSVersion)"
    exit 1
}

# Script logic here
```

## Error Handling

Always provide clear error messages that help users diagnose issues:

```powershell
$result = gh pr list 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error @"
Failed to list pull requests using the GitHub CLI ('gh').

Possible causes:
  - 'gh' is not installed or not available on PATH
  - You are not authenticated (run 'gh auth login')
  - There is a network or GitHub API issue

Details:
$result
"@
    exit 1
}
```

## Testing Recommendations

### Manual Testing

Test all scripts on:
1. **PowerShell 5.1** (Windows PowerShell) - Primary compatibility target
2. **PowerShell 7.x** (PowerShell Core) - Modern version

### Automated Testing (Future)

Planned improvements:
- CI matrix testing with PowerShell 5.1 and 7.x
- PSScriptAnalyzer integration for compatibility checking
- Automated Unicode character detection

## Common Pitfalls

### 1. Copy-Paste Emojis

**Problem**: Copying code with emojis from examples or other sources.

**Solution**: Always review pasted code and replace Unicode characters with ASCII equivalents.

### 2. IDE Auto-Formatting

**Problem**: Some IDEs may insert Unicode characters or change encoding.

**Solution**: Configure your IDE to use UTF-8 without BOM and ASCII-only characters.

### 3. Misleading Error Messages

**Problem**: PowerShell 5.1 reports "string terminator missing" at wrong line numbers when Unicode breaks parsing.

**Solution**: If you see this error, search for Unicode characters in the script using:
```bash
grep -P '[^\x00-\x7F]' script.ps1
```

## Summary

1. ✅ Always use ASCII characters in PowerShell scripts
2. ✅ Declare `#Requires -Version 5.1`
3. ✅ Add version check at script start
4. ✅ Use ASCII status indicators: `[OK]`, `[!!]`, `[WARN]`, etc.
5. ✅ Use ASCII separators: `=`, `-`, `|`, `+`
6. ✅ Document version requirements in `.NOTES`
7. ✅ Test on both PowerShell 5.1 and 7.x

## Related Documentation

- [CI Workflows](ci-workflows.md) - CI/CD configuration
- [Tools README](../tools/README.md) - PowerShell tools overview
- [Setup Guide](setup.md) - Development environment setup

## References

- [PowerShell 5.1 Documentation](https://docs.microsoft.com/en-us/powershell/scripting/windows-powershell/wmf/setup/install-configure)
- [PowerShell 7+ Documentation](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell)
- [PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer) - PowerShell linting tool
