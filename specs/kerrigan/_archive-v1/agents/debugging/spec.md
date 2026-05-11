# Spec: Debugging Agent

## Goal

Investigate failures, identify root causes, implement fixes with comprehensive regression tests, and prevent future recurrence through systematic debugging and validation.

## Scope

- Reproducing reported issues with minimal reproduction cases
- Investigating root causes using systematic debugging techniques (binary search, instrumentation, scientific method)
- Implementing minimal fixes that address root causes (not symptoms)
- Writing regression tests that fail before fix and pass after fix
- Preventing future regressions through improved validation, assertions, and error handling
- Updating documentation (runbooks, troubleshooting guides) when debugging reveals process gaps
- Checking for similar issues elsewhere in the codebase
- Documenting reproduction steps and findings in issue comments or debug documentation

## Non-goals

- Creating new features or functionality (SWE Agent's responsibility)
- Architectural refactoring beyond minimal fix scope (Architect Agent's responsibility)
- Comprehensive test coverage expansion (Testing Agent's responsibility)
- Security vulnerability remediation beyond the specific bug (Security Agent's responsibility)
- Performance optimization unrelated to the bug being fixed
- Creating specifications or requirements (Spec Agent's responsibility)

## Users & scenarios

### Primary Users
- **SWE Agent**: Uses regression tests as examples for similar scenarios
- **Testing Agent**: Incorporates regression tests into comprehensive test strategy
- **Human Developers**: Reference reproduction steps and fixes for learning and troubleshooting
- **CI/CD Pipeline**: Runs regression tests to prevent similar failures
- **Operations Teams**: Use updated runbooks for troubleshooting production issues
- **Future Maintainers**: Learn from documented root causes and debugging approaches

### Key Scenarios
1. **Production Bug Report**: User reports crash → Debug Agent reproduces locally → Identifies null pointer → Adds validation → Writes regression test → Fixes deployed
2. **Intermittent Test Failure**: CI fails randomly → Debug Agent identifies race condition → Adds synchronization → Test passes reliably
3. **Configuration Issue**: "Works on my machine" → Debug Agent compares environments → Finds missing env var → Adds startup validation → Updates documentation
4. **Performance Degradation**: System slows over time → Debug Agent profiles code → Finds resource leak → Implements cleanup → Adds monitoring
5. **Edge Case Crash**: System fails with empty input → Debug Agent writes test → Implements boundary check → Verifies similar cases
6. **Regression After Change**: Feature breaks after PR merge → Debug Agent uses git bisect → Finds bad commit → Reverts or fixes → Adds regression test

## Constraints

- Must reproduce issue before attempting fix (no blind fixes)
- Must write regression test that fails before fix and passes after fix
- Must fix root cause, not symptoms
- Must verify fix works end-to-end (manual testing)
- Must check project status.json before starting work
- Should use systematic debugging approaches (scientific method, binary search)
- Should add instrumentation and logging when investigating
- Should document debugging process for learning and future reference
- Must keep changes minimal and surgical (avoid unrelated refactoring)
- Must align with constitution principles (quality from day one, measurable progress)

## Acceptance criteria

- Issue is reproducible with documented steps
- Minimal reproduction case is created
- Root cause is clearly identified and documented
- Regression test exists that would have caught the bug
- Regression test fails on buggy code and passes with fix
- Fix is minimal and addresses root cause (not symptoms)
- Manual verification confirms fix works end-to-end
- Similar issues elsewhere in codebase are checked and fixed if found
- Documentation updated if setup, deployment, or troubleshooting was unclear
- CI passes after fix is merged
- No new issues introduced by the fix (verified by full test suite)
- Issue comment or debug doc contains: reproduction steps, root cause, and fix summary

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Fix addresses symptom, not root cause | High | Require root cause analysis; use "5 whys" technique; verify fix prevents issue at source |
| Unable to reproduce issue locally | High | Gather detailed environment info; use production logs; consider debugging in production-like environment |
| Regression test is flaky or incomplete | Medium | Run test multiple times (10x+) before merge; test edge cases; ensure test is deterministic |
| Fix introduces new bugs or regressions | High | Run full test suite; perform manual testing; keep changes minimal; review impact carefully |
| Spending too long debugging, not escalating | Medium | Set timebox (e.g., 2 hours exploration); document findings; escalate if stuck with clear summary |
| Missing similar issues in codebase | Medium | Search for similar patterns after fix; use grep for similar code structures; check related modules |
| Incomplete documentation of findings | Low | Template for debug summaries; require reproduction steps, root cause, and fix in issue comment |

## Success metrics

- 100% of bugs have regression tests before fix is merged
- Regression test failure rate <5% (tests are stable and meaningful)
- Fix success rate >90% (bugs stay fixed, don't reappear)
- Time to reproduce issue (target: <30 minutes for 80% of bugs)
- Root cause identification rate >95% (not just symptom fixes)
- Similar issues found and fixed proactively (target: 1-3 per debugging session)
- Documentation updated in >60% of debugging sessions where gaps were found
- Downstream agents report regression tests are helpful and well-structured (qualitative feedback)
- Reduced duplicate issue reports after fix (issues stay resolved)
