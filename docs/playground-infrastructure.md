# Design System Playground Infrastructure

## Overview

The Design System Playground is an interactive environment where users can explore, test, and provide feedback on design systems. It supports the interactive refinement workflow between users and the Design Agent.

## Purpose

- **Explore**: View all components and design tokens
- **Test**: Interact with components in realistic scenarios
- **Compare**: View multiple design philosophies side-by-side
- **Annotate**: Click-to-comment on any component
- **Adjust**: Live preview of token changes
- **Export**: Generate feedback files from annotations

## Architecture

### Components

1. **Playground Viewer** (`playground/index.html`)
   - Main interface for viewing components
   - Component gallery with all variants
   - Token visualization
   - Responsive layout switcher

2. **Annotation System** (`playground/annotation.js`)
   - Click-to-annotate any element
   - Rating system (like/dislike/neutral)
   - Comment collection
   - Screenshot capture
   - Export to feedback YAML

3. **Token Editor** (`playground/token-editor.html`)
   - Live color picker with contrast validation
   - Spacing sliders
   - Typography controls
   - Before/after comparison
   - Export modified tokens

4. **Comparison Mode** (`playground/comparison.html`)
   - Side-by-side layout for 2-3 design systems
   - Toggle between options
   - Synchronized scrolling
   - Vote/preference collection
   - Export comparison results

5. **Example Scenarios** (`playground/examples/`)
   - Realistic use cases with sample data
   - User flows (login, dashboard, forms)
   - Edge cases (long text, empty states, errors)
   - Responsive breakpoints

## Key Features

### 1. Annotation System

**User Experience**:
1. Click on any component in playground
2. Annotation form appears with:
   - Rating buttons (👍 👎 ❓)
   - Text input for comments
   - Screenshot capture button
   - Suggested changes input
3. Save annotation (stored in localStorage)
4. View all annotations in sidebar
5. Export all to feedback YAML file

**Technical Implementation**:
```javascript
// annotation.js
class AnnotationSystem {
  constructor() {
    this.annotations = [];
    this.initClickHandlers();
  }
  
  initClickHandlers() {
    // Add click handlers to annotatable elements
  }
  
  createAnnotation(element, position) {
    // Show annotation form at click position
  }
  
  saveAnnotation(data) {
    // Save to localStorage
  }
  
  exportToYAML() {
    // Generate feedback YAML file
  }
}
```

**Exported Format**:
```yaml
# Auto-generated from playground annotations
timestamp: "2026-01-17T14:30:00Z"
project: "task-dashboard-example"
component: "button"
feedback_type: "refinement"

annotations:
  - element: ".btn-primary"
    rating: "dislike"
    comment: "Too bright for extended use"
    screenshot: "data:image/png;base64,..."
  
  - element: ".btn-secondary"
    rating: "neutral"
    comment: "Padding feels cramped"
```

### 2. Token Editor with Live Preview

**User Experience**:
1. Open token editor panel
2. Select category (colors, spacing, typography)
3. Adjust token values with controls:
   - **Colors**: Color picker with hex input
   - **Spacing**: Slider with px values
   - **Typography**: Dropdowns and inputs
4. See instant preview across all components
5. Accessibility validation shown in real-time
6. Before/after comparison toggle
7. Export adjusted tokens to feedback file

**Technical Implementation**:
```javascript
// token-editor.js
class TokenEditor {
  constructor(designSystem) {
    this.tokens = designSystem.tokens;
    this.originalTokens = JSON.parse(JSON.stringify(this.tokens));
  }
  
  updateToken(path, value) {
    // Update token value
    // Apply to all components using CSS variables
    // Validate accessibility
    // Update preview
  }
  
  validateAccessibility(token, value) {
    // Check contrast ratios for color tokens
    // Validate spacing meets touch target minimums
    // Return validation results
  }
  
  exportChanges() {
    // Generate feedback YAML with token changes
  }
}
```

