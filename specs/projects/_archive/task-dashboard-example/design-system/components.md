# Component Specifications

This document defines the 5 core components of the Technical Precision design system for the Task Management Dashboard.

## 1. DataTable

**Purpose**: Display tabular data with sorting, filtering, and keyboard navigation.

### Anatomy
```
┌─────────────────────────────────────────────────┐
│ [Column Header ▼] [Column Header] [Column...]   │ ← Headers (sortable)
├─────────────────────────────────────────────────┤
│ Cell data         Cell data      Cell...        │ ← Row (hoverable)
│ Cell data         Cell data      Cell...        │ ← Row
│ Cell data         Cell data      Cell...        │ ← Row (focused)
└─────────────────────────────────────────────────┘
```

### Props & States
- **Columns**: Array of column definitions (name, key, sortable, width)
- **Rows**: Array of data objects
- **Sortable**: Enable column sorting (default: true)
- **Density**: `compact` | `default` | `comfortable`
- **Selection**: Enable row selection (optional)

### States
- **Default**: Standard row appearance
- **Hover**: Background changes to `surface-hover`
- **Focus**: 2px outline in accent color
- **Selected**: Background tint with primary color
- **Sorted column**: Subtle highlight on header

### Behavior
- Click column header to sort (ascending/descending/none)
- `↑`/`↓` keys navigate rows
- `Space` selects focused row (if selection enabled)
- `Home`/`End` jump to first/last row
- Horizontal scroll for wide tables

### Accessibility
- `role="table"` with proper ARIA structure
- `aria-sort` on sortable columns
- `aria-selected` on selected rows
- Keyboard navigation fully functional
- Screen reader announces sort direction

---

## 2. StatusBadge

**Purpose**: Display task status with clear visual distinction.

### Anatomy
```
┌──────────────┐
│ ● STATUS     │  ← Badge with dot indicator
└──────────────┘
```

### Variants
- **todo**: Gray dot, `text-secondary`
- **in-progress**: Yellow dot, warning color
- **done**: Green dot, success color
- **blocked**: Red dot, error color

### Props
- **status**: `"todo"` | `"in-progress"` | `"done"` | `"blocked"`
- **size**: `sm` | `md` (default: `md`)

### States
- **Static only**: No interactive states

### Styling
```css
/* Example: in-progress badge */
background: var(--warning-bg);
color: var(--warning);
border: 1px solid var(--warning);
padding: 4px 8px;
border-radius: 3px;
```

### Accessibility
- `role="status"` for screen readers
- `aria-label` with full status text
- Color is not the only differentiator (uses dot + text)

---

## 3. MetricCard

**Purpose**: Display key metrics with optional trend indicators.

### Anatomy
```
┌─────────────────────────┐
│ Label                   │ ← Metric name
│ 247 ▲ +12%            │ ← Value + trend
└─────────────────────────┘
```

### Props
- **label**: Metric name (string)
- **value**: Primary value (number or string)
- **trend**: Optional trend object `{direction: "up"|"down", value: string}`
- **variant**: `primary` | `success` | `warning` | `error`

### States
- **Default**: Surface background
- **Hover**: Slight elevation (if clickable)

### Behavior
- Static display (non-interactive by default)
- Optional `onClick` for drilldown

### Styling
- Large value: `xxl` type scale (32px)
- Label: `sm` type scale (14px), `text-secondary`
- Trend: `sm` type scale with semantic color

### Accessibility
- Semantic HTML (`<article>` or `<section>`)
- `aria-label` for full metric context
- Trend direction conveyed via text, not just arrow

---

## 4. CommandBar

**Purpose**: Keyboard-driven action bar for quick commands.

