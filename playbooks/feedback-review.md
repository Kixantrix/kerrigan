# Feedback Review Playbook

This playbook describes how Kerrigan reviews and processes agent and satellite feedback to drive continuous improvement.

## Overview

The feedback backchannel enables:
- **Agents** to report friction points, successes, and suggestions from their work
- **Satellite repos** (projects using Kerrigan) to share real-world experiences, bugs, and patterns

This playbook ensures all feedback is reviewed systematically and drives meaningful improvements.

## Review Cadence

**Weekly review**: Check feedback directories every week
- `feedback/agent-feedback/` - Internal agent feedback
- `feedback/satellite/` - Satellite repo feedback
- More frequent if actively working on meta-improvements
- Can be triggered by agent notification in PR or issue

**Quarterly analysis**: Analyze patterns and trends every quarter
- Identify systemic issues
- Prioritize major improvements
- Measure effectiveness of changes
- Review satellite adoption and contribution patterns

## Review Process

### 1. Collect New Feedback

```bash
# Check for new agent feedback entries
ls -lt feedback/agent-feedback/*.yaml | grep -v TEMPLATE

# Check for new satellite feedback
ls -lt feedback/satellite/*.md | grep -v TEMPLATE

# Count new feedback
find feedback/agent-feedback -name "*.yaml" ! -name "TEMPLATE.yaml" | wc -l
find feedback/satellite -name "*.md" ! -name "TEMPLATE.md" | wc -l
```

### 2. Triage Each Entry

For each feedback file, assess:

**Severity confirmation**:
- Is the reported severity accurate?
- Does this block work or just cause friction?

**Category validation**:
- Is the category correct?
- Does this fit multiple categories?

**Scope assessment**:
- Is this a one-off issue or systemic?
- How many agents/projects affected?

**Priority determination**:
- **P0 (immediate)**: Blocks work, causes errors
- **P1 (next sprint)**: Significant friction, multiple reports
- **P2 (backlog)**: Nice-to-have, single report

### 3. Investigate Root Cause

**Review related files**:
```bash
# For each file mentioned in related_files
cat .github/agents/role.swe.md
cat specs/kerrigan/020-artifact-contracts.md
```

**Check for patterns**:
```bash
# Search for similar issues in other feedback
grep -r "validator heading" feedback/
```

**Validate the issue**:
- Can you reproduce the problem?
- Is the agent's description accurate?
- What would have prevented this?

### 4. Determine Action

Choose appropriate response:

**A) Implement fix immediately**
- High severity issues
- Simple fixes (< 30 minutes)
- Clear solution proposed

**B) Create tracked issue**
- Needs design work
- Affects multiple components
- Requires discussion

**C) Document as known limitation**
- Cannot fix currently
- Acceptable tradeoff
- Workaround exists

**D) Request more information**
- Issue unclear
- Cannot reproduce
- Need agent input

### 5. Take Action

#### For immediate fixes:

1. Create PR with fix
2. Link to feedback file in PR description
3. Update feedback file with status and PR number
4. Move to processed/ after PR merges

#### For tracked issues:

1. Create GitHub issue
2. Link feedback file in issue description
3. Add appropriate labels (e.g., `meta`, `documentation`)
4. Update feedback file with issue number
5. Leave in agent-feedback/ until resolved

#### For won't-fix items:

1. Update feedback status to "wont_fix"
2. Add detailed notes explaining decision
3. Document workaround if available
4. Move to processed/

### 6. Update Status

Edit the feedback YAML file:

```yaml
# Before processing
status: "new"
reviewed_by: ""
reviewed_date: ""

# After review
status: "reviewed"  # or "implemented" if immediately fixed
reviewed_by: "kerrigan-maintainer"
reviewed_date: "2026-01-15T14:00:00Z"
implementation_pr: 123  # if fixed
notes: |
  Confirmed issue. Updated role.swe.md to include exact heading names.
  Also added examples to handoffs.md.
```

### 7. Archive Processed Feedback

```bash
# Move processed feedback to archive
mv feedback/agent-feedback/2026-01-15-42-heading-names.yaml \
   feedback/processed/2026-01-15-42-heading-names.yaml
```

## Implementation Patterns

### Pattern 1: Prompt Improvement

**Trigger**: Unclear instructions, missing information

**Actions**:
1. Update relevant agent prompt file
2. Add specific examples
3. Cross-check other prompts for same issue
4. Update handoffs.md if affects multiple agents

