# Plan: Validator Enhancement

Milestones must end with green CI.

## Milestone 1: Color utilities module
**Status**: Pending

- [ ] Create `tools/validators/colors.py` with ANSI color constants
- [ ] Add TTY detection function
- [ ] Add environment variable detection (CI, NO_COLOR)
- [ ] Add color wrapper function
- [ ] Write unit tests for color module

**Done when**: Color module exists with tests, CI passes

## Milestone 2: Integrate colors into validator
**Status**: Pending

- [ ] Add argparse for `--no-color` flag to check_artifacts.py
- [ ] Import color utilities
- [ ] Replace error messages with colored versions
- [ ] Replace warning messages with colored versions
- [ ] Replace success message with colored version
- [ ] Verify GitHub Actions annotations still work

**Done when**: Validator outputs colors in TTY, CI passes

## Milestone 3: Testing and documentation
**Status**: Pending

- [ ] Add integration tests for colored output
- [ ] Test in CI environment (verify colors disabled)
- [ ] Test with `--no-color` flag
- [ ] Update validator documentation
- [ ] Add color support note to README if relevant

**Done when**: All tests pass, documentation updated, CI green
