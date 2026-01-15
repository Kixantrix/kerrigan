# Handoffs

Handoffs are file-based. Each stage must produce the artifacts defined in:
- `specs/kerrigan/020-artifact-contracts.md`

## Workflow Refinements (from hello-api and Milestone 2 validation)

### Key Learnings from hello-api

1. **Validator expectations must be explicit**: The artifact validator expects exact heading names (case-sensitive), but this isn't documented in agent prompts or README. Agents should be told specific heading names: "Acceptance criteria" (not "Acceptance Criteria"), "Components & interfaces", "Security & privacy notes".

2. **Manual testing is essential**: Even with 97% automated test coverage, manual curl testing was critical for validating real behavior. Agent prompts should emphasize both automated AND manual verification.

3. **Testing guidance needed in SWE prompt**: The SWE agent prompt says "Add or update tests" but doesn't specify WHEN (before/during/after implementation) or what kind. Should encourage TDD or at minimum test-driven development practices.

4. **Architecture phase creates most artifacts**: The architect agent must create 6+ artifacts (spec, acceptance-tests, architecture, plan, tasks, test-plan, runbook, cost-plan). This is the heaviest phase and most prone to validator failures. Consider splitting or adding validation checkpoints.

5. **Linting configuration matters**: Projects need linting config files (.flake8, .eslintrc, etc.) from the start. SWE agent should create these alongside code, not as an afterthought.

6. **Deploy validation may require workarounds**: Some deployment environments (corporate networks, CI systems) have SSL/proxy issues that prevent Docker builds. Document alternative validation approaches.

7. **Security scanning must be continuous**: Dependencies can have vulnerabilities discovered after initial implementation. Always scan dependencies before finalizing work and document the scanning process. Example: Gunicorn 21.2.0 had HTTP smuggling vulnerabilities, required update to 22.0.0.

### Key Learnings from Milestone 2 Validation (validator-enhancement)

8. **Agent prompt validation is lightweight**: Creating artifacts following agent prompts (role.spec.md, role.architect.md) successfully produced valid, validator-passing artifacts without actual agent execution. This confirms prompts are clear and well-structured.

9. **Constitution compliance is checkable**: The Kerrigan meta-agent role can systematically validate projects against all 8 constitution principles. This provides confidence that work meets quality standards before implementation begins.

10. **Test projects are valuable documentation**: Creating a complete test project (validator-enhancement) serves dual purpose: validates the workflow AND provides a reference example for future agents and users.

11. **Small scope enables faster validation**: The validator-enhancement project is intentionally small (~150 LOC) which makes it ideal for workflow validation. Future validation efforts should also use small, focused test projects.

12. **Documentation bootstraps workflow**: Creating comprehensive label documentation (docs/github-labels.md) and test issue templates (docs/test-issue-agent-workflow.md) provides clear guidance for starting new agent workflows.

13. **Artifact creation is the heavy lift**: Spec and architecture phases require significant thought and writing (8 artifacts totaling ~3000 words for validator-enhancement). Implementation is often simpler than planning when scope is well-defined.

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

### Agent workflow procedures

**Before starting any work:**

1. **Check if status.json exists** in the project directory
   ```bash
   # Example: Check status for project 'my-api'
   cat specs/projects/my-api/status.json
   ```

2. **Parse and validate the status field**
   - If status is `blocked` or `on-hold`: **STOP immediately**
   - Read and report the `blocked_reason` to the user
   - Do NOT proceed with any work until status changes to `active`
   - If status.json doesn't exist: proceed normally (equivalent to `active`)
   - If status is `completed`: project is done, no further work needed

3. **During work (optional but recommended)**
   - When transitioning between phases, update `current_phase` and `last_updated`
   - Add `notes` to document progress or decisions
   - Never change status from `active` to `blocked` (human control only)

### Human control procedures

**To pause agent work (blocking):**
```bash
# Create or update status.json with blocked status
cat > specs/projects/myproject/status.json << 'EOF'
{
  "status": "blocked",
  "current_phase": "implementation",
  "last_updated": "2026-01-15T10:00:00Z",
  "blocked_reason": "Awaiting security review of authentication module"
}
EOF
```

**To resume agent work:**
```bash
# Update status.json to active
cat > specs/projects/myproject/status.json << 'EOF'
{
  "status": "active",
  "current_phase": "implementation",
  "last_updated": "2026-01-15T14:30:00Z",
  "notes": "Security review complete. Agent may proceed with remaining tasks."
}
EOF
```

**To temporarily pause without blocking:**
```bash
# Use on-hold for temporary pauses
cat > specs/projects/myproject/status.json << 'EOF'
{
  "status": "on-hold",
  "current_phase": "testing",
  "last_updated": "2026-01-15T16:00:00Z",
  "notes": "Waiting for upstream dependency release. Expected next week."
}
EOF
```

**To mark project complete:**
```bash
cat > specs/projects/myproject/status.json << 'EOF'
{
  "status": "completed",
  "current_phase": "deployment",
  "last_updated": "2026-01-15T18:00:00Z",
  "notes": "All milestones complete. Production deployment successful."
}
EOF
```

### Checking status across all projects

Use the status display tool to see all project states:
```bash
python tools/validators/show_status.py
```

This displays:
- Current status (active/blocked/on-hold/completed) for each project
- Current phase
- Last update timestamp
- Blocked reasons (if applicable)
- Brief notes

### Common status check scenarios

**Scenario 1: Agent receives a new task**
```
1. Identify project name from issue/task
2. Check if specs/projects/<project-name>/status.json exists
3. If exists, read status field
4. If blocked/on-hold → Report to user and STOP
5. If active/missing → Proceed with work
```

**Scenario 2: Human needs to review mid-implementation**
```
1. Human sets status="blocked" with clear blocked_reason
2. Agent sees blocked status on next check → pauses work
3. Human completes review
4. Human sets status="active" with notes about review outcome
5. Agent resumes work on next run
```

**Scenario 3: Waiting for external dependency**
```
1. Human sets status="on-hold" with notes about dependency
2. Agent respects on-hold same as blocked (does not proceed)
3. When dependency available, human sets status="active"
4. Agent continues work
```

**Scenario 4: CI status visibility**
```
1. CI runs show_status.py before validators
2. Displays all project statuses in GitHub Actions output
3. Shows warnings for blocked projects
4. Helps team understand current project states at a glance
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
