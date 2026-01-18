# Architecture: Design System Playground

## Overview

A static web application that provides an interactive environment for exploring and testing design system components and tokens.

## Technology Stack

- **HTML5**: Semantic markup for structure
- **CSS3**: Custom properties for theming, Grid/Flexbox for layout
- **Vanilla JavaScript**: No frameworks, minimal dependencies
- **Web APIs**: LocalStorage for theme preference

## Directory Structure

```
specs/projects/design-system-playground/
├── spec.md                 # This specification
├── architecture.md         # This file
├── plan.md                 # Implementation plan
├── playground/             # Actual playground files
│   ├── index.html         # Main HTML structure
│   ├── css/
│   │   ├── tokens.css     # Design tokens (colors, typography, spacing)
│   │   ├── components.css # Component styles
│   │   └── playground.css # Playground UI styles
│   ├── js/
│   │   ├── theme-toggle.js    # Theme switching logic
│   │   ├── responsive-preview.js # Viewport size control
│   │   └── code-viewer.js     # Code display and copy
│   └── assets/            # Images, icons (if needed)
└── runbook.md             # Usage and deployment guide
```

## Component Architecture

### 1. Navigation Bar
- Fixed header with playground branding
- Section links (Tokens, Components, Patterns)
- Theme toggle button
- Responsive hamburger menu for mobile

### 2. Token Display
- Color palette with hex/rgb values
- Typography scale with live text examples
- Spacing scale with visual representations
- Grid layout for token categories

### 3. Component Gallery
- Card-based layout for each component
- Live component preview
- State variation controls (hover, focus, disabled, error)
- Code viewer with copy button
- Component metadata (name, description, usage)

### 4. Responsive Preview
- Viewport size selector (mobile, tablet, desktop)
- Iframe or CSS transform for preview
- Device frame visualization (optional)

### 5. Code Viewer
- Syntax-highlighted HTML/CSS display
- Copy to clipboard functionality
- Toggle between HTML and CSS views

## Data Flow

```
User Action → JavaScript Event Handler → DOM Manipulation → Visual Update
     ↓
LocalStorage (for theme preference)
```

## Theme System

CSS custom properties enable theme switching:

```css
:root {
  --color-primary: #0066cc;
  --color-background: #ffffff;
  --color-text: #333333;
}

[data-theme="dark"] {
  --color-primary: #3399ff;
  --color-background: #1a1a1a;
  --color-text: #f0f0f0;
}
```

## State Management

- Theme preference stored in `localStorage`
- Viewport size stored in component state (not persisted)
- Active section tracked via URL hash or JavaScript variable
- No complex state management needed (vanilla JS sufficient)

## Performance Considerations

- Inline critical CSS for fast initial render
- Defer non-critical JavaScript
- Use CSS transitions for smooth theme switching
- Lazy load component examples if needed
- Minimize DOM manipulation

## Accessibility

- Semantic HTML elements
- ARIA labels for interactive controls
- Keyboard navigation support
- Focus indicators
- Color contrast compliance (WCAG AA)
- Screen reader announcements for theme changes

## Browser Compatibility

- Target: Modern browsers (last 2 versions)
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Extensibility

- Component catalog can be extended by adding new sections
- Token system supports additional categories
- Theme system can support more than 2 themes
- Code viewer can be enhanced with syntax highlighting libraries

## Security

- No user input processing (static content)
- No external data fetching
- No cookies or tracking
- Safe to deploy as static files
