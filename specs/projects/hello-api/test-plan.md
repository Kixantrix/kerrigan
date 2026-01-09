# Test Plan: Hello API

## Testing Strategy

This project follows a **test pyramid approach** with emphasis on fast, reliable automated tests.

### Test Levels

1. **Unit Tests** (60% of tests)
   - Test individual functions in isolation
   - Mock external dependencies
   - Fast execution (<100ms total)
   - Focus: validators, handlers, config

2. **Integration Tests** (35% of tests)
   - Test Flask routes with test client
   - Verify request/response handling
   - Test error handling end-to-end
   - Focus: Full HTTP request lifecycle

3. **Manual Tests** (5% of tests)
   - Docker container verification
   - Real curl commands against running service
   - Visual inspection of logs
   - Focus: Deployment and operational aspects

## Tooling Strategy

### Primary Tools
- **pytest**: Test runner and framework
- **pytest-flask**: Flask-specific fixtures and utilities
- **pytest-cov**: Code coverage reporting
- **pytest-mock**: Mocking utilities (if needed)

### Supporting Tools
- **flake8**: Code linting (PEP 8 compliance)
- **black**: Code formatting (optional, for consistency)
- **curl**: Manual API testing
- **Docker**: Container testing

### CI Integration
- Run pytest with coverage on every commit
- Require >80% coverage to pass
- Run linting checks
- Cache Python dependencies for speed

## Coverage Focus

### Must Cover (Critical Paths)
- ✅ All endpoint handlers (health, greet, echo)
- ✅ All validation logic (name validation, JSON parsing)
- ✅ Error handling for all endpoints
- ✅ Configuration loading from environment
- ✅ Request logging

### Should Cover (Important Paths)
- ✅ Edge cases (empty strings, special characters, long inputs)
- ✅ Different HTTP methods on each endpoint
- ✅ Content-Type handling
- ✅ Status code verification

### Nice to Cover (Low Risk)
- Configuration defaults when env vars missing
- Logging format and levels
- Application factory setup

## Risk Areas

### High Risk (Must Test Thoroughly)
1. **Input validation**: Prevents crashes and security issues
   - Test: Empty inputs, very long inputs, special characters
   - Mitigation: Comprehensive unit tests for validators

2. **JSON parsing**: Malformed JSON can crash handlers
   - Test: Invalid JSON, empty body, wrong Content-Type
   - Mitigation: Integration tests with various payloads

3. **Error responses**: Must not leak sensitive information
   - Test: All error scenarios return safe messages
   - Mitigation: Check error responses in tests

### Medium Risk (Should Test)
1. **Configuration**: Wrong port or settings can break deployment
   - Test: Environment variable loading
   - Mitigation: Unit tests for config module

2. **Container deployment**: Build or runtime failures
   - Test: Manual Docker build and run
   - Mitigation: Document in acceptance tests

### Low Risk (Basic Coverage OK)
1. **Health check**: Simple endpoint, low complexity
   - Test: Basic integration test sufficient
   
2. **Logging**: Non-critical if fails
   - Test: Verify logs are emitted, don't test format details

## Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_validators.py       # Unit tests for validators
├── test_handlers.py         # Unit tests for handlers
├── test_config.py          # Unit tests for config
├── test_health.py          # Integration tests for /health
├── test_greet.py           # Integration tests for /greet
├── test_echo.py            # Integration tests for /echo
└── test_integration.py     # Full request/response tests
```

## Test Fixtures (conftest.py)

```python
@pytest.fixture
def app():
    """Create and configure a test app instance."""
    # Return Flask app with test config
    
@pytest.fixture
def client(app):
    """Create a test client for the app."""
    # Return Flask test client

@pytest.fixture
def runner(app):
    """Create a CLI runner for the app."""
    # Return Flask CLI test runner (if needed)
```

## Coverage Goals

- **Overall**: >80% line coverage (required)
- **Critical modules**: >90% coverage
  - validators.py: 100% (small, critical)
  - handlers.py: >95% (core logic)
  - app.py: >85% (some startup code may be hard to test)
- **Configuration**: >70% (simple module)

## Test Execution

### Local Development
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_greet.py

# Run with verbose output
pytest -v
```

### CI Pipeline
```bash
# Install dependencies
pip install -r requirements.txt

# Run linting
flake8 .

# Run tests with coverage
pytest --cov=. --cov-report=xml --cov-report=term

# Fail if coverage < 80%
pytest --cov=. --cov-fail-under=80
```

## Performance Targets

- Unit tests: <100ms total execution time
- Integration tests: <500ms total execution time
- Full test suite: <1 second total
- CI pipeline: <2 minutes (including install)

These are achievable because:
- No database or external services
- Simple logic with minimal computation
- Flask test client is fast

## Test Data Strategy

### Approach
- **Inline test data**: Define test inputs directly in test functions
- **No fixtures for data**: Keep data close to tests for readability
- **Parametrized tests**: Use pytest.mark.parametrize for multiple inputs

### Examples
```python
@pytest.mark.parametrize("name,expected", [
    ("Alice", "Hello, Alice!"),
    ("José", "Hello, José!"),
    ("测试", "Hello, 测试!"),
])
def test_greet_with_various_names(client, name, expected):
    # Test implementation
```

## Regression Testing

- Every bug fix must include a test that would have caught the bug
- Add test before fixing bug (TDD approach)
- Keep regression tests in same file as related tests
- Document bug number/issue in test docstring if applicable

## Manual Testing Checklist

Before marking complete, manually verify:

- [ ] Run app locally and test all endpoints with curl
- [ ] Build Docker image and verify it runs
- [ ] Check logs for proper format and information
- [ ] Test with invalid inputs to see error messages
- [ ] Verify health check from browser
- [ ] Test all acceptance criteria from acceptance-tests.md

## Test Maintenance

- Run tests before every commit
- Update tests when changing functionality
- Remove tests only when removing features
- Keep test code as clean as production code
- Refactor tests if they become complex

## Exclusions

We intentionally do NOT test:
- Flask framework internals (trust the framework)
- Python standard library (trust the stdlib)
- Third-party libraries (trust pytest, etc.)
- Docker container orchestration (out of scope)

## Success Criteria

- ✅ >80% code coverage achieved
- ✅ All acceptance test scenarios have corresponding automated tests
- ✅ CI runs tests on every commit
- ✅ Tests are fast (<1s total)
- ✅ No flaky tests (all deterministic)
- ✅ Test failures are clear and actionable
