# Architecture: SWE Agent

## Overview

The SWE (Software Engineering) Agent serves as the primary implementation specialist within the Kerrigan agent swarm. It transforms architectural plans and task lists into working, tested, maintainable code following test-driven development practices. The agent bridges the gap between design artifacts and functioning software by implementing features incrementally, maintaining high code quality standards, and ensuring continuous integration remains green throughout development.

The agent's architecture emphasizes early quality infrastructure setup, continuous testing, and manual verification alongside automated checks. Unlike traditional "code-then-test" approaches, this agent integrates testing as a first-class activity during implementation, treating test code with the same importance as production code.

## Components & interfaces

### Input Sources
- **plan.md**: Milestone-based roadmap defining incremental deliverables
- **tasks.md**: Granular work items with "done when" criteria
- **architecture.md**: System design, components, interfaces, and tradeoffs
- **test-plan.md**: Testing strategy and coverage goals
- **spec.md**: Requirements and acceptance criteria for reference
- **status.json**: Project workflow status (must check before starting work)
- **Existing codebase**: Current implementation for consistency and patterns

### Core Processing Components

**Status Checker**
- Validates project status before starting work
- Reads status.json and checks for "blocked" or "on-hold" states
- Reports blocked_reason and stops if project is not active

**Input Analyzer**
- Reads plan.md to identify current milestone
- Parses tasks.md for work items with "done when" criteria
- Reviews architecture.md for design constraints and patterns
- Consults test-plan.md for testing requirements
- Identifies dependencies between tasks

**Test Generator**
- Creates test infrastructure early (test directories, fixtures, mocking utilities)
- Writes failing tests before or during implementation (TDD approach)
- Generates unit tests for individual functions and classes
- Creates integration tests for component interactions
- Develops edge case tests (error conditions, boundary values)
- Ensures tests are maintainable and follow testing best practices

**Code Implementer**
- Implements features incrementally following TDD cycle
- Creates modular, focused functions (<50 lines ideal)
- Structures code to avoid blob files (warns at 400 LOC, fails at 800 LOC)
- Handles errors explicitly (no silent failures)
- Follows existing code conventions and patterns
- Writes self-documenting code with meaningful names
- Adds comments sparingly (explains "why" not "what")

**Linter/Formatter Runner**
- Sets up linting configuration early (first milestone)
- Configures formatting tools (.editorconfig, .prettierrc, etc.)
- Runs linting tools frequently during development
- Fixes all linting issues before committing
- Ensures consistent code style across project
- Validates code against project conventions

**Manual Verifier**
- Runs application after implementation
- Exercises new functionality interactively
- Tests error cases with bad input, missing resources
- Verifies error messages are clear and actionable
- Checks logs for proper formatting and useful information
- Ensures performance is acceptable for typical use cases
- Documents verification steps in PR description

**Documentation Updater**
- Updates README when usage patterns change
- Creates or updates API documentation for public interfaces
- Documents configuration changes in setup guides
- Ensures documentation reflects current implementation
- Links documentation to relevant code sections

### Output Artifacts
- **Source code**: Modular, tested, well-structured implementation
- **Test code**: Comprehensive test suite with >80% coverage
- **Linting configuration**: .eslintrc, .flake8, clippy.toml, etc.
- **Formatting configuration**: .prettierrc, .editorconfig, etc.
- **CI configuration**: GitHub Actions, GitLab CI, or equivalent
- **Documentation updates**: README, API docs, setup guides
- **Git commits**: Focused commits with clear messages
- **Pull requests**: Small, reviewable PRs linking to artifacts

### Validation Interface
- Agent output must satisfy:
  - All tests pass (green CI)
  - Linting passes with no errors
  - Code coverage >80% for new code
  - No files exceed 800 lines without justification
  - Manual verification completed and documented
  - "Done when" criteria met for tasks

## Data flow (conceptual)

```
[plan.md, tasks.md, architecture.md]
        ↓
[Status Check] → (if blocked) → [Stop & Report]
        ↓
[Input Analyzer] → Identify current milestone/tasks
        ↓
[Test Infrastructure Setup] → (first milestone only)
        ↓
[For each task:]
        ↓
[Test Generator] → Write failing test
        ↓
[Code Implementer] → Implement feature
        ↓
[Run Tests] → Test passes
        ↓
[Linter/Formatter] → Fix issues
        ↓
[Manual Verifier] → Exercise functionality
        ↓
[Documentation Updater] → (if public API changed)
        ↓
[Commit & Push] → CI runs
        ↓
[CI Passes?] ─No→ [Fix immediately] ─→ [Commit & Push]
        ↓Yes
[Task Complete] → Next task or PR ready
```

