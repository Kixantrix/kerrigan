---
title: Artifact Contracts
version: 1.0.0
source: Kerrigan (original)
last_updated: 2026-01-22
license: MIT
---

# Artifact Contracts

Kerrigan's required file structures, naming conventions, and validation rules for all project artifacts. This skill ensures agents produce artifacts that pass validation and enable smooth handoffs between roles.

## When to Apply

Reference this skill when:
- Starting a new project or milestone
- Creating specs, architectures, plans, or other artifacts
- Unsure about required file structure or naming
- Preparing for validation or handoff to next agent
- Receiving validation failures

## Required Artifacts by Phase

### Specification Phase (Spec Agent)

**Location:** `specs/projects/<project>/`

| File | Required | Purpose |
|------|----------|---------|
| `spec.md` | ✅ Yes | Project goals, scope, user stories, acceptance criteria |
| `acceptance-tests.md` | ✅ Yes | Executable test scenarios for validating completion |
| `status.json` | Optional | Project status tracking (active, blocked, completed) |

**spec.md Structure:**
```markdown
# <Project Name>

## Overview
Brief description of what the project does.

## Goals
- Goal 1: Description
- Goal 2: Description

## Scope
What's included and what's explicitly out of scope.

## User Stories
- As a [role], I want [feature] so that [benefit]

## Acceptance Criteria
- [ ] Criterion 1: Specific, testable condition
- [ ] Criterion 2: Specific, testable condition

## Constraints
Technical, business, or resource constraints.

## Success Metrics (Optional)
How to measure success (performance, usage, etc.)
```

### Architecture Phase (Architect Agent)

**Location:** `specs/projects/<project>/`

| File | Required | Purpose |
|------|----------|---------|
| `architecture.md` | ✅ Yes | System design, components, data flow, tech choices |
| `plan.md` | ✅ Yes | Implementation roadmap and milestones |
| `tasks.md` | ✅ Yes | Concrete, prioritized task list for SWE agent |
| `test-plan.md` | ✅ Yes | Testing strategy and test coverage goals |

**architecture.md Structure:**
```markdown
# Architecture: <Project Name>

## System Overview
High-level description and diagram (ASCII or link to image).

## Components
- **Component 1**: Purpose, responsibilities, interfaces
- **Component 2**: Purpose, responsibilities, interfaces

## Data Flow
How information moves through the system.

## Technology Choices
Stack decisions with rationale (if required by project).

## Dependencies
External libraries, services, or systems.

## Security Considerations
Auth, data protection, input validation, secrets management.

## Quality Bar
File size limits, test coverage, linting rules.
```

**tasks.md Structure:**
```markdown
# Tasks: <Project Name>

## Milestone 1: <Name> (Priority: High)
- [ ] Task 1.1: Specific, actionable description (Est: X hours)
- [ ] Task 1.2: Specific, actionable description (Est: X hours)

## Milestone 2: <Name> (Priority: Medium)
- [ ] Task 2.1: Specific, actionable description (Est: X hours)

## Notes
Dependencies, blockers, or clarifications.
```

### Implementation Phase (SWE Agent)

**Location:** Project-specific (e.g., `src/`, `lib/`, `examples/<project>/`)

| Artifact | Required | Purpose |
|----------|----------|---------|
| Source code | ✅ Yes | Implementation files |
| Tests | ✅ Yes | Unit, integration, or acceptance tests |
| Linting config | Recommended | Code quality enforcement |
| Build config | If needed | Build system configuration |
| README | ✅ Yes | How to build, test, run the project |

**Quality Bar:**
- No files > 800 lines without justification
- Every feature has tests
- Tests pass before PR submission
- Code follows existing project style

### Deployment Phase (Deploy Agent)

**Location:** `specs/projects/<project>/`

| File | Required | Purpose |
|------|----------|---------|
| `runbook.md` | ✅ Yes | Operations guide (deploy, monitor, troubleshoot) |
| `cost-plan.md` | ✅ Yes | Resource costs and optimization strategies |

