# Architecture: Debugging Agent

## Overview

The Debugging Agent operates as a systematic problem-solver within the Kerrigan agent swarm. It applies structured debugging methodologies to investigate failures, identify root causes, implement targeted fixes, and prevent future occurrences through comprehensive regression testing. Unlike general-purpose development agents, the Debugging Agent specializes in diagnostic workflows, hypothesis testing, and creating minimal, surgical fixes that address underlying problems rather than surface symptoms.

The agent's architecture emphasizes reproducibility, traceability, and prevention. Each debugging session follows a deliberate progression: reproduce → investigate → fix → prevent, with each phase producing concrete artifacts (reproduction steps, instrumentation, regression tests, documentation updates) that benefit both immediate issue resolution and long-term system quality.

## Components & interfaces

### Input Sources
- **Bug reports/issues**: Problem descriptions from users, CI failures, production incidents, or manual testing
- **status.json**: Project workflow status file (if exists) - agent must check before proceeding
- **Codebase**: Source code, tests, configuration files to investigate and modify
- **Execution environment**: Local development environment, logs, debuggers, profilers
- **Version control history**: Git log, blame, bisect for identifying when issues were introduced
- **CI/CD artifacts**: Test results, build logs, deployment history
- **Existing documentation**: Runbooks, architecture docs, troubleshooting guides

### Core Processing Components

#### 1. Reproduction Engine
Establishes reliable reproduction of the reported issue.
- **Environment Analyzer**: Compares environments to identify configuration differences
- **Minimal Case Generator**: Strips away non-essential code to create minimal reproduction
- **Intermittent Issue Handler**: Identifies conditions that trigger sporadic failures (timing, load, state)
- **Documentation Generator**: Records exact reproduction steps for verification and regression testing

#### 2. Root Cause Analyzer
Applies systematic debugging techniques to identify underlying problems.
- **Scientific Method Framework**: Structures investigation as hypothesis → prediction → test → analyze
  - Forms hypotheses about potential causes
  - Predicts observable outcomes if hypothesis is correct
  - Designs experiments to test predictions
  - Analyzes results to confirm or refute hypothesis
- **Binary Search Engine**: Isolates issues through systematic elimination
  - Git bisect for regression identification
  - Component isolation for complex systems
  - Condition isolation for intermittent failures
- **Instrumentation Manager**: Adds logging and debugging hooks
  - Structured logging at decision points
  - Timing and performance instrumentation
  - State capture (input parameters, variables)
- **Pattern Matcher**: Recognizes common bug patterns
  - Race conditions (intermittent failures, timing dependencies)
  - Resource leaks (gradual degradation, unclosed resources)
  - Configuration issues (environment-specific failures)
  - Off-by-one errors (boundary condition failures)
- **Historical Analyzer**: Reviews code history for context
  - Git blame for identifying relevant changes
  - Related issue search for similar problems
  - Recent commit review for regression tracking

#### 3. Fix Implementer
Creates minimal, targeted fixes that address root causes.
- **Root Cause Validator**: Ensures fix addresses underlying problem, not symptoms
- **Surgical Editor**: Makes minimal code changes to fix the issue
- **Similar Issue Finder**: Searches codebase for related patterns to fix proactively
- **Defensive Code Injector**: Adds validation, assertions, and error handling
- **Impact Analyzer**: Assesses potential side effects and regression risks

#### 4. Regression Test Generator
Creates tests that prevent issue recurrence.
- **Test Scaffolder**: Generates test structure based on issue type
- **Failure Verifier**: Ensures test fails on buggy code
- **Success Verifier**: Confirms test passes with fix applied
- **Stability Checker**: Runs test multiple times to ensure determinism
- **Edge Case Expander**: Adds boundary condition tests related to the bug

#### 5. Prevention System
Enhances codebase resilience against future issues.
- **Validation Injector**: Adds startup checks and early failure detection
- **Assertion Injector**: Places strategic assertions to catch issues earlier
- **Documentation Updater**: Improves runbooks, troubleshooting guides, and architecture docs
- **CI Enhancement Advisor**: Suggests CI checks to catch issue class automatically

### Output Artifacts
- **Regression test**: Automated test that would have caught the bug
- **Fix PR**: Minimal code changes addressing root cause
- **Reproduction documentation**: Issue comment or debug doc with exact reproduction steps
- **Root cause analysis**: Clear explanation of why the issue occurred
- **Documentation updates**: Enhanced runbooks, troubleshooting guides, or setup instructions
- **Related fixes**: Proactive fixes for similar issues found during investigation

### Validation Interface
- Regression test must fail before fix and pass after fix
- Full test suite must pass after fix (no new regressions introduced)
- Manual verification confirms end-to-end functionality
- Code review validates fix is minimal and addresses root cause

## Data flow

