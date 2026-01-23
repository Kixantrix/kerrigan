---
title: Quality Bar
version: 1.0.0
source: Kerrigan (original)
quality_tier: 1
last_reviewed: 2026-01-23
last_updated: 2026-01-22
reviewed_by: kerrigan-maintainers
license: MIT
tags: [quality, standards, testing, code-review]
applies_to: [all]
---

# Quality Bar

Kerrigan's non-negotiable quality standards and enforcement mechanisms. This skill ensures agents produce maintainable, reviewable, and production-ready work from day one.

## When to Apply

Reference this skill when:
- Starting any implementation work
- Reviewing code or artifacts
- Receiving quality bar violations from CI
- Making architecture decisions that affect maintainability
- Unsure if code is "good enough" to submit

## Core Principles

From the [Kerrigan Constitution](../../specs/constitution.md):

1. **Quality from day one** - No "prototype mode", start with structure and tests
2. **Small, reviewable increments** - Keep PRs narrow and CI green
3. **Tests are part of the feature** - Every feature has tests, every bug fix has a regression test
4. **Maintainable code** - Prefer modular code over giant single files

## File Size Limits

### The 800-Line Rule

**No file should exceed 800 lines without justification.**

**Why 800 lines?**
- Reviewable in one session (~30 minutes)
- Fits on screen without excessive scrolling
- Encourages modular design
- Reduces cognitive load
- Makes debugging easier

**How to comply:**
```
✅ DO: Break into modules
src/
├── models/
│   ├── user.js (200 lines)
│   └── post.js (180 lines)
├── controllers/
│   ├── auth.js (250 lines)
│   └── posts.js (220 lines)
└── utils/
    └── validation.js (150 lines)

❌ DON'T: Monolithic files
src/
└── app.js (2400 lines) ← TOO LARGE
```

**When exceptions are needed:**
- Auto-generated files (mark with comment at top)
- Configuration files with repetitive structure (e.g., long enum lists)
- Test files with many similar test cases (consider test helpers)

If file MUST exceed 800 lines, add justification at top:
```javascript
/**
 * EXCEEDS_FILE_SIZE_LIMIT
 * Reason: Auto-generated OpenAPI client from spec (1200 lines)
 * Review status: Approved by architect 2026-01-20
 */
```

### Enforcement

CI automatically checks file sizes:
```bash
# Run locally before PR
python tools/validators/check_quality_bar.py

# Or use Kerrigan CLI
kerrigan validate --quality-bar
```

## Testing Standards

### Every Feature Has Tests

**Rule:** You don't have a feature unless it has tests.

**Test types:**
- **Unit tests**: Test functions/classes in isolation
- **Integration tests**: Test components working together
- **Acceptance tests**: Test user scenarios from spec.md

**Minimum coverage:**
- Happy path (normal use cases)
- Error paths (invalid inputs, failures)
- Edge cases (boundary conditions, empty/null/zero)

**Example:**
```typescript
// Feature: User registration
// Required tests:
describe('User Registration', () => {
  it('registers user with valid data (happy path)')
  it('rejects duplicate email (error path)')
  it('validates email format (edge case)')
  it('handles database errors gracefully (error path)')
  it('rejects empty name/email (edge case)')
})
```

### Every Bug Fix Has a Regression Test

**Rule:** Before fixing a bug, write a test that reproduces it.

**Process:**
1. Write test that fails (demonstrates bug)
2. Fix the bug
3. Verify test now passes
4. Submit both test and fix together

This prevents the bug from returning.

## Code Organization

### Modular Design

**Prefer many small files over few large files.**

**Good organization:**
```
src/
├── models/           # Data models
├── controllers/      # Business logic
├── routes/          # API endpoints
├── middleware/      # Express/similar middleware
├── utils/           # Shared utilities
└── config/          # Configuration
```

**Signs of poor organization:**
- Files with unrelated functions (utils.js with 50 random functions)
- Deeply nested directories (src/a/b/c/d/e/file.js)
- Unclear naming (stuff.js, temp.js, new-file-2.js)

### Clear Naming

**Use descriptive, consistent names.**

**Files:**
- `user-controller.js` not `uc.js`
- `email-validator.js` not `validator.js`
- `post-routes.js` not `routes2.js`

**Functions:**
- `calculateTotalPrice()` not `calc()`
- `isValidEmail()` not `check()`
- `fetchUserById()` not `get()`

**Variables:**
- `customerEmail` not `e`
- `productList` not `arr`
- `maxRetries` not `n`

## Code Quality

### No Dead Code

Remove unused:
- Functions not called anywhere
- Imports not used
- Commented-out code blocks
- Files not imported

Use linters to detect:
```bash
# JavaScript/TypeScript
npx eslint src/ --rule 'no-unused-vars: error'

# Python
pylint src/ --disable=all --enable=unused-import,unused-variable
```

### No Secrets in Code

**Never commit:**
- API keys
- Passwords
- Access tokens
- Private keys
- Database credentials

**Use instead:**
- Environment variables (`process.env.API_KEY`)
- Secret management (AWS Secrets Manager, etc.)
- .env files (with .env in .gitignore)

**Check before committing:**
```bash
# Scan for potential secrets
git diff | grep -i -E "(password|secret|key|token)" && echo "⚠️ Possible secret detected"
```

