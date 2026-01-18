# Interactive Design System Refinement

## Overview

Kerrigan now supports interactive design system refinement through the Design Agent role. This enables collaborative iteration between human users and AI agents to create and refine design systems based on feedback, preferences, and real-world usage.

## What Is This?

The interactive design system refinement feature enables:

1. **Design Agent Role**: A specialized agent that creates design systems and collaborates with users
2. **Feedback System**: Structured YAML files for design feedback and iteration tracking
3. **Interactive Playground**: Environment for testing and annotating design components
4. **Iterative Workflow**: Multiple collaboration scenarios for refining designs

## Key Capabilities

### Autonomous Mode
The Design Agent can create complete design systems from specifications:
- Propose multiple design philosophies
- Generate design tokens (colors, typography, spacing)
- Create component specifications
- Build framework implementations
- Generate interactive playground

### Interactive Mode
The Design Agent collaborates with users to refine designs:
- Process user feedback from structured YAML files
- Iterate on specific components based on testing
- Adjust design tokens with impact analysis
- Validate accessibility throughout
- Track iteration history

## Getting Started

### For Users Creating a Design System

1. **Create an issue** with design requirements
   ```markdown
   Need design system for developer dashboard
   - Target users: Software developers
   - Aesthetic: Technical, terminal-inspired
   - Platform: Web (React)
   - Accessibility: WCAG AA minimum
   ```

2. **Add label**: `role:design`

3. **Design Agent proposes** 2-3 design philosophies
   - Reviews proposals in comparison mode
   - Provides feedback via `feedback/design-feedback/`

4. **Select direction** and iterate
   - Agent creates complete system
   - Test in playground
   - Provide component-specific feedback
   - Iterate until approved

### For Providing Feedback

1. **Copy feedback template**:
   ```bash
   cp feedback/design-feedback/TEMPLATE.yaml \
      feedback/design-feedback/2026-01-17-myproject-button.yaml
   ```

2. **Fill in feedback** with specific requests
   ```yaml
   user_comment: |
     Button padding too small - increase by 4-8px
   requested_change:
     component_properties:
       padding: "12px 20px"
   ```

3. **Commit and notify** Design Agent

4. **Agent processes** and updates feedback file with response

5. **Review and approve** changes in playground

## Workflows

### Scenario 1: Initial Design Direction
- User provides requirements → Agent proposes 3 philosophies → User selects → Agent builds system
- **Timeline**: 2-3 days
- **Iterations**: 1-2 typically

### Scenario 2: Component Refinement
- Agent creates components → User tests in playground → User provides feedback → Agent iterates → Approval
- **Timeline**: 3-7 days
- **Iterations**: 2-3 per component

### Scenario 3: Token Adjustment
- User requests token change → Agent shows impact → User approves → Agent updates
- **Timeline**: 1-2 days
- **Iterations**: 1-2 typically

See [playbooks/design-iteration.md](../playbooks/design-iteration.md) for detailed workflows.

## Interactive Playground Features

### Annotation System
- Click on any component to add feedback
- Rate components (like/dislike/neutral)
- Capture screenshots
- Export annotations to feedback YAML

### Token Editor
- Live preview of token changes
- Accessibility validation in real-time
- Before/after comparison
- Export adjusted tokens

### Comparison Mode
- View 2-3 design systems side-by-side
- Toggle between options
- Vote on preferences
- Export comparison results

See [docs/playground-infrastructure.md](playground-infrastructure.md) for technical details.

## Feedback System

### Design Feedback Directory
Location: `feedback/design-feedback/`

Structure:
```
feedback/design-feedback/
├── README.md                   # Guidelines
├── TEMPLATE.yaml              # Feedback template
└── YYYY-MM-DD-project-component-feedback.yaml
```

### Feedback Types
- **philosophy**: Overall design direction selection
- **refinement**: Component improvements
- **token_adjustment**: Design token changes
- **component_addition**: New component requests
- **accessibility**: Accessibility concerns
- **comparison**: Multi-option comparisons
- **usability**: Usability issues

### Feedback Lifecycle
1. User creates feedback (status: "new")
2. Agent processes (status: "in_progress")
3. Agent implements (status: "implemented")
4. User approves (status: "approved")

Or: Agent requests clarification (status: "needs_clarification")

## Design Agent Resources

### Agent Prompt
- **Location**: `.github/agents/role.design.md`
- **Purpose**: Complete instructions for Design Agent role
- **Usage**: Copy to AI assistant when working as Design Agent

### Agent Specification
- **Location**: `specs/kerrigan/agents/design/spec.md`
- **Purpose**: Detailed role definition and requirements
- **Contents**: Responsibilities, inputs, outputs, workflows, quality standards

### Acceptance Tests
- **Location**: `specs/kerrigan/agents/design/acceptance-tests.md`
- **Purpose**: Validation criteria for Design Agent work
- **Contents**: Test scenarios for all modes and features

## Example Project

### Task Dashboard Design System
- **Location**: `examples/task-dashboard-design/`
- **Philosophy**: Technical Precision
- **Components**: Buttons, inputs, cards (examples)
- **Iterations**: 2 documented iterations
- **Status**: Example/demonstration

This example shows:
- How design philosophies are proposed and selected
- How component refinement works (button padding/color)
- How feedback files track iterations
- Expected timelines and effort

