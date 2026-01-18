# Spec: Design Agent

## Goal

Define a specialized agent role that creates modular, replaceable design systems with coherent visual philosophies, comprehensive component libraries, and interactive playgrounds for testing and demonstration.

## Scope

- Creating complete design systems under `design-system/` directory
- Defining design philosophies that embody distinct visual approaches
- Specifying design tokens (colors, typography, spacing, shadows, etc.)
- Creating comprehensive component library specifications
- Building interactive playgrounds for system testing and demonstration
- Writing integration guides for different frameworks (React, Vue, vanilla JS)
- Documenting accessibility standards and WCAG compliance
- Collaborating with Spec Agent on user experience requirements
- Supporting both autonomous and interactive design workflows
- Enabling easy design system replacement and swapping

## Non-goals

- Implementing production-ready components in specific frameworks (SWE Agent's responsibility)
- Writing business logic or application code (SWE Agent's responsibility)
- Creating detailed implementation roadmaps (Architect Agent's responsibility)
- Conducting user research or usability testing (outside agent scope)
- Designing marketing materials or brand assets (outside project scope)
- Creating pixel-perfect mockups in design tools (focus is on system specifications)

## Users & scenarios

### Primary Users
- **Architect Agent**: References design system in architecture.md to specify UI approach
- **SWE Agent**: Implements components following design system specifications
- **Spec Agent**: Collaborates on user experience requirements and accessibility criteria
- **Project Teams**: Use design systems to maintain consistent visual language
- **End Users**: Benefit from accessible, well-designed interfaces

### Key Scenarios
1. **New UI Project**: Project needs visual design → Design Agent creates complete design system
2. **Design System Selection**: Multiple options needed → Design Agent presents 2-3 philosophies with examples
3. **Component Addition**: New UI pattern needed → Design Agent extends component library
4. **System Replacement**: Design needs refresh → Design Agent creates new system, project swaps via architecture.md
5. **Accessibility Review**: Project needs WCAG compliance → Design Agent specifies accessible patterns
6. **Framework Integration**: React project needs components → Design Agent provides framework-specific integration guide

## Constraints

- Must follow design-system/ artifact contract structure
- Must create framework-agnostic design tokens (YAML/JSON format)
- Must build playgrounds that work standalone (no complex build requirements)
- Must meet WCAG 2.1 AA accessibility standards minimum
- Must enable system versioning and replacement
- Should keep design systems modular and self-contained
- Should collaborate with Spec Agent on user requirements
- Should document design decisions and rationale

## Acceptance criteria

- All design systems include required artifacts: philosophy.md, tokens.yaml, components.md, playground/, integration.md, a11y-checklist.md
- Design tokens are comprehensive and framework-agnostic
- Playgrounds demonstrate all components interactively
- Playgrounds work as standalone HTML files (no build step required)
- Component specifications include all states (default, hover, active, disabled, error)
- Accessibility checklist targets WCAG 2.1 AA or higher
- Integration guides cover at least vanilla JS + one framework
- Design philosophies clearly articulate target audience and use cases
- Systems can be swapped via architecture.md configuration changes
- Design tokens follow consistent naming conventions
- All color combinations meet contrast ratio requirements (4.5:1 for text)

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Design systems too framework-specific, not replaceable | High | Enforce framework-agnostic tokens; require YAML/JSON format; playground must be vanilla HTML |
| Playgrounds require complex build systems, hard to test | Medium | Mandate standalone HTML files; no build dependencies; inline CSS/JS acceptable |
| Missing accessibility considerations, excluding users | High | Require a11y-checklist.md; specify WCAG targets; include keyboard navigation in playground |
| Design tokens inconsistent, hard to customize | Medium | Enforce token naming conventions; document customization in integration.md |
| Components under-specified, implementation varies | Medium | Require state specifications; include interaction patterns; provide visual examples in playground |
| Design philosophy unclear, system lacks coherence | Medium | Require philosophy.md with rationale; examples of 3+ distinct philosophies in role prompt |

## Success metrics

- 100% of UI projects have design-system/ directory with all required artifacts
- Design systems can be swapped with minimal configuration changes in architecture.md (< 10 lines)
- Playgrounds demonstrate all components without requiring npm/build tools
- All design systems meet WCAG 2.1 AA color contrast requirements (verified in playground)
- SWE Agents report design specifications are sufficient for implementation (qualitative feedback)
- Integration guides enable component implementation in <1 hour (measured in acceptance tests)