**CSS Variables for Live Updates**:
```css
:root {
  --color-primary: #00FF41;
  --spacing-md: 16px;
  --font-size-base: 14px;
}

.btn-primary {
  background: var(--color-primary);
  padding: var(--spacing-md);
  font-size: var(--font-size-base);
}
```

When token is adjusted in editor:
```javascript
document.documentElement.style.setProperty('--color-primary', '#00CC34');
// All components update instantly
```

### 3. Comparison Mode

**User Experience**:
1. Select 2-3 design systems/versions to compare
2. Choose layout:
   - Side-by-side (2 columns)
   - Side-by-side-by-side (3 columns)
   - Toggle view (switch between options)
3. Synchronized scrolling between columns
4. Highlight differences
5. Vote on preferred option
6. Add comments explaining preference
7. Export comparison results

**Technical Implementation**:
```javascript
// comparison.js
class ComparisonMode {
  constructor(designSystems) {
    this.systems = designSystems; // Array of 2-3 systems
    this.votes = {};
    this.comments = {};
  }
  
  renderSideBySide() {
    // Create columns for each system
    // Synchronized scrolling
  }
  
  highlightDifferences() {
    // Visual indicators for token differences
  }
  
  recordVote(component, preferredSystem) {
    // Track user preferences
  }
  
  exportResults() {
    // Generate feedback YAML with comparison data
  }
}
```

**Comparison Output**:
```yaml
timestamp: "2026-01-17T15:00:00Z"
project: "task-dashboard-example"
feedback_type: "comparison"

compared_systems:
  - name: "minimalist-modern"
    votes: 2
  - name: "technical-precision"
    votes: 8
  - name: "warm-approachable"
    votes: 1

user_comment: |
  Technical precision wins clearly. The monospace accents and 
  terminal aesthetic fit our developer audience perfectly.
  
  Specific preferences:
  - Love the color palette
  - Monospace on code samples is essential
  - High contrast helps readability

selected_philosophy: "technical-precision"
```

### 4. Feedback Collection Forms

**Quick Feedback Button**:
- Fixed position button in playground
- Click to open feedback form
- Pre-filled with current context (component, page)
- Quick rating + comment
- Saves to localStorage
- Batch export later

**Keyboard Shortcuts**:
- `F` - Open feedback form
- `A` - Enable annotation mode
- `T` - Open token editor
- `C` - Toggle comparison mode
- `E` - Export all feedback

### 5. Live Editing

**Real-time Token Adjustments**:
- All components use CSS custom properties
- Token changes update all components instantly
- No page reload required
- Before/after toggle for comparison

**Validation in Real-time**:
- Contrast ratio calculation as colors change
- Touch target size validation
- Typography scale consistency check
- Visual indicators for pass/fail

## Playground Structure

```
design-systems/{system-name}/playground/
├── index.html                      # Main playground interface
├── token-editor.html              # Token editing interface
├── comparison.html                # Comparison mode
├── styles/
│   ├── playground.css            # Playground UI styles
│   └── design-system.css         # The design system being tested
├── scripts/
│   ├── annotation.js             # Annotation system
│   ├── token-editor.js           # Token editor
│   ├── comparison.js             # Comparison mode
│   ├── feedback-exporter.js      # Export to YAML
│   └── validation.js             # Accessibility validation
├── examples/
│   ├── dashboard.html            # Example dashboard
│   ├── form.html                 # Example form
│   ├── navigation.html           # Example navigation
│   └── cards.html                # Example card layouts
├── assets/
│   ├── sample-data.json          # Sample data for examples
│   └── screenshots/              # Captured screenshots
└── README.md                      # Playground usage guide
```

## User Experience Requirements

### Performance
- **Feedback submission**: < 30 seconds
- **Preview updates**: < 2 seconds
- **Comparison mode rendering**: < 5 seconds
- **Export to YAML**: < 5 seconds