## Tradeoffs

### TDD (Test-First) vs. Implementation-First
**Decision**: Tests written before or during implementation, never after
- **Pro**: Catches bugs early; ensures testable design; provides executable specifications; higher confidence
- **Con**: Slower initial implementation; requires discipline; may need test refactoring
- **Mitigation**: Accept slower pace as quality investment; use test patterns; refactor tests alongside code

### Early Quality Infrastructure vs. "Setup Later"
**Decision**: Linting, formatting, and CI configuration in first milestone
- **Pro**: Prevents quality debt; catches issues early; establishes standards from start; easier enforcement
- **Con**: Upfront overhead; may need reconfiguration; can feel like bureaucracy for small projects
- **Mitigation**: Use minimal sensible defaults; customize as needed; even small projects benefit from linting

### File Size Limits vs. Pragmatic Flexibility
**Decision**: Warn at 400 LOC, fail at 800 LOC without justification
- **Pro**: Encourages modularity; improves maintainability; easier testing and review
- **Con**: May force artificial splits; some files naturally larger (config, generated code)
- **Mitigation**: Allow exceptions with justification; focus on logical cohesion; generated files exempt

### Manual Verification vs. "Tests Are Enough"
**Decision**: Require both automated tests and manual verification
- **Pro**: Catches integration issues; validates user experience; verifies error messages; builds confidence
- **Con**: Takes time; may feel redundant; requires running environment
- **Mitigation**: Manual tests are quick smoke tests, not exhaustive; automate common verification scenarios

### Small PRs vs. Large Feature Branches
**Decision**: Keep PRs small (<500 lines typically), aligned with tasks or milestones
- **Pro**: Faster reviews; easier to understand; reduces merge conflicts; enables incremental delivery
- **Con**: More PRs to manage; may require feature flags; coordination overhead
- **Mitigation**: Use milestone-based PRs; keep milestones small; leverage CI for confidence

### Strict Code Standards vs. Developer Freedom
**Decision**: Enforce linting and conventions via automation, allow flexibility within guidelines
- **Pro**: Consistent codebase; reduces bikeshedding; automated enforcement; easier onboarding
- **Con**: May constrain creativity; linter may be wrong; can feel restrictive
- **Mitigation**: Team can customize rules; focus on important patterns; allow overrides with justification

### Dependency Minimalism vs. Using Libraries
**Decision**: Add dependencies judiciously; justify each; security-scan before adding
- **Pro**: Smaller attack surface; fewer updates; less bloat; better understanding
- **Con**: May reinvent wheels; more code to maintain; slower development
- **Mitigation**: Use well-maintained libraries for complex problems; avoid micro-dependencies; balance pragmatically

## Security & privacy notes

### Code Security Practices
- SWE Agent must follow secure coding practices:
  - **Input validation**: Validate and sanitize all external input
  - **Output encoding**: Encode output appropriately (HTML, SQL, etc.)
  - **Error handling**: Don't leak sensitive information in errors
  - **Authentication/Authorization**: Implement according to architecture.md
  - **Secret management**: Never hardcode secrets; use environment variables or secret management systems

### Dependency Security
- Security-scan all new dependencies before adding
- Keep dependencies updated with security patches
- Minimize dependency count to reduce attack surface
- Pin versions appropriately to ensure reproducible builds
- Document security-relevant dependencies

### Code Review for Security
- Security Agent reviews code after SWE Agent implementation
- SWE Agent focuses on basic security hygiene, Security Agent does deep review
- Common issues SWE Agent should avoid:
  - SQL injection (use parameterized queries)
  - Cross-site scripting (escape output)
  - Path traversal (validate file paths)
  - Insecure deserialization
  - Weak cryptography

### Secrets in Code
- Never commit secrets (API keys, passwords, tokens)
- Use .gitignore to exclude secret files
- Reference secrets via environment variables
- Document required secrets in README
- If secret accidentally committed, rotate immediately

### Test Data Security
- Don't use production data in tests
- Generate realistic test fixtures
- Sanitize any real data used for testing
- Be mindful of PII in test outputs and logs

### Manual Verification Security
- Test security features during manual verification:
  - Authentication works and fails appropriately
  - Authorization prevents unauthorized access
  - Error messages don't leak sensitive details
  - Logs don't contain secrets
- Verify security headers, HTTPS requirements, etc.

### Alignment with Security Agent
- SWE Agent implements security features per architecture.md
- Security Agent reviews and enhances security posture
- Handoff: SWE Agent provides working secure implementation → Security Agent validates and strengthens
- SWE Agent may need to implement security fixes identified by Security Agent
