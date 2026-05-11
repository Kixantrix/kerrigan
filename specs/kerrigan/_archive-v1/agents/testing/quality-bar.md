# Quality Bar: Testing Agent

## Definition of Done

Testing improvements are "done" when:
- [ ] Test coverage >80% for critical code paths (measured and documented)
- [ ] All tests pass consistently (flakiness rate <1% verified over 100+ runs)
- [ ] Unit test suite executes in <5 minutes
- [ ] Integration test suite executes in <15 minutes (if applicable)
- [ ] All test assertions include clear failure messages
- [ ] Edge cases and error conditions are tested
- [ ] Tests can run in any order (isolation verified)
- [ ] Test utilities and fixtures exist for common patterns
- [ ] Complex test scenarios are documented
- [ ] test-plan.md is updated with current coverage metrics and strategy
- [ ] CI passes reliably (>99% pass rate for non-bug failures)
- [ ] status.json was checked before starting work

## Structural Standards

### Test Coverage Requirements

**Minimum Coverage Targets**:
- Critical business logic: >90% coverage
- API endpoints: >85% coverage
- Error handling paths: >80% coverage
- Utility functions: >70% coverage
- Trivial code (getters/setters): Can be <50%

**Coverage Metrics to Track**:
- Line coverage (lines executed)
- Branch coverage (all branches taken)
- Function coverage (all functions called)

### Test Suite Organization

**Test Directory Structure**:
```
tests/
  unit/           # Fast, isolated tests (<1 sec each)
  integration/    # Component interaction tests
  e2e/            # End-to-end user flow tests (if applicable)
  fixtures/       # Test data and fixtures
  helpers/        # Test utilities and helpers
  mocks/          # Mock implementations
  conftest.py     # Shared pytest configuration (Python)
  setup.js        # Shared test setup (JavaScript)
```

**Test File Naming**:
- Mirror source structure: `src/auth.py` → `tests/unit/test_auth.py`
- Consistent naming convention per language
- Group related tests in classes or describe blocks

### Test Execution Time Guidelines

**Unit Tests**:
- Individual test: <100ms ideal, <1 second acceptable
- Full unit test suite: <5 minutes target
- If suite >5 minutes, prioritize optimization

**Integration Tests**:
- Individual test: <5 seconds typical, <30 seconds acceptable
- Full integration suite: <15 minutes target
- Separate from unit tests for selective execution

**End-to-End Tests**:
- Individual test: <30 seconds typical, <2 minutes acceptable
- Full e2e suite: <30 minutes target
- Run less frequently than unit/integration tests

### Flakiness Targets

**Acceptable Flakiness Rates**:
- Unit tests: <0.1% (virtually never flaky)
- Integration tests: <1%
- E2e tests: <5% (more tolerance due to complexity)
- Any test >5% flaky should be fixed or removed

**Flakiness Verification**:
- Run tests 100+ times before declaring non-flaky
- Use CI retry mechanisms only for tests explicitly marked as expected-flaky
- Document known flaky tests and their characteristics

## Content Quality Standards

### Good vs. Bad Test Examples

#### Clear Assertions with Failure Messages

✅ **Good** (specific with clear messages):
```python
def test_calculate_discount_for_premium_member():
    """Premium members get 20% discount on orders over $100."""
    member = Member(tier="premium")
    order = Order(total=150.00)
    
    discount = calculate_discount(member, order)
    
    assert discount == 30.00, \
        f"Expected $30 discount (20% of $150), got ${discount}"
    assert order.final_total == 120.00, \
        f"Expected final total $120, got ${order.final_total}"
```

❌ **Bad** (vague assertions):
```python
def test_discount():
    member = Member(tier="premium")
    order = Order(total=150.00)
    discount = calculate_discount(member, order)
    assert discount  # What should it be?
    assert order.final_total  # Is this correct?
```

#### Edge Case and Error Condition Coverage

