# Task Tracker Development Runbook

**Complete Development Process Demonstrating Milestone 3 & 4 Features**

This runbook documents the end-to-end development of the Task Tracker CLI, showing how Kerrigan's Milestone 3 & 4 features work together in practice.

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Development Setup](#pre-development-setup)
3. [Phase 1: Specification](#phase-1-specification-spec-agent)
4. [Phase 2: Architecture](#phase-2-architecture-architect-agent)
5. [Phase 3: Implementation](#phase-3-implementation-swe-agent)
6. [Phase 4: Testing](#phase-4-testing-testing-agent)
7. [Phase 5: Documentation](#phase-5-documentation)
8. [M3/M4 Features Summary](#m3m4-features-summary)
9. [Lessons Learned](#lessons-learned)

---

## Overview

### Project Details
- **Name**: Task Tracker
- **Type**: CLI Application
- **Purpose**: Demonstrate all M3/M4 features in a realistic project
- **Duration**: ~5 hours (simulated across multiple sessions)
- **Agents Involved**: Spec, Architect, SWE, Testing

### M3/M4 Features Demonstrated
- ✅ status.json workflow control
- ✅ Pause and resume functionality
- ✅ Agent:go labels and autonomy gates
- ✅ Agent signatures and auditing
- ✅ Agent spec references
- ✅ Phase transitions
- ✅ Blocked state handling

---

## Pre-Development Setup

### Step 1: Create GitHub Issue

**Issue Created**: #XX "Create Task Tracker CLI with authentication"

**Labels Applied**:
- `agent:go` - Grants autonomy to agents
- `role:spec` - Initial assignment to Spec agent
- `examples:task-tracker` - Project tracking

**Issue Description**:
```markdown
## Goal
Create a CLI task management tool with user authentication to demonstrate
all Kerrigan M3/M4 features.

## Requirements
- User authentication (register, login, logout)
- Task CRUD operations
- Task filtering and listing
- JSON persistence
- Comprehensive testing

## M3/M4 Features to Demonstrate
- status.json workflow control
- Pause/resume at phase boundaries
- Agent signatures throughout
- References to agent specs
- Autonomy gate enforcement
```

### Step 2: Initialize Project Structure

```bash
# Create project directory
mkdir -p specs/projects/task-tracker

# Create initial status.json
cat > examples/task-tracker/status.json << 'EOF'
{
  "status": "active",
  "current_phase": "spec",
  "last_updated": "2026-01-15T08:00:00Z",
  "notes": "Starting specification phase for Task Tracker CLI"
}
EOF
```

**M3 Feature**: status.json created to control workflow from start

---

## Phase 1: Specification (Spec Agent)

### Status Before Phase
```json
{
  "status": "active",
  "current_phase": "spec",
  "last_updated": "2026-01-15T08:00:00Z",
  "notes": "Starting specification phase"
}
```

### Agent Invocation

**Agent**: Spec Agent  
**Prompt Source**: `.github/agents/role.spec.md`  
**Agent Spec Reference**: `specs/kerrigan/agents/spec/spec.md`

**Checklist Followed**:
- [x] Checked status.json (status=active, phase=spec) ✅ **M3 Feature**
- [x] Read issue requirements
- [x] Referenced spec agent quality standards
- [x] Created spec.md with measurable acceptance criteria
- [x] Created acceptance-tests.md with Given/When/Then scenarios
- [x] Validated artifacts pass quality bar
- [x] Created agent signature ✅ **M4 Feature**

### Artifacts Created

1. **examples/task-tracker/docs/spec.md (documented in RUNBOOK)**
   - Goal and scope
   - User scenarios
   - Acceptance criteria (15 measurable criteria)
   - Success metrics

2. **specs/projects/task-tracker/acceptance-tests.md**
   - 12 test scenarios covering all features
   - Edge cases and failure modes

### PR Created: "Add Task Tracker specification"

**PR Description Included**:
```markdown
## Changes
- Created spec.md with complete project specification
- Created acceptance-tests.md with 12 test scenarios
- Demonstrates M3/M4 features from the start

## Agent Signature
<!-- AGENT_SIGNATURE: role=role:spec, version=1.0, timestamp=2026-01-15T08:30:00Z -->

## Agent Spec Reference
This work follows the quality standards defined in:
- specs/kerrigan/agents/spec/spec.md
- specs/kerrigan/agents/spec/quality-bar.md

## Status Check
Verified status.json: status=active, phase=spec ✅

## Fixes
#XX
```

**M4 Features Demonstrated**:
- ✅ Agent signature included
- ✅ Agent spec referenced
- ✅ Issue linked for autonomy gate
- ✅ Status.json checked before work

### Human Review and Pause

**After PR Merge**: Human reviews specification

**Status Updated to BLOCKED**:
```bash
cat > examples/task-tracker/status.json << 'EOF'
{
  "status": "blocked",
  "current_phase": "spec",
  "last_updated": "2026-01-15T09:00:00Z",
  "blocked_reason": "Awaiting human review of specification before proceeding to architecture",
  "notes": "Spec artifacts complete. Need approval on: auth approach, storage format, CLI framework choice."
}
EOF
```

**M3 Feature**: Pause workflow at critical decision point

**Review Outcome**: ✅ Approved after 30 minutes
- Auth approach approved (simple token-based)
- JSON storage approved
- Click framework approved

---

## Phase 2: Architecture (Architect Agent)

### Status After Resume

```json
{
  "status": "active",
  "current_phase": "architecture",
  "last_updated": "2026-01-15T10:00:00Z",
  "notes": "Spec approved. Starting architecture phase."
}
```

**M3 Feature**: Resume workflow with phase transition

### Agent Invocation

**Agent**: Architect Agent  
**Prompt Source**: `.github/agents/role.architect.md`  
**Agent Spec Reference**: `specs/kerrigan/agents/architect/spec.md`

**Checklist Followed**:
- [x] Checked status.json (status=active, phase=architecture) ✅ **M3 Feature**
- [x] Read spec.md and acceptance-tests.md
- [x] Referenced architect agent quality standards
- [x] Created architecture.md with component design
- [x] Created plan.md with incremental milestones
- [x] Created tasks.md with executable work items
- [x] Created test-plan.md
- [x] Created runbook.md (deployment guide)
- [x] Created cost-plan.md
- [x] Validated all artifacts
- [x] Created agent signature ✅ **M4 Feature**

### Artifacts Created

1. **architecture.md** - System design, components, data flows
2. **plan.md** - 4 milestones with clear deliverables
3. **tasks.md** - 18 executable tasks with done criteria
4. **test-plan.md** - Testing strategy (unit + integration)
5. **runbook.md** - Installation and usage guide
6. **cost-plan.md** - Zero cost (local tool)

### PR Created: "Add Task Tracker architecture and plan"

**PR Description Included**:
```markdown
## Changes
- Created complete architecture with 4 components
- Defined 4-milestone incremental plan
- Created 18 executable tasks
- Added test strategy and runbook

## Agent Signature
<!-- AGENT_SIGNATURE: role=role:architect, version=1.0, timestamp=2026-01-15T10:45:00Z -->

## Agent Spec Reference
This work follows:
- specs/kerrigan/agents/architect/spec.md
- specs/kerrigan/agents/architect/quality-bar.md
- specs/kerrigan/agents/architect/architecture.md

## Status Check
Verified status.json: status=active, phase=architecture ✅

## Fixes
#XX
```

**M4 Features Demonstrated**:
- ✅ Agent signature included
- ✅ Multiple agent specs referenced
- ✅ Status.json verified
- ✅ Issue linked for autonomy gate

### Human Review and Pause

**Status Updated to BLOCKED**:
```json
{
  "status": "blocked",
  "current_phase": "architecture",
  "last_updated": "2026-01-15T11:00:00Z",
  "blocked_reason": "Architecture review needed before implementation. Verify module structure and security approach.",
  "notes": "6 artifacts created. Need sign-off on: auth module design, task storage schema, error handling strategy."
}
```

**M3 Feature**: Second pause for architectural review

**Review Outcome**: ✅ Approved after 20 minutes
- Module structure approved
- Security approach adequate for demo
- Error handling comprehensive

---

## Phase 3: Implementation (SWE Agent)

### Status After Resume

```json
{
  "status": "active",
  "current_phase": "implementation",
  "last_updated": "2026-01-15T11:30:00Z",
  "notes": "Architecture approved. Starting implementation phase."
}
```

**M3 Feature**: Resume with phase transition to implementation

### Agent Invocation

**Agent**: SWE Agent  
**Prompt Source**: `.github/agents/role.swe.md`  
**Agent Spec Reference**: `specs/kerrigan/agents/swe/spec.md`

**Checklist Followed**:
- [x] Checked status.json (status=active, phase=implementation) ✅ **M3 Feature**
- [x] Read architecture.md and plan.md
- [x] Referenced SWE agent quality standards
- [x] Set up project structure
- [x] Implemented with TDD approach
- [x] Wrote tests alongside code
- [x] Set up linting (.flake8)
- [x] Achieved >80% coverage
- [x] All files under 800 LOC limit
- [x] Created agent signature ✅ **M4 Feature**

### Implementation Details

**Project Structure Created**:
```
examples/task-tracker/
├── task_tracker/
│   ├── __init__.py
│   ├── cli.py           # Main CLI entry point (150 LOC)
│   ├── auth.py          # Authentication module (120 LOC)
│   ├── tasks.py         # Task management (180 LOC)
│   ├── storage.py       # JSON persistence (100 LOC)
│   └── utils.py         # Utilities (50 LOC)
├── tests/
│   ├── test_auth.py     # Auth tests (150 LOC)
│   ├── test_tasks.py    # Task tests (200 LOC)
│   ├── test_storage.py  # Storage tests (100 LOC)
│   └── test_cli.py      # Integration tests (150 LOC)
├── setup.py
├── requirements.txt
├── .flake8
└── .gitignore
```

**Total LOC**: ~400 (code) + ~600 (tests)

### PR Created: "Implement Task Tracker CLI"

**PR Description Included**:
```markdown
## Changes
- Implemented complete CLI with Click
- Added authentication module with token-based auth
- Implemented task management (CRUD operations)
- Added JSON persistence layer
- Created comprehensive test suite (92% coverage)
- All files under 800 LOC limit ✅

## Agent Signature
<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T13:30:00Z -->

## Agent Spec Reference
Implemented following:
- specs/kerrigan/agents/swe/spec.md
- specs/kerrigan/agents/swe/quality-bar.md
- specs/kerrigan/agents/swe/architecture.md

## Testing
- Unit tests: 28 tests
- Integration tests: 8 tests
- Coverage: 92%
- Linting: 100% flake8 clean

## Status Check
Verified status.json: status=active, phase=implementation ✅

## Quality Bar
- [x] All files < 800 LOC
- [x] Coverage > 80%
- [x] Linting passes
- [x] CI green

## Fixes
#XX
```

**M4 Features Demonstrated**:
- ✅ Agent signature included
- ✅ Agent specs referenced
- ✅ Status.json verified
- ✅ Quality bar checklist
- ✅ Issue linked

**M3 Feature**: No pause after implementation (continued to testing)

---

## Phase 4: Testing (Testing Agent)

### Status Transition

```json
{
  "status": "active",
  "current_phase": "testing",
  "last_updated": "2026-01-15T14:00:00Z",
  "notes": "Implementation complete. Enhancing test coverage and reliability."
}
```

**M3 Feature**: Phase transition updated in status.json

### Agent Invocation

**Agent**: Testing Agent  
**Prompt Source**: `.github/agents/role.testing.md`  
**Agent Spec Reference**: `specs/kerrigan/agents/testing/spec.md`

**Checklist Followed**:
- [x] Checked status.json (status=active, phase=testing) ✅ **M3 Feature**
- [x] Read test-plan.md
- [x] Referenced testing agent quality standards
- [x] Analyzed coverage gaps
- [x] Added edge case tests
- [x] Verified no flaky tests
- [x] Improved test clarity
- [x] Updated test-plan.md
- [x] Created agent signature ✅ **M4 Feature**

### Enhancements Made

1. **Added edge case tests**:
   - Empty task list handling
   - Invalid credentials
   - Concurrent user sessions
   - Malformed JSON storage

2. **Improved test coverage**: 92% → 96%

3. **Enhanced test clarity**:
   - Better test names
   - Clear Given/When/Then structure
   - Comprehensive assertions

4. **Fixed flaky test**: Authentication token timing issue

### PR Created: "Enhance test coverage and reliability"

**PR Description Included**:
```markdown
## Changes
- Added 8 edge case tests
- Improved test coverage from 92% to 96%
- Fixed flaky authentication test
- Enhanced test clarity and documentation
- Updated test-plan.md with findings

## Agent Signature
<!-- AGENT_SIGNATURE: role=role:testing, version=1.0, timestamp=2026-01-15T15:00:00Z -->

## Agent Spec Reference
Testing performed per:
- specs/kerrigan/agents/testing/spec.md
- specs/kerrigan/agents/testing/quality-bar.md
- specs/kerrigan/agents/testing/acceptance-tests.md

## Test Metrics
- Total tests: 44 (was 36)
- Coverage: 96% (was 92%)
- Flaky tests: 0 (fixed 1)
- Test run time: 2.3s

## Status Check
Verified status.json: status=active, phase=testing ✅

## Fixes
#XX
```

**M4 Features Demonstrated**:
- ✅ Agent signature included
- ✅ Multiple agent specs referenced
- ✅ Status.json verified
- ✅ Issue linked

---

## Phase 5: Documentation

### Status Transition to Completed

```json
{
  "status": "completed",
  "current_phase": "deployment",
  "last_updated": "2026-01-15T16:00:00Z",
  "notes": "All development phases complete. Project ready for use."
}
```

**M3 Feature**: Final status transition to completed

### Final Documentation Created

1. **README.md** - This file you're reading
2. **RUNBOOK.md** - Complete development story (this document)
3. **WORKFLOW-PHASES.md** - Detailed phase breakdown
4. **AGENT-AUDIT-REPORT.md** - Complete audit trail
5. **User documentation** - Usage guides

---

## M3/M4 Features Summary

### Milestone 3: Status Tracking

| Feature | Demonstrated | Details |
|---------|-------------|---------|
| status.json creation | ✅ | Created at project start |
| Phase transitions | ✅ | 5 transitions documented |
| Pause workflow | ✅ | 2 pauses for human review |
| Resume workflow | ✅ | 2 resumes after approval |
| Blocked state | ✅ | Used with blocked_reason |
| Status verification | ✅ | Checked by every agent |

**Status Transitions**:
1. active/spec → blocked/spec (after spec phase)
2. blocked/spec → active/architecture (after approval)
3. active/architecture → blocked/architecture (after arch phase)
4. blocked/architecture → active/implementation (after approval)
5. active/implementation → active/testing (no pause)
6. active/testing → completed/deployment (final)

### Milestone 4: Autonomy Gates

| Feature | Demonstrated | Details |
|---------|-------------|---------|
| agent:go label | ✅ | Issue labeled from start |
| Role labels | ✅ | 4 different roles used |
| Issue linking | ✅ | All PRs linked to issue |
| Gate enforcement | ✅ | CI verified labels |
| Autonomy control | ✅ | Human control maintained |

**Autonomy Flow**:
1. Issue created with `agent:go` label
2. Role labels applied per phase
3. Each PR linked with "Fixes #XX"
4. CI verified autonomy grants
5. Human approvals required at key points

### Agent Auditing

| Feature | Demonstrated | Details |
|---------|-------------|---------|
| Agent signatures | ✅ | 4 signatures across phases |
| Signature format | ✅ | HTML comments with metadata |
| Role verification | ✅ | Signatures match labels |
| Timestamps | ✅ | All work timestamped |
| Audit trail | ✅ | Complete in AGENT-AUDIT-REPORT.md |

**Signatures Created**:
1. Spec Agent: `2026-01-15T08:30:00Z`
2. Architect Agent: `2026-01-15T10:45:00Z`
3. SWE Agent: `2026-01-15T13:30:00Z`
4. Testing Agent: `2026-01-15T15:00:00Z`

### Agent Specs References

| Agent | Specs Referenced | Purpose |
|-------|-----------------|---------|
| Spec | spec/spec.md, spec/quality-bar.md | Quality standards |
| Architect | architect/spec.md, architect/architecture.md | Design guidelines |
| SWE | swe/spec.md, swe/quality-bar.md | Implementation standards |
| Testing | testing/spec.md, testing/acceptance-tests.md | Test quality criteria |

---

## Lessons Learned

### What Worked Exceptionally Well

1. **status.json Provided Clear Control**
   - Always knew project state
   - Easy to pause/resume
   - Clear phase boundaries
   - Prevented agents from jumping ahead

2. **Agent Signatures Made Auditing Easy**
   - Clear who did what
   - Easy to track workflow
   - Timestamps helped correlate work
   - Simple to verify agent usage

3. **Pause Points Enabled Better Quality**
   - Spec review caught auth approach issues
   - Architecture review improved design
   - Human oversight at critical points
   - No rework needed later

4. **Agent Spec References Ensured Consistency**
   - All agents followed quality standards
   - Consistent artifact structure
   - No missing required sections
   - Quality bar met throughout

5. **Autonomy Gates Provided Safety**
   - No unexpected PR creation
   - Human always in control
   - Clear authorization model
   - Easy to grant/revoke access

### Challenges Encountered

1. **Manual Status Updates**
   - **Issue**: Agents didn't update status.json automatically
   - **Impact**: Required human intervention for transitions
   - **Mitigation**: Documented expected states clearly
   - **Future**: Could automate status updates by agents

2. **Audit Log Aggregation**
   - **Issue**: Signatures spread across PRs
   - **Impact**: Required manual aggregation for audit report
   - **Mitigation**: Created consolidated audit report
   - **Future**: Could aggregate automatically with script

3. **Agent Spec Discovery**
   - **Issue**: Agents need to know which specs to reference
   - **Impact**: Required explicit references in prompts
   - **Mitigation**: Added spec references to agent prompts
   - **Future**: Could include in agent context automatically

### Recommendations for Teams

#### For Small Projects (< 1 week)
1. **Do use**:
   - status.json with minimal notes
   - Agent signatures for auditing
   - At least one pause for review
   - Reference agent specs

2. **Can skip**:
   - Frequent pauses (1-2 is enough)
   - Detailed status notes
   - Complex audit reports

#### For Medium Projects (1-4 weeks)
1. **Do use**:
   - status.json with regular updates
   - Agent signatures consistently
   - Pause at phase boundaries
   - Detailed agent spec references
   - Regular autonomy gate reviews

2. **Add**:
   - More frequent status updates
   - Audit reports at milestones
   - Status checks in CI

#### For Large Projects (> 4 weeks)
1. **Must use**:
   - Comprehensive status tracking
   - Mandatory agent signatures
   - Formal approval gates
   - Complete audit trail
   - Automated status checks
   - Regular autonomy reviews

2. **Consider**:
   - Automated status updates
   - Audit dashboard
   - Integration with project management
   - Multiple approval layers

### Best Practices Identified

1. **Status Management**
   - Update status.json at every phase transition
   - Always include clear notes
   - Use blocked_reason when pausing
   - Document resumption decisions

2. **Agent Signatures**
   - Include in every PR description
   - Use HTML comments (invisible but trackable)
   - Include timestamp and version
   - Match signature role to PR labels

3. **Autonomy Gates**
   - Label issues before starting work
   - Link all PRs to labeled issues
   - Review labels regularly
   - Document autonomy decisions

4. **Agent Spec References**
   - Reference relevant specs in PR descriptions
   - Follow spec quality standards
   - Use specs for review criteria
   - Keep specs up to date

5. **Pause Points**
   - Always pause after spec phase
   - Consider pause after architecture
   - Pause before major implementation changes
   - Document approval criteria clearly

---

## Conclusion

This end-to-end example successfully demonstrates all Milestone 3 & 4 features working together in a realistic project. The combination of status tracking, agent auditing, autonomy gates, and agent specs provides a robust framework for controlled, auditable, high-quality agent-driven development.

**Key Takeaways**:
- M3/M4 features complement each other well
- Workflow control doesn't slow development
- Auditing is lightweight but valuable
- Quality remains high throughout
- Human oversight is effective and efficient

**For External Teams**:
This example serves as a complete template for adopting Kerrigan with all M3/M4 features. Follow this pattern for your own projects to benefit from controlled, auditable, high-quality agent workflows.

---

**Next Steps**: See [AGENT-AUDIT-REPORT.md](AGENT-AUDIT-REPORT.md) for the complete audit trail, or [WORKFLOW-PHASES.md](WORKFLOW-PHASES.md) for detailed phase breakdowns.
