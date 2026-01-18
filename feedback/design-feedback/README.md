# Design Feedback System

This directory houses user feedback on design system iterations for interactive refinement with the design agent.

## Overview

The design feedback system enables human users to provide structured feedback on design systems, components, tokens, and design philosophies. This feedback drives iterative refinement of design systems through collaboration between users and the design agent.

## Directory Structure

```
feedback/design-feedback/
├── README.md                           # This file
├── TEMPLATE.yaml                       # Feedback template
└── YYYY-MM-DD-<project>-<component>-feedback.yaml  # Feedback files
```

## Quick Start

### For Users Submitting Feedback

1. **Copy the template**:
   ```bash
   cp feedback/design-feedback/TEMPLATE.yaml \
      feedback/design-feedback/2026-01-17-my-project-button-feedback.yaml
   ```

2. **Fill in your feedback**: Edit the file with your observations and requests

3. **Submit**: Create PR or share with design agent

### For Design Agent Processing Feedback

1. **Check for new feedback**:
   ```bash
   ls -lt feedback/design-feedback/*.yaml | grep -v TEMPLATE
   ```

2. **Review and process**: Read user comments, analyze requests

3. **Propose updates**: Generate design system updates based on feedback

4. **Iterate**: Update feedback file with agent response and new iteration number

## Feedback Categories

Design feedback is organized by type:

- **philosophy**: Feedback on overall design direction and aesthetic
- **refinement**: Requests to adjust existing components
- **token_adjustment**: Changes to design tokens (colors, typography, spacing)
- **component_addition**: Requests for new components
- **accessibility**: Accessibility concerns or improvements
- **comparison**: Feedback from comparing multiple design philosophies
- **usability**: Usability issues discovered during testing

## Interactive Workflow Scenarios

### Scenario 1: Initial Design Direction

1. User provides high-level requirements
2. Agent proposes 3 design philosophy options with visual examples
3. User provides feedback selecting direction or requesting changes
4. Agent refines based on feedback
5. Process repeats until direction is confirmed

### Scenario 2: Component Refinement

1. Agent creates initial component set
2. User tests components in playground
3. User provides feedback via this system
4. Agent iterates on specific components
5. Updated components deployed to playground
6. Process repeats per component

### Scenario 3: Token Adjustment

1. User requests color/typography changes
2. Agent shows impact across all components
3. User approves or requests further changes via feedback
4. Agent updates tokens and regenerates components

## Feedback Structure

Each feedback file contains:

- **Metadata**: Project, component, timestamp, iteration number
- **User comment**: Natural language feedback
- **Current state**: What exists now (tokens, components)
- **Requested change**: What the user wants to see
- **Agent response**: How the agent addressed the feedback
- **Status**: new, in_progress, implemented, declined

## Best Practices

### For Users

- **Be specific**: Instead of "make it better", say "increase padding by 8px"
- **Explain why**: Help the agent understand your goals
- **Provide context**: Include use cases or scenarios
- **Attach visuals**: Screenshots or sketches when helpful
- **One topic per file**: Keep feedback focused

### For Design Agent

- **Acknowledge feedback**: Always respond to user comments
- **Explain changes**: Document what was changed and why
- **Show impact**: Describe how changes affect other components
- **Request clarification**: Ask questions if feedback is unclear
- **Track iterations**: Increment iteration number with each update

## Integration with Playground

This feedback system integrates with the interactive playground:

- **Annotation system**: Click-to-comment on components creates feedback files
- **Token editor**: Slider adjustments generate token feedback
- **Comparison mode**: Side-by-side views allow preference voting
- **Export**: Playground can export feedback summaries

## Success Metrics

- **Response time**: Feedback addressed within 24 hours
- **Iteration count**: Average 2-3 iterations to reach approval
- **User satisfaction**: 80%+ of feedback results in positive outcome
- **Clarity**: Agent understands feedback without clarification >90% of time

## Examples

Example feedback files in this directory demonstrate:
- How to write clear, actionable feedback
- Different feedback types (refinement, tokens, philosophy)
- Effective iteration and collaboration patterns
- Resolution of design disagreements

## Philosophy

Design is collaborative. This feedback system enables:

- **Transparency**: All feedback and responses are documented
- **Iteration**: Design improves through multiple rounds
- **Learning**: Both user and agent learn from each iteration
- **History**: Complete record of design decisions and rationale

The feedback loop closes when the user confirms the design meets their needs, documented in the final `status: "approved"` field.

## Related Documentation

- `specs/kerrigan/080-agent-feedback.md` - Overall feedback system
- `feedback/README.md` - General feedback overview
- `.github/agents/role.design.md` - Design agent prompt (when created)
- `playbooks/design-iteration.md` - Design iteration workflow (when created)
