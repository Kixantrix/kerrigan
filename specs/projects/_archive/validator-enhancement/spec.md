# Spec: Validator Enhancement

## Goal
Add color-coded output to the artifact validator to make validation errors more visible and easier to diagnose.

## Scope
- Add colored output for success (green), warnings (yellow), and errors (red)
- Maintain backward compatibility with CI systems
- Use standard ANSI color codes
- Add a `--no-color` flag for environments that don't support colors

## Non-goals
- HTML output or other complex formatting
- Progress bars or animated output
- Logging to files (stays stdout/stderr only)
- Changing the validation logic itself

## Acceptance criteria
- Successful validation messages appear in green
- Warning messages appear in yellow
- Error messages appear in red
- Colors are automatically disabled in non-TTY environments (e.g., CI)
- `--no-color` flag explicitly disables colors
- All existing validation tests continue to pass
- No external dependencies added (uses Python standard library only)
