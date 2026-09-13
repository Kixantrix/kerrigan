# Agent Feedback System

This directory houses the agent feedback backchannel system for continuous improvement of Kerrigan.

Current cross-device investigation: [Framework effectiveness audit (September 2026)](audits/2026-09-framework/README.md) -
evidence, proposed improvement slices, and a portable handoff. This is an audit,
not a replacement for the current operating rules.

## Overview

The feedback system enables agents to report friction points, unclear instructions, and successful patterns encountered during work. This structured feedback drives systematic improvements to agent prompts, artifact contracts, playbooks, and the overall Kerrigan system.

## Directory Structure

```
feedback/
├── README.md                    # This file
├── agent-feedback/              # Feedback submissions
│   ├── README.md               # Submission guidelines
│   ├── TEMPLATE.yaml           # Feedback template
│   └── *.yaml                  # Feedback files (all periods)
├── design-feedback/             # Design-specific feedback
│   └── *.yaml                  # Design feedback files
└── satellite/                   # Satellite repo feedback
    ├── README.md               # Satellite feedback guide
    ├── TEMPLATE.md             # Satellite feedback template
    └── *.md                    # Feedback from satellite installations
```

**Retention is outcome-based, not age-based.** Keep unresolved feedback until
its decision and accountable next action are recorded. Once the lesson is
absorbed into a canonical rule/change or a durable tracked follow-up, record
that link and disposition before removing the intake file through normal
review. Git history retains it; `processed/` is temporary staging, not an archive.
Do not delete unresolved evidence merely because it is old.

## Quick Start

### For Agents Submitting Feedback

1. **Copy the template**:
   ```bash
   cp feedback/agent-feedback/TEMPLATE.yaml \
      feedback/agent-feedback/2026-01-15-123-my-issue.yaml
   ```

2. **Fill in your feedback**: Edit the file with your experience

3. **Submit**: Include in your PR or create separate feedback PR

### For Satellite Repos Submitting Feedback

Satellite repos (projects using Kerrigan) can provide feedback too!

1. **Use the feedback script** (recommended):
   ```powershell
   ./tools/feedback-to-kerrigan.ps1
   ```

2. **Or use the template manually**: See `feedback/satellite/TEMPLATE.md`

3. **Submit**: The script creates a GitHub issue, or you can submit via PR

See `feedback/satellite/README.md` for detailed instructions.

### For Kerrigan Reviewing Feedback

1. **Check for new feedback**:
   ```bash
   ls -lt feedback/agent-feedback/*.yaml | grep -v TEMPLATE
   ls -lt feedback/satellite/*.md | grep -v TEMPLATE
   ```

2. **Review and triage**: Follow `playbooks/feedback-review.md`

3. **Take action**: Update prompts, contracts, or playbooks based on analysis

4. **Close the loop**: Record the canonical rule/change, owner and adoption outcome.
   Kerrigan's checked-in workflows do not provide a daily self-improvement
   automation; verify any satellite-specific automation rather than assuming
   one is running. Any recurring triage needs an explicit owner,
   bounded scope and stop conditions.

### From Observation to Reusable Learning

Use the existing feedback entry's context and notes (or a Markdown contribution),
not another mandatory artifact. Record what was observed versus reported or
proposed, the applicable runtime/harness revision and scope, counterexamples,
the decision owner, and the target canonical skill/playbook/rule. Keep private
source receipts outside public feedback.

When adopted, link the canonical change and record the satellite's adopted
revision, local overrides and observed result. A merged harness PR is not proof
that every repository or device adopted it. Keep domain-specific lessons local;
promote validated general lessons centrally. See the
[cross-device handoff](audits/2026-09-framework/handoff.md) for a concrete example.

## Feedback Categories

### Agent Feedback Categories

- **prompt_clarity**: Instructions are unclear or ambiguous
- **missing_information**: Prompt lacks necessary information
- **artifact_conflict**: Artifacts don't match between agents
- **tool_limitation**: Missing tools or permissions
- **quality_bar**: Unclear quality expectations
- **workflow_friction**: Process inefficiencies
- **success_pattern**: Effective techniques worth documenting

### Satellite Feedback Categories

- **bug**: Issues found in Kerrigan components
- **enhancement**: Improvements based on real-world usage
- **pattern**: Solutions that worked well in their context
- **question**: Clarifications needed about Kerrigan features

## Why This Matters

**Without feedback**: Same issues repeat, agents struggle with unclear prompts, system improvements are ad-hoc, satellite experiences are lost.

**With feedback**: Systematic improvement, pattern detection, clear communication, better agent experience, real-world validation from satellite installations.

## Success Metrics

- **Adoption**: Agents regularly submit feedback
- **Action rate**: High percentage of feedback implemented
- **Time to resolution**: Quick turnaround from submission to action
- **Impact**: Reduction in repeated issues

## Documentation

- **Full specification**: `specs/kerrigan/080-agent-feedback.md`
- **Review process**: `playbooks/feedback-review.md`
- **Agent prompts**: All role prompts include feedback sections
- **Tests**: `tests/test_feedback.py` validates system structure

## Examples

See the [framework audit](audits/2026-09-framework/README.md) and Git history for
examples of feedback and its disposition, demonstrating:
- How to write clear, actionable feedback
- What kinds of issues are valuable to report
- How feedback leads to system improvements

## Philosophy

Feedback is a **gift**. When agents take time to document friction or share success patterns, they're investing in making the system better for everyone. Each piece of feedback is an opportunity to:

- Reduce friction for future agents
- Clarify ambiguous instructions
- Document successful patterns
- Evolve the system based on real experience

The feedback loop closes when changes are made and documented, completing the cycle of continuous improvement.
