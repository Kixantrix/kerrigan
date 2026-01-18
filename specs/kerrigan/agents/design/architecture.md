# Architecture: Design Agent

## Overview

The Design Agent follows a **design-system-first** approach, creating complete, modular design systems rather than individual screens or components. The architecture emphasizes replaceability, accessibility, and framework-agnostic specifications.

**Core Principles:**
1. **Systems over screens**: Create coherent design systems, not isolated components
2. **Tokens first**: Define design tokens before component specifications
3. **Modularity**: Systems are self-contained and swappable
4. **Accessibility by default**: WCAG compliance built in from the start
5. **Framework agnostic**: Tokens and specs work with any framework
6. **Interactive validation**: Playgrounds prove the system works

## Components & interfaces

### 1. Design Philosophy Layer
**Responsibility**: Articulate visual direction and design rationale

**Inputs:**
- Project spec.md (target audience, use cases, constraints)
- User preferences (if interactive mode)
- Design system requirements from Spec Agent

**Outputs:**
- philosophy.md (design principles, target audience, rationale)

**Key decisions:**
- Which design philosophy to adopt (Minimal Brutalist, Warm Humanist, Technical Precision, etc.)
- How philosophy aligns with target audience and use cases
- Why this philosophy fits project goals

### 2. Design Token Layer
**Responsibility**: Define atomic design values

**Inputs:**
- Design philosophy decisions
- Accessibility requirements (contrast ratios, font sizes)
- Brand guidelines (if provided in spec.md)

**Outputs:**
- tokens.yaml (colors, typography, spacing, shadows, borders, animations)

**Key decisions:**
- Color palette selection (semantic naming, sufficient contrast)
- Typography scale (hierarchy, readability)
- Spacing scale (consistency, flexibility)
- Shadow and border styles (aligned with philosophy)

**Token categories:**
```yaml
colors:
  # Semantic colors (primary, secondary, success, warning, error)
  # Neutral palette (backgrounds, borders, text)
  # State colors (hover, active, disabled)

typography:
  # Font families (display, body, monospace)
  # Font sizes (scale with clear hierarchy)
  # Font weights (light, regular, medium, bold)
  # Line heights (comfortable reading)

spacing:
  # Scale (e.g., 0, 4, 8, 16, 24, 32, 48, 64)
  # Consistent progression

shadows:
  # Elevation levels (if applicable)
  # Glow effects (if applicable)

borders:
  # Radius values (sharp, rounded, pill)
  # Width values (hairline, default, thick)

animations:
  # Duration values (fast, normal, slow)
  # Easing functions
```

### 3. Component Specification Layer
**Responsibility**: Define UI component library

**Inputs:**
- Design tokens from tokens.yaml
- Common UI patterns needed for project type
- Accessibility requirements from a11y-checklist.md

**Outputs:**
- components.md (component specs with states and behaviors)

**Component categories:**
1. **Base components**: Buttons, links, inputs, textareas, selects, checkboxes, radio buttons
2. **Layout primitives**: Containers, grids, flexbox utilities, spacers
3. **Navigation**: Menus, tabs, breadcrumbs, pagination
4. **Feedback**: Alerts, toasts, modals, tooltips
5. **Data display**: Tables, lists, cards, badges
6. **Forms**: Field groups, labels, validation messages, form layouts

**State specifications for interactive components:**
- Default (initial appearance)
- Hover (pointer over element)
- Active (being clicked/pressed)
- Focus (keyboard navigation)
- Disabled (non-interactive state)
- Error (validation failure)
- Loading (async operation in progress)

### 4. Playground Layer
**Responsibility**: Interactive demonstration and validation

**Inputs:**
- Design tokens (tokens.yaml)
- Component specifications (components.md)
- Accessibility patterns (a11y-checklist.md)

**Outputs:**
- playground/index.html (complete interactive demo)
- playground/styles.css (design token implementation)
- playground/components.js (interactive behaviors)

