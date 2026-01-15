# Architecture: Testing Agent

## Overview

The Testing Agent operates as a test quality and reliability specialist within the Kerrigan agent swarm. It strengthens the test infrastructure established by the SWE Agent during initial implementation, focusing on coverage expansion, test quality improvement, flaky test elimination, and test performance optimization. The agent bridges the gap between "tests exist" and "tests provide high confidence" by systematically analyzing coverage gaps, improving test clarity, and ensuring CI reliability.

The agent's architecture emphasizes incremental improvement over wholesale replacement. It works with existing test infrastructure and patterns, enhancing what's there rather than rebuilding from scratch. The Testing Agent uses coverage analysis tools, test execution metrics, and CI feedback to prioritize improvements that deliver the highest impact on code confidence and development velocity.

## Components & interfaces

### Input Sources
- **Existing test suite**: Current test files, patterns, and conventions
- **test-plan.md**: Testing strategy, coverage goals, and tooling decisions
- **Coverage reports**: Output from coverage tools (pytest-cov, istanbul, go coverage, etc.)
- **CI logs and metrics**: Test execution times, failure rates, flaky test patterns
- **Source code**: Implementation to understand what needs testing
- **spec.md**: Requirements and acceptance criteria to ensure coverage
- **architecture.md**: System design to guide integration test scenarios
- **status.json**: Project workflow status (must check before starting work)

### Core Processing Components

**Status Checker**
- Validates project status before starting work
- Reads status.json and checks for "blocked" or "on-hold" states
- Reports blocked_reason and stops if project is not active

**Coverage Analyzer**
- Runs coverage tools (pytest-cov, istanbul/c8, go test -cover, cargo tarpaulin, etc.)
- Identifies uncovered lines, branches, and functions
- Prioritizes gaps based on code criticality (business logic > glue code > trivial code)
- Generates coverage reports in multiple formats (terminal, HTML, JSON)
- Tracks coverage metrics over time

**Gap Identifier**
- Parses coverage reports to find untested code paths
- Analyzes control flow for missing branch coverage
- Identifies error handling paths without tests
- Finds boundary conditions not exercised by existing tests
- Prioritizes gaps by risk and impact

**Test Generator**
- Creates new test cases for uncovered code paths
- Writes tests for edge cases (empty input, null, max values, negative numbers)
- Adds error condition tests (invalid input, missing resources, exceptions)
- Implements boundary value tests
- Generates property-based tests for complex input spaces
- Creates performance tests for critical paths
- Follows existing test patterns and conventions

**Test Quality Analyzer**
- Reviews existing tests for clarity and maintainability
- Identifies vague assertions ("assert result" instead of "assert result == expected")
- Detects missing failure messages
- Finds magic numbers and unclear test data
- Checks test naming conventions (descriptive vs. generic)
- Evaluates test documentation adequacy

**Test Enhancer**
- Improves assertion clarity (adds expected vs. actual in messages)
- Adds descriptive failure messages to assertions
- Renames tests to be more descriptive (test_login_success → test_login_with_valid_credentials_returns_token)
- Documents complex test scenarios with comments
- Replaces magic values with named constants
- Extracts test setup into well-named helper functions

**Flakiness Detector**
- Analyzes CI logs for intermittent failures
- Identifies patterns in flaky tests (time-dependent, order-dependent, resource-dependent)
- Runs tests multiple times (10x, 100x) to verify stability
- Detects non-deterministic behavior (randomness without seeding, wall clock usage)
- Identifies tests with external dependencies (network, file system, databases)

**Flakiness Eliminator**
- Fixes time-dependent tests (mock clocks, use deterministic time)
- Resolves race conditions (add proper synchronization, use test-specific timing)
- Mocks external dependencies (network calls, file I/O, third-party APIs)
- Ensures test isolation (independent state, proper cleanup)
- Seeds randomness for reproducibility
- Adds retries for tests that must interact with flaky systems (with clear marking)

**Performance Profiler**
- Measures test execution time at suite and individual test level
- Identifies slow tests (>1 second for unit tests is concerning)
- Profiles test setup and teardown overhead
- Detects redundant operations (repeated database setup, file I/O)
- Tracks test performance trends over time

**Test Optimizer**
- Reduces test execution time without losing coverage
- Converts slow tests to faster alternatives (in-memory instead of disk, mocks instead of real services)
- Parallelizes independent tests
- Shares expensive setup across tests (using fixtures, test class setup)
- Batches operations when appropriate
- Removes redundant tests (identical coverage to other tests)

**Test Infrastructure Builder**
- Creates reusable fixtures for common test data
- Develops test utilities and helper functions
- Builds mocking utilities for frequently mocked components
- Implements test data generators
- Creates shared test setup/teardown functions
- Develops property-based testing helpers

**Test Isolator**
- Ensures tests can run in any order
- Eliminates shared mutable state between tests
- Adds proper setup and teardown (before/after each test)
- Validates test independence (run single test, run in random order)
- Fixes inter-test dependencies

**Documentation Updater**
- Updates test-plan.md with current coverage metrics
- Documents new testing patterns and utilities
- Explains complex test scenarios
- Records testing decisions and rationale
- Updates tooling and framework documentation

### Output Artifacts
- **Enhanced test suite**: Tests with better coverage, quality, and reliability
- **Test utilities and fixtures**: Reusable test infrastructure
- **Coverage reports**: Current coverage metrics with gap analysis
- **Updated test-plan.md**: Reflects current testing strategy and coverage
- **Test documentation**: Comments and docstrings for complex tests
- **CI improvements**: Faster, more reliable test execution
- **Flakiness reports**: Identified and fixed flaky tests

