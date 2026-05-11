# Quality Bar: Debugging Agent

## Definition of Done

A debugging session is "done" when:
- [ ] Issue is reproducible with documented steps
- [ ] Minimal reproduction case is created
- [ ] Root cause is identified and documented (not just symptom)
- [ ] Regression test exists that fails before fix and passes after fix
- [ ] Fix is minimal and surgical (addresses root cause)
- [ ] Full test suite passes (no new regressions)
- [ ] Manual end-to-end verification confirms fix works
- [ ] Similar issues in codebase are checked and fixed if found
- [ ] Documentation updated if debugging revealed gaps (runbook, README, troubleshooting)
- [ ] Issue comment includes reproduction steps, root cause, and fix summary
- [ ] status.json was checked before starting work

## Structural Standards

### Regression Test Requirements
A good regression test MUST:
- **Fail before fix**: Proves it catches the bug
- **Pass after fix**: Proves the fix works
- **Be minimal**: Tests exactly the bug, no unrelated code
- **Be clear**: Name describes the bug being prevented
- **Be fast**: Runs quickly (<1 second for unit tests, <5 seconds for integration tests)
- **Be deterministic**: Passes reliably (no flakiness)
- **Reference issue**: Comment or docstring links to original bug report

### Test Naming Convention
✅ **Good** (descriptive and specific):
- `test_empty_input_doesnt_crash_parser()` – references issue #123
- `test_concurrent_writes_dont_corrupt_data()` – references issue #456
- `test_missing_config_shows_clear_error()` – references issue #789
- `test_null_user_handled_gracefully()` – references issue #234

❌ **Bad** (vague or generic):
- `test_parser()` – doesn't indicate what bug is prevented
- `test_bug_123()` – doesn't describe the issue
- `test_fix()` – no context about what was fixed
- `test_edge_case()` – not specific about which edge case

### Fix Size Guidelines
- **Typical fix**: 5-20 lines changed
- **Small fix**: <50 lines changed
- **Medium fix**: 50-200 lines changed
- **Large fix**: >200 lines (should be rare; consider if this is really a minimal fix)

If fix exceeds 200 lines, re-evaluate:
- Is this fixing root cause or symptoms?
- Should this be broken into multiple fixes?
- Is broader refactoring being mixed with bug fix?
- Should Architect Agent redesign this component?

### Documentation Standards
Issue comment or debug doc MUST include:
- **Reproduction steps**: Exact commands/actions to reproduce
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens (including error messages, stack traces)
- **Root cause**: Why the issue occurs (1-2 sentences minimum)
- **Fix summary**: What was changed and why (reference PR/commit)
- **Verification**: How fix was verified (automated test + manual testing)

Optional but valuable:
- **Environment details**: OS, versions, configuration if relevant
- **Investigation notes**: Hypotheses tested, blind alleys explored
- **Similar issues**: Related problems found and fixed
- **Prevention measures**: Additional checks or validation added

## Content Quality Standards

### Root Cause Clarity

✅ **Good** (explains why, not just what):
- "Root cause: Parser assumes input is non-empty and dereferences first character without checking length. Fix: Add length check before access."
- "Root cause: Database connection pool exhausted because connections not returned to pool after errors. Fix: Use try-finally to ensure release."
- "Root cause: Race condition between read and write threads accessing shared cache without synchronization. Fix: Add mutex lock around cache operations."

❌ **Bad** (describes symptom or fix without explaining why):
- "Root cause: NullPointerException. Fix: Added null check."
- "Root cause: Test was failing. Fix: Changed assertion."
- "Root cause: Code was wrong. Fix: Fixed code."

### Minimal Fix Principles

✅ **Good** (surgical and focused):
```python
# Before: Bug in authentication
def authenticate(username, password):
    user = db.get_user(username)
    return user.password == password  # Bug: user could be None

# After: Minimal fix
def authenticate(username, password):
    user = db.get_user(username)
    if user is None:
        return False  # Fix: Handle missing user
    return user.password == password
```

❌ **Bad** (unnecessary changes mixed in):
```python
# After: Over-engineered fix with refactoring
def authenticate(username, password):
    """Authenticate user with password."""  # Unrelated: Added docstring
    if not username:  # Unrelated: New validation
        raise ValueError("Username required")
    user = self._get_user_from_database(username)  # Unrelated: Extracted method
    if user is None:
        logger.info(f"Login attempt for unknown user: {username}")  # Unrelated: Added logging
        return False
    is_valid = self._check_password(user, password)  # Unrelated: Extracted method
    if is_valid:
        self._record_login(user)  # Unrelated: New feature
    return is_valid
```

