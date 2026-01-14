# Plan: hello-cli

Milestones must end with green CI.

## Milestone 1: Core Implementation
**Status**: Complete

**Goal**: Implement basic CLI structure with greet and echo commands

**Tasks**:
- [x] Set up package structure and setup.py
- [x] Create CLI entry point with Click
- [x] Implement greet command with --name and --json options
- [x] Implement echo command with --upper, --repeat, --json options
- [x] Add version command
- [x] Create utilities for output formatting
- [x] Add basic error handling
- [x] Write unit tests for all commands (>80% coverage)
- [x] Add .gitignore, requirements.txt
- [x] Create comprehensive README

**Deliverable**: Working CLI tool with all core commands and tests passing

**Success criteria**:
- All commands execute correctly
- Tests pass with >80% coverage
- Code passes flake8 linting
- Can be installed via `pip install .`
- CI validates successfully

## Milestone 2: Configuration and Polish
**Status**: Complete

**Goal**: Add configuration file support and final polish

**Tasks**:
- [x] Implement configuration loader (YAML)
- [x] Add --config option to CLI
- [x] Support default config locations
- [x] Add tests for configuration loading
- [x] Polish error messages with helpful suggestions
- [x] Add Dockerfile for containerized usage
- [x] Document all features in README
- [x] Validate cross-platform compatibility
- [x] Final CI validation

**Deliverable**: Production-ready CLI tool with configuration support

**Success criteria**:
- Config file support works correctly
- All acceptance tests pass
- Documentation is complete
- Docker image builds successfully
- CI green on all checks

## Rollback Plan
If issues arise:
- Milestone 1: Revert to clean state, start over with simpler scope
- Milestone 2: Can ship without config support if needed
