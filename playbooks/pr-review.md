# PR review expectations

Every PR should include:
- Link to the project folder: `specs/projects/<project-name>/`
- Which milestone/task it advances
- Tests added or updated (or rationale if none)
- Any docs updates required by the artifact contract

Preferred:
- Small, focused diffs
- Clear commit messages
- Screenshots/logs for UX changes (when applicable)

## Handling Copilot PR Reviewer Feedback

When the Copilot pull-request-reviewer bot leaves feedback on PRs:

### Detection
Check for review comments from Copilot reviewers:
```bash
# View all review comments
gh pr view <PR#>

# List PRs with review feedback
.\tools\handle-reviews.ps1
```

### Categorization

**Critical feedback (must fix before merge):**
- Missing functional tests
- Security vulnerabilities
- Breaking changes

**Important feedback (should fix):**
- Missing file encoding
- Imports in wrong location
- Unused imports
- Best practice violations

**Nice-to-have feedback:**
- Style suggestions
- Minor optimizations

### Actions

**For critical/important feedback:**
```bash
# Assign agent to fix
gh pr comment <PR#> --body "@copilot Please address all review comments"

# Or use bulk tool
.\tools\handle-reviews.ps1 --assign-fixes
```

**For nice-to-have feedback:**
- Consider creating follow-up issues
- Don't block PR merge

**Verification:**
- Monitor for new commits addressing feedback
- Re-review after fixes
- Merge when addressed or create follow-up issues

## Agent Spec Compliance

PRs created by agents are subject to additional compliance checks to ensure agents follow their specifications:

### Quality Bar Requirements

All source files must adhere to quality bar standards:
- **Warning threshold**: Files with >400 lines trigger a warning
- **Hard limit**: Files with >800 lines will fail the quality bar check
- **Exception**: Documentation files (.md, .json, .yaml) are excluded from line count checks

**How to check locally:**
```bash
python tools/agent_audit.py check-quality-bar <role> <file1> <file2> ...
```

**Example:**
```bash
python tools/agent_audit.py check-quality-bar role:swe src/auth/login.js src/auth/middleware.js
```

### Agent Signature Requirements

PRs with `role:*` or `agent:*` labels should include an agent signature in the PR description for auditability:

**Format:**
```html
<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->
```

**How to generate:**
```bash
python tools/agent_audit.py create-signature <role>
```

**Example:**
```bash
python tools/agent_audit.py create-signature role:swe
```

See `docs/agent-spec-validation.md` for details on agent signatures and validation.

### Spec Reference Requirements

Agent prompts in `.github/agents/` must reference their specification files:
- `specs/kerrigan/agents/<agent>/spec.md` - Complete responsibility definitions
- `specs/kerrigan/agents/<agent>/quality-bar.md` - Output quality standards
- `specs/kerrigan/agents/<agent>/architecture.md` - Approach guidelines
- `specs/kerrigan/agents/<agent>/acceptance-tests.md` - Validation scenarios

**How to check locally:**
```bash
python tools/agent_audit.py check-spec-references
```

This check runs automatically on PRs that modify agent prompts.

### Compliance Validation

Agent PRs are validated against their role's specification:

**How to check locally:**
```bash
# Basic compliance check
python tools/agent_audit.py validate-compliance <role>

# With PR body validation
python tools/agent_audit.py validate-compliance <role> pr_description.txt
```

**Example:**
```bash
python tools/agent_audit.py validate-compliance role:swe pr_body.txt
```

### Automated Checks in CI

The following compliance checks run automatically in CI:

1. **Quality Bar Check** (all PRs): Validates file size limits
   - Runs in: `.github/workflows/ci.yml`
   - Command: `python tools/validators/check_quality_bar.py`

2. **Spec Reference Check** (agent prompt updates): Verifies prompts link to specs
   - Runs in: `.github/workflows/agent-spec-compliance.yml`
   - Triggers on: Changes to `.github/agents/**` or label `agent:prompt-update`
   - Command: `python tools/agent_audit.py check-spec-references`

3. **Agent Compliance Check** (agent-labeled PRs): Validates signatures and compliance
   - Runs in: `.github/workflows/agent-spec-compliance.yml`
   - Triggers on: PRs with `role:*` or `agent:*` labels
   - Validates: Agent signature, spec compliance

### Override Mechanisms

For exceptional cases, the following labels can override compliance checks:
- `allow:large-file` - Bypass quality bar file size warnings (informational)
- `autonomy:override` - Bypass autonomy gates (requires human approval)

### Failure Guidance

When compliance checks fail, error messages include:
- **Clear explanation** of what failed
- **Actionable commands** to fix the issue locally
- **Documentation links** for additional context

See `docs/agent-spec-validation.md` for complete validation documentation and examples.