### Regression Test Quality

✅ **Good** (clear, minimal, references issue):
```python
def test_authenticate_returns_false_for_nonexistent_user():
    """Regression test for issue #123: NullPointerException on missing user.
    
    Previously, authenticate() would crash with NullPointerException when
    user doesn't exist. Now it should return False gracefully.
    """
    result = authenticate("nonexistent_user", "any_password")
    assert result is False, "Should return False for nonexistent user, not crash"
```

❌ **Bad** (unclear purpose, tests too much):
```python
def test_authentication():
    """Test authentication."""
    # Tests both the bug AND unrelated functionality
    assert authenticate("admin", "correct") is True
    assert authenticate("admin", "wrong") is False
    assert authenticate("nonexistent", "any") is False  # Buried bug fix
    assert authenticate("", "") is False
```

## Common Mistakes to Avoid

### Investigation Errors
- ❌ Skipping reproduction step and fixing based on guess
- ❌ Fixing symptoms without understanding root cause
- ❌ Not documenting reproduction steps for verification
- ❌ Accepting "I can't reproduce it" without gathering more information
- ❌ Ignoring intermittent failures as "flaky tests"

### Fix Errors
- ❌ Making large refactoring changes while fixing bug
- ❌ Fixing multiple unrelated issues in same PR
- ❌ Adding features or improvements while fixing bug
- ❌ Over-engineering solution (complex fix for simple bug)
- ❌ Copy-pasting similar code instead of creating shared utility

