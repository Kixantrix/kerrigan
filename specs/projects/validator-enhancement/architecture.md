# Architecture: Validator Enhancement

## Overview
Add ANSI color support to check_artifacts.py using Python's standard library. The implementation will wrap existing print statements with color codes while maintaining full backward compatibility with CI and non-TTY environments.

## Components & interfaces

### Color Module (`tools/validators/colors.py`)
- **Purpose**: Centralize color code definitions and TTY detection
- **Functions**:
  - `should_use_color() -> bool`: Detect if colors are supported (TTY check, CI env check)
  - `colorize(text: str, color: str) -> str`: Wrap text in ANSI codes or return plain text
  - Color constants: `GREEN`, `YELLOW`, `RED`, `RESET`
- **Dependencies**: `sys`, `os` (standard library only)

### Modified Validator (`tools/validators/check_artifacts.py`)
- **Changes**:
  - Import color utilities at top
  - Replace `print(f"::error::{msg}")` with colored version
  - Replace `print(f"::warning::{msg}")` with colored version
  - Replace success message with colored version
  - Add `--no-color` CLI argument
- **Backward compatibility**: GitHub Actions `::error::` and `::warning::` annotations preserved

### CLI Argument Parsing
- Add argparse for `--no-color` flag
- Default behavior: auto-detect color support
- Override: explicit `--no-color` disables colors

## Tradeoffs

### ANSI codes vs. external library
- **Chosen**: ANSI codes via standard library
  - Pro: No dependencies, works everywhere Python works
  - Pro: Simple and maintainable
  - Con: No Windows legacy console support (acceptable since Windows Terminal and CI support ANSI)
- **Alternative**: colorama or termcolor
  - Pro: Better Windows legacy support
  - Con: External dependency violates project constraints

### GitHub Actions annotation format
- **Chosen**: Keep `::error::` and `::warning::` prefixes, add color to the message part
  - Pro: CI still parses annotations correctly
  - Pro: Local TTY gets colored output
  - Con: Slightly more complex string formatting
- **Alternative**: Remove annotations when colors are enabled
  - Pro: Cleaner output in TTY
  - Con: Breaks CI integration

## Security & privacy notes
- No security implications: changes are cosmetic only
- No user data handled
- No network access required
- Colors are client-side terminal rendering