✅ **Good** (comprehensive edge cases):
```javascript
describe('User Registration', () => {
  it('should create user with valid email and password', async () => {
    const user = await register('test@example.com', 'Password123!');
    expect(user).toBeDefined();
    expect(user.email).toBe('test@example.com');
  });

  it('should reject registration with invalid email format', async () => {
    await expect(register('invalid-email', 'Password123!'))
      .rejects.toThrow('Invalid email format');
  });

  it('should reject weak password (no uppercase)', async () => {
    await expect(register('test@example.com', 'password123'))
      .rejects.toThrow('Password must contain uppercase letter');
  });

  it('should reject empty email', async () => {
    await expect(register('', 'Password123!'))
      .rejects.toThrow('Email is required');
  });

  it('should reject duplicate email', async () => {
    await register('test@example.com', 'Password123!');
    await expect(register('test@example.com', 'Password456!'))
      .rejects.toThrow('Email already registered');
  });
});
```

❌ **Bad** (only happy path):
```javascript
describe('User Registration', () => {
  it('should register user', async () => {
    const user = await register('test@example.com', 'Password123!');
    expect(user).toBeDefined();
  });
});
```

#### Test Isolation and Independence

✅ **Good** (isolated tests):
```go
func TestUserService(t *testing.T) {
    t.Run("CreateUser returns user with generated ID", func(t *testing.T) {
        db := setupTestDB(t) // Fresh DB per test
        defer db.Close()
        
        service := NewUserService(db)
        user, err := service.CreateUser("test@example.com")
        
        assert.NoError(t, err)
        assert.NotEmpty(t, user.ID)
        assert.Equal(t, "test@example.com", user.Email)
    })
    
    t.Run("CreateUser rejects duplicate email", func(t *testing.T) {
        db := setupTestDB(t) // Independent test DB
        defer db.Close()
        
        service := NewUserService(db)
        _, _ = service.CreateUser("test@example.com")
        
        _, err := service.CreateUser("test@example.com")
        assert.Error(t, err)
        assert.Contains(t, err.Error(), "duplicate")
    })
}
```

❌ **Bad** (tests depend on each other):
```go
var testUser User // Shared state

func TestCreateUser(t *testing.T) {
    testUser = service.CreateUser("test@example.com")
    assert.NotNil(t, testUser)
}

func TestGetUser(t *testing.T) {
    // Depends on TestCreateUser running first
    user := service.GetUser(testUser.ID)
    assert.Equal(t, testUser.Email, user.Email)
}
```

#### Non-Flaky Time Handling

✅ **Good** (deterministic time):
```python
def test_token_expiration_after_one_hour():
    """Token should expire exactly 1 hour after creation."""
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    
    with freeze_time(fixed_time):
        token = create_token(user_id=123)
    
    with freeze_time(fixed_time + timedelta(hours=1, seconds=1)):
        is_valid = validate_token(token)
    
    assert not is_valid, "Token should be expired after 1 hour"
```

❌ **Bad** (flaky time-dependent):
```python
def test_token_expiration():
    token = create_token(user_id=123)
    time.sleep(3600)  # Wait 1 hour - flaky, slow, unreliable
    is_valid = validate_token(token)
    assert not is_valid
```

#### Fast Tests with Mocking

✅ **Good** (mocked external dependencies):
```javascript
describe('Weather Service', () => {
  it('should return weather data for valid city', async () => {
    const mockHttpClient = {
      get: jest.fn().mockResolvedValue({
        data: { temp: 72, condition: 'sunny' }
      })
    };
    
    const service = new WeatherService(mockHttpClient);
    const weather = await service.getWeather('Seattle');
    
    expect(weather.temp).toBe(72);
    expect(weather.condition).toBe('sunny');
    expect(mockHttpClient.get).toHaveBeenCalledWith(
      expect.stringContaining('Seattle')
    );
  });
});
```

