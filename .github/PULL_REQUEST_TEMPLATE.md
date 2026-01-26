## What
Describe what this PR changes.

## Why
Why is this change needed?

## Links
- Project folder: `specs/projects/<project-name>/`
- Milestone/task:

## Agent Signature (if applicable)
<!-- If you're working as an agent, include your signature below to verify you used the agent prompt -->
<!-- Generate using: python tools/agent_audit.py create-signature role:yourRole -->
<!-- Example: -->
<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->

## Testing Classification

### Automated Tests
<!-- List automated tests added or modified -->
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All existing tests pass

### Manual Testing Required
<!-- List functionality that requires manual verification. Add `needs:manual-testing` label if applicable. -->
- [ ] No manual testing required

<!-- Examples:
- [ ] **Workflow: workflow-name.yml** - Trigger condition, verify expected behavior
- [ ] **UI Component** - Visual verification of styling and interactions
- [ ] **Authentication Flow** - Test with real credentials
- [ ] **External API Integration** - Test with real endpoints
-->

### Cannot Test (with justification)
<!-- List items that cannot be tested and explain why -->
- N/A

<!-- Examples:
- External webhook signatures - Requires third-party signing keys
- Production environment configuration - No test environment available
-->

## Checklist
- [ ] CI is green
- [ ] Tests added/updated (or justified)
  - If tests added: Cite specific test files and counts
  - If no tests added: Explain why (e.g., "Documentation only", "Requires manual OAuth flow")
  - Report actual test counts from test runner output
- [ ] Manual testing completed (if required)
- [ ] Docs updated (spec/plan/runbook as needed)
- [ ] No unnecessary large files or monoliths
- [ ] Secrets not committed

## Testing Details

### Automated Tests
<!-- Be specific and factually accurate about testing. Do NOT fabricate test counts. -->

**Tests Added:**
<!-- Example: "Added 5 new tests in tests/test_auth.py (lines 34-67)" -->
<!-- Or: "No new tests added - changes are documentation only" -->

**Test Results:**
<!-- Example: "All 236 tests pass - Ran 236 tests in 0.4s" -->
<!-- Include actual output from test runner -->

### Manual Testing
<!-- If applicable, describe manual testing performed -->
<!-- Example: "Manually verified authentication flow with OAuth provider" -->
<!-- Or: "No manual testing required" -->
