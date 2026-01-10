# Plan: hello-cli

Milestones must end with green CI.

## Milestone 1: Core Implementation
**Status**: In Progress

**Goal**: Implement basic CLI structure with greet and echo commands

**Tasks**:
- [ ] Set up package structure and setup.py
- [ ] Create CLI entry point with Click
- [ ] Implement greet command with --name and --json options
- [ ] Implement echo command with --upper, --repeat, --json options
- [ ] Add version command
- [ ] Create utilities for output formatting
- [ ] Add basic error handling
- [ ] Write unit tests for all commands (>80% coverage)
- [ ] Add .gitignore, requirements.txt
- [ ] Create comprehensive README

**Deliverable**: Working CLI tool with all core commands and tests passing

**Success criteria**:
- All commands execute correctly
- Tests pass with >80% coverage
- Code passes flake8 linting
- Can be installed via `pip install .`
- CI validates successfully

## Milestone 2: Configuration and Polish
**Status**: Not Started

**Goal**: Add configuration file support and final polish

**Tasks**:
- [ ] Implement configuration loader (YAML)
- [ ] Add --config option to CLI
- [ ] Support default config locations
- [ ] Add tests for configuration loading
- [ ] Polish error messages with helpful suggestions
- [ ] Add Dockerfile for containerized usage
- [ ] Document all features in README
- [ ] Validate cross-platform compatibility
- [ ] Final CI validation

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
