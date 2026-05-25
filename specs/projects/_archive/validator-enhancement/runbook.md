# Runbook: Validator Enhancement

## Overview
This runbook covers operational aspects of the color-enhanced artifact validator.

## Running the Validator

### Standard Usage
```bash
# Run with automatic color detection
python tools/validators/check_artifacts.py

# Explicitly disable colors
python tools/validators/check_artifacts.py --no-color
```

### Environment Variables
- `CI=true` - Automatically disables colors in CI environments
- `NO_COLOR=1` - Standard env var to disable colors (any value works)

## Troubleshooting

### Colors not appearing in terminal
**Symptom**: Validator outputs plain text even in interactive terminal

**Possible causes**:
1. Terminal doesn't support ANSI codes (very rare with modern terminals)
2. `NO_COLOR` environment variable is set
3. Output is being piped/redirected

**Resolution**:
```bash
# Check if stdout is a TTY
python -c "import sys; print(sys.stdout.isatty())"

# Check environment variables
env | grep -i color
env | grep -i ci

# Unset NO_COLOR if needed
unset NO_COLOR
```

### Colors appearing in CI logs
**Symptom**: ANSI codes visible in GitHub Actions logs

**Possible causes**:
1. TTY detection failing in CI
2. Force-color flag being passed (shouldn't exist in this implementation)

**Resolution**:
- Check CI environment sets `CI=true`
- Verify stdout is not a TTY in CI: `[ -t 1 ] && echo "TTY" || echo "Not TTY"`

### GitHub Actions not detecting errors
**Symptom**: CI doesn't fail on validation errors

**Possible causes**:
1. Annotations format changed
2. Exit codes not preserved

**Resolution**:
- Check validator output contains `::error::` prefix
- Verify exit code: `echo $?` should be 1 on error
- Review changes to `fail()` function

## Rollback Procedure

If color support causes issues:

```bash
# Revert check_artifacts.py changes
git checkout HEAD^ -- tools/validators/check_artifacts.py

# Remove colors module
rm tools/validators/colors.py

# Run tests to confirm rollback
python tools/validators/check_artifacts.py
```

## Monitoring

No ongoing monitoring required. This is a local tool with no runtime dependencies.

## Maintenance

### Adding New Color Support
To add color to additional messages:

```python
from colors import colorize, GREEN, YELLOW, RED

# Colorize a message
print(colorize("Success!", GREEN))
```

### Updating Color Codes
Edit `tools/validators/colors.py` to change color constants.

Standard ANSI codes:
- Green: `\033[92m`
- Yellow: `\033[93m`
- Red: `\033[91m`
- Reset: `\033[0m`

## Dependencies
- Python 3.7+ (uses standard library only)
- No external packages required
