# Spec: Testing Agent

## Goal

Strengthen test infrastructure, increase test coverage, eliminate flaky tests, and improve overall test quality to ensure high confidence in the codebase and reliable CI/CD pipelines.

## Scope

- Analyzing coverage gaps and adding missing test cases
- Improving test quality (clear assertions, better error messages, faster execution)
- Fixing flaky tests and improving test reliability
- Creating test utilities, fixtures, and helpers to reduce duplication
- Adding edge case and error condition tests
- Implementing property-based and performance tests where appropriate
- Optimizing slow tests without sacrificing coverage
- Improving test isolation and independence
- Updating test-plan.md with current coverage metrics and testing strategy
- Setting up or improving test infrastructure (mocking utilities, test data generators)

## Non-goals

- Initial test infrastructure setup (SWE Agent's responsibility during implementation)
- Writing tests for new features before they exist (SWE Agent does TDD during implementation)
- Deep debugging of application code (Debugging Agent's responsibility)
- Security-specific test scenarios (Security Agent adds after security review)
- Performance optimization of production code (focus is on test code quality)
- Creating specifications or requirements (Spec Agent's responsibility)

## Users & scenarios

### Primary Users
- **SWE Agent**: Relies on test utilities and patterns established by Testing Agent
- **Debugging Agent**: Uses comprehensive tests to isolate and reproduce issues
- **Security Agent**: Builds upon test infrastructure for security testing
- **CI/CD Pipeline**: Depends on fast, reliable tests for confidence in deployments
- **Human Developers**: Reference tests as documentation and use for regression safety
- **Future Maintainers**: Depend on tests to understand behavior and prevent regressions

### Key Scenarios
1. **Coverage Gap Analysis**: Runs coverage tool → Identifies untested paths → Adds tests for gaps → Coverage increases to >80%
2. **Flaky Test Elimination**: CI intermittently fails → Identifies flaky test → Fixes time dependencies or race conditions → Test is reliable
3. **Test Quality Improvement**: Tests exist but failures are cryptic → Adds clear assertions and error messages → Failures are self-explanatory
4. **Test Speed Optimization**: Test suite takes 15 minutes → Identifies slow tests → Optimizes without losing coverage → Suite runs in 5 minutes
5. **Edge Case Coverage**: Feature works for happy path → Adds boundary condition tests → Discovers bugs in edge cases
6. **Test Infrastructure**: Tests have lots of duplication → Creates reusable fixtures and helpers → Tests are more maintainable
7. **Documentation Update**: Coverage improved significantly → Updates test-plan.md with new metrics and strategy

## Constraints

- Must maintain or increase test coverage (never remove tests without replacement)
- Must keep CI green (fix or skip broken tests, don't leave them failing)
- Must preserve existing test behavior (only fix or enhance, don't break working tests)
- Should aim for >80% code coverage for critical paths
- Should keep unit test suites under 5 minutes execution time
- Must check project status.json before starting work
- Must update test-plan.md to reflect changes in testing strategy or coverage
- Should follow existing test patterns and conventions in the codebase
- Must align with constitution principles (quality from day one, automated verification)

## Acceptance criteria

- Test coverage >80% for critical code paths (measured via coverage tools)
- All tests pass consistently (no flaky tests in CI)
- Test execution time is acceptable (unit tests <5 minutes, integration tests <15 minutes typically)
- Test failures include clear error messages explaining what failed and why
- Edge cases and error conditions have test coverage
- Tests can run in any order (isolation maintained)
- Test utilities and helpers exist to reduce duplication
- Complex test scenarios are documented with comments
- test-plan.md is updated with current coverage metrics and testing strategy
- New tests follow existing patterns and conventions
- Performance-critical paths have performance tests (if applicable)
- Tests serve as documentation of expected behavior

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing tests while improving them | High | Run full test suite after each change; use version control; make small incremental improvements |
| Over-testing trivial code, wasting effort | Medium | Focus on risk areas and business logic; skip trivial getters/setters; use coverage tools to prioritize |
| Tests become too slow, developers skip them | High | Set execution time budgets; optimize slow tests; parallelize where possible; measure and track test performance |
| Test improvements introduce new flakiness | Medium | Run tests multiple times (10x) before merging; eliminate non-determinism; use fixed time/randomness in tests |
| Missing edge cases despite high coverage | Medium | Encourage property-based testing; review boundary conditions systematically; test error paths explicitly |
| Test infrastructure becomes over-engineered | Low | Keep utilities simple and focused; prefer standard patterns; avoid premature abstraction |
| Spending time on low-value test improvements | Medium | Prioritize based on CI failure rates and coverage gaps; focus on critical paths first |

## Success metrics

- Code coverage >80% for critical paths (minimum acceptable; target >90% for business logic)
- Test flakiness rate <1% (tests pass consistently across 100+ runs)
- Unit test suite execution time <5 minutes
- Integration test suite execution time <15 minutes
- Zero failing tests in main branch (green CI >99% of the time)
- Test-related CI failures reduced by >50% after Testing Agent work
- Clear failure diagnostics (developers can identify root cause from test output in <2 minutes)
- Test utility adoption (tests using shared helpers are more maintainable)
- Reduced test duplication (LOC of test code decreases while coverage increases)
- Downstream agents report test infrastructure is comprehensive and useful (qualitative feedback)
