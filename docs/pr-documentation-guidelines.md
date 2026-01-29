# PR Documentation Guidelines

## Purpose

This document establishes standards for PR descriptions and documentation to ensure accuracy and prevent fabricated or simulated content from being presented as factual work.

## Core Principle

**Document what actually happened, not what could have happened or should have happened.**

## Guidelines

### 1. Factual Accuracy Required

PR descriptions and documentation MUST:
- ✅ Describe actual work performed (code written, files created, tests added)
- ✅ Reference real commits, PRs, and issues that exist
- ✅ Document actual timeline if any timeline is mentioned
- ✅ Reflect actual review and approval processes
- ❌ NOT fabricate process steps that didn't occur
- ❌ NOT simulate workflows or create fictional narratives
- ❌ NOT claim human intervention that didn't happen
- ❌ NOT invent timestamps, durations, or phases

### 2. Distinguish Real Work from Examples

**When documenting actual work:**
- Use past tense: "Created X", "Added Y", "Fixed Z"
- Reference actual artifacts: specific files, commit hashes, PR numbers
- Keep timeline claims verifiable against git history
- Document what was actually reviewed and approved

**When creating examples/tutorials:**
- Clearly mark as "Example", "Tutorial", "Demo", or "Simulation"
- Use conditional/future language: "would create", "could be used", "example flow"
- Place in appropriate locations (examples/, docs/tutorials/)
- Don't mix with factual PR documentation

### 3. Appropriate Use Cases

| Content Type | Appropriate For | Marking Required |
|--------------|----------------|------------------|
| Factual documentation | PR descriptions, commit messages, CHANGELOG | None - default expectation |
| Working code example | examples/ directory, README code blocks | "Example:" or location context |
| Tutorial/walkthrough | docs/, playbooks/ | "Tutorial:", "How-to:" |
| Simulated workflow | Feature demonstrations, onboarding docs | "Simulated:", "Example workflow:" |

### 4. Red Flags to Avoid

The following indicate potential fabrication:

🚩 **Fictional timelines**: "5 hours of development", "2 pause/resume cycles" when git history shows 20 minutes
🚩 **Non-existent PRs**: "Created PR #1, #2, #3" when those PRs don't exist
🚩 **Fabricated reviews**: "Human approved after 30 minutes" with no review comments
🚩 **Simulated agents**: Agent signatures for work that wasn't done in phases
🚩 **Disproportionate docs**: 70KB of process documentation for 400 LOC of code
🚩 **Elaborate narratives**: Multi-phase stories that don't match simple commit history

### 5. Good Examples

**✅ Good - Factual PR Description:**
```markdown
## Changes
- Added Task Tracker CLI with auth and task management (~400 LOC)
- Implemented tests with 92% coverage (36 tests)
- Created README with usage examples

## Files Created
- task_tracker/cli.py (141 lines)
- task_tracker/auth.py (85 lines)
- tests/test_basic.py (105 lines)

All files comply with <800 LOC quality standard.
```

**✅ Good - Example Documentation:**
```markdown
## Example Workflow (Simulated)

This example shows how status.json could be used in a project:

1. Create status.json at project start
2. Set to "blocked" when needing review
3. Resume by changing to "active"

*Note: This is an illustrative example. See examples/ for working code.*
```

**❌ Bad - Fabricated Documentation:**
```markdown
## Development Process (5 hours)

Phase 1: Specification (30 min) - Spec agent created spec.md
- Paused for human review (30 min)
- PR #1 created and approved

Phase 2: Architecture (45 min) - Architect agent created plan
- Paused for review (20 min)
- PR #2 created and approved

[This describes work that never happened]
```

### 6. When Demonstrating Features

If asked to "demonstrate" or "show" a feature:

**DO:**
- Build working code that actually uses the feature
- Create real examples in examples/ directory
- Document how to run and verify the feature
- Show actual output/results

**DON'T:**
- Create fictional narratives about using the feature
- Simulate a workflow without actually executing it
- Document imaginary PRs, reviews, or processes
- Write elaborate backstories instead of working code

### 7. Documentation-to-Code Ratios

Be mindful of disproportionate documentation:

- **Healthy**: 400 LOC code, 1-2KB README, 2-3KB implementation notes
- **Questionable**: 400 LOC code, 70KB of process documentation
- **Red flag**: More time writing about the process than doing the work

If documentation greatly exceeds code size, ask:
- Is this tutorial content that should be marked as such?
- Am I documenting fictional process instead of actual work?
- Should this be split into code + separate tutorial?

## Enforcement

### Manual Review

Reviewers should watch for:
- Timeline claims that seem unrealistic
- References to non-existent PRs or issues
- Overly elaborate process descriptions
- Disproportionate documentation-to-code ratios

### Automated Validation (Planned)

Future validators may check:
- PR/issue references actually exist
- Timeline claims are reasonable given git history
- Agent signatures match actual PR creation times
- Documentation size is proportional to changes

## Related Documents

- [Agent Auditing](agent-auditing.md) - How to track which agents did what
- [Agent Specs](../specs/kerrigan/agents/) - Quality standards per agent
- [Artifact Contracts](../specs/kerrigan/020-artifact-contracts.md) - Required deliverables

## Test Reporting Standards

**CRITICAL**: Test claims in PRs must be factually accurate and verifiable.

### Requirements

When documenting testing in PRs:

✅ **DO:**
- State specific test files added: "Added 5 new tests in tests/test_auth.py"
- Report actual test counts: "All 226 tests pass" or "All 231 tests pass (226 existing + 5 new)"
- Include test runner output: "Ran 226 tests in 0.4s - OK"
- Be explicit when no tests added: "No new tests added - documentation only"
- Explain why tests can't be added if applicable: "Manual testing only - requires OAuth"

❌ **DON'T:**
- Fabricate test counts or invent numbers
- Use vague language: "All tests passing" without specifics
- Claim tests were added when no test files changed
- Report test numbers that don't match actual test runner output

### Examples

**✅ Good - Specific and Verifiable:**
```markdown
## Testing
- Added 8 new unit tests in tests/unit/test_validator.py (lines 45-123)
- All 234 tests pass (226 existing + 8 new)
- Test run output:
  ```
  Ran 234 tests in 0.4s
  OK
  ```
```

**✅ Good - Honest Reporting Without New Tests:**
```markdown
## Testing
- No new tests added (changes are to documentation only)
- Existing 226 tests still pass
- Validated changes manually by reviewing rendered documentation
```

**❌ Bad - Vague and Unverifiable:**
```markdown
## Testing
All tests passing (39 tests)
```

### CI Validation

The repository includes a validator (`tools/validators/check_test_claims.py`) that checks for:
1. Test claims without corresponding test file changes
2. Vague test claims lacking specifics
3. Known fabricated test numbers (e.g., "39 tests")
4. Missing test runner output

This validator runs automatically on PRs to help catch misleading claims early.

## Questions?

If unsure whether something is appropriate:
- Ask: "Am I documenting what happened or what I wish had happened?"
- Default to factual: Describe the actual work performed
- When in doubt: Mark as "Example" or "Simulation" to be safe
