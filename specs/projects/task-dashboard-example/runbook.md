# Runbook: Task Dashboard Example

## Overview

The Task Dashboard Example is a static design system playground that demonstrates the Technical Precision design system. It consists of HTML/CSS/JavaScript files that can be viewed directly in a browser.

## How to Deploy

### Local Viewing (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Kixantrix/kerrigan.git
   cd kerrigan
   ```

2. **Navigate to playground**:
   ```bash
   cd specs/projects/task-dashboard-example/design-system/playground
   ```

3. **Open in browser**:
   - **macOS**: `open index.html`
   - **Linux**: `xdg-open index.html`
   - **Windows**: `start index.html`
   - **Any OS**: Double-click `index.html` in file explorer

4. **Verify**:
   - Page loads without errors
   - All components are visible
   - Open browser console (F12) to check for errors

### Web Server (Optional)

If you need to serve over HTTP (e.g., for testing CORS):

```bash
# Using Python 3
cd specs/projects/task-dashboard-example/design-system/playground
python3 -m http.server 8000

# Using Node.js (http-server)
npm install -g http-server
cd specs/projects/task-dashboard-example/design-system/playground
http-server -p 8000

# Using PHP
cd specs/projects/task-dashboard-example/design-system/playground
php -S localhost:8000
```

Then open: `http://localhost:8000`

### GitHub Pages (Optional)

To host publicly:

1. **Enable GitHub Pages** in repository settings
2. **Select source**: main branch, `/specs/projects/task-dashboard-example/design-system/playground` folder (requires moving to root or docs/)
3. **Alternative**: Copy playground files to `docs/` or root and enable Pages

Note: This is an example/demo, not intended for production hosting.

## How to Operate

### Normal Operation

**There is no "operation" required**—this is a static playground.

**Daily Tasks**: None  
**Monitoring**: None  
**Maintenance**: None

### Using the Playground

**View Components**:
- Scroll through page to see all components
- Token visualization at top
- Each component has its own section

**Interactive Features**:
- Click DataTable headers to sort
- Press `Cmd+K` (Mac) or `Ctrl+K` (Windows) to open CommandBar
- Check TaskRow checkboxes to select
- Use keyboard navigation (Tab, Arrow keys)

**Testing Changes**:
1. Edit `components.css` to change styles
2. Edit `demo-data.js` to change data or behavior
3. Refresh browser to see changes

## How to Debug

### Common Issues

#### Issue: Playground doesn't load
**Symptoms**: Blank page or error message  
**Diagnosis**:
1. Open browser console (F12)
2. Check for JavaScript errors
3. Check for CSS loading errors

**Solutions**:
- Verify all files present (index.html, components.css, demo-data.js)
- Check file paths in HTML (should be relative)
- Ensure browser supports ES6 JavaScript
- Try different browser

#### Issue: Components don't display correctly
**Symptoms**: Layout broken, missing styles  
**Diagnosis**:
1. Check CSS file loaded (Network tab in DevTools)
2. Check CSS custom properties supported (no IE11)
3. Verify CSS syntax

**Solutions**:
- Check browser compatibility (modern browsers only)
- Inspect element to see computed styles
- Look for CSS syntax errors in console

#### Issue: Interactive features don't work
**Symptoms**: CommandBar won't open, table won't sort  
**Diagnosis**:
1. Check JavaScript console for errors
2. Verify demo-data.js loaded
3. Check event listeners attached

**Solutions**:
- Reload page
- Check JavaScript syntax in demo-data.js
- Verify DOM elements exist before JS runs

#### Issue: Keyboard navigation not working
**Symptoms**: Can't Tab through elements, arrow keys don't work  
**Diagnosis**:
1. Check focus on page (click page first)
2. Verify tabindex attributes
3. Check keyboard event listeners

**Solutions**:
- Click page to give it focus
- Check that elements are focusable (tabindex="0")
- Verify JavaScript event handlers attached

### Debugging Tools

**Browser DevTools**:
- **Console**: Check for JavaScript errors
- **Elements**: Inspect HTML and CSS
- **Network**: Verify files loaded
- **Sources**: Debug JavaScript

**Accessibility Tools**:
- **axe DevTools**: Check accessibility issues
- **Lighthouse**: Run audit
- **Screen reader**: Test with NVDA or VoiceOver

### Logs

**No server logs** (static site)  
**Browser console**: Only place for debugging output

## Oncall / Incident Basics

**This is a static example—there is no oncall or incident response.**

If the playground is hosted and becomes unavailable:
1. Check if web server is running
2. Check if files are accessible
3. Restart web server if needed
4. No data to lose, no state to maintain

## Configuration

### Changing Design Tokens

Edit CSS custom properties in `components.css`:

```css
:root {
  --color-primary: #00FF41;  /* Change this */
  --color-background: #0D1117;  /* Or this */
  /* etc. */
}
```

Save and refresh browser to see changes.

### Changing Sample Data

Edit the `tasks` array in `demo-data.js`:

```javascript
const tasks = [
  { id: 'TASK-123', title: 'Fix login bug', ... },
  // Add, remove, or modify tasks here
];
```

Save and refresh browser to see changes.

### Adding New Components

1. Add HTML to `index.html`
2. Add styles to `components.css`
3. Add JavaScript (if needed) to `demo-data.js`
4. Refresh browser

## Monitoring

**Not applicable**—this is a static example with no monitoring requirements.

If hosted:
- Monitor web server uptime (if applicable)
- Monitor HTTP errors (if using analytics)
- No application metrics needed

## Backup & Recovery

**No backup needed**—all files in Git repository.

**Recovery**: Clone repository again.

## Dependencies

### External Dependencies
- None (vanilla HTML/CSS/JS)

### Browser Requirements
- Modern browser with ES6 support
- CSS custom properties support
- No IE11 support

### Font Dependencies
- JetBrains Mono (loaded from CDN or system fallback)
- Fallbacks: Consolas, Monaco, Courier New, monospace

## Performance

### Expected Performance
- Load time: < 2 seconds
- Page size: ~50KB (HTML + CSS + JS)
- No external requests (except fonts)

### Performance Issues

**Slow loading**:
- Check network tab in DevTools
- Verify no external resources timing out
- Check large CSS/JS files

**Sluggish interactions**:
- Check JavaScript performance in DevTools
- Verify no infinite loops
- Check for memory leaks (unlikely in this simple example)

## Security

### Security Considerations

**No security risks**—static HTML with no:
- User input processing
- Server communication
- Data persistence
- External API calls

**Content Security Policy** (optional):
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; style-src 'self' 'unsafe-inline';">
```

## Access Control

**Not applicable**—playground is meant to be publicly accessible.

If hosting internally:
- Use standard web server access controls
- Basic auth if needed
- No application-level authentication

## Disaster Recovery

**Recovery Time Objective (RTO)**: N/A (static example)  
**Recovery Point Objective (RPO)**: N/A (no data to lose)

**Recovery Process**:
1. Re-clone repository
2. Open index.html
3. Done

## Contact Information

**Oncall**: None (static example)  
**Escalation**: N/A  
**Repository**: https://github.com/Kixantrix/kerrigan  
**Documentation**: See design-system/ directory for all specs

## Changelog

- 2026-01-18: Initial creation of runbook
- Future: Updates as playground evolves
