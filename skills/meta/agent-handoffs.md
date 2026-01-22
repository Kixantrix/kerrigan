---
title: Agent Handoffs
version: 1.0.0
source: Kerrigan (original)
last_updated: 2026-01-22
license: MIT
---

# Agent Handoffs

How agents pass work between roles in Kerrigan's sequential workflow. This skill ensures smooth transitions, clear expectations, and artifact-driven collaboration.

## When to Apply

Reference this skill when:
- Completing work and preparing for next agent
- Starting work and consuming artifacts from previous agent
- Unsure what to produce or expect at handoff boundaries
- Encountering unclear or incomplete handoff artifacts
- Planning multi-phase projects

## Kerrigan Workflow Overview

```
Issue → Spec Agent → Architect → SWE → Testing → Deploy → Complete
         ↓ Artifacts  ↓ Artifacts ↓ Code+Tests ↓ Enhanced Tests ↓ Operations
```

Each phase:
1. **Reads** artifacts from previous phase
2. **Produces** artifacts for next phase
3. **Validates** artifacts pass quality checks
4. **Signals** completion via PR

## Handoff Patterns

### Pattern 1: Human → Spec Agent

**Human provides:**
- GitHub issue with project idea
- Label `role:spec` to assign work
- Label `agent:go` or `agent:sprint` to enable work
- Context: problem statement, goals, constraints

**Spec Agent produces:**
- `specs/projects/<project>/spec.md` - Goals, scope, user stories, acceptance criteria
- `specs/projects/<project>/acceptance-tests.md` - Executable test scenarios
- `specs/projects/<project>/status.json` - Initial status tracking

**Handoff signal:** PR with spec artifacts for human review

### Pattern 2: Spec Agent → Architect Agent

**Architect reads:**
- `spec.md` - Understand goals, scope, user stories
- `acceptance-tests.md` - Know what success looks like
- `status.json` - Verify project is active (not blocked)

**Architect produces:**
- `architecture.md` - System design, components, data flow, tech choices
- `plan.md` - Implementation roadmap and milestones
- `tasks.md` - Concrete, prioritized task list for SWE
- `test-plan.md` - Testing strategy and coverage goals

**Handoff signal:** PR with architecture artifacts, references spec.md for traceability

**Critical checks before starting:**
```bash
# 1. Check project status
cat specs/projects/<project>/status.json
# Must be "active" - if "blocked" or "on-hold", stop and report

# 2. Verify spec completeness
# - spec.md has all required sections
# - Acceptance criteria are clear and testable
# - Constraints are documented

# 3. Ask clarifying questions if needed
# - Create GitHub comment on issue
# - Don't proceed with unclear requirements
```

### Pattern 3: Architect → SWE Agent

**SWE reads:**
- `architecture.md` - Understand system design
- `tasks.md` - Get specific implementation tasks
- `test-plan.md` - Know testing expectations
- `plan.md` - See milestone structure and priorities

**SWE produces:**
- Source code (location per architecture.md)
- Tests (unit, integration, acceptance)
- Build/lint configuration
- Updated README with build/test instructions

**Handoff signal:** PR with working code and passing tests, references tasks.md for traceability

**Critical checks before starting:**
```bash
# 1. Verify architecture clarity
# - Components and responsibilities are clear
# - Technology choices are specified (or flexibility noted)
# - Security considerations documented

# 2. Check task specificity
# - Tasks are actionable (not "Implement feature X")
# - Good: "Implement User model with id, name, email fields"
# - Bad: "Add user management"

# 3. Understand quality bar
# - File size limits (usually 800 lines max)
# - Test coverage requirements
# - Code style expectations
```

### Pattern 4: SWE → Testing Agent

**Testing reads:**
- Source code - Understand implementation
- Existing tests - Identify coverage gaps
- `test-plan.md` - Know testing strategy goals
- `architecture.md` - Understand system design for integration tests

**Testing produces:**
- Additional tests (edge cases, error handling, integration)
- Updated `test-plan.md` with coverage analysis
- Bug fixes if issues discovered
- Test documentation/examples

**Handoff signal:** PR with enhanced test suite, coverage report

**Critical checks before starting:**
```bash
# 1. Run existing tests
# - All tests must pass before adding more
# - Fix any broken tests first

# 2. Analyze coverage
# - What's missing? Edge cases, error paths, integration
# - What's over-tested? Redundant or fragile tests

# 3. Check test quality
# - Tests are clear and maintainable
# - Tests don't just test implementation details
# - Tests cover real user scenarios
```

### Pattern 5: SWE/Testing → Deploy Agent

**Deploy reads:**
- Source code - Understand what's being deployed
- `architecture.md` - Know system components and dependencies
- Tests - Verify project is ready for production
- `spec.md` - Understand goals and success metrics

**Deploy produces:**
- `runbook.md` - Deployment, configuration, monitoring, troubleshooting
- `cost-plan.md` - Resource costs and optimization
- Deployment scripts/configs (optional)
- CI/CD pipeline updates (if needed)