**Playground architecture:**
```
index.html
├── Header (system name, version, navigation)
├── Token Examples
│   ├── Color palette with contrast ratios
│   ├── Typography scale
│   └── Spacing scale
├── Component Demonstrations
│   ├── Buttons (all states, all variants)
│   ├── Forms (inputs, validation, accessibility)
│   ├── Navigation (tabs, menus, breadcrumbs)
│   ├── Feedback (alerts, modals, toasts)
│   └── Layouts (grids, flex, containers)
└── Accessibility Features
    ├── Keyboard navigation demo
    ├── Screen reader landmarks
    └── Focus management examples
```

**Playground requirements:**
- Standalone HTML file (no external dependencies)
- Inline or embedded CSS/JS acceptable
- All components interactive (not static screenshots)
- Responsive design demonstrations
- Accessibility features highlighted

### 5. Integration Layer
**Responsibility**: Guide implementation in projects

**Inputs:**
- Design tokens (tokens.yaml)
- Component specifications (components.md)
- Common framework patterns (React, Vue, Svelte, vanilla JS)

**Outputs:**
- integration.md (setup guides, code examples, customization)

**Integration patterns:**

**Vanilla JavaScript:**
```html
<link rel="stylesheet" href="design-system/styles.css">
<button class="btn btn-primary">Click me</button>
```

**React:**
```jsx
// With build-time YAML to JSON conversion
import tokens from './design-system/tokens.json';
const Button = ({ children }) => (
  <button style={{ backgroundColor: tokens.colors.primary }}>
    {children}
  </button>
);
// Or use js-yaml library: import yaml from 'js-yaml';
```

**CSS Variables:**
```css
:root {
  --color-primary: #0066CC;
  --font-body: 'Inter', sans-serif;
  --spacing-md: 16px;
}
```

### 6. Accessibility Layer
**Responsibility**: Ensure inclusive design

**Inputs:**
- WCAG 2.1 guidelines
- Design tokens (for contrast checking)
- Component specifications (for interaction patterns)

**Outputs:**
- a11y-checklist.md (compliance requirements, verification steps)

**Accessibility checks:**
- Color contrast ratios (text 4.5:1, UI elements 3:1)
- Keyboard navigation patterns
- Screen reader compatibility
- Focus indicator visibility
- Touch target sizes (44x44px minimum)
- Motion and animation considerations

## Tradeoffs

### Tradeoff 1: Standalone playgrounds vs. framework demos
**Decision**: Use standalone HTML playgrounds

**Rationale:**
- Pro: No build dependencies, works immediately in any browser
- Pro: Framework-agnostic, demonstrates design system without bias
- Pro: Easy to test and validate across environments
- Con: Can't demonstrate framework-specific patterns (React hooks, Vue reactivity)
- Con: May not look identical to production implementation

**Mitigation**: Include framework-specific examples in integration.md with code snippets

### Tradeoff 2: Design tokens in YAML vs. CSS variables
**Decision**: Use YAML for source of truth, generate CSS variables

**Rationale:**
- Pro: YAML is framework-agnostic and parseable by any language
- Pro: Can generate CSS, SCSS, JS objects, etc. from YAML
- Pro: Clear hierarchical structure for token organization
- Con: Requires parsing step to use in web projects
- Con: Not natively supported in browsers

**Mitigation**: Provide specific conversion examples in integration.md:
- CSS variables generation script
- JSON export for JavaScript consumption
- Framework-specific token import patterns (React useState, Vue ref, etc.)
- Build-time vs runtime token parsing strategies

### Tradeoff 3: Comprehensive component library vs. minimal set
**Decision**: Provide comprehensive library (20-30 components)

**Rationale:**
- Pro: Covers 80%+ of typical UI needs out of the box
- Pro: Reduces need for custom components in projects
- Pro: Demonstrates system coherence across many patterns
- Con: More work to create and maintain
- Con: Some components may go unused in specific projects

