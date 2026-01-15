# Agent Specification Validation

This document describes how to validate that agents are using their specifications and following quality standards.

## Overview

As of PR #XX, all agent role prompts now reference their comprehensive specifications. This ensures agents have access to:

- **Role specifications** (`specs/kerrigan/agents/<agent>/spec.md`) - Complete responsibility definitions
- **Quality bars** (`specs/kerrigan/agents/<agent>/quality-bar.md`) - Output quality standards
- **Architectures** (`specs/kerrigan/agents/<agent>/architecture.md`) - Approach guidelines
- **Acceptance tests** (`specs/kerrigan/agents/<agent>/acceptance-tests.md`) - Validation scenarios

## Validation Tools

The `tools/agent_audit.py` script provides several commands to validate spec compliance:

### Check Spec References

Verify that all agent prompts properly reference their specification files:

```bash
python tools/agent_audit.py check-spec-references
```

**Expected output:**
```
Checking if agent prompts reference their specifications...
✅ All agent prompts properly reference their specifications
```

This validates that each `role.*.md` file in `.github/agents/` contains links to all four specification documents for that agent.

### Validate Spec Compliance

Check that an agent's work complies with its specification:

```bash
# Basic compliance check (checks prompt references)
python tools/agent_audit.py validate-compliance role:swe

# With PR body validation (checks signature and role match)
python tools/agent_audit.py validate-compliance role:swe pr_description.txt
```

**Expected output:**
```
Validating spec compliance for role:swe...
✅ role:swe is compliant with its specification
```

This command validates:
- Agent prompt references its specifications
- If PR body is provided, checks for valid agent signature
- If signature is present, validates role matches expected role

### Check Quality Bar Compliance

Validate that artifacts meet quality bar standards:

```bash
python tools/agent_audit.py check-quality-bar role:swe src/file1.py src/file2.js
```

**Expected output:**
```
Checking quality bar compliance for role:swe...
⚠️  Warning: File src/file2.js has 450 lines (approaching 800 line limit)
✅ All artifacts meet quality bar standards for role:swe
```

This command checks:
- **File size limits**: Source files should not exceed 800 lines (warning at 400+)
- **Required sections**: For architect/spec roles, validates required sections in documentation
- **Markdown files are excluded**: Documentation files are not subject to line limits

### Generate Agent Checklist

Create a checklist of agent responsibilities:

```bash
python tools/agent_audit.py generate-checklist role:swe
```

**Expected output:**
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

## Workflow Validation Example

Here's a complete example of validating an agent workflow:

### Step 1: Agent Reviews Specifications

When starting work, an agent sees this in their role prompt:

```markdown
## Agent Specification

**Before you begin**, review your comprehensive agent specification to understand your full responsibilities:

- 📋 Specification: specs/kerrigan/agents/swe/spec.md
- ✅ Quality Bar: specs/kerrigan/agents/swe/quality-bar.md
- 🏗️ Architecture: specs/kerrigan/agents/swe/architecture.md
- 🧪 Acceptance Tests: specs/kerrigan/agents/swe/acceptance-tests.md
```

### Step 2: Agent Performs Work

The agent implements features following their spec:
- Writes tests before/during implementation (TDD)
- Keeps files under 800 lines
- Runs linting and fixes issues
- Manually verifies functionality
- Updates documentation

### Step 3: Agent Creates PR with Signature

```bash
# Generate signature
python tools/agent_audit.py create-signature role:swe

# Output: <!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T07:00:00Z -->
```

Include this in the PR description.

### Step 4: Validation Before Merge

```bash
# Save PR description to file
cat > pr_body.txt << 'EOF'
# Implement user authentication

<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T07:00:00Z -->

## Changes
- Added login endpoint
- Added registration endpoint
- Added JWT token generation
- Added authentication middleware
- Tests included with >80% coverage

## Manual Verification
✓ curl POST /api/register - returns 201
✓ curl POST /api/login - returns token
✓ curl GET /api/protected with token - returns 200
✓ curl GET /api/protected without token - returns 401
EOF

# Validate PR signature
python tools/agent_audit.py validate-pr pr_body.txt

# Validate spec compliance
python tools/agent_audit.py validate-compliance role:swe pr_body.txt

# Check quality bar for new files
python tools/agent_audit.py check-quality-bar role:swe src/auth/login.js src/auth/register.js
```

**Expected results:**
```
✅ Agent signature is valid
   Role: role:swe
   Version: 1.0
   Timestamp: 2026-01-15T07:00:00Z

✅ role:swe is compliant with its specification

✅ All artifacts meet quality bar standards for role:swe
```

## Quality Bar Standards by Agent

### All Agents

- **File size**: No source files >800 lines (warning at 400+)
- **Status check**: Must check `status.json` before starting work
- **Agent signature**: Must include signature in PR description

### SWE Agent

- **Test coverage**: >80% for new code
- **Linting**: All linting issues resolved
- **Manual verification**: Functionality tested manually
- **Documentation**: Updated when public APIs change

### Architect Agent

- **Required sections in architecture.md**:
  - `## Overview`
  - `## Components & interfaces`
  - `## Tradeoffs`
  - `## Security & privacy notes`
- **Milestone structure**: Each milestone ends with "CI passes"
- **Task clarity**: Each task has clear "done when" criteria

### Spec Agent

- **Required sections in spec.md**:
  - `## Goal`
  - `## Scope`
  - `## Non-goals`
  - `## Acceptance criteria`
- **Measurability**: Criteria must be measurable
- **Completeness**: Acceptance tests cover all criteria

## Gap Analysis

### Current Implementation

✅ **Completed:**
- All 7 agent role prompts reference their specifications
- `agent_audit.py` provides spec reference validation
- Quality bar compliance checking for file size limits
- Required section validation for architect/spec artifacts
- Comprehensive test coverage for new validation functions

### Potential Enhancements

🔄 **Future Improvements:**
- **Automated PR checks**: GitHub Actions workflow to validate signatures automatically
- **Quality bar scoring**: Numeric score for spec compliance (0-100)
- **Historical tracking**: Track spec compliance over time in audit log
- **Content analysis**: Use LLM to validate agent output matches spec intent
- **Template validation**: Check if artifacts follow expected templates
- **Cross-references**: Validate that plan.md tasks reference architecture.md components

## Testing the System

To verify the validation system works end-to-end:

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kixantrix/kerrigan.git
   cd kerrigan
   ```

2. **Run validation checks**
   ```bash
   # Check all agent prompts have spec references
   python tools/agent_audit.py check-spec-references
   
   # Validate each agent role
   for role in architect debugging deployment security spec swe testing; do
     echo "Checking role:$role..."
     python tools/agent_audit.py validate-compliance "role:$role"
   done
   ```

3. **Run the test suite**
   ```bash
   python -m unittest tests.test_agent_audit -v
   ```

All tests should pass, validating that:
- Spec references are correctly formatted
- Validation logic works as expected
- Quality bar checks function properly
- Agent signatures are validated correctly

## Summary

This implementation achieves the goals outlined in the requirements:

✅ **Agent prompts link to their specifications** - All 7 agent role files now include prominent references to their spec, quality bar, architecture, and acceptance tests.

✅ **Agent audit can verify spec compliance** - The `agent_audit.py` tool provides commands to check spec references, validate compliance, and verify quality bar standards.

✅ **Workflow validation** - This document demonstrates a complete workflow showing how agents reference and follow their specs.

✅ **Documentation updated** - README in `.github/agents/` updated with spec validation instructions, and this comprehensive validation document created.

The system provides a foundation for ensuring agents follow their specifications, with room for future enhancements like automated CI checks and deeper content analysis.
