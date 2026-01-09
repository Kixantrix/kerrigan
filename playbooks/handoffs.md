# Handoffs

Handoffs are file-based. Each stage must produce the artifacts defined in:
- `specs/kerrigan/020-artifact-contracts.md`

## Workflow Refinements (from hello-api end-to-end validation)

### Key Learnings

1. **Validator expectations must be explicit**: The artifact validator expects exact heading names (case-sensitive), but this isn't documented in agent prompts or README. Agents should be told specific heading names: "Acceptance criteria" (not "Acceptance Criteria"), "Components & interfaces", "Security & privacy notes".

2. **Manual testing is essential**: Even with 97% automated test coverage, manual curl testing was critical for validating real behavior. Agent prompts should emphasize both automated AND manual verification.

3. **Testing guidance needed in SWE prompt**: The SWE agent prompt says "Add or update tests" but doesn't specify WHEN (before/during/after implementation) or what kind. Should encourage TDD or at minimum test-driven development practices.

4. **Architecture phase creates most artifacts**: The architect agent must create 6+ artifacts (spec, acceptance-tests, architecture, plan, tasks, test-plan, runbook, cost-plan). This is the heaviest phase and most prone to validator failures. Consider splitting or adding validation checkpoints.

5. **Linting configuration matters**: Projects need linting config files (.flake8, .eslintrc, etc.) from the start. SWE agent should create these alongside code, not as an afterthought.

6. **Deploy validation may require workarounds**: Some deployment environments (corporate networks, CI systems) have SSL/proxy issues that prevent Docker builds. Document alternative validation approaches.

7. **Security scanning must be continuous**: Dependencies can have vulnerabilities discovered after initial implementation. Always scan dependencies before finalizing work and document the scanning process. Example: Gunicorn 21.2.0 had HTTP smuggling vulnerabilities, required update to 22.0.0.

### Improved Handoff Checklist

**Before moving to next phase, verify:**
- [ ] All required artifacts exist and pass validators
- [ ] Required section headings match validator expectations EXACTLY
- [ ] Manual smoke testing completed (where applicable)
- [ ] Linting/formatting tools configured and passing
- [ ] Dependencies scanned for security vulnerabilities
- [ ] Documentation updated with current state
- [ ] CI is green

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
