# Handoffs

Handoffs are file-based. Each stage must produce the artifacts defined in:
- `specs/kerrigan/020-artifact-contracts.md`

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
