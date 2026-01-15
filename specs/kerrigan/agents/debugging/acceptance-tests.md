# Acceptance tests: Debugging Agent

## Issue Reproduction

- [ ] **Given** a bug report with reproduction steps, **When** Debugging Agent investigates, **Then** issue is reproduced locally with exact steps documented
- [ ] **Given** a bug report without clear steps, **When** Debugging Agent investigates, **Then** agent requests additional information (environment, input, expected vs actual behavior)
- [ ] **Given** a reproduced issue, **When** creating minimal reproduction, **Then** reproduction case removes all non-essential code and dependencies
- [ ] **Given** an intermittent bug, **When** Debugging Agent investigates, **Then** conditions that trigger the bug are identified and documented
- [ ] **Given** "works on my machine" issue, **When** Debugging Agent investigates, **Then** environment differences are identified (OS, versions, configuration)

## Root Cause Analysis

- [ ] **Given** a reproduced bug, **When** Debugging Agent investigates, **Then** root cause is identified (not just symptoms)
- [ ] **Given** a crash or error, **When** analyzing root cause, **Then** stack trace and logs are examined systematically
- [ ] **Given** a bug with unknown cause, **When** Debugging Agent investigates, **Then** instrumentation (logging, debugging) is added to gather data
- [ ] **Given** a bug in recent code, **When** investigating, **Then** git blame and recent commits are reviewed
- [ ] **Given** a complex bug, **When** analyzing, **Then** scientific method is applied (hypothesis → prediction → test → analyze → iterate)
- [ ] **Given** multiple potential causes, **When** debugging, **Then** binary search approach is used to isolate the issue
- [ ] **Given** root cause identified, **When** documenting, **Then** explanation uses "5 whys" or similar deep analysis technique

## Fix Implementation

- [ ] **Given** root cause identified, **When** implementing fix, **Then** fix addresses root cause (not symptoms)
- [ ] **Given** a fix implemented, **When** reviewing changes, **Then** fix is minimal and surgical (no unrelated changes)
- [ ] **Given** a bug with multiple instances, **When** fixing, **Then** all similar issues in codebase are identified and fixed
- [ ] **Given** a fix that could introduce regressions, **When** implementing, **Then** full test suite is run to verify no new issues
- [ ] **Given** a configuration bug, **When** fixing, **Then** startup validation is added to catch issue early
- [ ] **Given** a null pointer bug, **When** fixing, **Then** defensive checks are added with clear error messages

## Regression Testing

- [ ] **Given** a bug fix, **When** creating regression test, **Then** test fails on buggy code before fix
- [ ] **Given** a bug fix, **When** creating regression test, **Then** test passes after fix is applied
- [ ] **Given** a regression test, **When** reviewing, **Then** test name clearly describes the bug being prevented
- [ ] **Given** a regression test, **When** it fails in CI, **Then** failure message explains what broke and references original issue
- [ ] **Given** a regression test, **When** running multiple times (10x+), **Then** test passes consistently (no flakiness)
- [ ] **Given** a regression test, **When** checking execution time, **Then** test completes quickly (<1 second for unit tests)
- [ ] **Given** an edge case bug, **When** creating regression test, **Then** test covers boundary conditions (empty input, max values, null)
- [ ] **Given** an intermittent bug, **When** creating regression test, **Then** test uses deterministic conditions (mocked time, fixed randomness)

## Common Bug Patterns

### Race Conditions
- [ ] **Given** an intermittent failure, **When** Debugging Agent investigates, **Then** race conditions are considered and tested
- [ ] **Given** a race condition identified, **When** fixing, **Then** proper synchronization (locks, events) is added
- [ ] **Given** a race condition fix, **When** testing, **Then** test verifies proper ordering or uses deterministic timing

### Resource Leaks
- [ ] **Given** performance degrading over time, **When** Debugging Agent investigates, **Then** resource usage (memory, file handles) is monitored
- [ ] **Given** a resource leak identified, **When** fixing, **Then** proper cleanup (try/finally, context managers) is implemented
- [ ] **Given** a resource leak fix, **When** testing, **Then** test verifies resources are released properly

### Configuration Issues
- [ ] **Given** a "works on my machine" bug, **When** Debugging Agent investigates, **Then** configuration differences are compared
- [ ] **Given** missing configuration identified, **When** fixing, **Then** startup validation is added with clear error message
- [ ] **Given** a configuration fix, **When** updating documentation, **Then** required configuration is explicitly documented

### Off-by-One Errors
- [ ] **Given** edge case failures, **When** Debugging Agent investigates, **Then** boundary conditions are tested (0, 1, 2 items, max values)
- [ ] **Given** an off-by-one error identified, **When** fixing, **Then** loop bounds and array indices are carefully reviewed
- [ ] **Given** an off-by-one fix, **When** testing, **Then** regression test includes boundary cases

## Debugging Techniques

### Instrumentation
- [ ] **Given** an unclear bug, **When** adding instrumentation, **Then** detailed logging is added at key decision points
- [ ] **Given** a performance issue, **When** adding instrumentation, **Then** timing information is logged
- [ ] **Given** a state-related bug, **When** adding instrumentation, **Then** full context (input parameters, state) is logged
- [ ] **Given** instrumentation added, **When** logging, **Then** structured logging (JSON) is used for easier parsing

