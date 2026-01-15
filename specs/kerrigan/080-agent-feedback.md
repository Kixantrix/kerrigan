# Agent Feedback Backchannel

This document defines the feedback mechanism for agents to report issues, friction points, and suggestions that Kerrigan can review and use to improve agent construction.

## Problem Statement

Agents currently have no way to leave structured notes for Kerrigan about what is working or not working. This prevents systematic improvement of agent prompts and contracts.

## Goal

Create a low-overhead, high-signal feedback mechanism where agents can report issues and suggestions that Kerrigan can review and use to improve agent construction.

## Feedback File Format

### Location
- **Feedback directory**: `feedback/`
- **Agent feedback**: `feedback/agent-feedback/`
- **Processed feedback**: `feedback/processed/`

### Format
Feedback entries are YAML files with structured metadata for easy processing and analysis.

**Filename convention**: `YYYY-MM-DD-<issue-number>-<short-slug>.yaml`

Example: `2026-01-15-42-prompt-clarity.yaml`

### Schema

```yaml
# REQUIRED FIELDS
timestamp: "ISO 8601 timestamp"
issue_number: 123                    # GitHub issue number where feedback originated
agent_role: "spec|architect|swe|testing|deployment|debugging|security|kerrigan"
category: "prompt_clarity|missing_information|artifact_conflict|tool_limitation|quality_bar|workflow_friction|success_pattern"
severity: "low|medium|high"          # Impact on agent effectiveness
title: "Brief description"           # 1-line summary

# REQUIRED: Detailed description
description: |
  Clear explanation of the issue, friction point, or suggestion.
  Include specific examples where possible.

# OPTIONAL FIELDS
related_files:                       # Files involved in the feedback
  - "path/to/file1"
  - "path/to/file2"

related_artifacts:                   # Artifacts involved
  - "spec.md"
  - "architecture.md"

context: |                          # Additional context
  Any relevant background information.

proposed_solution: |                # Suggested fix (optional)
  If the agent has ideas for improvement.

# METADATA (added by Kerrigan during processing)
status: "new|reviewed|implemented|wont_fix"
reviewed_by: "username"
reviewed_date: "ISO 8601 timestamp"
implementation_pr: 123              # PR number where fix was implemented
notes: |                           # Processing notes
  Notes from review and implementation.
```

## Feedback Categories

### 1. Prompt Clarity Issues
Agent prompts are unclear, ambiguous, or missing critical information.

**Examples:**
- Validator expects exact heading names, but prompt doesn't specify them
- Instructions conflict with each other
- Unclear what "done" looks like

### 2. Missing Information
Agent prompts lack necessary information to complete tasks effectively.

**Examples:**
- No mention of required dependencies
- Missing security considerations
- Unclear testing expectations

### 3. Artifact Contract Conflicts
Artifacts produced by one agent don't match what the next agent expects.

**Examples:**
- Spec agent creates "Acceptance Criteria" but validator expects "Acceptance criteria"
- Missing required sections in artifacts
- Inconsistent naming conventions

### 4. Tool/Permission Limitations
Agent lacks necessary tools or permissions to complete tasks.

**Examples:**
- Cannot access required APIs
- Missing CLI tools
- File system permissions issues

### 5. Quality Bar Misalignments
Quality expectations are unclear or inconsistent.

**Examples:**
- Unclear what constitutes "sufficient" test coverage
- Conflicting guidance on file size limits
- Ambiguous documentation requirements

### 6. Workflow Friction Points
Process inefficiencies that slow down agent effectiveness.

**Examples:**
- Redundant validation steps
- Unclear handoff process
- Too many required artifacts for small changes

### 7. Success Patterns to Amplify
Techniques and approaches that work well and should be documented.

**Examples:**
- Effective TDD approach
- Useful debugging techniques
- Good testing patterns

## Collection Process

### For Agents