**Mitigation**: Organize components.md by category, mark optional components

### Tradeoff 4: Multiple design philosophies vs. one standard
**Decision**: Support multiple distinct philosophies (3+ examples in prompt)

**Rationale:**
- Pro: Different projects have different audiences and needs
- Pro: Demonstrates modularity and replaceability
- Pro: Provides clear options for design direction
- Con: More complex to document and maintain
- Con: Risk of philosophy confusion or mixing

**Mitigation**: Clearly distinguish philosophies in examples; projects choose one

## Security & privacy notes

### Design System Security Considerations

1. **XSS Prevention in Playgrounds**
   - Sanitize any user input in interactive playground demos
   - Use textContent instead of innerHTML for dynamic content
   - Validate form inputs to prevent injection attacks

2. **Dependency Management**
   - Avoid external dependencies in playgrounds (inline all assets)
   - If CDN links required, use SRI (Subresource Integrity) hashes
   - Document any external resources in integration.md

3. **Accessibility as Security**
   - Proper focus management prevents keyboard traps
   - Clear error messages avoid user confusion
   - Sufficient contrast aids users with visual impairments

4. **Privacy in Examples**
   - Use fictional data in playground examples
   - No real user data, emails, or PII in demos
   - Document privacy considerations in integration.md if relevant

### No Sensitive Data in Design Systems

Design systems should not contain:
- API keys or credentials
- Real user data or PII
- Internal URLs or infrastructure details
- Proprietary design assets (use open-source fonts and resources)

## Workflow

### Autonomous Mode Workflow
1. Read project spec.md for requirements and target audience
2. Select appropriate design philosophy based on use cases
3. Create philosophy.md with rationale
4. Define comprehensive design tokens in tokens.yaml
5. Specify component library in components.md
6. Build interactive playground demonstrating system
7. Write integration guide with framework examples
8. Document accessibility requirements and compliance
9. Validate system completeness against quality bar
10. Update architecture.md to reference design system

### Interactive Mode Workflow
1. Review spec.md and identify design requirements
2. Present 2-3 design philosophy options with visual examples
3. Gather user feedback on direction and preferences
4. Refine design tokens based on feedback
5. Create initial playground for validation
6. Iterate on components based on user testing
7. Adjust accessibility features based on requirements
8. Finalize integration guide and documentation
9. Deliver complete design system with user sign-off

### Collaboration Points with Other Agents

**With Spec Agent:**
- Review spec.md for user requirements, target audience, constraints
- Align design philosophy with project goals
- Ensure accessibility requirements are captured
- Validate that design system supports acceptance criteria

**With Architect Agent:**
- Provide design system reference for architecture.md
- Coordinate on component structure and organization
- Align on framework choices and integration patterns
- Discuss performance implications of design decisions

**With SWE Agent:**
- Provide clear component specifications for implementation
- Answer questions about design intent and behavior
- Review implemented components against specifications
- Assist with framework-specific integration challenges

## Tool Usage

**Design Token Management:**
- YAML for token source of truth
- CSS variables for web implementation
- JSON export for JavaScript consumption

**Playground Development:**
- Semantic HTML5 for structure
- CSS (vanilla or custom properties) for styling
- Vanilla JavaScript for interactivity (no frameworks)

**Accessibility Validation:**
- WebAIM Contrast Checker for color validation
- Keyboard testing for navigation patterns
- Screen reader testing (NVDA, VoiceOver, or JAWS)

**Version Control:**
- Semantic versioning (major.minor.patch)
- Document breaking changes in version updates
- Maintain changelog for design system evolution

## Success Metrics

- Time to create complete design system: < 2 hours (autonomous mode)
- Time to swap design systems in project: < 5 minutes (architecture.md change)
- Playground load time: < 3 seconds on 3G connection
- Accessibility compliance: 100% of components meet WCAG 2.1 AA
- Integration time: SWE Agent implements components in < 1 hour per component
- System adoption: 80%+ of UI projects use design systems