**Example**:
```markdown
# Before
Create necessary artifacts following the spec.

# After
Create the following artifacts:
- spec.md with exact headings: "Goal", "Scope", "Non-goals", "Acceptance criteria"
- acceptance-tests.md with Given/When/Then format
```

### Pattern 2: Contract Clarification

**Trigger**: Mismatched expectations between agents

**Actions**:
1. Update artifact contract document
2. Align all agent prompts with contract
3. Add validation rules if possible
4. Update examples

**Example**: Specify exact case-sensitive heading names in contract

### Pattern 3: Process Refinement

**Trigger**: Workflow friction, redundant steps

**Actions**:
1. Update relevant playbook
2. Simplify or streamline process
3. Update agent prompts with new workflow
4. Document rationale in handoffs.md

**Example**: Reduce required artifacts for small changes

### Pattern 4: Success Amplification

**Trigger**: Agent reports effective technique

**Actions**:
1. Document pattern in relevant playbook
2. Add to agent prompt as recommended approach
3. Create example in examples/ if valuable
4. Share in handoffs.md

**Example**: Effective TDD workflow that caught bugs early

## Pattern Detection

### Monthly Pattern Analysis

Look for recurring themes:

```bash
# Count feedback by category
for category in prompt_clarity missing_information artifact_conflict tool_limitation quality_bar workflow_friction success_pattern; do
  echo "$category: $(grep -r "category: \"$category\"" feedback/ | wc -l)"
done

# Count feedback by severity
for severity in high medium low; do
  echo "$severity: $(grep -r "severity: \"$severity\"" feedback/ | wc -l)"
done

# Count feedback by agent role
for role in spec architect swe testing deployment debugging security kerrigan; do
  echo "$role: $(grep -r "agent_role: \"$role\"" feedback/ | wc -l)"
done
```

### Systemic Issues

Look for:
- **Repeated categories**: Same type of issue from multiple agents
- **Multiple roles affected**: Issue spans agent boundaries
- **Escalating severity**: Issues getting worse over time

**Response**: Create epic issue to address root cause systematically

## Satellite Feedback Review

Satellite feedback comes from repos using Kerrigan in production. This feedback is especially valuable as it represents real-world usage and battle-tested patterns.

### Satellite Feedback Location

- `feedback/satellite/` - Markdown files or GitHub issues labeled `satellite-feedback`

### Satellite Feedback Categories

- **bug**: Issues found in Kerrigan components
- **enhancement**: Improvements based on real usage
- **pattern**: Successful techniques worth sharing
- **question**: Clarifications needed

### Special Considerations for Satellite Feedback

**Real-world validation**:
- Satellite feedback represents production usage
- Bugs from satellites are likely to affect others
- Patterns from satellites are battle-tested

**Credit and attribution**:
- Always credit satellite contributors in changelogs
- If satellite is anonymous, credit as "community contributor"
- Link to satellite repo when provided (helps others learn)

**Response priority**:
- **High**: Bugs blocking satellites, security issues
- **Medium**: Enhancements with clear use cases, patterns worth documenting
- **Low**: Nice-to-have improvements, questions (still answer promptly)

### Triage Process for Satellite Feedback

For each satellite feedback entry:

1. **Acknowledge**: Respond to the issue/PR thanking the contributor
2. **Verify**: Can you reproduce the issue? Does the pattern make sense?
3. **Assess impact**: How many satellites might be affected?
4. **Determine action**:
   - **Immediate fix**: Critical bugs, security issues
   - **Create issue**: Track enhancement, needs design
   - **Document pattern**: Add to playbook or examples
   - **Answer question**: Respond with clarification, update docs

5. **Credit**: Add to CHANGELOG when implemented
6. **Close loop**: Update the satellite on resolution

### Example Satellite Feedback Actions

**Bug report**:
```bash
# Fix immediately if critical
git checkout -b fix/satellite-windows-path-issue
# Make fix
# Test on Windows
# Create PR referencing satellite feedback
# Credit in commit message: "Fix path separator issue (reported by @satellite-user)"
```

**Enhancement suggestion**:
```bash
# Create tracked issue
gh issue create --title "Add multi-repo handoff pattern" \
  --body "Enhancement suggested by satellite repo financial-api..." \
  --label "enhancement,satellite-feedback,documentation"
```

**Pattern sharing**:
```bash
# Document in playbook
# Add to examples/ if substantial
# Update relevant agent prompts
# Credit in changelog: "Added documentation pattern from docs-site satellite"
```