**When to provide feedback:**
- When you encounter unclear instructions
- When you discover missing information
- When you find conflicts between documents
- When you identify workflow friction
- When you discover a successful pattern worth sharing

**How to provide feedback:**

1. **During work**: Note friction points in your PR description or comments
2. **After completing work**: Create a structured feedback file
3. **Use the template**: Copy from `feedback/agent-feedback/TEMPLATE.yaml`
4. **Submit with work**: Include feedback file in your PR or create separate feedback PR

**Template location**: `feedback/agent-feedback/TEMPLATE.yaml`

### For Humans

Humans can also submit feedback by creating YAML files using the same format. This is useful when:
- Observing agent behavior
- Reviewing PRs
- Identifying patterns across multiple issues

## Review Process

### Kerrigan Agent Responsibilities

1. **Regular review**: Check `feedback/agent-feedback/` for new entries weekly
2. **Triage**: Categorize and prioritize feedback
3. **Analysis**: Identify patterns and systemic issues
4. **Action**: Create issues or PRs to address feedback
5. **Archive**: Move processed feedback to `feedback/processed/` with status updates

### Review Criteria

**Immediate action (high severity):**
- Blocks agents from completing work
- Causes repeated errors
- Security or quality concerns

**Plan for next iteration (medium severity):**
- Causes friction but has workarounds
- Affects efficiency but not correctness
- Multiple reports of same issue

**Backlog (low severity):**
- Nice-to-have improvements
- Single isolated report
- Cosmetic or minor issues

## Implementation Loop

1. **Feedback submitted**: Agent or human creates feedback file
2. **Kerrigan reviews**: Kerrigan agent triages and analyzes
3. **Issue created**: Significant feedback becomes tracked issue
4. **Fix implemented**: Prompts, contracts, or playbooks updated
5. **Feedback archived**: Original feedback moved to processed/ with status
6. **Documentation updated**: Changes reflected in relevant docs

### Example Workflow

```
1. SWE agent reports: "role.swe.md doesn't mention exact validator heading names"
   → Creates feedback/agent-feedback/2026-01-15-42-heading-names.yaml

2. Kerrigan reviews feedback, confirms issue
   → Updates status to "reviewed"
   → Creates issue #43: "Update SWE prompt with exact heading names"

3. Kerrigan updates role.swe.md with specific heading examples
   → Creates PR #44 linking to issue #43

4. PR merged, Kerrigan updates feedback file
   → status: "implemented"
   → implementation_pr: 44
   → Moves to feedback/processed/

5. Documentation updated
   → handoffs.md updated with this learning
   → Other agent prompts checked for same issue
```

## Acceptance Criteria

- ✅ Agents can easily leave structured feedback using YAML format
- ✅ Feedback directory structure is clear and organized
- ✅ Kerrigan has a defined process to review and act on feedback
- ✅ Feedback loop is documented in playbooks
- ✅ Template provides clear guidance for feedback creation
- ✅ Low overhead: feedback creation takes < 5 minutes
- ✅ High signal: structured format enables pattern detection

## Success Metrics

- **Adoption**: Number of feedback entries per month
- **Action rate**: Percentage of feedback implemented or addressed
- **Time to resolution**: Days from feedback to implementation
- **Pattern detection**: Number of systemic issues identified
- **Agent effectiveness**: Reduction in repeated issues

## Non-Goals

- Real-time feedback or chat systems (keep it file-based)
- Complex feedback workflows or approval processes
- Automated feedback collection (agents decide what to report)
- Integration with external tools (stay within repo)

## Related Documents

- `specs/kerrigan/010-agent-archetypes.md`: Agent roles and responsibilities
- `specs/kerrigan/020-artifact-contracts.md`: Required artifacts
- `specs/kerrigan/030-quality-bar.md`: Quality standards
- `playbooks/feedback-review.md`: Detailed review process
- `feedback/agent-feedback/TEMPLATE.yaml`: Feedback template
