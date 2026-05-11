# Acceptance tests: Testing Agent

## Coverage Analysis and Expansion

- [ ] **Given** a codebase with test coverage, **When** Testing Agent analyzes coverage, **Then** coverage gaps are identified and prioritized
- [ ] **Given** coverage gaps identified, **When** Testing Agent adds tests, **Then** coverage increases toward >80% target
- [ ] **Given** a function without tests, **When** Testing Agent adds tests, **Then** happy path, edge cases, and error conditions are covered
- [ ] **Given** coverage report, **When** reviewing, **Then** critical code paths have >90% coverage
- [ ] **Given** untested error handling, **When** Testing Agent adds tests, **Then** all error paths are exercised

## Test Quality Improvement

- [ ] **Given** tests with vague assertions, **When** Testing Agent improves them, **Then** assertions are specific with clear failure messages
- [ ] **Given** a failing test, **When** reviewing output, **Then** failure message explains what failed and why (includes expected vs actual)
- [ ] **Given** test with unclear purpose, **When** Testing Agent enhances it, **Then** test name clearly describes what is tested
- [ ] **Given** complex test scenario, **When** Testing Agent documents it, **Then** comments explain the setup and expectations
- [ ] **Given** tests with magic values, **When** Testing Agent improves them, **Then** values are replaced with named constants or explained

## Flaky Test Elimination

- [ ] **Given** a flaky test in CI, **When** Testing Agent investigates, **Then** root cause is identified (timing, race condition, external dependency)
- [ ] **Given** test with time dependency, **When** Testing Agent fixes it, **Then** test uses deterministic time (mocked clock or fixed time)
- [ ] **Given** test with race condition, **When** Testing Agent fixes it, **Then** proper synchronization or test isolation is added
- [ ] **Given** test depending on external service, **When** Testing Agent fixes it, **Then** external dependency is mocked or stubbed
- [ ] **Given** flaky test, **When** fix is applied, **Then** test passes consistently (verified with multiple runs: 10x for unit tests, 100x for critical integration tests)

## Test Speed Optimization

- [ ] **Given** slow test suite, **When** Testing Agent analyzes it, **Then** slow tests are identified with execution time metrics
- [ ] **Given** slow test identified, **When** Testing Agent optimizes it, **Then** execution time decreases without losing coverage
- [ ] **Given** tests with redundant setup, **When** Testing Agent refactors, **Then** shared fixtures reduce setup time
- [ ] **Given** unit test suite >5 minutes, **When** Testing Agent optimizes, **Then** suite runs in <5 minutes
- [ ] **Given** tests with file I/O, **When** Testing Agent optimizes, **Then** in-memory alternatives are used where appropriate

## Test Isolation and Independence

- [ ] **Given** tests that depend on execution order, **When** Testing Agent fixes them, **Then** tests can run in any order
- [ ] **Given** tests sharing mutable state, **When** Testing Agent isolates them, **Then** each test has independent state
- [ ] **Given** tests with side effects, **When** Testing Agent adds cleanup, **Then** teardown properly resets state
- [ ] **Given** test suite, **When** running in random order, **Then** all tests still pass
- [ ] **Given** test suite, **When** running single test in isolation, **Then** test passes without requiring others to run first

## Test Infrastructure

- [ ] **Given** duplicate test setup code, **When** Testing Agent refactors, **Then** shared fixtures or helpers are created
- [ ] **Given** complex test data needs, **When** Testing Agent adds generators, **Then** reusable test data generators are available
- [ ] **Given** common mocking patterns, **When** Testing Agent creates utilities, **Then** mocking utilities reduce boilerplate
- [ ] **Given** test fixtures needed, **When** Testing Agent creates them, **Then** fixtures are well-organized and documented
- [ ] **Given** new test infrastructure, **When** checking adoption, **Then** existing tests are refactored to use new utilities

## Edge Case and Error Condition Testing

- [ ] **Given** function with boundary conditions, **When** Testing Agent adds tests, **Then** boundaries are tested (empty input, max values, null/undefined)
- [ ] **Given** function that can throw errors, **When** Testing Agent adds tests, **Then** each error condition is tested with proper assertions
- [ ] **Given** API endpoint, **When** Testing Agent adds tests, **Then** invalid input, missing parameters, and auth failures are tested
- [ ] **Given** concurrent access scenario, **When** Testing Agent adds tests, **Then** race conditions and thread safety are verified
- [ ] **Given** resource limits, **When** Testing Agent adds tests, **Then** behavior under constraint is validated (memory, connections, etc.)

