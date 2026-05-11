# Quality Bar: SWE Agent

## Definition of Done

A feature implementation is "done" when:
- [ ] Tests written before or during implementation (TDD approach followed)
- [ ] All automated tests pass (green CI build)
- [ ] Code coverage >80% for new code
- [ ] Linting configuration exists (from first milestone)
- [ ] All linting issues resolved
- [ ] No source files exceed 800 lines without justification
- [ ] Manual verification performed and documented
- [ ] Error handling is explicit (no silent failures)
- [ ] Functions are small and focused (<50 lines ideal)
- [ ] Documentation updated if public APIs changed
- [ ] PR links to relevant artifacts (spec, plan, tasks)
- [ ] "Done when" criteria met for task
- [ ] status.json was checked before starting work

## Structural Standards

### Project Structure Requirements

**Initial Project Setup** (Milestone 1):
- `src/` or equivalent source directory
- `tests/` directory with subdirectories (unit/, integration/, e2e/ as appropriate)
- Linting configuration (.eslintrc.json, .flake8, clippy.toml, etc.)
- Formatting configuration (.prettierrc, .editorconfig, etc.)
- `.gitignore` appropriate for language/framework
- CI configuration (.github/workflows/, .gitlab-ci.yml, etc.)
- `README.md` with setup and usage instructions

**Test Structure**:
- Test directory mirrors source structure
- Test files named consistently (test_*.py, *.test.js, *_test.go, etc.)
- Test fixtures in dedicated directory (tests/fixtures/)
- Shared test utilities (tests/helpers/, tests/utils/, conftest.py)
- Mocking utilities set up early

### File Size Guidelines
- **Preferred**: < 200 lines per file
- **Warning threshold**: 400 lines (consider refactoring)
- **Hard limit**: 800 lines (requires justification in PR)
- **Exceptions**: Generated code, configuration files with extensive data

### Function/Method Size Guidelines
- **Ideal**: < 50 lines
- **Acceptable**: < 100 lines
- **Red flag**: > 100 lines (likely needs decomposition)
- **Focus**: Single responsibility, clear purpose

### Test Coverage Standards
- **Minimum**: 80% code coverage for new code
- **Goal**: > 90% coverage for business logic
- **Focus areas**: Happy path, edge cases, error conditions
- **Test types**:
  - Unit tests: Individual functions/classes (fast, isolated)
  - Integration tests: Component interactions
  - E2E tests: Critical user flows (for applications with UI/API)

## Content Quality Standards

### Good vs. Bad Code Examples

#### Modular vs. Blob Files
✅ **Good** (modular):
```
src/
  auth/
    login.js (120 lines)
    registration.js (95 lines)
    middleware.js (75 lines)
  api/
    users.js (150 lines)
    posts.js (140 lines)
  utils/
    validation.js (80 lines)
    logging.js (60 lines)
```

❌ **Bad** (blob):
```
src/
  app.js (1200 lines - everything in one file)
```

#### Error Handling
✅ **Good** (explicit):
```javascript
async function fetchUser(userId) {
  if (!userId) {
    throw new Error('User ID is required');
  }
  
  try {
    const user = await db.users.findById(userId);
    if (!user) {
      throw new Error(`User not found: ${userId}`);
    }
    return user;
  } catch (error) {
    logger.error('Failed to fetch user', { userId, error });
    throw error;
  }
}
```

❌ **Bad** (silent failures):
```javascript
async function fetchUser(userId) {
  try {
    const user = await db.users.findById(userId);
    return user; // Returns undefined if not found, no error
  } catch (error) {
    // Swallows error
  }
}
```

#### Function Size and Focus
✅ **Good** (small and focused):
```python
def validate_email(email: str) -> bool:
    """Check if email format is valid."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> bool:
    """Check if password meets minimum requirements."""
    return len(password) >= 8 and any(c.isupper() for c in password)

def validate_registration(email: str, password: str) -> tuple[bool, str]:
    """Validate registration input."""
    if not validate_email(email):
        return False, "Invalid email format"
    if not validate_password(password):
        return False, "Password must be at least 8 characters with uppercase"
    return True, ""
```

❌ **Bad** (large and unfocused):
```python
def validate_and_register_user(email, password, name, age, preferences):
    # 150 lines of validation, database calls, email sending,
    # logging, error handling, etc. all in one function
    # Violates function size guidelines (>100 lines) and single responsibility principle
    pass
```

#### Meaningful Names
✅ **Good**:
```go
func calculateMonthlyInterest(principal float64, annualRate float64) float64 {
    monthlyRate := annualRate / 12.0
    return principal * monthlyRate
}
```

❌ **Bad**:
```go
func calc(p float64, r float64) float64 {
    m := r / 12.0
    return p * m
}
```

### Good vs. Bad Test Examples