**Question**:
```bash
# Answer on the issue/PR
# If FAQ-worthy, add to docs/FAQ.md
# Update docs to be clearer
```

### Quarterly Satellite Analysis

Every quarter, analyze satellite feedback for:

- **Adoption signals**: How many satellites are contributing?
- **Common pain points**: What issues come up repeatedly?
- **Feature requests**: What do satellites need most?
- **Success patterns**: What patterns are working well?
- **Documentation gaps**: Where do satellites get stuck?

**Actions**:
- Prioritize features based on satellite needs
- Create targeted documentation
- Reach out to satellites for case studies
- Celebrate and showcase satellite contributions

## Metrics and Reporting

### Track Progress

**Feedback flow**:
- New agent feedback per week
- New satellite feedback per week
- Average time from submission to action
- Implementation rate (% of feedback acted upon)
- Satellite contribution rate (active satellites)

**Impact**:
- Reduction in similar issues over time
- Agent satisfaction (qualitative)
- Satellite adoption and contribution
- Decreased friction (measured by completion time)
- Documentation improvements driven by feedback

### Quarterly Report

Summarize in issue or doc:
1. Total feedback received (agent + satellite)
2. Breakdown by category and severity
3. Actions taken (PRs, issues, changes)
4. Patterns identified
5. Key improvements made
6. Outstanding items
7. Satellite contributions and impact
8. Credit to satellite contributors

## Communication

### To Agents

When processing feedback:
- Comment on original issue thanking agent
- Link to PR or issue created
- Explain decision for won't-fix items

**Example comment**:
```
Thanks for the feedback! You're right that the heading names weren't clear.
I've updated role.swe.md with specific examples in #44.
The feedback has been processed and moved to the archive.
```

### To Satellites

When processing satellite feedback:
- Respond promptly (within a week)
- Thank contributor for their input
- Explain action being taken
- Credit in changelog when implemented
- Close the loop when resolved

**Example response**:
```
Thank you for reporting this Windows path separator issue! This is definitely
a bug that affects real-world usage. I've created PR #123 to fix it using
Join-Path for cross-platform compatibility. You'll be credited in the changelog.

We really appreciate satellite feedback - it helps make Kerrigan more robust!
```

### To Maintainers

When significant patterns emerge:
- Create issue summarizing pattern
- Propose systemic improvements
- Link all related feedback entries

## Tools and Automation

### Validation Script

Create `tools/validators/check_feedback.py` to validate:
- Required fields present
- Valid categories and severities
- Proper YAML syntax
- Filename matches convention

### Summary Script

Create `tools/feedback/summarize.py` to:
- Generate statistics
- Identify patterns
- Create reports

## Best Practices

### Do:
- ✅ Review feedback weekly
- ✅ Acknowledge all submissions
- ✅ Act on high-severity items quickly
- ✅ Look for patterns
- ✅ Update documentation
- ✅ Close the loop with agents

### Don't:
- ❌ Let feedback accumulate unreviewed
- ❌ Ignore low-severity items indefinitely
- ❌ Fix symptoms without addressing root cause
- ❌ Make changes without updating docs
- ❌ Forget to move processed feedback to archive

## Examples

### Example 1: High-Severity Prompt Issue

**Feedback**: Validator heading names not in prompt
**Action**: Immediate fix to role.swe.md
**Time**: Same day
**Result**: No more reports of this issue

### Example 2: Workflow Friction Pattern

**Feedback**: Multiple agents report artifact creation is heavy
**Action**: Created issue #50 to redesign artifact contracts
**Time**: Next sprint
**Result**: Reduced required artifacts for small projects

### Example 3: Success Pattern

**Feedback**: TDD approach caught integration bugs early
**Action**: Added TDD guidance to testing playbook
**Time**: Next weekly review
**Result**: Other agents adopt pattern

## Related Documents

- `specs/kerrigan/080-agent-feedback.md`: Complete feedback specification
- `feedback/agent-feedback/TEMPLATE.yaml`: Agent feedback template
- `feedback/satellite/TEMPLATE.md`: Satellite feedback template
- `feedback/satellite/README.md`: Satellite feedback guide
- `tools/feedback-to-kerrigan.ps1`: Satellite feedback submission script
- `playbooks/handoffs.md`: Agent handoff process
- `specs/kerrigan/010-agent-archetypes.md`: Agent roles
