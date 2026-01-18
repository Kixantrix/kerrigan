# Quality Bar: Design Agent

This document defines the quality standards that Design Agent output must meet.

## Definition of Done

A design system is complete when:

1. ✅ All required artifacts exist in `design-system/` directory
2. ✅ Design philosophy clearly articulates target audience and visual principles
3. ✅ Design tokens are comprehensive (colors, typography, spacing, shadows, borders)
4. ✅ Component library covers common UI patterns (buttons, forms, layouts, navigation)
5. ✅ Playground demonstrates all components interactively
6. ✅ Playground works as standalone HTML (no build required)
7. ✅ Accessibility checklist specifies WCAG compliance targets
8. ✅ Integration guide covers setup for multiple frameworks
9. ✅ All color combinations meet contrast requirements
10. ✅ System is versioned and can be swapped via architecture.md

## Design Philosophy Standards

**philosophy.md must include:**
- [ ] Clear statement of design principles (3-5 core principles)
- [ ] Target audience and use cases
- [ ] Visual tone and personality description
- [ ] Rationale for design decisions
- [ ] Accessibility philosophy and commitments
- [ ] Examples of when to use (and not use) this system

**Quality indicators:**
- ✅ Philosophy is coherent and internally consistent
- ✅ Target audience is specific, not generic ("developers" vs. "everyone")
- ✅ Design decisions are justified, not arbitrary
- ✅ Philosophy differentiates from other design approaches

## Design Token Standards

**tokens.yaml must include:**
- [ ] Color palette (primary, secondary, semantic colors)
- [ ] Typography scale (families, sizes, weights, line heights)
- [ ] Spacing scale (consistent progression)
- [ ] Shadow definitions (if applicable to philosophy)
- [ ] Border radius values (if applicable)
- [ ] Animation timings (if applicable)

**Quality indicators:**
- ✅ Tokens use semantic naming (primary-color, not blue-500)
- ✅ Spacing follows consistent scale (e.g., 4px base, powers of 2)
- ✅ Typography scale has clear hierarchy (6-8 sizes)
- ✅ Color palette includes semantic variants (success, warning, error)
- ✅ All colors have sufficient contrast against backgrounds
- ✅ Tokens are framework-agnostic (no CSS-specific syntax)

## Component Specification Standards

**components.md must include:**
- [ ] All common UI patterns (buttons, inputs, selects, checkboxes, radio buttons)
- [ ] Layout primitives (containers, grids, flex layouts)
- [ ] Navigation components (menus, tabs, breadcrumbs)
- [ ] State specifications (default, hover, active, disabled, error, loading)
- [ ] Responsive behavior descriptions
- [ ] Composition patterns (how components combine)

**Quality indicators:**
- ✅ Components cover 80%+ of typical UI needs
- ✅ All interactive components specify all states
- ✅ Responsive breakpoints are defined
- ✅ Components are composable (can be combined)
- ✅ Specifications are implementation-agnostic

## Playground Standards

**playground/ must include:**
- [ ] Working index.html demonstrating all components
- [ ] Complete styles.css implementing design tokens
- [ ] Interactive demonstrations (clickable buttons, editable inputs)
- [ ] All component states visible (hover, active, disabled, etc.)
- [ ] Responsive behavior demonstrations
- [ ] Keyboard navigation support
- [ ] Visual accessibility indicators (focus rings, contrast)

**Quality indicators:**
- ✅ Playground opens in browser without build step
- ✅ All components are demonstrated, not just listed
- ✅ Interactive elements actually work (forms validate, buttons respond)
- ✅ Code examples are provided for each component
- ✅ Playground is well-organized and easy to navigate
- ✅ Visual regression test markers are included

**Playground file size limits:**
- index.html: < 1000 lines (split into sections if needed)
- styles.css: < 2000 lines (use CSS variables for tokens)
- components.js: < 1000 lines (vanilla JS, no framework dependencies)

## Integration Guide Standards

**integration.md must include:**
- [ ] Quick start instructions (< 5 steps)
- [ ] Vanilla JavaScript integration example
- [ ] At least one framework integration example (React, Vue, or Svelte)
- [ ] Customization guide (overriding tokens)
- [ ] Theming instructions (if applicable)
- [ ] Migration guide for system updates

**Quality indicators:**
- ✅ Setup instructions are clear and tested
- ✅ Code examples are complete and runnable
- ✅ Customization options are documented
- ✅ Framework-specific patterns are explained
- ✅ Common pitfalls are addressed

