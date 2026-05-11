# Acceptance Tests: Design Agent

This document defines test scenarios to validate Design Agent behavior and output quality.

## Test Scenario 1: Create Minimal Brutalist Design System

**Given** a project for a developer documentation site
**And** the spec.md specifies "target audience: software engineers, focus: technical clarity"
**When** Design Agent creates a design system autonomously
**Then** philosophy.md articulates Minimal Brutalist approach with high contrast and system fonts
**And** tokens.yaml includes black/white color palette with minimal accent colors
**And** components.md specifies grid-based layouts without decorative elements
**And** playground/index.html demonstrates all components with stark typography
**And** all text has 4.5:1 or higher contrast ratio
**And** playground opens in browser without build step

## Test Scenario 2: Create Warm Humanist Design System

**Given** a project for a community forum application
**And** the spec.md specifies "target audience: general public, focus: welcoming and friendly"
**When** Design Agent creates a design system autonomously
**Then** philosophy.md articulates Warm Humanist approach with rounded corners and soft colors
**And** tokens.yaml includes earth tones or pastel color palette
**And** tokens.yaml includes border radius values (8px+)
**And** components.md specifies friendly form elements with validation
**And** playground/index.html demonstrates all components with approachable aesthetics
**And** all interactive elements have visible hover and focus states

## Test Scenario 3: Create Technical Precision Design System