### Testing Errors
- ❌ Writing test that passes even before fix (doesn't catch bug)
- ❌ Writing flaky test that sometimes fails
- ❌ Test is too broad and covers unrelated functionality
- ❌ Test name doesn't describe what bug is prevented
- ❌ Not verifying test is deterministic (running 10x+)

### Process Errors
- ❌ Starting work when status.json shows "blocked" or "on-hold"
- ❌ Not checking for similar issues elsewhere in codebase
- ❌ Not updating documentation when gaps are discovered
- ❌ Not running full test suite to check for regressions
- ❌ Skipping manual verification after fix

### Communication Errors
- ❌ Not documenting findings in issue comment
- ❌ Marking issue as "fixed" without explaining root cause
- ❌ Not linking regression test to original issue
- ❌ Failing to escalate when stuck after reasonable effort

## Validation Checklist

Before considering debugging complete, verify:

### Reproduction
- [ ] Issue reproduced locally with exact steps documented
- [ ] Minimal reproduction case created (removed non-essential code)
- [ ] Environment details documented if issue is environment-specific
- [ ] Intermittent issues have triggering conditions identified

### Root Cause
- [ ] Root cause clearly identified (not just symptom)
- [ ] Analysis uses systematic approach (scientific method, binary search, etc.)
- [ ] "5 whys" or similar deep analysis performed
- [ ] Root cause explanation is clear and understandable

### Regression Test
- [ ] Test exists and is committed
- [ ] Test fails on buggy code (verified by temporarily reverting fix)
- [ ] Test passes with fix applied
- [ ] Test runs quickly (<1 second for unit test)
- [ ] Test passes consistently when run 10+ times (no flakiness)
- [ ] Test name clearly describes bug being prevented
- [ ] Test includes comment referencing original issue

### Fix Quality
- [ ] Fix addresses root cause (not symptom)
- [ ] Fix is minimal and surgical (<50 lines ideal, <200 lines acceptable)
- [ ] No unrelated changes mixed in
- [ ] No over-engineering or premature optimization
- [ ] Similar issues in codebase checked and fixed

### Verification
- [ ] Full test suite passes (no new regressions)
- [ ] Manual end-to-end verification performed
- [ ] Original reproduction steps no longer cause issue
- [ ] Edge cases related to bug are tested

### Documentation
- [ ] Issue comment includes reproduction steps
- [ ] Issue comment includes root cause explanation
- [ ] Issue comment includes fix summary
- [ ] Runbook or troubleshooting guide updated if applicable
- [ ] README updated if setup was unclear

### Prevention
- [ ] Additional validation or assertions considered
- [ ] CI checks considered for preventing this class of bugs
- [ ] Team awareness if bug represents common pattern

## Review Standards

### Self-Review
Before submitting fix, agent should:
1. Re-read root cause explanation and verify it makes sense
2. Verify regression test actually fails before fix
3. Run full test suite to check for regressions
4. Check for similar issues elsewhere in codebase
5. Confirm fix is minimal (no unrelated changes)
6. Verify documentation updates are clear and helpful

### Peer Review (Human or Agent)
Reviewers should validate:
- Root cause analysis is sound and addresses "why" not just "what"
- Regression test is meaningful and would catch the bug
- Fix is minimal and doesn't include unrelated changes
- No new issues introduced by the fix
- Documentation is sufficient for future debugging

### Acceptance Criteria for the Fix Itself
A good fix passes this test:
- [ ] Can answer: "What was the root cause?" (specific, not vague)
- [ ] Can answer: "Why does this fix solve it?" (not just "it works now")
- [ ] Can answer: "How do we know it won't happen again?" (regression test)
- [ ] Can answer: "Are there similar issues?" (checked and addressed)
- [ ] Cannot answer: "What other improvements are included?" (none - focused fix only)

## Examples

### Minimal Reproduction Case
✅ **Good** (stripped to essentials):
```python
# Bug: Parser crashes on empty input
# Minimal reproduction:
result = parse("")  # Crashes with IndexError
```

❌ **Bad** (too much context):
```python
# Bug: Parser crashes on empty input
# Includes unnecessary setup
app = create_app()
client = app.test_client()
response = client.post('/api/parse', json={'input': ''})
# Harder to see the core issue
```

### Root Cause Documentation
✅ **Good** (clear and specific):
```markdown
**Root Cause**: 
Parser assumes input has at least one character and accesses `input[0]` 
without checking length. When input is empty string, this causes IndexError.

**Why it wasn't caught**: 
No tests with empty input. All existing tests used non-empty strings.

**Fix**: 
Added length check before accessing first character. Returns empty list for 
empty input (consistent with spec).
```

### Systematic Debugging Example
✅ **Good** (shows methodology):
```markdown
**Investigation Process**:

Hypothesis 1: Input validation is missing
- Prediction: Adding print statement before `input[0]` will show empty string
- Test: Added `print(f"input: '{input}'")`
- Result: Confirmed input is "" ✓

Hypothesis 2: Empty input should be rejected earlier
- Checked spec: Spec says "return empty list for empty input"
- Conclusion: Parser should handle empty input, not reject it

**Root Cause Identified**: 
Parser accesses `input[0]` without checking if input is non-empty.

**Fix**: 
Add `if not input: return []` before accessing input[0].
```

## Debugging Technique Examples

### Binary Search with Git Bisect
```markdown
**Issue**: Test started failing sometime in last 20 commits

**Investigation**:
```bash
git bisect start
git bisect bad HEAD  # Current commit fails
git bisect good HEAD~20  # 20 commits ago passes
# Git bisect finds the bad commit automatically
git bisect run ./run_test.sh test_authentication
# Result: Commit abc123 introduced the bug
```

**Root Cause**: 
Commit abc123 changed password hashing algorithm but didn't update test fixtures.
```

### Instrumentation for Race Condition
```markdown
**Issue**: Test fails intermittently (1 in 10 runs)

**Investigation**:
Added logging around shared cache access:
```python
logger.debug(f"[{thread_name}] Acquiring cache lock")
with cache_lock:
    logger.debug(f"[{thread_name}] Lock acquired, reading cache")
    value = cache.get(key)
    logger.debug(f"[{thread_name}] Cache value: {value}")
```

**Analysis of logs**:
- Thread A reads cache, value is None
- Thread B writes to cache
- Thread A attempts to use value (None) and crashes
- **Root Cause**: Race condition - no lock protecting read-modify-write

**Fix**: 
Extended lock to cover entire read-modify-write sequence.
```

## Continuous Improvement

The Debugging Agent role should evolve based on:
- Patterns in bugs that could have been caught earlier
- Effectiveness of regression tests (do they actually prevent recurrence?)
- Feedback from downstream agents on debugging artifacts
- Time to reproduction and time to fix metrics
- Quality of root cause analysis (are fixes lasting?)

Changes to this quality bar should be proposed via:
1. Issue documenting recurring problem or improvement opportunity
2. Example of current vs. improved approach
3. Update to this quality-bar.md
4. Update to role.debugging.md agent prompt
5. Validation that change improves debugging outcomes
