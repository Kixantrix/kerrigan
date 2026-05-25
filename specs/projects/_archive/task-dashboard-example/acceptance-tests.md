# Acceptance Tests: Task Dashboard Example

## Overview

These tests verify that the example design system demonstrates the design agent workflow and serves as a reference implementation.

---

## Design System Documentation

### Test 1: Philosophy Document Exists and is Complete
**Given**: A design system in `specs/projects/task-dashboard-example/design-system/`  
**When**: I open `philosophy.md`  
**Then**: It should contain:
- Overview section explaining the design philosophy
- Core principles (3+)
- Design characteristics (typography, color, layout, interaction)
- Target audience definition
- Tone & voice guidelines
- Anti-patterns (what to avoid)
- Use cases (ideal for / not ideal for)

### Test 2: Design Tokens are Comprehensive
**Given**: The design system directory  
**When**: I open `tokens.yaml`  
**Then**: It should define:
- Colors (primary, background, text, semantic colors)
- Typography (font families, scale, weights, line heights)
- Spacing scale (at least 6 values)
- Sizing values (input, button, row heights)
- Border radius options
- Shadows
- Transitions
- Z-index layers
- Opacity values

### Test 3: Component Specifications are Detailed
**Given**: The design system directory  
**When**: I open `components.md`  
**Then**: It should specify all 5 components:
- DataTable
- StatusBadge
- MetricCard
- CommandBar
- TaskRow

**And** each component should include:
- Purpose statement
- Anatomy (visual structure)
- Props & States
- Behavior description
- Accessibility requirements

### Test 4: Accessibility Checklist is Comprehensive
**Given**: The design system directory  
**When**: I open `a11y-checklist.md`  
**Then**: It should cover:
- Color & contrast requirements
- Keyboard navigation
- Screen reader support
- Responsive & zoom
- Forms & inputs
- Interactive element states
- Motion & animation
- Testing tools

### Test 5: Integration Guide is Practical
**Given**: The design system directory  
**When**: I open `integration.md`  
**Then**: It should include:
- Quick start instructions
- CSS custom properties setup
- Component HTML patterns for all 5 components
- JavaScript hooks for interactive components
- Theming instructions
- Performance considerations
- Migration guide

---

## Playground Implementation

### Test 6: Playground Files Exist
**Given**: The design system playground directory  
**When**: I list files in `playground/`  
**Then**: I should see:
- index.html
- components.css
- demo-data.js

### Test 7: Playground Opens Without Build Process
**Given**: The playground directory  
**When**: I open `index.html` directly in a browser  
**Then**: The page should load without errors  
**And**: All components should be visible  
**And**: No console errors should appear

### Test 8: All Components are Showcased
**Given**: The playground is open  
**When**: I scroll through the page  
**Then**: I should see working examples of:
- Token visualization (colors, typography, spacing)
- MetricCard (3 variations)
- StatusBadge (4 states: todo, in-progress, done, blocked)
- TaskRow (at least 3 examples)
- DataTable (with sample data)
- CommandBar (can be opened)

### Test 9: DataTable is Sortable
**Given**: The playground is open  
**When**: I click on a table column header  
**Then**: The column should show a sort indicator (▲ or ▼)  
**And**: The table rows should reorder based on that column

### Test 10: CommandBar Opens and Closes
**Given**: The playground is open  
**When**: I press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux)  
**Then**: The command bar should open  
**And**: The input should be focused  
**When**: I press `Escape`  
**Then**: The command bar should close

### Test 11: TaskRow Checkboxes Work
**Given**: The playground is open  
**When**: I click a checkbox in a TaskRow  
**Then**: The row should show selected state  
**And**: The checkbox should be checked

---

## Accessibility

### Test 12: Keyboard Navigation Works
**Given**: The playground is open  
**When**: I navigate using only keyboard (Tab, Arrow keys)  
**Then**: I should be able to:
- Navigate through all interactive elements
- See focus indicators on focused elements
- Activate buttons with Enter/Space
- Sort table with Enter on headers
- Navigate table rows with arrow keys