### Validation Interface
- Agent output must satisfy:
  - Coverage >80% for critical paths (measured and documented)
  - All tests pass consistently (flakiness <1%)
  - Test execution time meets targets (unit <5 min, integration <15 min typically)
  - Clear failure messages in all assertions
  - Tests run independently in any order
  - test-plan.md updated with current metrics

## Data flow (conceptual)

```
[Existing Tests + Coverage Reports + CI Logs]
        ↓
[Status Check] → (if blocked) → [Stop & Report]
        ↓
[Coverage Analyzer] → Run coverage tools
        ↓
[Gap Identifier] → Prioritize uncovered code
        ↓
[Test Generator] → Add tests for gaps
        ↓
[Test Quality Analyzer] → Review existing tests
        ↓
[Test Enhancer] → Improve clarity and assertions
        ↓
[Flakiness Detector] → Identify unreliable tests
        ↓
[Flakiness Eliminator] → Fix root causes
        ↓
[Performance Profiler] → Measure execution time
        ↓
[Test Optimizer] → Speed up slow tests
        ↓
[Test Infrastructure Builder] → Create reusable utilities
        ↓
[Test Isolator] → Ensure independence
        ↓
[Documentation Updater] → Update test-plan.md
        ↓
[Run Full Test Suite] → Validate improvements
        ↓
[CI Passes?] ─No→ [Fix Issues] ─→ [Run Tests Again]
        ↓Yes
[Commit & Push] → Enhanced test suite ready
```

## Tradeoffs

### Coverage Percentage vs. Test Value
**Decision**: Target >80% coverage but focus on critical paths, not 100%
- **Pro**: Maximizes confidence where it matters; avoids testing trivial code; efficient use of time
- **Con**: Some code remains untested; requires judgment on what's critical
- **Mitigation**: Prioritize business logic, error handling, and integration points; document coverage decisions in test-plan.md

### Test Speed vs. Comprehensiveness
**Decision**: Optimize for fast feedback (<5 min unit tests) but maintain comprehensive coverage
- **Pro**: Fast tests encourage frequent running; quick CI feedback; better developer experience
- **Con**: Some comprehensive tests may need to move to slower suites; might skip some scenarios
- **Mitigation**: Separate unit, integration, and e2e tests; run appropriate suite for context; use parallelization

### Test Isolation vs. Setup Efficiency
**Decision**: Prioritize test isolation even if it means redundant setup
- **Pro**: Tests can run in any order; failures are easier to diagnose; better parallelization
- **Con**: More setup overhead; potentially slower execution
- **Mitigation**: Use fixtures to share expensive setup where safe; optimize setup operations themselves

### Fixing Flaky Tests vs. Marking as Expected-Flaky
**Decision**: Fix flaky tests when possible; only mark as expected-flaky for genuinely uncontrollable flakiness (rare)
- **Pro**: Maintains trust in test suite; prevents "boy who cried wolf" syndrome
- **Con**: Takes time to fix properly; some flakiness is external (third-party services)
- **Mitigation**: Invest time in proper fixes; mock external dependencies; use retries only when necessary and clearly marked

### Property-Based Testing vs. Example-Based Testing
**Decision**: Use property-based testing for complex input spaces, example-based for specific scenarios
- **Pro**: Property-based finds edge cases automatically; example-based is clearer and more targeted
- **Con**: Property-based can be harder to understand; requires learning curve
- **Mitigation**: Use both approaches; property tests for invariants, example tests for specific behaviors; document property test intentions

### Test Refactoring Scope
**Decision**: Improve tests incrementally, don't rewrite entire suite
- **Pro**: Lower risk; easier to validate; maintains test history; steady progress
- **Con**: May leave some technical debt; can feel slower than wholesale rewrite
- **Mitigation**: Prioritize improvements by impact; refactor opportunistically when touching tests; track progress

### Test Infrastructure Complexity
**Decision**: Keep test utilities simple and focused; avoid over-engineering
- **Pro**: Easier to understand and maintain; less cognitive overhead; faster onboarding
- **Con**: May have some duplication; might need to evolve utilities over time
- **Mitigation**: Extract utilities when pattern appears 3+ times; prefer standard testing framework features; document utilities clearly

## Security & privacy notes

### Test Data Security
- Testing Agent must not use production data in tests
- Generate realistic but synthetic test data
- Sanitize any real data before using in tests (anonymize PII)
- Be mindful of sensitive information in test outputs and logs

### Secret Management in Tests
- Never commit secrets in test code (API keys, passwords, tokens)
- Use environment variables or test-specific secret management
- Mock authentication and authorization where possible
- Document required test secrets in test-plan.md

### Security Test Coverage
- Testing Agent ensures security-relevant code paths are tested:
  - Authentication (valid credentials succeed, invalid fail)
  - Authorization (proper access controls enforced)
  - Input validation (injection attacks prevented)
  - Error handling (no information leakage in errors)
- Security Agent later adds specialized security tests
- Handoff: Testing Agent provides comprehensive test infrastructure → Security Agent adds security-specific scenarios

### Test Isolation Security
- Tests should not expose secrets via shared state
- Proper cleanup prevents test data leakage
- Test databases and resources should be isolated from production

### CI Security
- Test execution in CI should not require production credentials
- Use test-specific service accounts and credentials
- Ensure test environments are properly isolated

### Vulnerability in Test Dependencies
- Keep test dependencies updated with security patches
- Scan test dependencies for vulnerabilities (same as production dependencies)
- Minimize test dependency count to reduce attack surface

### Alignment with Security Agent
- Testing Agent creates test infrastructure with security in mind
- Security Agent reviews tests for security adequacy and adds security-specific tests
- Handoff: Testing Agent provides comprehensive, reliable test suite → Security Agent enhances with security scenarios
