# Integration Guide: Technical Precision Design System

This guide explains how to integrate the Technical Precision design system into your application.

## Quick Start

### 1. Include Design Tokens as CSS Custom Properties

Copy the design tokens into your CSS as custom properties. This example shows the conversion from `tokens.yaml` to CSS:

```css
:root {
  /* Colors */
  --color-primary: #00FF41;
  --color-primary-dim: #00CC34;
  --color-background: #0D1117;
  --color-surface: #161B22;
  --color-surface-hover: #1C2128;
  --color-text-primary: #C9D1D9;
  --color-text-secondary: #8B949E;
  --color-text-tertiary: #6E7681;
  --color-text-inverse: #0D1117;
  --color-border: #30363D;
  --color-border-hover: #484F58;
  --color-border-focus: #00FF41;
  
  /* Semantic colors */
  --color-success: #3FB950;
  --color-success-bg: #1B2B22;
  --color-warning: #D29922;
  --color-warning-bg: #2B2418;
  --color-error: #F85149;
  --color-error-bg: #2C1A1A;
  --color-info: #58A6FF;
  --color-info-bg: #1A2332;
  
  /* Typography */
  --font-mono: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
  --font-system: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica', 'Arial', sans-serif;
  
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 20px;
  --font-size-xl: 24px;
  --font-size-xxl: 32px;
  
  --font-weight-regular: 400;
  --font-weight-bold: 600;
  
  --line-height-tight: 1.2;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.6;
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-xxl: 48px;
  --spacing-xxxl: 64px;
  
  /* Sizing */
  --size-input-height: 32px;
  --size-button-height: 32px;
  --size-row-height: 40px;
  --size-row-height-compact: 32px;
  --size-header-height: 56px;
  --size-sidebar-width: 240px;
  
  /* Border radius */
  --radius-none: 0;
  --radius-sm: 3px;
  --radius-md: 6px;
  
  /* Shadows */
  --shadow-none: none;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 2px 8px rgba(0, 0, 0, 0.4);
  --shadow-focus: 0 0 0 2px #00FF41;
  
  /* Transitions */
  --transition-fast: 150ms ease-in-out;
  --transition-none: none;
  
  /* Z-index */
  --z-base: 0;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-modal-backdrop: 300;
  --z-modal: 400;
  --z-tooltip: 500;
  --z-toast: 600;
  
  /* Opacity */
  --opacity-disabled: 0.5;
  --opacity-hover: 0.8;
  --opacity-muted: 0.6;
}
```

### 2. Set Base Styles

Apply the design system's base styles to your application:

```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  color: var(--color-text-primary);
  background-color: var(--color-background);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Focus styles */
:focus {
  outline: 2px solid var(--color-border-focus);
  outline-offset: 2px;
}

:focus:not(:focus-visible) {
  outline: none;
}

:focus-visible {
  outline: 2px solid var(--color-border-focus);
  outline-offset: 2px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 3. Use Components

Each component is implemented as HTML + CSS. See the playground for complete examples.

---

## Component HTML Patterns

### DataTable

```html
<div class="data-table" role="table">
  <div class="data-table__header" role="rowgroup">
    <div class="data-table__row" role="row">
      <div class="data-table__cell data-table__cell--header" role="columnheader" aria-sort="ascending">
        Task ID ▼
      </div>
      <div class="data-table__cell data-table__cell--header" role="columnheader">
        Title
      </div>
      <div class="data-table__cell data-table__cell--header" role="columnheader">
        Status
      </div>
    </div>
  </div>
  <div class="data-table__body" role="rowgroup">
    <div class="data-table__row" role="row" tabindex="0">
      <div class="data-table__cell" role="cell">TASK-123</div>
      <div class="data-table__cell" role="cell">Fix login bug</div>
      <div class="data-table__cell" role="cell">
        <span class="status-badge status-badge--in-progress">
          <span class="status-badge__dot"></span>
          in-progress
        </span>
      </div>
    </div>
  </div>
</div>
```

### StatusBadge

```html
<span class="status-badge status-badge--todo" role="status" aria-label="Task status: To Do">
  <span class="status-badge__dot"></span>
  todo
</span>

<span class="status-badge status-badge--in-progress" role="status" aria-label="Task status: in-progress">
  <span class="status-badge__dot"></span>
  in-progress
</span>

<span class="status-badge status-badge--done" role="status" aria-label="Task status: Done">
  <span class="status-badge__dot"></span>
  done
</span>

<span class="status-badge status-badge--blocked" role="status" aria-label="Task status: Blocked">
  <span class="status-badge__dot"></span>
  blocked
</span>
```

### MetricCard

```html
<article class="metric-card" aria-label="Active tasks: 247, up 12% from last week">
  <div class="metric-card__label">Active Tasks</div>
  <div class="metric-card__value">247</div>
  <div class="metric-card__trend metric-card__trend--up">
    <span class="metric-card__trend-icon">▲</span>
    <span class="metric-card__trend-text">+12%</span>
  </div>
</article>
```

### CommandBar

```html
<div class="command-bar" role="dialog" aria-modal="true" aria-label="Command palette">
  <div class="command-bar__backdrop"></div>
  <div class="command-bar__container">
    <input
      type="text"
      class="command-bar__input"
      placeholder="⌘ Search or type command..."
      role="combobox"
      aria-expanded="true"
      aria-autocomplete="list"
      aria-controls="command-list"
    />
    <ul class="command-bar__list" id="command-list" role="listbox">
      <li class="command-bar__item" role="option" tabindex="-1">
        <span class="command-bar__item-label">> New Task</span>
        <span class="command-bar__item-shortcut">⌘N</span>
      </li>
      <li class="command-bar__item" role="option" tabindex="-1">
        <span class="command-bar__item-label">> Filter by Status</span>
        <span class="command-bar__item-shortcut">⌘F</span>
      </li>
    </ul>
  </div>