### Test 13: Color Contrast Meets Standards
**Given**: The playground CSS  
**When**: I check text color against background color  
**Then**: All text should meet 4.5:1 contrast ratio minimum (WCAG AA)  
**Verify**:
- Primary text (#C9D1D9) on background (#0D1117): > 4.5:1
- Secondary text (#8B949E) on background: > 4.5:1
- Primary accent (#00FF41) on background: > 4.5:1

### Test 14: ARIA Attributes are Present
**Given**: The playground HTML  
**When**: I inspect the components  
**Then**: I should find:
- `role="table"` on DataTable
- `role="status"` on StatusBadge
- `aria-sort` on sortable table headers
- `aria-label` on MetricCards
- `role="dialog"` on CommandBar
- `aria-expanded` on CommandBar input

### Test 15: Screen Reader Compatibility
**Given**: The playground is open  
**When**: I use a screen reader (NVDA, JAWS, or VoiceOver)  
**Then**: The screen reader should:
- Announce table structure
- Read status badges with full text
- Announce metric values with context
- Identify interactive elements correctly

---

## Integration

### Test 16: Spec References Design System
**Given**: The project spec at `specs/projects/task-dashboard-example/spec.md`  
**When**: I read the "Visual Design" section  
**Then**: It should:
- Reference the Technical Precision design system
- Specify the design system location
- List the components used
- Explain key design characteristics

### Test 17: Component Code is Copy-Paste Ready
**Given**: The integration guide  
**When**: I copy a component HTML pattern  
**And**: I paste it into a new HTML file with the CSS included  
**Then**: The component should render correctly  
**And**: The styling should match the playground

### Test 18: CSS Custom Properties Work
**Given**: The components.css file  
**When**: I change a CSS custom property value (e.g., `--color-primary`)  
**Then**: All components using that property should update  
**And**: The visual change should be consistent

---

## Responsive Design

### Test 19: Mobile Layout Works
**Given**: The playground is open  
**When**: I resize the browser to 320px width  
**Then**: The content should be readable  
**And**: No horizontal scroll should be required (except DataTable)  
**And**: Components should stack vertically

### Test 20: Desktop Layout is Optimal
**Given**: The playground is open  
**When**: I view at 1920px width  
**Then**: Components should use available space efficiently  
**And**: No excessive whitespace  
**And**: Text should remain readable

---

## Performance

### Test 21: Page Loads Quickly
**Given**: The playground HTML  
**When**: I open it in a browser  
**Then**: The page should load in < 2 seconds  
**And**: All components should be interactive immediately

### Test 22: No JavaScript Errors
**Given**: The playground is open  
**When**: I open browser DevTools console  
**Then**: There should be no error messages  
**And**: Only expected log messages should appear

---

## Documentation Quality

### Test 23: README or Instructions Exist
**Given**: The design system directory  
**When**: I look for getting started information  
**Then**: Either the spec.md or a README should explain:
- How to view the playground
- What the design system demonstrates
- Where to find documentation

### Test 24: Code is Readable
**Given**: The playground CSS and JavaScript  
**When**: I review the code  
**Then**: It should:
- Have clear class names following the BEM (Block__Element--Modifier) convention consistently
- Include comments for complex logic
- Use consistent formatting
- Be organized logically (tokens → base → components)

---

## Edge Cases

### Test 25: Empty States Handled
**Given**: The playground JavaScript  
**When**: The data array is empty  
**Then**: The table should not break  
**And**: An appropriate message or empty state should appear

### Test 26: Long Text Handles Gracefully
**Given**: A TaskRow with very long title  
**When**: Viewing on mobile  
**Then**: Text should truncate or wrap  
**And**: Layout should not break

### Test 27: Multiple Command Bar Opens
**Given**: The playground is open  
**When**: I open the command bar, close it, and open it again  
**Then**: It should work correctly each time  
**And**: No duplicate elements should appear

---

## Success Criteria

All tests should pass for the design system to be considered complete and ready for use as a reference implementation.
