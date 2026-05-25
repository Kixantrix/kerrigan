# Spec: Hello CLI

## Goal
Create a simple, well-structured command-line interface (CLI) tool that demonstrates best practices for CLI development and serves as a reference example for the Kerrigan agent workflow with a different project type than hello-api.

## Scope

- Command-line tool with subcommands (greet, echo, version)
- Argument parsing and validation
- Configuration file support (YAML/JSON)
- Structured output (plain text and JSON formats)
- Error handling with helpful messages
- Comprehensive help documentation
- Installable as a Python package
- Cross-platform compatibility (Linux, macOS, Windows)

## Non-goals

- GUI or web interface
- Database integration
- Network communication (keep it local)
- Complex business logic
- Plugin architecture
- Auto-update functionality

## Users & scenarios

**Primary users**: Developers learning the Kerrigan workflow and CLI best practices

**Key scenarios**:
1. **Greeting**: User runs `hello greet --name Alice` to get a personalized greeting
2. **Echo**: User runs `hello echo "Hello World"` to echo text with optional formatting
3. **Version**: User runs `hello --version` to check the installed version
4. **Help**: User runs `hello --help` or `hello greet --help` for usage information
5. **JSON output**: User runs `hello greet --name Bob --json` for machine-readable output

## Constraints

- Must be simple enough to implement in < 4 hours
- Should demonstrate code quality from day one (no prototype exceptions)
- Must use a mainstream CLI framework (suggest: Python/Click or argparse)
- Must include tests from the start
- CI must stay green throughout implementation
- Should be installable via pip (setup.py or pyproject.toml)
- Must work on Python 3.8+

## Acceptance criteria

### Functional
- [ ] `hello greet --name X` returns personalized greeting
- [ ] `hello greet` without name returns error with helpful message
- [ ] `hello echo "text"` echoes the provided text
- [ ] `hello echo --upper "text"` echoes text in uppercase
- [ ] `hello echo --repeat N "text"` repeats text N times
- [ ] `hello --version` displays version number
- [ ] `hello --help` shows usage information for all commands
- [ ] `hello greet --json` outputs in JSON format
- [ ] Invalid commands show helpful error messages
- [ ] Config file support (optional --config flag)

### Non-functional
- [ ] Execution time < 100ms for all commands
- [ ] Test coverage > 80%
- [ ] All commands have unit tests
- [ ] Help text is clear and follows CLI conventions
- [ ] Error messages include suggestions for fixes
- [ ] Can be installed via `pip install .`
- [ ] README includes installation and usage instructions

### Quality
- [ ] Code passes linting/formatting checks (flake8, black)
- [ ] No security vulnerabilities in dependencies
- [ ] CI workflow validates all checks
- [ ] Code is modular (separate files for commands, config, utils)
- [ ] Follows Python packaging best practices

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CLI framework complexity | Medium | Use simple framework like Click; document rationale |
| Cross-platform issues | Low | Test on multiple OSes via CI; use os.path for paths |
| Package installation issues | Medium | Use standard setuptools; include clear install docs |
| Argument parsing edge cases | Low | Add comprehensive tests; validate all inputs |

## Success metrics

- All acceptance criteria met
- CI passes on all commits
- Implementation completes in single milestone
- Example serves as CLI project template
- Code demonstrates CLI best practices (help text, error handling, exit codes)