</div>
```

### TaskRow

```html
<div class="task-row" role="row" tabindex="0">
  <input type="checkbox" class="task-row__checkbox" id="task-123" aria-label="Select task: Fix login bug" />
  <label class="task-row__content" for="task-123">
    <div class="task-row__primary">
      <span class="task-row__id">[TASK-123]</span>
      <span class="task-row__title">Fix login bug</span>
      <span class="status-badge status-badge--in-progress">
        <span class="status-badge__dot"></span>
        in-progress
      </span>
      <span class="task-row__assignee">👤</span>
    </div>
    <div class="task-row__secondary">
      due: 2026-01-20
    </div>
  </label>
</div>
```

---

## JavaScript Hooks

### DataTable Sorting

```javascript
document.querySelectorAll('.data-table__cell--header').forEach(header => {
  header.addEventListener('click', () => {
    const currentSort = header.getAttribute('aria-sort');
    const newSort = currentSort === 'ascending' ? 'descending' : 'ascending';
    
    // Clear other headers
    document.querySelectorAll('.data-table__cell--header').forEach(h => {
      h.setAttribute('aria-sort', 'none');
    });
    
    // Set new sort
    header.setAttribute('aria-sort', newSort);
    
    // Trigger sort logic (implement based on your data structure)
    sortTable(header.dataset.column, newSort);
  });
});
```

### CommandBar Toggle

```javascript
// Open command bar
document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    document.querySelector('.command-bar').classList.add('command-bar--open');
    document.querySelector('.command-bar__input').focus();
  }
});

// Close command bar
document.querySelector('.command-bar__backdrop').addEventListener('click', () => {
  document.querySelector('.command-bar').classList.remove('command-bar--open');
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelector('.command-bar').classList.remove('command-bar--open');
  }
});
```

### TaskRow Selection

```javascript
document.querySelectorAll('.task-row__checkbox').forEach(checkbox => {
  checkbox.addEventListener('change', (e) => {
    const row = e.target.closest('.task-row');
    if (e.target.checked) {
      row.classList.add('task-row--selected');
    } else {
      row.classList.remove('task-row--selected');
    }
  });
});
```

---

## Theming

### Light Mode Support

To add light mode support, define an alternate color scheme:

```css
@media (prefers-color-scheme: light) {
  :root {
    --color-background: #FFFFFF;
    --color-surface: #F6F8FA;
    --color-surface-hover: #EFF1F3;
    --color-text-primary: #24292F;
    --color-text-secondary: #57606A;
    --color-text-tertiary: #8B949E;
    --color-border: #D0D7DE;
    --color-border-hover: #BCC3CA;
  }
}
```

Or allow manual toggle:

```css
[data-theme="light"] {
  --color-background: #FFFFFF;
  --color-surface: #F6F8FA;
  /* ... etc */
}
```

```javascript
document.body.setAttribute('data-theme', 'light');
```

### Density Levels

Add density variants for compact or comfortable layouts:

```css
[data-density="compact"] {
  --size-row-height: 32px;
  --spacing-md: 12px;
  --font-size-sm: 12px;
}

[data-density="comfortable"] {
  --size-row-height: 48px;
  --spacing-md: 20px;
  --font-size-sm: 16px;
}
```

---

## Performance Considerations

### Large Tables
For tables with >100 rows, implement virtual scrolling:

```javascript
// Use libraries like react-window or implement custom virtual scrolling
// Render only visible rows + buffer
```

### CSS Loading
Load critical CSS inline, defer non-critical styles:

```html
<style>/* Critical CSS here */</style>
<link rel="preload" href="components.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
```

### Font Loading
Optimize font loading to prevent layout shift:

```css
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/fonts/jetbrains-mono.woff2') format('woff2');
  font-display: swap;
}
```

---

## Migration Guide

### From Card-Based Layouts
1. Replace card containers with table rows
2. Remove border-radius, shadows, padding from cards
3. Use `--color-surface` for elevated sections
4. Consolidate whitespace (reduce padding)

### From Bootstrap/Material UI
1. Remove framework CSS completely (avoid conflicts)
2. Replace semantic color classes with design system tokens
3. Update button styles to match Technical Precision aesthetic
4. Replace modal dialogs with command bar pattern

### From Custom Designs
1. Audit color palette—reduce to design system tokens
2. Switch to monospace typography for data-heavy views
3. Implement keyboard shortcuts for all actions
4. Add focus indicators to all interactive elements

---

## Troubleshooting

### Fonts Not Loading
- Verify font files are accessible
- Check CORS headers if loading from CDN
- Use `font-display: swap` to prevent invisible text

### Focus Indicators Not Visible
- Check z-index of focused element
- Ensure outline not overridden by other styles
- Test with keyboard navigation

### Colors Look Different
- Verify CSS custom properties loaded
- Check for conflicting styles from other frameworks
- Validate hex values in tokens

### Components Not Responsive
- Test at 320px, 768px, 1024px breakpoints
- Ensure no fixed widths on containers
- Use `overflow-x: auto` on tables

---

## Resources

- **Playground**: See `playground/index.html` for live examples
- **Components**: Full specifications in `components.md`
- **Tokens**: Complete token reference in `tokens.yaml`
- **Accessibility**: Checklist in `a11y-checklist.md`
- **Philosophy**: Design principles in `philosophy.md`