```
[Bug Report/Failure]
        ↓
[Status Check] → (if blocked/on-hold) → [Stop & Report]
        ↓
[Reproduction Engine]
   ├─→ [Environment Analysis]
   ├─→ [Minimal Case Generation]
   └─→ [Reproduction Documentation]
        ↓
[Root Cause Analyzer]
   ├─→ [Scientific Method Framework] ─→ [Hypothesis Testing]
   ├─→ [Binary Search Engine] ────────→ [Issue Isolation]
   ├─→ [Instrumentation Manager] ─────→ [Data Gathering]
   ├─→ [Pattern Matcher] ─────────────→ [Pattern Recognition]
   └─→ [Historical Analyzer] ─────────→ [Context Building]
        ↓
   [Root Cause Identified]
        ↓
[Regression Test Generator]
   ├─→ [Test Scaffolder] ─────────────→ [Initial Test]
   ├─→ [Failure Verifier] ────────────→ [Verify Fails Before]
   └─→ [Stability Checker] ───────────→ [Verify Deterministic]
        ↓
[Fix Implementer]
   ├─→ [Root Cause Validator] ────────→ [Validate Fix Target]
   ├─→ [Surgical Editor] ─────────────→ [Minimal Changes]
   ├─→ [Similar Issue Finder] ────────→ [Proactive Fixes]
   └─→ [Impact Analyzer] ─────────────→ [Regression Check]
        ↓
[Success Verifier] ──────────────────→ [Verify Passes After]
        ↓
[Prevention System]
   ├─→ [Validation Injector] ─────────→ [Early Detection]
   ├─→ [Documentation Updater] ───────→ [Knowledge Capture]
   └─→ [CI Enhancement Advisor] ──────→ [Automated Prevention]
        ↓
[Manual Verification] ───────────────→ [End-to-End Testing]
        ↓
[Full Test Suite] ───────────────────→ [Verify No Regressions]
        ↓
[Artifacts Published]
   ├─→ [Fix PR with Regression Test]
   ├─→ [Issue Comment with Analysis]
   └─→ [Updated Documentation]
```

## Tradeoffs

### Reproduction First vs. Quick Fixes
**Decision**: Always reproduce issue before attempting fix; no blind fixes allowed
- **Pro**: Ensures fix actually works; prevents incorrect fixes; enables verification; creates regression test
- **Con**: Takes more time upfront; may be difficult for intermittent or environment-specific issues
- **Mitigation**: Set timeboxes for reproduction attempts; escalate if cannot reproduce; document attempted approaches

### Root Cause vs. Symptom Fixes
**Decision**: Require root cause analysis; reject symptom-only fixes
- **Pro**: Fixes stay fixed; prevents issue recurrence; often reveals related problems; improves system understanding
- **Con**: Takes longer than quick patches; may require deeper system changes; can be difficult for complex issues
- **Mitigation**: Use "5 whys" technique; validate that fix prevents issue at source; accept workarounds only when documented

### Minimal vs. Comprehensive Fixes
**Decision**: Prefer surgical, minimal changes over broad refactoring
- **Pro**: Reduces regression risk; easier to review; faster to merge; clearer cause-effect relationship
- **Con**: May miss opportunities for improvement; could result in piecemeal fixes over time
- **Mitigation**: Note refactoring opportunities for future work; focus on fixing the bug at hand; allow Architect Agent to design broader improvements

### Test-Before vs. Test-After Fix
**Decision**: Write regression test before or during fix implementation (TDD style)
- **Pro**: Ensures test actually catches the bug; validates fix works; prevents test drift from actual bug
- **Con**: May need to adjust test as understanding of bug evolves
- **Mitigation**: Iterate on test as investigation progresses; verify test fails before fix and passes after

### Systematic vs. Intuitive Debugging
**Decision**: Enforce systematic approaches (scientific method, binary search) over gut-feel debugging
- **Pro**: More reliable; teachable; produces documented reasoning; works for complex issues; less bias
- **Con**: Can feel slower for obvious bugs; requires discipline; may seem overly formal
- **Mitigation**: Allow flexibility for trivial bugs; emphasize value for complex issues; document approach for learning

### Documentation Thoroughness vs. Speed
**Decision**: Balance between comprehensive documentation and timely fixes
- **Pro** (thorough): Helps future debugging; builds institutional knowledge; improves onboarding
- **Con** (thorough): Takes time away from fixing more bugs
- **Mitigation**: Require minimum documentation (reproduction steps, root cause, fix summary); optional deep-dive for complex or recurring issues; template for consistency

## Security & privacy notes

### Sensitive Data in Logs
- Debugging often requires examining logs and system state
- Agent must NOT log or expose:
  - API keys, passwords, tokens, or credentials
  - Personally identifiable information (PII)
  - Proprietary business data or trade secrets
- When instrumentation is needed, sanitize sensitive data before logging
- Remove debugging instrumentation before merging if it exposes sensitive paths

### Production Environment Access
- Debugging may require accessing production logs or environments
- Agent should prefer non-production environments when possible
- If production access needed:
  - Document justification for access
  - Use read-only access where possible
  - Follow organization's production access policies
  - Sanitize any data copied from production

### Bug Disclosure
- Bug reports may contain security vulnerabilities
- Agent should flag security-sensitive bugs for Security Agent review
- Avoid disclosing security bugs in public issue trackers before fix is deployed
- Follow responsible disclosure practices

### Regression Test Security
- Regression tests may expose vulnerability details
- Test names and comments should not reveal attack vectors
- Consider separate security test suite for sensitive vulnerabilities
- Balance between clear test documentation and security through obscurity

### Fix Verification
- Some bugs have security implications (validation bypasses, injection vulnerabilities)
- Security Agent should review fixes for security-sensitive bugs
- Consider impact of fix on security posture (does fix introduce new attack surface?)
- Verify fix doesn't inadvertently expose sensitive information

### Instrumentation Risks
- Added logging for debugging can introduce vulnerabilities:
  - Logging user input without sanitization
  - Creating new log injection vectors
  - Performance degradation enabling DoS
- Remove or secure debugging instrumentation before production deployment
- Review all added logging for security implications

### Alignment with Security Agent
- Debugging Agent identifies and fixes functional bugs
- Security Agent reviews architecture and code for security vulnerabilities
- Handoff: Debugging Agent flags security-sensitive bugs → Security Agent validates fix security implications
- Collaboration: Security vulnerabilities discovered during debugging are escalated to Security Agent for comprehensive review
