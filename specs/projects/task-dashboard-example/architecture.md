# Architecture: Task Dashboard Example Design System

## Overview

The Task Dashboard Example is a reference implementation demonstrating how to create and use a complete design system within the Kerrigan framework. It showcases a "Technical Precision" design philosophy optimized for developer-focused applications.

The architecture consists of three main layers:
1. **Design System Documentation**: Philosophy, tokens, component specs, accessibility guidelines
2. **Playground Implementation**: Working HTML/CSS/JS examples of all components
3. **Integration Examples**: Demonstration of how to reference and use the design system in specs

## Key Components

### 1. Design System Documentation Layer

**Purpose**: Define the design language and component specifications

**Components**:
- `philosophy.md`: Design principles, target audience, tone & voice
- `tokens.yaml`: Design tokens (colors, typography, spacing, sizing)
- `components.md`: Detailed specifications for 5 core components
- `a11y-checklist.md`: Accessibility requirements and testing guidelines
- `integration.md`: Usage guide for implementing the design system

**Interfaces**:
- Read by design agents to understand design principles
- Referenced by SWE agents during implementation
- Used by spec agents to specify visual design

### 2. Playground Implementation Layer

**Purpose**: Demonstrate working implementation of all components

**Components**:
- `playground/index.html`: Component showcase page
- `playground/components.css`: CSS implementation with design tokens
- `playground/demo-data.js`: Interactive functionality and sample data

**Interfaces**:
- Opens directly in browser (no build process)
- Provides copy-paste ready code examples
- Demonstrates component behavior and interactions

**Key Features**:
- Token visualization (colors, typography, spacing)
- 5 interactive components (DataTable, StatusBadge, MetricCard, CommandBar, TaskRow)
- Keyboard navigation support
- Responsive design (320px - 1920px)

### 3. Integration Layer

**Purpose**: Show how to reference and use the design system in project specs

**Components**:
- `spec.md`: Example spec with design system reference
- Integration patterns in `integration.md`

**Interfaces**:
- Spec agents reference design system location
- Component selection explained in spec
- Visual design characteristics documented

## Data Flows

### Design Agent → Playground Creation Flow
```
1. Design agent defines philosophy → philosophy.md
2. Design agent specifies tokens → tokens.yaml
3. Design agent documents components → components.md
4. Design agent creates accessibility checklist → a11y-checklist.md
5. Design agent writes integration guide → integration.md
```

### SWE Agent → Implementation Flow
```
1. SWE agent reads component specs → components.md
2. SWE agent references tokens → tokens.yaml
3. SWE agent creates HTML structure → index.html
4. SWE agent implements CSS with tokens → components.css
5. SWE agent adds interactivity → demo-data.js
6. SWE agent validates accessibility → a11y-checklist.md
```

### Spec Agent → Integration Flow
```
1. Spec agent identifies need for visual design
2. Spec agent references design system location in spec.md
3. Spec agent specifies which components to use
4. Spec agent documents design characteristics
```

### User → Playground Interaction Flow
```
1. User opens index.html in browser
2. Browser loads CSS and applies design tokens
3. JavaScript populates components with demo data
4. User interacts via mouse or keyboard
5. Components respond with appropriate state changes
```

## Technology Choices

### No Framework Decision
**Choice**: Vanilla HTML/CSS/JavaScript only  
**Rationale**:
- Maximum portability across projects
- No build process required
- Easy to understand and modify
- Demonstrates pure web standards
- Copy-paste ready code

**Tradeoffs**:
- More verbose than framework code
- Manual state management
- No virtual DOM optimizations
- Limited to static demo data

### CSS Custom Properties for Tokens
**Choice**: Use CSS variables for all design tokens  
**Rationale**:
- Native browser support
- Easy to theme (swap values)
- Clear relationship to tokens.yaml
- No preprocessor required

**Tradeoffs**:
- Slightly verbose syntax
- No type checking
- Limited browser support (IE11)

### Monospace Typography
**Choice**: JetBrains Mono as primary font  
**Rationale**:
- Aligns with "Technical Precision" philosophy
- Excellent for tabular data
- Clear distinction from consumer designs
- Good readability for developers

**Tradeoffs**:
- Less suitable for prose content
- Unusual for non-technical users
- Slightly lower information density vs. proportional fonts

### Dark Theme Primary
**Choice**: Dark background with light text  
**Rationale**:
- Reduces eye strain for developers
- Popular in developer tools (GitHub, VS Code)
- High contrast for data visibility
- Terminal-inspired aesthetic

**Tradeoffs**:
- Less suitable for print
- May not match corporate brand guidelines
- Accessibility concerns if not implemented carefully

## Component Architecture

### DataTable
**Structure**: CSS Grid-based layout  
**State**: Sorting direction (ascending/descending/none)  
**Interactions**: Click headers to sort, arrow keys to navigate rows  
**Accessibility**: Full ARIA table structure, keyboard navigation

