# Agent Auditing System

This document describes the agent usage auditing mechanism that helps verify that labeled agents are actually using their specific prompts.

## Overview

The agent auditing system provides lightweight mechanisms to track and verify that agents tagged with role labels (like `role:swe`, `role:spec`) are following their designated prompts, rather than just performing generic work.

## Key Components

### 1. Agent Signatures

Agent signatures are HTML comments embedded in PR descriptions that identify which agent role created the PR.

**Format:**
```markdown
<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->
```

**Purpose:**
- Provides verifiable evidence that an agent used its specific prompt
- Includes timestamp to track when work was performed
- Version number allows tracking prompt changes over time
- Lightweight and doesn't interfere with PR readability (HTML comments are hidden)

### 2. Audit Log

The audit log is a JSON file that tracks which agents worked on which issues and PRs.

**Location:** `tools/.audit/agent_audit.json` (created automatically when first entry is added)

**Format:**
```json
{
  "version": "1.0",
  "last_updated": "2026-01-15T06:00:00Z",
  "entries": [
    {
      "timestamp": "2026-01-15T06:00:00Z",
      "agent_role": "role:swe",
      "pr_number": 123,
      "issue_number": 456,
      "signature": {
        "role": "role:swe",
        "version": "1.0",
        "timestamp": "2026-01-15T06:00:00Z"
      }
    }
  ]
}
```

### 3. Agent Checklists

Each agent prompt includes a checklist of responsibilities that agents should complete. This helps verify that agents are following their specific workflows.

**Example for SWE Agent:**
```markdown
## Agent Checklist (SWE Agent)
- [ ] Checked project status.json before starting
- [ ] Read architecture and plan
- [ ] Implemented features with tests
- [ ] Ran linting and fixed all issues
- [ ] Achieved >80% code coverage
- [ ] Manually verified functionality
- [ ] Kept files under quality bar limits
- [ ] Updated documentation as needed
```

## How to Use

### For Agents (AI Assistants)

When you are working as an agent:

1. **Include a signature in your PR description:**
   ```bash
   # Generate a signature
   python tools/agent_audit.py create-signature role:swe
   ```

2. **Copy the output and paste it into your PR description** (it's an HTML comment, so it won't be visible in the rendered markdown)

3. **Optionally, include a checklist** to show you followed the agent's workflow:
   ```bash
   # Generate a checklist for your role
   python tools/agent_audit.py generate-checklist role:swe
   ```

4. **Add the checklist to your PR description** so reviewers can verify you completed the expected steps

### For Reviewers

When reviewing a PR from an agent:

1. **Check for agent signature:** View the PR description's raw markdown to see the signature comment

2. **Verify the signature matches the PR labels:** If the PR has `role:swe` label, the signature should say `role=role:swe`

3. **Review the checklist:** If present, verify that the checklist items are actually completed

4. **Check audit log (optional):** Review `tools/.audit/agent_audit.json` to see history of agent work

### Validation

The system includes validators that can check PR signatures:

```bash
# Check a PR description for valid signature
echo "<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->" > /tmp/pr.md
python tools/agent_audit.py validate-pr /tmp/pr.md
```

**Note:** The signature validator is currently informational only and runs as a warning, not a failure, to keep the system lightweight.

## Command-Line Tools

The `agent_audit.py` script provides several commands:

### Create Signature
Generate a signature for a specific agent role:
```bash
python tools/agent_audit.py create-signature role:swe
# Output: <!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:14:11Z -->
```

### Generate Checklist
Generate a responsibility checklist for an agent role:
```bash
python tools/agent_audit.py generate-checklist role:spec
```

### Validate PR
Validate that a PR description has a proper agent signature:
```bash
python tools/agent_audit.py validate-pr /path/to/pr_description.md
```

## Signature Format Specification

### Required Fields

1. **role**: Agent role in format `role:name` (e.g., `role:swe`, `role:spec`)
2. **version**: Semver format (e.g., `1.0` or `1.0.0`)
3. **timestamp**: ISO 8601 format with Z suffix (e.g., `2026-01-15T06:00:00Z`)

### Validation Rules

- Role must start with `role:` or `agent:` prefix
- Version must match semver pattern: `\d+\.\d+(\.\d+)?`
- Timestamp must be valid ISO 8601 format
- Signature must be in HTML comment format: `<!-- AGENT_SIGNATURE: ... -->`

## Integration with CI

The agent signature validator can be integrated into CI workflows:

```yaml
# Example: Add to .github/workflows/ci.yml
- name: Check agent signatures
  run: python tools/validators/check_agent_signature.py
```

**Current behavior:** The validator runs in informational mode and only produces warnings, not failures. This keeps the auditing system lightweight and non-blocking.

## Benefits

### Auditability
- Track which agents worked on which PRs/issues
- Historical record of agent usage patterns
- Easy to identify if an agent is being used consistently

### Verification
- Confirm agents are following their specific prompts
- Checklists help ensure agents complete expected steps
- Timestamps help correlate agent work with prompt versions

### Lightweight
- Signatures are HTML comments (invisible in rendered markdown)
- No external dependencies or infrastructure required
- Validation is informational only (doesn't block PRs)
- Optional audit log (created only if used)

## Agent Prompt Updates

All agent role prompts have been updated to include signature instructions:

- `role.spec.md` - Spec Agent
- `role.architect.md` - Architect Agent
- `role.swe.md` - SWE Agent
- `role.testing.md` - Testing Agent
- `role.debugging.md` - Debugging Agent
- `role.deployment.md` - Deployment Agent
- `role.security.md` - Security Agent

Each prompt now includes a section titled "Agent Signature (Required)" with instructions on how to generate and include signatures.

## Testing

The auditing system includes comprehensive tests:

- `tests/test_agent_audit.py` - Tests for signature validation, audit log, and checklists
- `tests/test_agent_prompts.py` - Tests that all prompts include signature instructions

Run tests:
```bash
python -m unittest tests.test_agent_audit -v
python -m unittest tests.test_agent_prompts.TestAgentSignatureInPrompts -v
```

## Future Enhancements

Possible future improvements (not currently implemented):

1. **Automated audit log population** - GitHub Actions that automatically record signatures to audit log
2. **Signature enforcement** - Make signatures required instead of optional
3. **Prompt versioning** - Track which version of a prompt was used
4. **Analytics dashboard** - Visualize agent usage patterns
5. **Behavioral validation** - Check that PR contents match expected agent behaviors

## FAQ

**Q: Are signatures required?**
A: Currently signatures are recommended but not enforced. The validator produces warnings, not errors.

**Q: What if I forget to include a signature?**
A: The PR will still be accepted, but it may be flagged in review as lacking auditability.

**Q: Can I use this with non-Kerrigan agents?**
A: Yes, any agent system can adopt this signature pattern.

**Q: Does the audit log need to be committed?**
A: No, the audit log is optional and typically excluded from version control (add to .gitignore if generated).

**Q: How do I verify an agent is using its prompt?**
A: Check three things: (1) PR has the signature, (2) signature role matches PR labels, (3) PR checklist shows agent followed workflow steps.

## See Also

- [Agent Assignment Guide](agent-assignment.md) - How to assign work to agents
- [Agent Prompts README](../.github/agents/README.md) - All agent role definitions
- [Autonomy Modes](../playbooks/autonomy-modes.md) - Control when agents can work