#### Comprehensive Test Coverage
✅ **Good** (covers happy path, edge cases, errors):
```python
class TestUserLogin:
    def test_login_with_valid_credentials(self):
        # Happy path
        token = login("user@example.com", "password123")
        assert token is not None
        assert decode_token(token)["email"] == "user@example.com"
    
    def test_login_with_invalid_password(self):
        # Error case
        with pytest.raises(AuthenticationError):
            login("user@example.com", "wrongpassword")
    
    def test_login_with_nonexistent_user(self):
        # Edge case
        with pytest.raises(UserNotFoundError):
            login("nobody@example.com", "password123")
    
    def test_login_with_empty_credentials(self):
        # Edge case
        with pytest.raises(ValidationError):
            login("", "")
```

❌ **Bad** (only happy path):
```python
class TestUserLogin:
    def test_login(self):
        token = login("user@example.com", "password123")
        assert token is not None
```

#### Test Independence
✅ **Good** (isolated tests):
```javascript
describe('User API', () => {
  beforeEach(async () => {
    await db.users.deleteAll();
    await db.users.create({ email: 'test@example.com', password: 'hashed' });
  });

  it('should fetch user by id', async () => {
    const user = await fetchUser(1);
    expect(user.email).toBe('test@example.com');
  });

  it('should return 404 for missing user', async () => {
    await expect(fetchUser(999)).rejects.toThrow('User not found');
  });
});
```

❌ **Bad** (tests depend on each other):
```javascript
describe('User API', () => {
  let userId;

  it('should create user', async () => {
    userId = await createUser({ email: 'test@example.com' });
    expect(userId).toBeDefined();
  });

  it('should fetch user', async () => {
    // Depends on previous test
    const user = await fetchUser(userId);
    expect(user).toBeDefined();
  });
});
```

### Good vs. Bad Documentation Examples

#### API Documentation
✅ **Good** (clear and complete):
```python
def create_invoice(customer_id: str, items: List[InvoiceItem], due_date: datetime) -> Invoice:
    """
    Create a new invoice for a customer.
    
    Args:
        customer_id: Unique identifier for the customer
        items: List of invoice items with quantity and price
        due_date: Payment due date (must be future date)
        
    Returns:
        Created invoice with generated ID and total
        
    Raises:
        ValueError: If customer_id is invalid or items list is empty
        CustomerNotFoundError: If customer doesn't exist
        
    Example:
        >>> items = [InvoiceItem(product="Widget", quantity=2, price=10.00)]
        >>> invoice = create_invoice("cust_123", items, datetime.now() + timedelta(days=30))
    """
```

❌ **Bad** (vague or missing):
```python
def create_invoice(customer_id, items, due_date):
    # Creates an invoice
    pass
```

#### README Documentation
✅ **Good** (actionable):
```markdown
## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and set DATABASE_URL and API_KEY
   # Note: Never commit .env to version control
   ```

3. Run database migrations:
   ```bash
   npm run migrate
   ```

4. Start development server:
   ```bash
   npm run dev
   ```

5. Run tests:
   ```bash
   npm test
   ```
```

❌ **Bad** (incomplete):
```markdown
## Setup