### Binary Search
- [ ] **Given** a recent regression, **When** Debugging Agent investigates, **Then** git bisect is used to find the bad commit
- [ ] **Given** an intermittent bug, **When** isolating conditions, **Then** binary search approach identifies triggering factors
- [ ] **Given** a complex system bug, **When** debugging, **Then** components are eliminated one by one to isolate issue

### Rubber Duck Debugging
- [ ] **Given** a complex bug, **When** Debugging Agent documents analysis, **Then** problem is explained step-by-step in writing
- [ ] **Given** debugging explanation documented, **When** reviewing, **Then** explanation helps future developers understand the issue

## Manual Verification

- [ ] **Given** a fix implemented, **When** verifying, **Then** issue is tested manually end-to-end
- [ ] **Given** a fix for a crash, **When** verifying, **Then** original reproduction steps no longer cause crash
- [ ] **Given** a fix for data corruption, **When** verifying, **Then** data integrity is validated manually
- [ ] **Given** a fix for intermittent issue, **When** verifying, **Then** issue is tested multiple times to ensure stability
- [ ] **Given** a fix deployed, **When** verifying, **Then** related functionality is smoke-tested to ensure no regressions

## Documentation Updates

- [ ] **Given** unclear setup discovered during debugging, **When** fixing bug, **Then** README.md is updated with clarifications
- [ ] **Given** troubleshooting steps discovered, **When** fixing bug, **Then** runbook.md is updated with troubleshooting section
- [ ] **Given** incorrect assumptions in architecture, **When** debugging reveals them, **Then** architecture.md is updated
- [ ] **Given** insufficient test coverage discovered, **When** fixing bug, **Then** test-plan.md is updated with identified gaps
- [ ] **Given** documentation updated, **When** reviewing, **Then** updates are clear and actionable for future debugging

## Issue Communication

- [ ] **Given** debugging completed, **When** updating issue, **Then** comment includes reproduction steps
- [ ] **Given** debugging completed, **When** updating issue, **Then** comment includes root cause explanation
- [ ] **Given** debugging completed, **When** updating issue, **Then** comment includes fix summary and verification
- [ ] **Given** debugging incomplete, **When** stuck, **Then** agent documents what was tried and results
- [ ] **Given** debugging needs more info, **When** requesting information, **Then** specific questions are asked (environment, logs, steps)

## Proactive Issue Prevention

- [ ] **Given** a bug fixed, **When** checking codebase, **Then** similar patterns are searched and fixed proactively
- [ ] **Given** a validation bug fixed, **When** reviewing code, **Then** additional assertions are considered to catch similar issues earlier
- [ ] **Given** a bug class identified, **When** fixing, **Then** CI checks are considered to prevent this class of bugs
- [ ] **Given** a common bug pattern, **When** fixing, **Then** team is notified of the pattern for awareness

## Status and Workflow

- [ ] **Given** project with status.json, **When** Debugging Agent starts work, **Then** agent checks status is "active" or file doesn't exist
- [ ] **Given** status.json shows "blocked", **When** Debugging Agent starts work, **Then** agent stops and reports blocked_reason
- [ ] **Given** status.json shows "on-hold", **When** Debugging Agent starts work, **Then** agent stops without proceeding

## Escalation

- [ ] **Given** 2 hours of debugging without progress, **When** Debugging Agent evaluates, **Then** findings are documented and escalation is considered
- [ ] **Given** unable to reproduce issue, **When** escalating, **Then** agent documents attempted approaches and requests specific information
- [ ] **Given** fix unclear or risky, **When** escalating, **Then** agent proposes workarounds and outlines risks
- [ ] **Given** stuck on complex issue, **When** escalating, **Then** agent provides clear summary for human developer handoff

## Edge Cases

- [ ] **Given** a bug in third-party dependency, **When** debugging, **Then** agent documents findings and considers workarounds or updates
- [ ] **Given** a bug requiring environment-specific testing, **When** debugging, **Then** agent requests access or guidance for testing
- [ ] **Given** a bug with security implications, **When** fixing, **Then** Security Agent is notified for review
- [ ] **Given** a bug requiring architectural change, **When** identified, **Then** Architect Agent is consulted for design guidance
- [ ] **Given** a bug in legacy code without tests, **When** fixing, **Then** characterization tests are added before making changes
- [ ] **Given** a bug requiring breaking change, **When** fixing, **Then** impact is assessed and documented before proceeding

## Quality Metrics

- [ ] **Given** debugging completed, **When** measuring outcomes, **Then** regression test exists and is stable
- [ ] **Given** bug fixed, **When** checking CI, **Then** all tests pass including the new regression test
- [ ] **Given** fix merged, **When** checking later, **Then** issue does not reappear (fix is permanent)
- [ ] **Given** debugging session, **When** reviewing time spent, **Then** reproduction took <30 minutes for straightforward bugs
- [ ] **Given** fix implemented, **When** reviewing, **Then** root cause was addressed (not just symptom)