### StatusBadge
**Structure**: Inline-flex with dot + text  
**State**: Static (no interactive states)  
**Variations**: 4 status types (todo, in-progress, done, blocked)  
**Accessibility**: role="status", color + text combination

### MetricCard
**Structure**: Vertical flex layout  
**State**: Static (optionally clickable)  
**Data**: Label, value, optional trend  
**Accessibility**: Semantic HTML, full context in aria-label

### CommandBar
**Structure**: Modal dialog with input + list  
**State**: Open/closed, focused command index  
**Interactions**: Keyboard shortcut to open, arrow keys to navigate, enter to execute  
**Accessibility**: role="dialog", focus trap, aria-expanded

### TaskRow
**Structure**: Horizontal flex with checkbox + content  
**State**: Selected/unselected, hover, focus  
**Interactions**: Checkbox toggle, row click  
**Accessibility**: Proper label association, keyboard navigation

## File Organization

```
specs/projects/task-dashboard-example/
├── spec.md                          # Project specification
├── acceptance-tests.md              # Acceptance criteria
├── architecture.md                  # This file
├── plan.md                          # Implementation plan
├── tasks.md                         # Task breakdown
├── test-plan.md                     # Testing strategy
└── design-system/
    ├── philosophy.md                # Design principles
    ├── tokens.yaml                  # Design tokens
    ├── components.md                # Component specs
    ├── a11y-checklist.md           # Accessibility guidelines
    ├── integration.md              # Integration guide
    └── playground/
        ├── index.html               # Component showcase
        ├── components.css           # Styles implementation
        └── demo-data.js            # Interactive functionality
```

## Security & Privacy Notes

### Security Considerations

**No user input processing**: Playground is static demo with hardcoded data
- No XSS risk from user input
- No server communication
- No data persistence

**Content Security Policy**: Inline scripts in demo-data.js
- For playground only (not production pattern)
- Could be moved to external file if needed
- No eval() or unsafe operations

### Privacy Considerations

**No data collection**: Playground runs entirely client-side
- No analytics
- No external requests
- No cookies or local storage

**Accessibility tracking**: No usage tracking
- Screen reader usage not monitored
- Interaction patterns not recorded

## Tradeoffs

### 1. Vanilla JS vs. Framework
**Decision**: Vanilla JavaScript  
**Pros**: Portability, simplicity, no dependencies  
**Cons**: More code, manual state management  
**Context**: Playground is a demo, not production app

### 2. Static Demo Data vs. API
**Decision**: Hardcoded data in JavaScript  
**Pros**: Self-contained, works offline, no backend needed  
**Cons**: Not realistic for large datasets, no real persistence  
**Context**: Focus is on design system, not application logic

### 3. Single Design System vs. Multiple Examples
**Decision**: One complete system (Technical Precision)  
**Pros**: Deep example, complete workflow demonstration  
**Cons**: Limited diversity, no comparison  
**Context**: Follow-up work will add more design systems

### 4. Dark Theme Only vs. Multiple Themes
**Decision**: Dark theme primary, light theme as future work  
**Pros**: Focused scope, clear target audience  
**Cons**: Less flexible, not suitable for all contexts  
**Context**: Technical Precision philosophy is dark-first

### 5. 5 Components vs. Comprehensive Library
**Decision**: 5 core components only  
**Pros**: Manageable scope, clear examples  
**Cons**: Not comprehensive, may need more for real apps  
**Context**: Example is for demonstration, not production use

## Extensibility

### Adding New Components
1. Document in `components.md` (anatomy, states, behavior)
2. Implement HTML in `index.html`
3. Add styles to `components.css`
4. Add interactivity to `demo-data.js` if needed
5. Update `integration.md` with usage pattern

### Creating Alternative Design Systems
1. Copy directory structure
2. Write new `philosophy.md` with different principles
3. Update `tokens.yaml` with new palette/typography
4. Redefine components in `components.md`
5. Implement playground with new styles

### Theming Existing System
1. Update CSS custom properties in `:root`
2. Test contrast ratios for accessibility
3. Update `tokens.yaml` documentation
4. Add theme toggle if supporting multiple themes

## Quality Attributes

### Performance
- Target: < 2 second load time
- Approach: Minimal CSS/JS, no external dependencies
- Measurement: Browser DevTools Performance tab

### Accessibility
- Target: WCAG 2.1 AA compliance
- Approach: Semantic HTML, ARIA attributes, keyboard navigation
- Measurement: axe DevTools, manual testing with screen readers

### Maintainability
- Target: Easy to understand and modify
- Approach: Clear naming, comments, consistent structure
- Measurement: Code review, documentation completeness

### Usability
- Target: Easy to copy and use components
- Approach: Self-contained code, clear examples
- Measurement: User feedback, adoption in other projects