❌ **Bad** (slow external calls):
```javascript
describe('Weather Service', () => {
  it('should return weather data', async () => {
    // Actual HTTP call - slow, flaky, requires network
    const service = new WeatherService();
    const weather = await service.getWeather('Seattle');
    expect(weather).toBeDefined();
  });
});
```

#### Reusable Test Fixtures

✅ **Good** (shared fixtures):
```python
import pytest

@pytest.fixture
def sample_user():
    """Create a standard test user."""
    return User(
        id=1,
        email="test@example.com",
        name="Test User",
        created_at=datetime(2024, 1, 1)
    )

@pytest.fixture
def premium_member():
    """Create a premium tier member for discount tests."""
    return Member(
        tier="premium",
        discount_rate=0.20,
        benefits=["free-shipping", "priority-support"]
    )

def test_calculate_discount(premium_member):
    order = Order(total=100.00)
    discount = calculate_discount(premium_member, order)
    assert discount == 20.00

def test_member_benefits(premium_member):
    assert "free-shipping" in premium_member.benefits
```

❌ **Bad** (duplicated setup):
```python
def test_calculate_discount():
    member = Member(tier="premium", discount_rate=0.20, 
                    benefits=["free-shipping", "priority-support"])
    order = Order(total=100.00)
    discount = calculate_discount(member, order)
    assert discount == 20.00

def test_member_benefits():
    member = Member(tier="premium", discount_rate=0.20,
                    benefits=["free-shipping", "priority-support"])
    assert "free-shipping" in member.benefits
```

### Good vs. Bad Coverage Improvements

#### Targeted Coverage Expansion

✅ **Good** (focus on critical gaps):
```
Coverage analysis shows:
- auth.py: 45% coverage (CRITICAL - needs tests)
  Missing: password validation, token refresh, logout
- utils.py: 95% coverage (good)
- config.py: 30% coverage (low priority - mostly constants)

Action: Add 15 tests for auth.py critical paths
- test_password_validation_with_weak_passwords (5 cases)
- test_token_refresh_with_valid_token
- test_token_refresh_with_expired_token
- test_token_refresh_with_invalid_token
- test_logout_clears_session
...
```

❌ **Bad** (unfocused coverage):
```
Coverage is 75%, let's get it to 100% by testing everything including:
- Trivial getters/setters
- Configuration loading
- Logging statements
- Generated code
```

## Common Mistakes to Avoid

