# Handoffs

Handoffs are file-based. Each stage must produce the artifacts defined in:
- `specs/kerrigan/020-artifact-contracts.md`

## Status tracking and workflow control

Projects can include a `status.json` file to control agent workflow state:

**Location**: `specs/projects/<project-name>/status.json`

**Agent workflow**:
1. Before starting any work, agents MUST check if status.json exists
2. If status.json exists and status is `blocked` or `on-hold`, agents MUST NOT proceed
3. Agents SHOULD update `last_updated` timestamp when changing phases
4. Agents MAY add `notes` for context but MUST NOT change status from `active` to `blocked`

**Human control**:
- Set `status: "blocked"` to pause agent work (e.g., for review, discussion, or external dependencies)
- Include `blocked_reason` to explain why work is paused
- Set `status: "active"` to resume agent work
- Set `status: "on-hold"` for temporary pauses without blocking
- Set `status: "completed"` when project is done

**Example pause workflow**:
```bash
# Human pauses work for review
echo '{"status":"blocked","current_phase":"implementation","last_updated":"2026-01-06T21:00:00Z","blocked_reason":"Awaiting security review"}' > specs/projects/myproject/status.json

# Agent checks status before proceeding and sees blocked state - does not continue

# After review, human resumes work
echo '{"status":"active","current_phase":"implementation","last_updated":"2026-01-06T21:30:00Z","notes":"Security review complete"}' > specs/projects/myproject/status.json

# Agent can now proceed
```

See `specs/kerrigan/020-artifact-contracts.md` for full status.json schema.

## Spec → Architecture
Required:
- spec.md
- acceptance-tests.md
Optional:
- early decisions.md

## Architecture → Implementation
Required:
- architecture.md
- plan.md (milestones with green CI)
- tasks.md (executable items)

## Implementation → Testing hardening
Required:
- test-plan.md (or updated plan section)
- CI improvements as needed

## Testing/Debugging → Deployment
Required:
- runbook.md
- cost-plan.md (if paid resources)
- deploy steps + rollback notes
