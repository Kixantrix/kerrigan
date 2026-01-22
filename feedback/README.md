# Agent Feedback System

This directory houses the agent feedback backchannel system for continuous improvement of Kerrigan.

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
└── design-feedback/             # Design-specific feedback
    └── *.yaml                  # Design feedback files
```

**Note:** Feedback files remain in `agent-feedback/` indefinitely. The daily self-improvement workflow uses date-based filtering (`--since-days 7`) to automatically skip older feedback during analysis. Files older than 30 days should be periodically deleted to keep the directory manageable.

## Quick Start

### For Agents Submitting Feedback

1. **Copy the template**:
   ```bash
   cp feedback/agent-feedback/TEMPLATE.yaml \
      feedback/agent-feedback/2026-01-15-123-my-issue.yaml
   ```

2. **Fill in your feedback**: Edit the file with your experience

3. **Submit**: Include in your PR or create separate feedback PR

### For Kerrigan Reviewing Feedback

1. **Check for new feedback**:
   ```bash
   ls -lt feedback/agent-feedback/*.yaml | grep -v TEMPLATE
   ```

2. **Review and triage**: Follow `playbooks/feedback-review.md`

3. **Take action**: Update prompts, contracts, or playbooks based on analysis

4. **Monitor automated workflow**: Daily self-improvement workflow creates issues for high/medium priority items

## Feedback Categories

- **prompt_clarity**: Instructions are unclear or ambiguous
- **missing_information**: Prompt lacks necessary information
- **artifact_conflict**: Artifacts don't match between agents
- **tool_limitation**: Missing tools or permissions
- **quality_bar**: Unclear quality expectations
- **workflow_friction**: Process inefficiencies
- **success_pattern**: Effective techniques worth documenting

## Why This Matters

**Without feedback**: Same issues repeat, agents struggle with unclear prompts, system improvements are ad-hoc.

**With feedback**: Systematic improvement, pattern detection, clear communication, better agent experience.

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

See `processed/` directory for examples of feedback that has been reviewed and acted upon, demonstrating:
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
