# Tasks: Validator Enhancement

## Milestone 1: Color utilities module

- [ ] Task: Create colors.py module
  - Done when: `tools/validators/colors.py` exists with ANSI color constants (GREEN, YELLOW, RED, RESET)
  - Links: architecture.md (Color Module section)

- [ ] Task: Implement TTY detection
  - Done when: `should_use_color()` function checks `sys.stdout.isatty()` and returns bool
  - Links: architecture.md, acceptance-tests.md (auto-disable test)

- [ ] Task: Implement environment detection
  - Done when: `should_use_color()` checks CI, NO_COLOR env vars and disables colors appropriately
  - Links: architecture.md, acceptance-tests.md (CI test)

- [ ] Task: Implement colorize function
  - Done when: `colorize(text, color)` returns colored text in TTY or plain text otherwise
  - Links: architecture.md

- [ ] Task: Write color module tests
  - Done when: Unit tests cover TTY detection, env var detection, colorize function
  - Links: test-plan.md

## Milestone 2: Integrate colors into validator

- [ ] Task: Add CLI argument parsing
  - Done when: check_artifacts.py accepts `--no-color` flag using argparse
  - Links: architecture.md (CLI Argument Parsing)

- [ ] Task: Import color utilities
  - Done when: check_artifacts.py imports colors module at top
  - Links: architecture.md

- [ ] Task: Colorize error messages
  - Done when: `fail()` function outputs red text while preserving `::error::` annotation
  - Links: acceptance-tests.md (error test)

- [ ] Task: Colorize warning messages
  - Done when: `warn()` function outputs yellow text while preserving `::warning::` annotation
  - Links: acceptance-tests.md (warning test)

- [ ] Task: Colorize success message
  - Done when: Final "Artifact checks passed." message appears in green
  - Links: acceptance-tests.md (success test)

- [ ] Task: Verify GitHub Actions compatibility
  - Done when: Run validator in CI, confirm annotations still detected by GitHub Actions
  - Links: architecture.md (Tradeoffs section)

## Milestone 3: Testing and documentation

- [ ] Task: Add integration tests
  - Done when: Tests verify colored output in TTY, plain output in CI, --no-color flag works
  - Links: test-plan.md

- [ ] Task: Test in CI environment
  - Done when: Push changes, verify CI runs successfully and colors are disabled
  - Links: acceptance-tests.md (CI test)

- [ ] Task: Manual testing
  - Done when: Run validator locally, confirm colors appear correctly in terminal
  - Links: test-plan.md

- [ ] Task: Update documentation
  - Done when: Add usage note about colors to validator README or docstring
  - Links: architecture.md
