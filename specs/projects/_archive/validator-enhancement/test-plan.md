# Test Plan: Validator Enhancement

## Testing Strategy

This project requires both unit and integration testing to ensure color support works correctly across environments.

## Unit Tests

### colors.py Module Tests
**Location**: `tests/validators/test_colors.py`

**Coverage goals**: 100% of colors.py functions

**Test cases**:
1. `test_should_use_color_tty()` - Verify TTY detection
2. `test_should_use_color_ci_env()` - Verify CI environment disables colors
3. `test_should_use_color_no_color_env()` - Verify NO_COLOR env var
4. `test_colorize_with_colors()` - Verify ANSI codes added when colors enabled
5. `test_colorize_without_colors()` - Verify plain text when colors disabled
6. `test_color_constants()` - Verify color constants are valid ANSI codes

**Tools**: pytest (if available) or Python's unittest

## Integration Tests

### Validator Output Tests
**Location**: `tests/validators/test_check_artifacts_colors.py`

**Test cases**:
1. `test_success_message_colored()` - Run validator on valid project, check for green output
2. `test_error_message_colored()` - Run validator on invalid project, check for red output
3. `test_warning_message_colored()` - Trigger warning, check for yellow output
4. `test_no_color_flag()` - Run with `--no-color`, verify plain output
5. `test_github_actions_annotations()` - Verify `::error::` and `::warning::` preserved

**Approach**: Subprocess execution with captured output, parse for ANSI codes

## Manual Testing

### Local Terminal Testing
1. Run `python tools/validators/check_artifacts.py` in terminal
2. Verify colors appear for success, warnings, errors
3. Run with `--no-color`, verify no colors
4. Set `NO_COLOR=1`, verify no colors

### CI Testing
1. Push changes to trigger CI
2. Review Actions logs
3. Verify no ANSI codes in log output
4. Verify GitHub Actions still detects errors/warnings

## Regression Testing

### Existing Validation Tests
- All current validator behavior must remain unchanged
- Run existing test suite (if any) before and after changes
- Validate same projects pass/fail as before

## Coverage Goals

- **Unit tests**: 100% of colors.py
- **Integration tests**: Core validator functions (fail, warn, main)
- **Manual testing**: Required for visual verification

## Test Execution

```bash
# Run unit tests
python -m pytest tests/validators/test_colors.py -v

# Run integration tests
python -m pytest tests/validators/test_check_artifacts_colors.py -v

# Run all validator tests
python -m pytest tests/validators/ -v --cov=tools/validators

# Manual test
python tools/validators/check_artifacts.py

# Manual test with no color
python tools/validators/check_artifacts.py --no-color
```

## Success Criteria

- All unit tests pass
- All integration tests pass
- Manual testing confirms visual output
- CI remains green
- No regressions in existing validation logic