### Anatomy
```
┌─────────────────────────────────────────────────┐
│ ⌘ Search or type command...                    │ ← Input field
│ ┌─────────────────────────────────────────────┐ │
│ │ > New Task              ⌘N                  │ │ ← Command list
│ │ > Filter by Status      ⌘F                  │ │
│ │ > Export                ⌘E                  │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Props
- **commands**: Array of command objects `{label, shortcut, action, icon}`
- **placeholder**: Input placeholder text
- **onSelect**: Callback when command is selected

### States
- **Closed**: Hidden
- **Open**: Visible with input focused
- **Command focused**: Highlighted command in list

### Behavior
- `⌘K` (Mac) or `Ctrl+K` (Windows/Linux) to open
- Type to filter commands
- `↑`/`↓` to navigate commands
- `Enter` to execute focused command
- `Esc` to close

### Styling
- Modal overlay with backdrop
- Command bar centered on screen
- List below input with smooth transitions

### Accessibility
- `role="combobox"` on input
- `role="listbox"` on command list
- `aria-expanded`, `aria-activedescendant` for state
- Keyboard shortcuts announced by screen readers

---

## 5. TaskRow

**Purpose**: Compact representation of a task in a list view.

### Anatomy
```
┌────────────────────────────────────────────────────────┐
│ ☐ [TASK-123] Fix login bug          ● in-progress  👤│ ← Checkbox, ID, Title, Badge, Assignee
│   due: 2026-01-20                                     │ ← Metadata row
└────────────────────────────────────────────────────────┘
```

### Props
- **task**: Task object with `{id, title, status, assignee, dueDate}`
- **selectable**: Enable checkbox (default: true)
- **onSelect**: Callback when checkbox toggled
- **onClick**: Callback when row clicked

### States
- **Default**: Standard appearance
- **Hover**: Background to `surface-hover`
- **Selected**: Checkbox checked, subtle highlight
- **Focus**: 2px outline on row

### Layout
- **Primary row**: Checkbox, ID badge, title, status badge, assignee avatar
- **Secondary row**: Metadata (due date, priority, tags)

### Behavior
- Click checkbox to select
- Click row (outside checkbox) to open task
- `Space` toggles selection when focused
- `Enter` opens task when focused

### Styling
- Height: `row-height` (40px) in default density
- Monospace font for ID and metadata
- System font for title (better readability for prose)

### Accessibility
- `role="row"` with proper table structure
- Checkbox properly labeled with task title
- Focus management on checkbox vs. row
- All actions keyboard accessible

---

## Layout Guidelines

### Spacing Between Components
- Stack components with `md` (16px) vertical spacing
- Use `lg` (24px) for major section breaks
- Use `xl` (32px) for page-level separations

### Responsive Behavior

**Mobile (320px - 767px)**:
- DataTable: Horizontal scroll or card view
- CommandBar: Full screen overlay
- MetricCard: Single column stack
- TaskRow: Truncate long titles

**Tablet (768px - 1023px)**:
- DataTable: Show fewer columns
- MetricCard: 2-column grid
- TaskRow: Full metadata visible

**Desktop (1024px+)**:
- DataTable: All columns visible
- MetricCard: 3-4 column grid
- TaskRow: Full layout with avatars

---

## Component Composition Examples

### Task List View
```
┌─────────────────────────────────────┐
│ CommandBar (at top)                 │
├─────────────────────────────────────┤
│ MetricCard | MetricCard | MetricCard│ ← Summary metrics
├─────────────────────────────────────┤
│ DataTable                           │
│   TaskRow                           │
│   TaskRow                           │
│   TaskRow                           │
└─────────────────────────────────────┘
```

### Dashboard View
```
┌─────────────────────────────────────┐
│ MetricCard | MetricCard | MetricCard│
├─────────────────────────────────────┤
│ DataTable: Recent Tasks             │
└─────────────────────────────────────┘
```

---

## Implementation Notes

1. **CSS Custom Properties**: All components use tokens via CSS custom properties
2. **No framework dependencies**: Vanilla JS for interactivity
3. **Progressive enhancement**: Works without JS for static content
4. **Copy-paste ready**: Each component is self-contained HTML/CSS
5. **Performance**: Virtualization for large tables (>100 rows) recommended
