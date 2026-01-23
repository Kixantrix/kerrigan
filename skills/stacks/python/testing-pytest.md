---
title: Python Testing with Pytest
version: 1.0.0
source: Community (adapted)
source_url: https://docs.pytest.org/en/stable/
quality_tier: 2
last_reviewed: 2026-01-23
last_updated: 2026-01-23
reviewed_by: kerrigan-swe-team
license: MIT
tags: [python, testing, pytest, tdd]
applies_to: [python]
---

# Python Testing with Pytest

*Adapted from pytest documentation and community best practices for Kerrigan projects.*

This skill covers testing patterns for Python projects using pytest, aligned with Kerrigan's quality bar.

## When to Apply

Reference this skill when:
- Starting a Python project that needs tests
- Setting up test infrastructure for Python code
- Writing unit, integration, or acceptance tests in Python
- Debugging test failures or improving test coverage
- Following Kerrigan quality bar (every feature has tests)

## Test Structure

### Directory Layout

```
project/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── models.py
│       └── utils.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── unit/
│   │   ├── test_models.py
│   │   └── test_utils.py
│   └── integration/
│       └── test_api.py
├── pyproject.toml
└── pytest.ini (or pyproject.toml)
```

### Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=src
    --cov-report=term-missing
    --cov-report=html
```

## Key Patterns

### Pattern 1: Arrange-Act-Assert (AAA)

Structure tests clearly:
```python
def test_calculate_total_price_with_discount():
    # Arrange: Set up test data
    items = [
        {"price": 10.0, "quantity": 2},
        {"price": 5.0, "quantity": 3}
    ]
    discount = 0.1  # 10% discount
    
    # Act: Execute the function under test
    total = calculate_total_price(items, discount)
    
    # Assert: Verify the result
    assert total == 31.5  # (20 + 15) * 0.9
```

### Pattern 2: Fixtures for Shared Setup

Use fixtures to avoid repetition:
```python
# conftest.py
import pytest

@pytest.fixture
def sample_user():
    return {"id": "123", "name": "Alice", "email": "alice@example.com"}

@pytest.fixture
def db_session():
    session = create_test_db_session()
    yield session
    session.close()
```

### Pattern 3: Parametrize for Multiple Cases

Test multiple inputs efficiently:
```python
import pytest

@pytest.mark.parametrize("input_email,expected_valid", [
    ("user@example.com", True),
    ("invalid-email", False),
])
def test_email_validation(input_email, expected_valid):
    result = is_valid_email(input_email)
    assert result == expected_valid
```

## References

- [pytest Documentation](https://docs.pytest.org/)
- [Kerrigan Quality Bar](../../meta/quality-bar.md)

## Updates

**v1.0.0 (2026-01-23):** Initial version adapted from pytest documentation for Kerrigan projects