### Input Validation

**Always validate external input:**
- User input (forms, APIs)
- File uploads
- Environment variables
- External API responses

**Example:**
```typescript
// ✅ Good: Validate before use
function getUserByEmail(email: string) {
  if (!isValidEmail(email)) {
    throw new ValidationError('Invalid email format')
  }
  return db.users.findByEmail(email)
}

// ❌ Bad: No validation
function getUserByEmail(email: string) {
  return db.users.findByEmail(email) // SQL injection risk
}
```

## Documentation Standards

### Inline Documentation

Document:
- **Why** not **what** (code shows what, comments explain why)
- Complex algorithms or business logic
- Non-obvious decisions
- Workarounds for bugs/limitations

**Good comments:**
```javascript
// Use bcrypt with 12 rounds per OWASP recommendations (2026)
const hash = await bcrypt.hash(password, 12)

// Retry up to 3 times to handle transient network errors
const result = await retryOperation(fetchData, { maxAttempts: 3 })
```

**Bad comments:**
```javascript
// Set i to 0
let i = 0

// Loop through array
for (let item of items) { ... }
```

### Public API Documentation

Document all public APIs/functions:
- Purpose
- Parameters (types, constraints)
- Return values
- Exceptions/errors
- Examples (if complex)

**Example:**
```typescript
/**
 * Fetches user by ID from database
 * 
 * @param userId - Unique user identifier (UUID format)
 * @returns User object or null if not found
 * @throws DatabaseError if query fails
 * 
 * @example
 * const user = await getUserById('123e4567-e89b-12d3-a456-426614174000')
 */
async function getUserById(userId: string): Promise<User | null>
```

### README Requirements

Every project must have README.md with:
- **What it does**: Brief description
- **How to build**: Build commands
- **How to test**: Test commands
- **How to run**: Run commands
- **Dependencies**: What needs to be installed first

## PR Standards

### Keep PRs Small

**Ideal PR size:** 200-500 lines of code changes

**Why small PRs?**
- Faster reviews (30 minutes vs. 3 hours)
- Easier to understand
- Lower risk of bugs
- Simpler to revert if needed

**How to keep PRs small:**
- Break work into milestones
- One feature per PR
- Refactoring separate from features
- Documentation updates separate from code

### Keep CI Green

**Rule:** All PRs must pass CI before merge.

**CI checks:**
- Validators (artifacts, contracts)
- Tests (unit, integration)
- Linters (code style)
- Security scans (CodeQL)

**If CI fails:**
1. Read the error message carefully
2. Reproduce locally if possible
3. Fix the issue
4. Re-run CI
5. Don't bypass CI (no `[skip ci]` unless approved)

### PR Description Checklist

Every PR should include:
- [ ] What changed (summary)
- [ ] Why it changed (rationale)
- [ ] How to test it (steps)
- [ ] Related artifacts (spec, architecture, tasks)
- [ ] Agent signature (for auditing)
- [ ] Screenshots (if UI changes)

## Common Quality Issues

### ❌ Prototype Mode
**Problem:** "I'll clean this up later" - quick hack without tests

**Impact:** Technical debt, hard to maintain, bugs

**Solution:** Write it right the first time. Tests and structure from day one.

### ❌ Giant PRs
**Problem:** 3000-line PR with 20 files changed

**Impact:** Impossible to review thoroughly, high risk

**Solution:** Break into milestones. Submit 3 PRs of 1000 lines each, or 10 PRs of 300 lines.

### ❌ Unclear Naming
**Problem:** Variables named `data`, `temp`, `x`, functions named `doIt()`

**Impact:** Code is unreadable, hard to maintain

**Solution:** Spend 10 seconds to name things clearly. Future you will thank you.

### ❌ No Error Handling
**Problem:** Code assumes everything works, no error paths

**Impact:** Crashes on unexpected input, poor user experience

**Solution:** Add try/catch, validate inputs, handle failures gracefully.

### ❌ Missing Tests
**Problem:** "It works on my machine" - no automated tests

**Impact:** Breaks in production, regressions, no confidence

**Solution:** Write tests before or during implementation, not after.

## Enforcement Mechanisms

### Automated (CI)
- File size limits (800 lines)
- Test execution (all must pass)
- Linting (code style)
- Security scanning (secrets, vulnerabilities)
- Artifact validation (structure, content)

### Human (PR Review)
- Code clarity and maintainability
- Architecture alignment
- Test quality (not just coverage)
- Documentation completeness
- Security considerations

### Agent Self-Check
Before submitting PR, ask:
- [ ] All tests pass locally?
- [ ] No files > 800 lines (or justified)?
- [ ] New features have tests?
- [ ] Code is clear and well-organized?
- [ ] No secrets committed?
- [ ] README updated if needed?

## References

- [Constitution](../../specs/constitution.md) - Core principles
- [Quality Bar Spec](../../specs/kerrigan/030-quality-bar.md) - Full specification
- [Artifact Contracts](./artifact-contracts.md) - File structure requirements
- [Examples](../../examples/) - See quality bar in practice

## Updates

**v1.0.0 (2026-01-22):** Initial version based on Kerrigan quality bar specification