**runbook.md Structure:**
```markdown
# Runbook: <Project Name>

## Deployment
Step-by-step deployment instructions.

## Configuration
Environment variables, secrets, configuration files.

## Monitoring
Key metrics, logging, alerts.

## Troubleshooting
Common issues and solutions.

## Rollback
How to revert to previous version.

## Dependencies
Services, databases, external APIs.
```

## Validation Rules

### File Naming
- Use kebab-case for files: `spec.md`, `architecture.md`, `test-plan.md`
- No spaces, underscores, or capital letters in artifact names
- Project directories: `specs/projects/<project-name>/`

### Required Sections
Each artifact type has mandatory headings (case-sensitive):
- **spec.md**: Overview, Goals, Scope, User Stories, Acceptance Criteria
- **architecture.md**: System Overview, Components, Data Flow, Technology Choices, Security Considerations
- **tasks.md**: At least one Milestone section
- **runbook.md**: Deployment, Configuration, Monitoring, Troubleshooting

### File Size Limits
- Maximum 800 lines per file (exceptions require justification)
- Break large artifacts into modules or milestones
- Use includes or references for shared content

### Status Tracking
**status.json format:**
```json
{
  "status": "active" | "blocked" | "on-hold" | "completed" | "archived",
  "current_phase": "specification" | "architecture" | "implementation" | "testing" | "deployment",
  "last_updated": "2026-01-22T12:00:00Z",
  "blocked_reason": "Optional: why blocked"
}
```

Agents MUST check status.json before starting work. If status is "blocked" or "on-hold", stop and report why.

## Handoff Checklist

Before handing off to the next agent:

### Spec → Architect
- [ ] spec.md complete with all required sections
- [ ] Acceptance criteria are specific and testable
- [ ] Constraints and success metrics documented
- [ ] No validation errors

### Architect → SWE
- [ ] architecture.md describes system design clearly
- [ ] tasks.md has concrete, prioritized tasks
- [ ] test-plan.md covers testing strategy
- [ ] Dependencies and security considerations documented

### SWE → Testing/Deploy
- [ ] All planned tasks completed
- [ ] Tests written and passing
- [ ] Code follows quality bar (no files > 800 lines)
- [ ] README updated with build/test instructions

### Deploy → Complete
- [ ] runbook.md covers operations completely
- [ ] cost-plan.md documents resource usage
- [ ] Project is production-ready

## Common Mistakes

### ❌ Missing Required Sections
**Problem:** Validator fails because spec.md is missing "Acceptance Criteria" heading

**Solution:** Use exact heading names (case-sensitive) from templates. Check specs/kerrigan/020-artifact-contracts.md for full list.

### ❌ Files > 800 Lines
**Problem:** Validator rejects 1200-line implementation file

**Solution:** Split into multiple files (components, modules). If truly necessary, add justification comment at top of file explaining why.

### ❌ Forgetting status.json
**Problem:** Multiple agents work on blocked project simultaneously

**Solution:** Always check `specs/projects/<project>/status.json` before starting. Create it if missing with status: "active".

### ❌ Incomplete Handoffs
**Problem:** SWE agent can't start because tasks.md is vague ("Implement feature X")

**Solution:** Architect must provide specific, actionable tasks: "Implement User model with fields: id, name, email. Add validation for email format."

### ❌ Wrong Directory Structure
**Problem:** Agent creates artifacts in root directory instead of `specs/projects/<project>/`

**Solution:** All projects go in `specs/projects/<project>/`. Check existing examples for structure.

## Validation Tools

Run validators locally before submitting PR:

```bash
# Check artifact structure and required sections
python tools/validators/check_artifacts.py

# Or use Kerrigan CLI
cd tools/cli/kerrigan && pip install -e .
kerrigan validate
```

CI automatically runs validators on all PRs. Fix validation errors before requesting review.

## References

- [Full Artifact Contracts Spec](../../specs/kerrigan/020-artifact-contracts.md) - Complete specification
- [Quality Bar Spec](../../specs/kerrigan/030-quality-bar.md) - Quality standards
- [Example Projects](../../examples/) - See artifact examples
- [Agent Handoffs Playbook](../../playbooks/handoffs.md) - Detailed handoff process

## Updates

**v1.0.0 (2026-01-22):** Initial version based on Kerrigan artifact contracts specification