Install dependencies and run the app.
```

## Common Mistakes to Avoid

### Process Mistakes
- ❌ Starting work when status.json shows "blocked" or "on-hold"
- ❌ Writing all code first, then adding tests afterward
- ❌ Skipping manual verification because "tests pass"
- ❌ Ignoring linting errors ("I'll fix them later")
- ❌ Committing code that breaks CI
- ❌ Creating 800+ line files instead of refactoring early
- ❌ Forgetting to setup linting/formatting until PR review
- ❌ Not linking PR to relevant artifacts (spec, plan, tasks)

### Code Quality Mistakes
- ❌ Silent error handling (catch without logging or re-throwing)
- ❌ Generic error messages ("Something went wrong")
- ❌ Magic numbers and strings instead of named constants
- ❌ Deep nesting (>3 levels of indentation)
- ❌ Global state or mutable shared state
- ❌ Commented-out code left in commits
- ❌ Console.log or print statements left in production code
- ❌ TODO comments without issue references

### Testing Mistakes
- ❌ Testing implementation details instead of behavior
- ❌ Tests that depend on execution order
- ❌ Over-mocking (testing mocks instead of real behavior)
- ❌ No assertions in tests (test passes but doesn't verify anything)
- ❌ Flaky tests that randomly fail
- ❌ Tests without error case coverage
- ❌ Testing private methods directly instead of through public API

### Security Mistakes
- ❌ Hardcoding secrets (API keys, passwords)
- ❌ Not validating/sanitizing input
- ❌ Logging sensitive data (passwords, tokens)
- ❌ Using weak cryptographic algorithms
- ❌ Ignoring dependency security vulnerabilities
- ❌ Not implementing proper authorization checks

## Validation Checklist

Before considering implementation complete:

### Tests
- [ ] Test infrastructure exists (directories, fixtures, helpers)
- [ ] Tests written before or during implementation
- [ ] All tests pass locally
- [ ] CI tests pass
- [ ] Code coverage >80% for new code
- [ ] Tests cover happy path, edge cases, and error conditions
- [ ] Tests are independent and repeatable
- [ ] Test names clearly describe what they test

### Code Quality
- [ ] All linting issues resolved
- [ ] Code formatted consistently
- [ ] No files exceed 800 lines (or justification provided)
- [ ] Functions are small and focused (<50 lines ideal)
- [ ] Variable and function names are meaningful
- [ ] Error handling is explicit
- [ ] No commented-out code
- [ ] No debug logging statements

### Manual Verification
- [ ] Application runs successfully
- [ ] New functionality exercised manually
- [ ] Error cases tested with bad input
- [ ] Error messages are clear and actionable
- [ ] Logs provide useful information
- [ ] Performance is acceptable
- [ ] Verification steps documented in PR

### Documentation
- [ ] README updated if setup changed
- [ ] API documentation updated if public interfaces changed
- [ ] Configuration documented if new settings added
- [ ] Comments explain "why" for non-obvious code

### Project Standards
- [ ] Follows existing code conventions
- [ ] Dependencies justified and security-scanned
- [ ] Git commits are focused with clear messages
- [ ] PR description links to spec, plan, and tasks
- [ ] "Done when" criteria met for task

## Review Standards

### Self-Review
Before submitting PR, agent should:
1. Run all tests locally and verify they pass
2. Run linter and fix all issues
3. Review git diff for unintended changes
4. Verify manual verification was performed
5. Check that "done when" criteria are met
6. Ensure PR links to relevant artifacts
7. Confirm CI will pass (based on local testing)

### Code Review Criteria (Human or Agent)
Reviewers should validate:
- **Correctness**: Does it implement the requirement correctly?
- **Tests**: Are tests comprehensive and passing?
- **Quality**: Is code modular, readable, and maintainable?
- **Standards**: Does it follow project conventions?
- **Security**: Are there obvious security issues?
- **Documentation**: Is documentation updated appropriately?
- **Size**: Is PR appropriately sized and focused?

### Acceptance Criteria for Implementation
Good implementation passes this test:
- [ ] Can answer: "What does this code do?" (clear purpose)
- [ ] Can answer: "How do I test this?" (tests exist and are clear)
- [ ] Can answer: "Why was it implemented this way?" (tradeoffs documented if non-obvious)
- [ ] Can answer: "What happens if it fails?" (error handling present)
- [ ] Cannot easily break it with common inputs (edge cases handled)

## Examples

### Minimal but Complete Feature Implementation

Even small features need structure:
```
# Feature: Add UUID generation command

src/uuid.py (45 lines):
  - generate_uuid_v4() function
  - CLI argument parsing
  - Error handling

tests/test_uuid.py (60 lines):
  - test_generate_uuid_v4_format()
  - test_uuid_uniqueness()
  - test_cli_returns_uuid()
  - test_cli_exit_code_success()

.flake8 (10 lines):
  - Basic Python linting rules

.github/workflows/test.yml (25 lines):
  - Run tests on push
  - Run linter

README.md (updated):
  - Usage: uuid-gen command
  - Installation instructions
```

### Comprehensive Feature with Tests

```
# Feature: User authentication API

src/auth/
  login.js (120 lines)
  registration.js (95 lines)
  middleware.js (75 lines)
  validation.js (60 lines)

tests/unit/
  login.test.js (150 lines)
    - Valid credentials
    - Invalid password
    - Nonexistent user
    - Account locked
    - Rate limiting
  registration.test.js (140 lines)
    - Valid registration
    - Duplicate email
    - Invalid email format
    - Weak password
    - Missing fields

tests/integration/
  auth-flow.test.js (180 lines)
    - Full registration to login flow
    - Token refresh flow
    - Password reset flow
    - Session management

Manual verification:
  ✓ curl -X POST /api/register with valid data → 201
  ✓ curl -X POST /api/register with duplicate email → 409
  ✓ curl -X POST /api/login with valid creds → 200 + token
  ✓ curl -X POST /api/login with invalid creds → 401
  ✓ curl -X GET /api/protected with token → 200
  ✓ curl -X GET /api/protected without token → 401
```

## Continuous Improvement

The SWE Agent role should evolve based on:
- Code review feedback on quality and maintainability
- Patterns in bugs found during testing or production
- CI failure rates and causes
- Test coverage gaps discovered
- Manual verification findings
- Feedback from downstream agents (Debugging, Security, Testing)

Changes to this quality bar should be proposed via:
1. Issue documenting the problem or pattern
2. Examples of current behavior vs. improved approach
3. Update to this quality-bar.md
4. Update to role.swe.md agent prompt
5. Validation that change doesn't compromise other quality aspects