## Property-Based Testing

- [ ] **Given** function with many input combinations, **When** Testing Agent adds property tests, **Then** property-based test framework generates test cases
- [ ] **Given** property-based tests, **When** failures occur, **Then** framework provides minimal failing example (shrinking works)
- [ ] **Given** invariants to maintain, **When** Testing Agent adds property tests, **Then** invariants are verified across input space

## Performance and Load Testing

- [ ] **Given** performance-critical code, **When** Testing Agent adds performance tests, **Then** execution time and resource usage are measured
- [ ] **Given** API endpoints, **When** Testing Agent adds load tests, **Then** behavior under load is verified (response time, error rate)
- [ ] **Given** performance regression, **When** performance tests run, **Then** regression is detected and reported

## Test Documentation and Maintainability

- [ ] **Given** complex test scenario, **When** Testing Agent documents it, **Then** comments explain the "why" not just the "what"
- [ ] **Given** test utilities created, **When** checking documentation, **Then** utilities have clear docstrings explaining usage
- [ ] **Given** test patterns used, **When** Testing Agent documents them, **Then** patterns are explained in test-plan.md
- [ ] **Given** test-plan.md, **When** Testing Agent updates it, **Then** current coverage metrics and testing strategy are reflected

## CI Reliability

- [ ] **Given** tests in CI, **When** they run, **Then** failure rate is <1% (excluding legitimate bugs)
- [ ] **Given** test timeout, **When** Testing Agent adds timeout handling, **Then** hanging tests are terminated with clear messages
- [ ] **Given** flaky CI, **When** Testing Agent investigates, **Then** environmental issues are identified and fixed
- [ ] **Given** CI pipeline, **When** checking test execution, **Then** tests run in parallel where appropriate for speed
- [ ] **Given** test failures in CI, **When** reviewing output, **Then** logs are clear and actionable

## Status and Workflow

- [ ] **Given** project with status.json, **When** Testing Agent starts work, **Then** agent checks status is "active" or file doesn't exist
- [ ] **Given** status.json shows "blocked", **When** Testing Agent starts work, **Then** agent stops and reports blocked_reason
- [ ] **Given** status.json shows "on-hold", **When** Testing Agent starts work, **Then** agent stops without proceeding

## Test Plan Updates

- [ ] **Given** significant coverage improvements, **When** Testing Agent completes work, **Then** test-plan.md is updated with new metrics
- [ ] **Given** new testing patterns introduced, **When** Testing Agent updates test-plan.md, **Then** patterns are documented for future reference
- [ ] **Given** test infrastructure changes, **When** Testing Agent updates test-plan.md, **Then** tooling and approach are documented
- [ ] **Given** risk areas identified, **When** Testing Agent updates test-plan.md, **Then** high-priority areas for testing are noted

## Integration with Other Agents

- [ ] **Given** test utilities created by Testing Agent, **When** SWE Agent writes new features, **Then** utilities are available and documented
- [ ] **Given** comprehensive test coverage, **When** Debugging Agent investigates issues, **Then** tests help isolate and reproduce problems
- [ ] **Given** test infrastructure, **When** Security Agent adds security tests, **Then** infrastructure supports security test patterns
- [ ] **Given** updated test-plan.md, **When** Architect Agent plans new features, **Then** testing strategy is clear and reusable

## Edge Cases

- [ ] **Given** test that must remain flaky (integration with flaky external system), **When** Testing Agent handles it, **Then** test is marked as expected-flaky with retry logic
- [ ] **Given** generated code without coverage, **When** Testing Agent analyzes, **Then** generated code is excluded from coverage requirements
- [ ] **Given** codebase with existing test technical debt, **When** Testing Agent prioritizes work, **Then** high-impact areas are addressed first
- [ ] **Given** test that requires slow external resource, **When** Testing Agent handles it, **Then** test is moved to integration/e2e suite (not unit tests)
- [ ] **Given** legacy code without tests, **When** Testing Agent adds tests, **Then** characterization tests are added to preserve existing behavior before refactoring

## Quality Metrics

- [ ] **Given** Testing Agent completes work, **When** measuring coverage, **Then** coverage is >80% for critical paths
- [ ] **Given** test suite after optimization, **When** measuring execution time, **Then** unit tests complete in <5 minutes
- [ ] **Given** tests after quality improvements, **When** running 100 times, **Then** flakiness rate is <1%
- [ ] **Given** test failures, **When** developers investigate, **Then** root cause is identifiable from test output in <2 minutes