### Process Mistakes
- ❌ Starting work when status.json shows "blocked" or "on-hold"
- ❌ Breaking existing tests while improving coverage
- ❌ Removing tests to "fix" flakiness (fix the test, don't delete it)
- ❌ Adding tests without running them first (TDD even for test improvement)
- ❌ Ignoring test execution time (slow tests won't get run)
- ❌ Not updating test-plan.md after significant improvements
- ❌ Optimizing tests without measuring first (premature optimization)

### Test Quality Mistakes
- ❌ Vague test names (test_1, test_feature, test_works)
- ❌ Assertions without failure messages
- ❌ Testing implementation instead of behavior
- ❌ Tests that don't actually assert anything (no assertions)
- ❌ Too many assertions in one test (test multiple behaviors separately)
- ❌ Magic numbers and strings without explanation
- ❌ Complex test logic (tests should be simple and obvious)

### Coverage Mistakes
- ❌ Chasing 100% coverage for its own sake
- ❌ Testing trivial code (simple getters, configuration constants)
- ❌ Ignoring error paths in favor of happy paths
- ❌ Missing boundary conditions (empty, null, max values)
- ❌ Not testing integration points between components
- ❌ Forgetting to test concurrent access scenarios

### Flakiness Mistakes
- ❌ Using time.sleep() or setTimeout() for synchronization
- ❌ Depending on wall clock time instead of mocked time
- ❌ Sharing state between tests without proper cleanup
- ❌ Making real network calls instead of mocking
- ❌ Using non-deterministic randomness without seeding
- ❌ Assuming test execution order
- ❌ Not verifying flakiness elimination (run tests multiple times)

### Performance Mistakes
- ❌ Real database operations in unit tests
- ❌ File I/O when in-memory alternatives exist
- ❌ Network calls to external services
- ❌ Heavy setup/teardown for every single test
- ❌ Not parallelizing independent tests
- ❌ Sequential execution when parallel is safe

## Validation Checklist

Before considering testing improvements complete:

### Coverage
- [ ] Coverage >80% for critical code paths (business logic, API endpoints)
- [ ] All error handling paths have tests
- [ ] Boundary conditions tested (empty, null, max values, negative)
- [ ] Edge cases covered (concurrent access, race conditions, limits)
- [ ] Coverage report generated and reviewed
- [ ] Gaps prioritized and addressed or documented

### Test Quality
- [ ] All assertions include clear failure messages
- [ ] Test names are descriptive and follow conventions
- [ ] Complex test scenarios have explanatory comments
- [ ] Magic values replaced with named constants or explained
- [ ] Test code is clean and maintainable
- [ ] Follows existing test patterns and conventions

### Test Reliability
- [ ] All tests pass consistently (100 consecutive runs)
- [ ] Flakiness rate <1% verified
- [ ] No time-dependent flakiness (mocked time used)
- [ ] No race conditions or order dependencies
- [ ] External dependencies mocked or stubbed
- [ ] Tests can run in isolation and in any order

### Test Performance
- [ ] Unit test suite completes in <5 minutes
- [ ] Integration test suite completes in <15 minutes (if applicable)
- [ ] Individual unit tests <1 second
- [ ] Slow tests identified and optimized or moved to appropriate suite
- [ ] Test execution time tracked and documented

### Test Infrastructure
- [ ] Reusable fixtures created for common patterns
- [ ] Test utilities and helpers documented
- [ ] Mocking utilities available for common scenarios
- [ ] Test data generators created where appropriate
- [ ] Shared setup/teardown functions are efficient

### Documentation
- [ ] test-plan.md updated with current coverage metrics
- [ ] New testing patterns documented
- [ ] Complex test scenarios explained
- [ ] Test utilities have clear docstrings
- [ ] Coverage gaps and decisions documented

### CI Integration
- [ ] All tests pass in CI
- [ ] CI execution time acceptable
- [ ] Test failures provide clear, actionable output
- [ ] Flaky tests fixed or marked as expected-flaky
- [ ] CI reliability >99% (excluding legitimate bugs)

## Review Standards

### Self-Review
Before submitting test improvements, agent should:
1. Run full test suite and verify all tests pass
2. Run coverage analysis and verify targets met
3. Run tests 100 times to verify flakiness eliminated
4. Measure test execution time and verify targets met
5. Review test code for clarity and maintainability
6. Verify test-plan.md is updated
7. Confirm CI will pass based on local testing

### Peer Review (Human or Agent)
Reviewers should validate:
- **Coverage**: Are critical paths tested? Are gaps justified?
- **Quality**: Are tests clear, maintainable, and following conventions?
- **Reliability**: Are tests deterministic and non-flaky?
- **Performance**: Are tests fast enough? Any obvious optimizations missed?
- **Value**: Do improvements provide meaningful confidence increase?

### Acceptance Criteria for Test Improvements
Good test improvements pass this test:
- [ ] Can answer: "What does this test verify?" (clear purpose)
- [ ] Can answer: "Why did this test fail?" (clear failure messages)
- [ ] Can answer: "What coverage gap does this fill?" (targeted improvement)
- [ ] Can answer: "Will this test remain reliable?" (no flakiness indicators)
- [ ] Cannot easily make it fail spuriously (robust against environment)

## Examples

### Comprehensive Coverage Improvement

**Before** (45% coverage, happy path only):
```python
# tests/test_auth.py
def test_login():
    result = login("user@example.com", "password")
    assert result
```

**After** (95% coverage, comprehensive):
```python
# tests/test_auth.py
class TestAuthentication:
    def test_login_with_valid_credentials_returns_jwt_token(self):
        """Successful login returns valid JWT with user claims."""
        user = create_test_user("user@example.com", "ValidPass123!")
        
        result = login("user@example.com", "ValidPass123!")
        
        assert result["success"] is True, "Login should succeed with valid credentials"
        assert "token" in result, "Response should include JWT token"
        token_claims = decode_jwt(result["token"])
        assert token_claims["email"] == "user@example.com"
    
    def test_login_with_invalid_password_returns_error(self):
        """Invalid password should return authentication error."""
        user = create_test_user("user@example.com", "ValidPass123!")
        
        result = login("user@example.com", "WrongPassword")
        
        assert result["success"] is False, "Login should fail with wrong password"
        assert "error" in result
        assert "authentication failed" in result["error"].lower()
    
    def test_login_with_nonexistent_email_returns_error(self):
        """Login with email that doesn't exist should fail gracefully."""
        result = login("nobody@example.com", "anypassword")
        
        assert result["success"] is False
        assert "user not found" in result["error"].lower()
    
    def test_login_with_empty_credentials_returns_validation_error(self):
        """Empty email or password should fail validation."""
        with pytest.raises(ValidationError) as exc:
            login("", "")
        assert "required" in str(exc.value).lower()
    
    def test_login_rate_limiting_after_failed_attempts(self):
        """Multiple failed login attempts should trigger rate limiting."""
        user = create_test_user("user@example.com", "ValidPass123!")
        
        # Try 5 failed logins
        for _ in range(5):
            login("user@example.com", "WrongPassword")
        
        # 6th attempt should be rate limited
        result = login("user@example.com", "WrongPassword")
        assert result["success"] is False
        assert "rate limit" in result["error"].lower()
```

### Flakiness Elimination

**Before** (flaky - depends on system time):
```javascript
test('session expires after timeout', async () => {
  const session = createSession(userId);
  await sleep(5000); // Flaky: depends on system clock
  const isValid = validateSession(session);
  expect(isValid).toBe(false);
});
```

**After** (deterministic):
```javascript
test('session expires after 5 second timeout', async () => {
  const mockClock = new MockClock('2024-01-01T12:00:00Z');
  
  const session = createSession(userId, { clock: mockClock });
  expect(validateSession(session, mockClock)).toBe(true);
  
  mockClock.advance(5001); // Advance 5.001 seconds
  expect(validateSession(session, mockClock)).toBe(false);
});
```

### Test Performance Optimization

**Before** (slow - real database):
```python
def test_user_creation():
    db = connect_to_postgres()  # Slow: real DB connection
    user = db.users.create(email="test@example.com")
    assert user.id is not None
    db.close()  # Time: ~500ms per test
```

**After** (fast - in-memory):
```python
@pytest.fixture
def mock_db():
    return InMemoryDatabase()  # Fast: in-memory

def test_user_creation(mock_db):
    user = mock_db.users.create(email="test@example.com")
    assert user.id is not None
    # Time: ~5ms per test (100x faster)
```

## Continuous Improvement

The Testing Agent role should evolve based on:
- Coverage trends over time (is coverage increasing or decreasing?)
- CI failure patterns (what causes test failures most often?)
- Test execution time trends (are tests getting slower?)
- Flakiness reports (which tests are unreliable?)
- Developer feedback on test quality and usefulness
- Emerging testing tools and best practices

Changes to this quality bar should be proposed via:
1. Issue documenting the problem or improvement opportunity
2. Data showing the impact (coverage metrics, flakiness rates, execution times)
3. Example of current vs. improved approach
4. Update to this quality-bar.md
5. Update to role.testing.md agent prompt
6. Validation that changes improve test confidence without excessive cost