## Accessibility Standards

**a11y-checklist.md must include:**
- [ ] WCAG compliance target (AA or AAA)
- [ ] Color contrast requirements with ratios
- [ ] Keyboard navigation patterns
- [ ] Screen reader considerations
- [ ] Focus management guidelines
- [ ] ARIA attributes and roles
- [ ] Touch target sizes (minimum 44x44px)

**Quality indicators:**
- ✅ All text has 4.5:1 contrast ratio (AA standard)
- ✅ UI elements have 3:1 contrast ratio
- ✅ Keyboard navigation is fully specified
- ✅ Focus indicators are visible (3:1 contrast)
- ✅ ARIA patterns follow W3C recommendations
- ✅ Checklist is verifiable (not subjective)

## Modularity & Replaceability Standards

**Design systems must be:**
- [ ] Self-contained (all assets in design-system/ directory)
- [ ] Framework-agnostic (no React/Vue/Svelte-specific code in tokens)
- [ ] Versioned (semantic versioning specified)
- [ ] Documented for swapping (architecture.md example provided)
- [ ] Tested independently (playground doesn't require project context)

**Quality indicators:**
- ✅ System can be copied to another project without modifications
- ✅ Changing design system in architecture.md requires < 10 line changes
- ✅ Playground works without external dependencies
- ✅ Design tokens can be imported into any framework
- ✅ Version number follows semver (1.0.0)

## Collaboration Standards

**Design Agent should:**
- [ ] Reference spec.md for user requirements and target audience
- [ ] Align design philosophy with project goals
- [ ] Document design decisions that affect implementation
- [ ] Provide clear specifications for SWE Agent to implement
- [ ] Include visual examples for ambiguous patterns

**Quality indicators:**
- ✅ Design philosophy references spec.md requirements
- ✅ Component specifications are unambiguous
- ✅ Design decisions are justified and documented
- ✅ Integration examples are tested and accurate

## Common Quality Issues to Avoid

❌ **Poor Philosophy**: Vague principles like "make it look good" without rationale
✅ **Good Philosophy**: "High contrast and system fonts for technical audiences who value speed over aesthetics"

❌ **Incomplete Tokens**: Only defining colors, missing typography and spacing
✅ **Complete Tokens**: Comprehensive coverage of all visual properties

❌ **Framework-Specific Tokens**: CSS classes or React component names in tokens
✅ **Agnostic Tokens**: Pure values (colors, sizes, weights) without framework assumptions

❌ **Static Playground**: Components displayed but not interactive
✅ **Interactive Playground**: Buttons click, forms validate, states change

❌ **Missing States**: Only showing default component appearance
✅ **Complete States**: Default, hover, active, disabled, error, loading

❌ **Build-Dependent Playground**: Requires npm install and build process
✅ **Standalone Playground**: Opens directly in browser

❌ **Poor Contrast**: Text at 3:1 contrast ratio
✅ **Accessible Contrast**: Text at 4.5:1 or higher

❌ **Vague Integration**: "Just use the CSS file"
✅ **Clear Integration**: Step-by-step examples with code snippets

## Validation Checklist

Before submitting design system work, verify:

- [ ] All 6 required files exist in design-system/
- [ ] philosophy.md articulates clear design principles
- [ ] tokens.yaml includes all token categories
- [ ] components.md specifies states for all interactive elements
- [ ] playground/index.html opens and works in browser
- [ ] integration.md includes at least 2 integration examples
- [ ] a11y-checklist.md specifies WCAG target and requirements
- [ ] All color combinations pass contrast checks
- [ ] Playground demonstrates keyboard navigation
- [ ] System version number is specified
- [ ] Architecture.md example shows how to reference the system

## Success Indicators

High-quality design systems demonstrate:

1. **Coherence**: All components feel like part of the same system
2. **Completeness**: Covers common UI patterns without gaps
3. **Clarity**: Specifications are unambiguous and actionable
4. **Accessibility**: Meets or exceeds WCAG 2.1 AA standards
5. **Modularity**: Can be swapped or versioned independently
6. **Usability**: Integration is straightforward with clear examples
7. **Testability**: Playground validates all components interactively

## References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Inclusive Components](https://inclusive-components.design/)
- [Design Systems Handbook](https://www.designbetter.co/design-systems-handbook)
