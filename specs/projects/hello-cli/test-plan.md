# Test plan: hello-cli

## Levels

### Unit Tests
- **Scope**: Individual functions and command handlers
- **Coverage**: All command functions, utilities, configuration loader
- **Approach**: 
  - Mock Click context and arguments
  - Test output formatting logic
  - Test error handling paths
  - Verify exit codes are set correctly
- **Tools**: unittest with unittest.mock
- **Target coverage**: >85% of code

**Test files**:
- `test_greet.py`: Test greet command with various inputs
- `test_echo.py`: Test echo command and transformations
- `test_utils.py`: Test output and error formatting
- `test_config.py`: Test configuration loading and validation
- `test_cli.py`: Test main CLI group and global options

### Integration Tests
- **Scope**: Full command execution from CLI entry point
- **Coverage**: End-to-end command workflows
- **Approach**:
  - Use subprocess to invoke CLI as user would
  - Verify stdout/stderr output
  - Check exit codes
  - Test with real config files
- **Tools**: unittest with subprocess
- **Target coverage**: All user-facing commands

**Test files**:
- `test_integration.py`: Test complete command execution flows

### E2E Tests
Not needed for this simple CLI tool. Integration tests with subprocess provide sufficient end-to-end coverage.

## Tooling

### Test Runner
- **unittest**: Python standard library test framework
- Run with: `python -m unittest discover -s tests -p "test_*.py" -v`

### Coverage
- **coverage.py**: Standard Python coverage tool
- Run with: `coverage run -m unittest discover -s tests`
- Report: `coverage report -m` or `coverage html`

### Linting
- **flake8**: Style and error checking
- Config: `.flake8` with max-line-length=100
- Run with: `flake8 .`

### CI Integration
- Run tests and linting in CI workflow
- Fail build if tests fail or coverage < 80%

## Risk areas / focus

### High Priority Testing

1. **Argument parsing edge cases**
   - Missing required arguments
   - Invalid argument types
   - Unknown options
   - Conflicting options
   - **Why critical**: Poor error messages frustrate users

2. **Output formatting**
   - JSON serialization of various data types
   - Unicode handling in text output
   - Newlines and whitespace handling
   - **Why critical**: Broken output breaks pipelines

3. **Configuration loading**
   - Invalid YAML syntax
   - Missing config files
   - Invalid config structure
   - Config overrides from CLI
   - **Why critical**: Config errors should be clear

4. **Exit codes**
   - Success: 0
   - User error: 1
   - Usage error: 2
   - **Why critical**: Scripts rely on exit codes

### Medium Priority Testing

5. **Cross-platform compatibility**
   - Path handling (os.path vs hardcoded /)
   - Line endings (CRLF vs LF)
   - **Why important**: Tool should work everywhere

6. **Error messages**
   - Clarity and helpfulness
   - Suggested commands
   - **Why important**: Good UX

### Test Data

**Valid inputs**:
- Names: "Alice", "Bob", "Jean-Pierre", "José", "李明" (unicode)
- Text: "hello", "hello world", "multi\nline", "" (empty)
- Numbers: 1, 5, 100, 0

**Invalid inputs**:
- Missing required arguments
- Wrong types (string where number expected)
- Out-of-range values (negative repeat count)

**Config files**:
- Valid YAML: `{name: "Alice", format: "json"}`
- Invalid YAML: `{invalid syntax`
- Missing file: `/nonexistent/config.yml`

## Test Naming Convention

Follow pattern: `test_<function>_<scenario>_<expected>`

Examples:
- `test_greet_with_name_returns_message`
- `test_greet_without_name_raises_error`
- `test_echo_with_upper_returns_uppercase`
- `test_format_output_as_json_returns_valid_json`

## Success Criteria

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Test coverage >80% (target: 85%+)
- [ ] flake8 passes with no errors
- [ ] Manual testing confirms all acceptance criteria met
- [ ] CI validates successfully