**Handoff signal:** PR with operational artifacts, project is production-ready

**Critical checks before starting:**
```bash
# 1. Verify project readiness
# - All tests pass
# - Quality bar met (no files > 800 lines without justification)
# - Security considerations addressed

# 2. Understand deployment context
# - Where will this run? (cloud, on-prem, edge)
# - What are dependencies? (databases, APIs, services)
# - What are resource constraints? (cost, performance)

# 3. Plan operations
# - How to deploy and rollback
# - What to monitor and alert on
# - How to troubleshoot common issues
```

## Handoff Quality Checklist

Before creating PR for handoff:

### Content Quality
- [ ] All required artifacts created (see artifact-contracts.md)
- [ ] Required sections present with exact heading names
- [ ] Content is clear, specific, actionable
- [ ] No files > 800 lines (or justified if necessary)

### Traceability
- [ ] References to previous phase artifacts (e.g., "per spec.md section X")
- [ ] Clear connection between goals → design → implementation
- [ ] Decisions explained with rationale

### Validation
- [ ] Local validation passes (`kerrigan validate` or `python tools/validators/check_artifacts.py`)
- [ ] Tests pass (if code phase)
- [ ] No broken links or missing files

### Communication
- [ ] PR description explains what was done and why
- [ ] Agent signature included (for auditing)
- [ ] Next agent knows what to do (clear handoff point)

## Common Handoff Failures

### ❌ Vague Tasks
**Problem:** Architect produces tasks like "Implement authentication"

**Impact:** SWE agent can't start, needs clarification, delays project

**Solution:** Tasks must be specific and actionable:
- ✅ Good: "Implement User model with id, name, email fields. Add bcrypt password hashing. Create login endpoint POST /auth/login."
- ❌ Bad: "Add user authentication"

### ❌ Missing Dependencies
**Problem:** Architect doesn't document external API dependency

**Impact:** SWE agent implements without proper error handling, Deploy agent misses monitoring

**Solution:** Document all dependencies in architecture.md:
- External APIs (with auth requirements)
- Databases (with schema expectations)
- Services (with availability requirements)

### ❌ Incomplete Status Checking
**Problem:** Agent starts work on blocked project

**Impact:** Wasted effort, conflicting changes, frustration

**Solution:** ALWAYS check status.json first:
```bash
cd specs/projects/<project>
cat status.json
# If not "active", stop and report why
```

### ❌ Skipping Validation
**Problem:** Agent creates PR without running validators

**Impact:** CI fails, requires fixes, slows down pipeline

**Solution:** Run validators before PR:
```bash
python tools/validators/check_artifacts.py
# Or: kerrigan validate
# Fix all errors before submitting PR
```

### ❌ No Traceability
**Problem:** SWE implements feature not mentioned in spec or tasks

**Impact:** Scope creep, reviewer confusion, potential rework

**Solution:** Reference source artifacts in commits and PR:
```markdown
Implemented User authentication per tasks.md section "Milestone 1, Task 1.3"
Following security patterns from architecture.md section "Security Considerations"
```

## Handoff Communication

### In Commits
```bash
git commit -m "Add User model per architecture.md component design"
git commit -m "Implement login endpoint per tasks.md M1.T3"
```

### In PR Descriptions
```markdown
## What Changed
Implemented authentication system per architecture.md.

## Artifacts Produced
- src/models/user.js - User model
- src/routes/auth.js - Login/logout endpoints
- tests/auth.test.js - Authentication tests

## Next Steps for Testing Agent
- Enhance edge case coverage (see test-plan.md section "Authentication Testing")
- Add integration tests with database
- Test rate limiting and error paths

## References
- Spec: specs/projects/<project>/spec.md (User Stories 1-3)
- Architecture: specs/projects/<project>/architecture.md (Auth Component)
- Tasks: specs/projects/<project>/tasks.md (Milestone 1)
```

### When Stuck
If handoff artifacts are unclear:

1. **Check examples:** Look at `examples/` for similar projects
2. **Ask questions:** Comment on GitHub issue with specific questions
3. **Document assumptions:** If you must proceed, document what you assumed
4. **Don't guess:** Better to ask than produce wrong artifacts

## Status Tracking

Use `status.json` to coordinate:

```json
{
  "status": "active",
  "current_phase": "implementation",
  "last_updated": "2026-01-22T12:00:00Z",
  "notes": "Milestone 1 complete, starting Milestone 2"
}
```

Or pause work:
```json
{
  "status": "blocked",
  "blocked_reason": "Waiting for API access credentials",
  "last_updated": "2026-01-22T12:00:00Z"
}
```

Agents MUST check this before starting work.

## References

- [Artifact Contracts](./artifact-contracts.md) - What to produce at each phase
- [Quality Bar](./quality-bar.md) - Quality standards for handoffs
- [Handoffs Playbook](../../playbooks/handoffs.md) - Detailed process guide
- [Agent Prompts](../../.github/agents/) - Role-specific instructions

## Updates

**v1.0.0 (2026-01-22):** Initial version based on Kerrigan handoffs playbook