## Quality Standards

### Accessibility
- **WCAG AA minimum** (AAA preferred)
- Contrast ratios: 4.5:1 text, 3:1 UI
- Touch targets: 44x44px minimum
- Keyboard navigation fully supported
- Screen reader compatible

### Design Tokens
- Consistent naming conventions
- Semantic vs primitive separation
- Complete documentation
- Accessibility validation

### Components
- Multiple variants (primary, secondary, etc.)
- All states (hover, active, focus, disabled)
- Multiple sizes (sm, md, lg)
- Usage guidelines with do's/don'ts
- Accessibility notes

### Documentation
- Clear and comprehensive
- Examples for all features
- Do's and don'ts
- Edge cases covered

## Integration with Workflow

### Before Design Agent
```
Spec Agent → Architect Agent → SWE Agent
```

### With Design Agent
```
Spec Agent → Design Agent (if UI needed) → Architect Agent → SWE Agent
             ↑ iterates with user ↓
```

### Handoff Points
1. **Spec → Design**: Design requirements in spec.md
2. **Design → User**: Proposals and iterations via feedback
3. **Design → SWE**: Approved design system ready for implementation

## Success Metrics

### Adoption
- Used in projects requiring UI/UX design
- Positive feedback from design collaborations
- Reduces back-and-forth during implementation

### Efficiency
- 3-7 days from start to approved design system
- 2-5 iterations per component typically
- 80%+ of feedback is actionable and specific

### Quality
- 100% WCAG AA compliance
- Zero accessibility regressions
- Clear documentation
- User approval before implementation

## Best Practices

### For Users
- ✓ Be specific in feedback ("increase padding by 8px")
- ✓ Explain reasoning ("for better touch targets")
- ✓ Test in realistic scenarios
- ✓ Respond to clarification requests promptly
- ✗ Don't give vague feedback ("make it better")
- ✗ Don't skip accessibility considerations

### For Design Agent
- ✓ Respond to all feedback within 24 hours
- ✓ Explain design decisions clearly
- ✓ Show impact analysis for token changes
- ✓ Validate accessibility for every change
- ✓ Ask questions when feedback is unclear
- ✗ Don't make changes that break accessibility
- ✗ Don't assume what user means - ask

## Common Use Cases

### 1. New Project with UI
Create complete design system from requirements

### 2. Existing Project Needing Redesign
Iterate on current design with user feedback

### 3. Component Library Creation
Build reusable component set for organization

### 4. Design System Migration
Move from one design system to another

### 5. Accessibility Improvements
Upgrade existing designs to WCAG standards

## Limitations

### What This Enables
- Structured design collaboration
- Iterative refinement with feedback tracking
- Accessibility validation
- Multiple design philosophy exploration

### What This Doesn't Replace
- Professional design tools (Figma, Sketch)
- Visual design expertise
- User research and testing
- Brand strategy development

### Future Enhancements
See [docs/playground-infrastructure.md](playground-infrastructure.md) for planned features:
- Integration with design tools
- Multi-user collaboration
- A/B testing automation
- Design system marketplace

## Related Documentation

### Core Documents
- [Design Agent Prompt](.github/agents/role.design.md)
- [Design Agent Spec](../specs/kerrigan/agents/design/spec.md)
- [Design Iteration Playbook](../playbooks/design-iteration.md)
- [Playground Infrastructure](playground-infrastructure.md)

### Feedback System
- [Design Feedback README](../feedback/design-feedback/README.md)
- [Design Feedback Template](../feedback/design-feedback/TEMPLATE.yaml)
- [Example Feedback](../feedback/design-feedback/2026-01-17-task-dashboard-button-feedback.yaml)

### Examples
- [Task Dashboard Example](../examples/task-dashboard-design/README.md)

### Testing
- [Design Agent Acceptance Tests](../specs/kerrigan/agents/design/acceptance-tests.md)

## FAQ

### Q: When should I use the Design Agent?
**A**: Use when your project needs UI/UX design, especially for web applications, design systems, or component libraries.

### Q: How long does design iteration take?
**A**: Typically 3-7 days from start to approved design system, with 2-5 iterations per component.

### Q: Can I skip the Design Agent and go straight to implementation?
**A**: Yes, if you already have designs or don't need custom UI. The Design Agent is optional.

### Q: What if I disagree with the Design Agent's proposals?
**A**: Provide specific feedback via feedback files. The agent will iterate based on your requirements. You maintain full control.

### Q: How is accessibility ensured?
**A**: The Design Agent validates WCAG compliance at every iteration. All color contrasts, touch targets, and interactive elements are checked.

### Q: Can I use existing design systems?
**A**: Yes, the Design Agent can work with existing systems, proposing improvements or migrations while respecting established patterns.

### Q: What frameworks are supported?
**A**: The Design Agent can generate implementations for CSS, Tailwind, React, Vue, and others based on project requirements.

## Getting Help

- **Questions**: Check this document and related documentation
- **Issues**: Open GitHub issue with `role:design` label
- **Feedback**: Use `feedback/agent-feedback/` for system improvements
- **Examples**: See `examples/task-dashboard-design/` for reference

---

**Ready to create a design system?** Start by creating an issue with your requirements and adding the `role:design` label!