### Usability
- **Keyboard navigation**: Full keyboard accessibility
- **Undo/Redo**: All interactions are undoable
- **Clear indication**: Pending vs implemented changes
- **Mobile responsive**: Works on tablets and phones
- **Screen reader support**: Accessible to all users

### Visual Design
- **Non-intrusive**: Annotation tools don't obscure content
- **Clear affordances**: Interactive elements clearly indicated
- **Helpful tooltips**: Guidance without overwhelming
- **Consistent UI**: Playground UI uses its own minimal style

## Implementation Phases

### Phase 1: Basic Playground (MVP)
- [ ] Component gallery with all variants
- [ ] Token visualization
- [ ] Basic annotation (click and comment)
- [ ] Export to YAML

### Phase 2: Interactive Features
- [ ] Token editor with live preview
- [ ] Contrast ratio validation
- [ ] Screenshot capture
- [ ] Rating system

### Phase 3: Advanced Features
- [ ] Comparison mode
- [ ] Synchronized scrolling
- [ ] Before/after toggle
- [ ] Keyboard shortcuts

### Phase 4: Polish
- [ ] Mobile responsive design
- [ ] Performance optimization
- [ ] Comprehensive documentation
- [ ] Video tutorials

## Technical Specifications

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Dependencies
- No heavy frameworks (vanilla JS preferred)
- Optional: CSS custom properties polyfill for older browsers
- Optional: YAML parser for import/export

### File Size Targets
- HTML + CSS + JS: < 100KB total
- Fast load times even on slow connections
- Progressive enhancement for older browsers

### Data Storage
- localStorage for annotations during session
- Export to YAML for persistent storage
- No server-side storage (privacy-friendly)

## Accessibility Requirements

The playground itself must be fully accessible:

- [ ] WCAG AA compliant
- [ ] Keyboard navigation for all features
- [ ] Screen reader announcements for changes
- [ ] Focus indicators on all interactive elements
- [ ] Accessible color contrast in playground UI
- [ ] Alt text for all images and icons
- [ ] ARIA labels where needed

## Testing Checklist

Before launching playground:

- [ ] Test on all supported browsers
- [ ] Test on mobile devices
- [ ] Test with keyboard only
- [ ] Test with screen reader
- [ ] Test annotation system
- [ ] Test token editor
- [ ] Test comparison mode
- [ ] Test export functionality
- [ ] Verify accessibility compliance
- [ ] Performance test on slow connections

## Example Scenarios

### Scenario 1: User testing a button
1. Opens playground
2. Navigates to buttons section
3. Clicks on primary button
4. Annotation form appears
5. Rates "dislike" 👎
6. Comments: "Too bright, reduce saturation"
7. Saves annotation
8. Continues testing other components
9. Clicks "Export Feedback"
10. YAML file downloaded with all annotations

### Scenario 2: Adjusting color token
1. Opens token editor
2. Selects "Colors" category
3. Clicks on "primary" color
4. Color picker appears
5. Adjusts saturation slider
6. Sees instant preview across all components
7. Validation shows: "Contrast: 4.8:1 ✓"
8. Clicks "Export Changes"
9. YAML file with token changes downloaded

### Scenario 3: Comparing design philosophies
1. Opens comparison mode
2. Selects "Technical Precision" and "Minimalist Modern"
3. Side-by-side view loads
4. Scrolls through components (synchronized)
5. Votes for "Technical Precision" on each component
6. Adds comment: "Better fit for developer audience"
7. Exports comparison results

## Related Documentation

- `playbooks/design-iteration.md` - Workflow using playground
- `feedback/design-feedback/README.md` - Feedback system
- `specs/kerrigan/agents/design/spec.md` - Design Agent spec
- `.github/agents/role.design.md` - Design Agent prompt

## Future Enhancements

- Integration with design tools (Figma, Sketch)
- A/B testing with real user metrics
- Version history with rollback
- Multi-user collaboration features
- Design system marketplace for sharing
- Automated accessibility auditing
- Performance profiling for components
- Code generation from playground adjustments
