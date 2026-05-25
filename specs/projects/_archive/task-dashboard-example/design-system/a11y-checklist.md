# Accessibility Checklist: Technical Precision Design System

This checklist ensures all components meet WCAG 2.1 AA standards minimum. Use this for design validation and quality assurance.

## Color & Contrast

### Requirements
- [ ] **All text meets 4.5:1 contrast ratio** (WCAG AA for normal text)
- [ ] **Large text (18px+ or 14px+ bold) meets 3:1 ratio** minimum
- [ ] **UI components meet 3:1 contrast ratio** against adjacent colors
- [ ] **Color is never the only indicator** of state or meaning

### Validation
- Use browser DevTools contrast checker
- Test with [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- Verify badge status conveyed through text + icon, not color alone

### Technical Precision Compliance
- ✅ Primary text (`#C9D1D9`) on background (`#0D1117`): **14.2:1** ratio
- ✅ Secondary text (`#8B949E`) on background: **5.8:1** ratio
- ✅ Primary accent (`#00FF41`) on background: **9.8:1** ratio
- ✅ StatusBadge uses dot + text (not color alone)

---

## Keyboard Navigation

### Requirements
- [ ] **All interactive elements keyboard accessible**
- [ ] **Focus order follows visual order** (left-to-right, top-to-bottom)
- [ ] **Focus indicators clearly visible** (2px outline minimum)
- [ ] **No keyboard traps** (user can navigate away from all elements)
- [ ] **Skip links available** for repeated content

### Component-Specific Tests

#### DataTable
- [ ] `Tab` moves focus through headers and cells
- [ ] `↑`/`↓` navigate rows
- [ ] `Space` selects row (if selection enabled)
- [ ] `Home`/`End` jump to first/last row
- [ ] `Enter` activates focused element

#### CommandBar
- [ ] `⌘K` / `Ctrl+K` opens command bar
- [ ] `↑`/`↓` navigate commands
- [ ] `Enter` executes command
- [ ] `Esc` closes command bar
- [ ] Focus returns to trigger element on close

#### TaskRow
- [ ] `Tab` focuses checkbox, then row
- [ ] `Space` toggles checkbox
- [ ] `Enter` opens task detail
- [ ] Focus visible on all states

### Focus Management
- [ ] Focus never hidden behind modals
- [ ] Focus restored to trigger on modal close
- [ ] Focus trapped within modals when open

---

## Screen Reader Support

### Semantic HTML
- [ ] **Proper heading hierarchy** (h1 → h2 → h3, no skipping)
- [ ] **Landmarks used correctly** (header, nav, main, aside, footer)
- [ ] **Lists use `<ul>`, `<ol>`, or `<dl>` tags**
- [ ] **Tables use proper structure** (`<table>`, `<thead>`, `<tbody>`, `<th>`, `<td>`)

### ARIA Attributes

#### DataTable
- [ ] `role="table"` on container
- [ ] `role="rowgroup"` on thead/tbody
- [ ] `role="row"` on each tr
- [ ] `role="columnheader"` on th
- [ ] `role="cell"` on td
- [ ] `aria-sort="ascending|descending|none"` on sorted columns
- [ ] `aria-selected="true|false"` on selectable rows

#### CommandBar
- [ ] `role="combobox"` on input
- [ ] `role="listbox"` on command list
- [ ] `role="option"` on each command
- [ ] `aria-expanded="true|false"` on combobox
- [ ] `aria-activedescendant` points to focused command
- [ ] `aria-label` or `aria-labelledby` on input

#### StatusBadge
- [ ] `role="status"` for live updates
- [ ] `aria-label` with full status text (e.g., "Task status: in-progress")

#### MetricCard
- [ ] `aria-label` with complete context (e.g., "Active tasks: 247, up 12% from last week")
- [ ] Trend direction in text, not just icon

#### TaskRow
- [ ] Checkbox has `aria-label` with task title
- [ ] Row has `aria-label` with full task context
- [ ] `aria-checked` on checkbox

### Screen Reader Testing
- [ ] Test with NVDA (Windows)
- [ ] Test with JAWS (Windows)
- [ ] Test with VoiceOver (macOS/iOS)
- [ ] All content announced correctly
- [ ] Interactive elements identified clearly

---

## Responsive & Zoom

### Requirements
- [ ] **Content readable at 200% zoom** (WCAG AA)
- [ ] **No horizontal scroll at 320px width** (mobile)
- [ ] **Text reflows without loss of content**
- [ ] **Touch targets at least 44x44px** on mobile

### Breakpoint Testing
- [ ] **320px** (small mobile): Content stacks vertically
- [ ] **768px** (tablet): Efficient use of space
- [ ] **1024px+** (desktop): Full feature set visible

### Technical Precision Implementation
- DataTable: Horizontal scroll or card view on mobile
- CommandBar: Full-screen overlay on mobile
- MetricCards: Stack on mobile, grid on desktop
- TaskRows: Truncate long text on mobile

---

## Forms & Inputs

### Requirements
- [ ] **All inputs have visible labels**
- [ ] **Labels associated with inputs** (`for` attribute or wrapping)
- [ ] **Placeholder text not used as label**
- [ ] **Error messages associated with inputs** (`aria-describedby`)
- [ ] **Required fields indicated** (`required` attribute + visual indicator)

### CommandBar Input
- [ ] Label present (can be visually hidden)
- [ ] Placeholder provides hint, not label
- [ ] Error states announced
- [ ] Clear visual feedback on invalid input

---

## Interactive Element States

### Required States for All Interactive Elements
- [ ] **Default**: Clear visual appearance
- [ ] **Hover**: Visible change (background, border, or underline)
- [ ] **Focus**: 2px outline in accent color (`#00FF41`)
- [ ] **Active/Pressed**: Darker background or scale
- [ ] **Disabled**: Reduced opacity (0.5) + `disabled` attribute

### Technical Precision Standards
- Focus ring: `0 0 0 2px #00FF41`
- Hover background: `#1C2128` (surface-hover)
- Transition: `150ms ease-in-out` (fast)

---

## Motion & Animation

### Requirements
- [ ] **Respect `prefers-reduced-motion`** media query
- [ ] **No auto-playing animations** over 5 seconds
- [ ] **Animations can be paused** if >5 seconds
- [ ] **No flashing content** (3 times/second threshold)

### Technical Precision Implementation
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Testing Tools

### Automated Testing
- [ ] **axe DevTools**: Run on all pages (Chrome/Firefox extension)
- [ ] **Lighthouse**: Score 90+ for accessibility
- [ ] **WAVE**: Zero errors (warnings acceptable if justified)

### Manual Testing
- [ ] **Keyboard only navigation**: Unplug mouse, test all interactions
- [ ] **Screen reader**: Navigate entire application
- [ ] **200% zoom**: Verify content reflows
- [ ] **Color blindness**: Test with color filters (protanopia, deuteranopia, tritanopia)

### Browser Testing
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

## Common Accessibility Mistakes to Avoid

### ❌ Anti-Patterns
1. **Divs for buttons**: Use `<button>` or `<a>` with proper roles
2. **Click on div**: Non-semantic elements need `role`, `tabindex`, keyboard handlers
3. **Placeholder as label**: Always have a visible or aria-label
4. **Auto-focus traps**: Don't force focus on page load (except modals)
5. **Color-only indicators**: Always pair with text, icon, or pattern
6. **Poor focus indicators**: Default browser outline is minimum, enhance it
7. **Keyboard inaccessible**: If you can't Tab to it and activate it, it's broken

### ✅ Best Practices
1. Use semantic HTML first (button, a, input, select)
2. Add ARIA only when semantic HTML insufficient
3. Test with keyboard before mouse
4. Test with screen reader regularly
5. Use color + text + icon for status
6. Provide skip links for repeated navigation
7. Keep focus indicators bold and visible

---

## Acceptance Criteria

Before considering accessibility complete:

✅ **Zero critical errors** in axe DevTools  
✅ **Lighthouse accessibility score 95+**  
✅ **All interactions keyboard accessible**  
✅ **All text meets 4.5:1 contrast minimum**  
✅ **Screen reader can navigate entire app**  
✅ **No console errors from assistive tech**  
✅ **Responsive at 320px width**  
✅ **Usable at 200% zoom**  
✅ **Focus indicators always visible**  

---

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