**Given** a project for an analytics dashboard
**And** the spec.md specifies "target audience: data analysts, focus: information density"
**When** Design Agent creates a design system autonomously
**Then** philosophy.md articulates Technical Precision approach with dark theme
**And** tokens.yaml includes dark background colors (below #202020)
**And** tokens.yaml includes monospace font family for headers or data
**And** components.md includes table-heavy layout patterns
**And** playground/index.html demonstrates data visualization styles
**And** color palette includes semantic colors for success/warning/error states

## Test Scenario 4: Interactive Design System Selection

**Given** a project with unclear design direction
**And** the spec.md has general requirements
**When** Design Agent operates in interactive mode
**Then** Design Agent presents 2-3 design philosophy options
**And** each option includes visual examples in playground format
**And** each option explains target audience and use cases
**And** user can provide feedback on preferred direction
**And** Design Agent refines selected option based on feedback
**And** final system aligns with user preferences

## Test Scenario 5: Complete Design System Artifacts

**Given** any project requiring a design system
**When** Design Agent completes its work
**Then** design-system/ directory exists under specs/projects/<project-name>/
**And** philosophy.md exists and includes design principles, target audience, rationale
**And** tokens.yaml exists and includes colors, typography, spacing, shadows, borders
**And** components.md exists and includes base components, layouts, navigation, forms
**And** playground/index.html exists and opens in browser without errors
**And** playground/styles.css exists and implements design tokens
**And** playground/components.js exists with interactive demonstrations
**And** integration.md exists with setup instructions for 2+ frameworks
**And** a11y-checklist.md exists with WCAG compliance targets
**And** all files are well-formatted and complete

## Test Scenario 6: Framework-Agnostic Tokens

**Given** a design system has been created
**When** examining tokens.yaml
**Then** tokens use semantic names (primary-color, not blue-500)
**And** tokens contain pure values (hex colors, px/rem sizes, font names)
**And** tokens do not contain CSS-specific syntax (no var() or calc())
**And** tokens do not contain React/Vue/Svelte-specific code
**And** tokens can be parsed by any YAML parser
**And** integration.md shows how to use tokens in vanilla JS, React, and CSS variables

## Test Scenario 7: Interactive Playground Validation

**Given** a design system with playground
**When** opening playground/index.html in a browser
**Then** page loads without errors
**And** all components are visible and rendered
**And** buttons are clickable and show state changes
**And** form inputs accept text and validate on submission
**And** navigation tabs/menus switch between sections
**And** keyboard Tab key moves focus through interactive elements
**And** focus indicators are visible (3:1 contrast with background)
**And** no external dependencies fail to load (all assets inline or local)

## Test Scenario 8: Accessibility Compliance

**Given** a design system with accessibility checklist
**When** reviewing a11y-checklist.md
**Then** WCAG compliance target is specified (AA or AAA)
**And** color contrast requirements are documented with ratios
**And** keyboard navigation patterns are specified
**And** screen reader considerations are documented
**And** focus management guidelines are provided
**And** ARIA attributes and roles are specified for interactive components
**And** touch target sizes are specified (minimum 44x44px)

**When** testing playground/index.html
**Then** all text has 4.5:1 contrast ratio with background
**And** all UI elements have 3:1 contrast ratio with adjacent colors
**And** focus indicators have 3:1 contrast ratio with background
**And** all interactive elements are reachable via keyboard
**And** Tab order is logical and predictable

## Test Scenario 9: Design System Versioning and Replacement

**Given** a project using design-system-v1 (Minimal Brutalist)
**And** architecture.md specifies:
```yaml
design:
  system: minimal-brutalist
  version: 1.0.0
```

**When** Design Agent creates design-system-v2 (Warm Humanist)
**And** architecture.md is updated to:
```yaml
design:
  system: warm-humanist
  version: 1.0.0
```

**Then** new design system is self-contained in its own directory
**And** SWE Agent can regenerate UI components using new tokens
**And** no changes to business logic are required
**And** playground demonstrates new system independently
**And** integration.md explains migration process

## Test Scenario 10: Collaboration with Spec Agent

**Given** Spec Agent has created spec.md with user requirements
**And** spec.md includes "target audience: elderly users, focus: accessibility"
**And** spec.md includes "acceptance criteria: WCAG 2.1 AAA compliance"

**When** Design Agent creates design system
**Then** philosophy.md references spec.md requirements
**And** tokens.yaml includes larger font sizes (16px+ for body text)
**And** tokens.yaml ensures high contrast colors (7:1 for text)
**And** a11y-checklist.md targets WCAG 2.1 AAA
**And** components.md includes larger touch targets (48x48px minimum)
**And** playground demonstrates accessibility features prominently

## Test Scenario 11: Component State Specifications

**Given** a design system with component specifications
**When** reviewing components.md for a button component
**Then** default state is specified (background, text, border)
**And** hover state is specified (changes on pointer over)
**And** active state is specified (changes on click/press)
**And** focus state is specified (keyboard navigation indicator)
**And** disabled state is specified (non-interactive appearance)
**And** loading state is specified (if applicable)

**When** reviewing playground/index.html
**Then** all button states are demonstrated
**And** hovering over button shows hover state
**And** clicking button shows active state
**And** tabbing to button shows focus state
**And** disabled button cannot be interacted with

## Test Scenario 12: Integration Guide Completeness

**Given** a design system with integration guide
**When** reviewing integration.md
**Then** quick start section provides setup in < 5 steps
**And** vanilla JavaScript integration example is complete and runnable
**And** at least one framework integration example exists (React, Vue, or Svelte)
**And** customization section explains how to override tokens
**And** theming instructions are provided (if applicable)
**And** code examples are complete (no placeholders like "TODO" or "...")

**When** SWE Agent follows integration.md
**Then** design system can be integrated in < 1 hour
**And** implemented components match playground appearance
**And** no undocumented steps are required

## Test Scenario 13: Token Consistency and Hierarchy

**Given** a design system with tokens.yaml
**When** reviewing color tokens
**Then** semantic colors are defined (primary, secondary, success, warning, error)
**And** neutral palette is defined (backgrounds, borders, text shades)
**And** color naming is consistent (primary-color, primary-hover, primary-active)

**When** reviewing typography tokens
**Then** font scale has clear hierarchy (6-8 sizes)
**And** font sizes progress logically (e.g., 14, 16, 20, 24, 32, 48)
**And** line heights are specified for each size
**And** font families are specified (display, body, monospace)

**When** reviewing spacing tokens
**Then** spacing scale follows consistent progression (e.g., 4, 8, 16, 24, 32, 48, 64)
**And** scale is sufficient for common layout needs (6-8 values)

## Test Scenario 14: Playground Performance

**Given** a design system playground
**When** opening playground/index.html on 3G connection
**Then** page loads in < 5 seconds
**And** all components are visible (no missing images or fonts)
**And** interactive elements respond immediately (< 100ms)
**And** page file size is < 500KB (including inline assets)

**When** viewing playground on mobile device (375px width)
**Then** page is responsive and usable
**And** touch targets are at least 44x44px
**And** text is readable without zooming
**And** horizontal scrolling is not required

## Test Scenario 15: Documentation Clarity

**Given** a complete design system
**When** a developer unfamiliar with the system reviews documentation
**Then** philosophy.md clearly explains design direction in < 500 words
**And** tokens.yaml is organized by category with clear naming
**And** components.md includes visual examples or playground references
**And** integration.md provides step-by-step instructions
**And** a11y-checklist.md is actionable with specific requirements

**When** asking "How do I use this design system?"
**Then** answer is found in integration.md within 2 minutes
**When** asking "What colors are available?"
**Then** answer is found in tokens.yaml within 1 minute
**When** asking "How do I make buttons accessible?"
**Then** answer is found in a11y-checklist.md within 2 minutes

## Test Scenario 16: Design System Modularity

**Given** a design system created for project A
**When** copying design-system/ directory to project B
**Then** all artifacts are self-contained (no external dependencies)
**And** playground works without modifications
**And** tokens can be imported into project B
**And** integration guide applies to project B
**And** no project A-specific references exist in design system

## Edge Cases and Failure Modes

### Edge Case 1: Missing Spec Requirements
**Given** spec.md does not specify target audience
**When** Design Agent creates design system
**Then** Design Agent makes reasonable assumption based on project type
**And** philosophy.md documents assumption and rationale
**Or** Design Agent requests clarification in interactive mode

### Edge Case 2: Conflicting Design Requirements
**Given** spec.md specifies "high information density" and "large touch targets"
**When** Design Agent creates design system
**Then** Design Agent documents tradeoff in philosophy.md
**And** balances requirements (e.g., compact layout with adequate spacing)
**Or** Design Agent requests clarification on priority

### Edge Case 3: Extremely Limited Color Palette
**Given** project requires black and white only (no color)
**When** Design Agent creates design system
**Then** tokens.yaml defines grayscale palette
**And** components.md uses patterns, borders, and typography for differentiation
**And** accessibility checklist ensures sufficient contrast (21:1 for black on white)

### Edge Case 4: Accessibility Conflicts with Brand Guidelines
**Given** brand colors fail contrast requirements
**When** Design Agent creates design system
**Then** Design Agent documents conflict in philosophy.md
**And** suggests adjusted colors meeting contrast ratios
**And** includes original brand colors as reference
**Or** Design Agent requests clarification on priority (brand vs. accessibility)

### Failure Mode: Playground Doesn't Load
**Given** playground/index.html has syntax errors
**When** opening in browser
**Then** browser console shows clear error messages
**And** Design Agent validates HTML/CSS/JS before submission
**Mitigation**: Test playground in multiple browsers during creation

### Failure Mode: Framework-Specific Tokens
**Given** tokens.yaml includes React component names
**When** integrating with Vue project
**Then** integration fails with unclear errors
**Mitigation**: Validate tokens are pure values (no framework syntax)

### Failure Mode: Missing Component States
**Given** components.md omits disabled state for buttons
**When** SWE Agent implements buttons
**Then** disabled buttons may be interactive or poorly styled
**Mitigation**: Quality bar checklist ensures all states specified
