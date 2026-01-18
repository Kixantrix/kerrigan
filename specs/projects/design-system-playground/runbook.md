# Runbook: Design System Playground

## Overview

The Design System Playground is a static web application for exploring and testing design system components and tokens. This runbook provides instructions for deployment, usage, and maintenance.

## Quick Start

### Local Development

1. **Navigate to playground directory**:
   ```bash
   cd specs/projects/design-system-playground/playground/
   ```

2. **Open in browser**:
   - Double-click `index.html`, or
   - Use a local server:
     ```bash
     python -m http.server 8000
     # or
     npx serve
     ```
   - Open `http://localhost:8000`

3. **Make changes**:
   - Edit HTML, CSS, or JS files
   - Refresh browser to see changes
   - No build step required

## Deployment

### GitHub Pages

1. **Push to repository**:
   ```bash
   git add .
   git commit -m "Update playground"
   git push
   ```

2. **Enable GitHub Pages**:
   - Go to repository Settings > Pages
   - Select branch and `/specs/projects/design-system-playground/playground/` folder
   - Save

3. **Access playground**:
   - URL: `https://<username>.github.io/<repo>/specs/projects/design-system-playground/playground/`

### Netlify

1. **Connect repository**:
   - Sign in to Netlify
   - Click "New site from Git"
   - Select repository

2. **Configure build**:
   - Base directory: `specs/projects/design-system-playground/playground/`
   - Build command: (leave empty)
   - Publish directory: `/`

3. **Deploy**:
   - Click "Deploy site"
   - Get custom URL or configure domain

### Static File Hosting (S3, CDN)

1. **Upload files**:
   - Upload entire `playground/` directory
   - Ensure `index.html` is the root file

2. **Configure**:
   - Set content types (HTML, CSS, JS)
   - Enable gzip compression
   - Add cache headers

3. **Access**:
   - URL: Based on hosting provider

## Usage Guide

### For Developers

**Viewing Components**:
1. Open playground in browser
2. Navigate to "Components" section
3. Browse available components
4. Click component to view code
5. Copy code using copy button

**Using Tokens**:
1. Navigate to "Tokens" section
2. View color palette, typography, spacing
3. Note token names (e.g., `--color-primary`)
4. Use tokens in your CSS

**Testing Themes**:
1. Click theme toggle button in header
2. Observe component appearance in dark mode
3. Theme preference saved automatically

**Responsive Testing**:
1. Use viewport size buttons (mobile/tablet/desktop)
2. Or resize browser window
3. Components adapt to screen size

### For Designers

**Component Reference**:
- Use as visual reference for designs
- Check component states (hover, focus, disabled)
- Verify color contrast and spacing

**Token Reference**:
- Use token values in design tools
- Maintain consistency across designs
- Share tokens with developers

## Maintenance

### Adding New Components

1. **Create component HTML** in `index.html`:
   ```html
   <div class="component-card">
     <h3>Component Name</h3>
     <p>Description</p>
     <div class="component-preview">
       <!-- Component example -->
     </div>
     <pre class="component-code">
       <!-- Component HTML -->
     </pre>
   </div>
   ```

2. **Add component styles** in `css/components.css`:
   ```css
   .new-component {
     /* styles */
   }
   ```

3. **Test**:
   - View in browser
   - Check both themes
   - Verify responsive behavior

### Updating Tokens

1. **Edit** `css/tokens.css`:
   ```css
   :root {
     --color-new: #value;
   }
   ```

2. **Update token display** in `index.html`:
   ```html
   <div class="token-swatch" style="background: var(--color-new);">
     <span>--color-new</span>
     <span>#value</span>
   </div>
   ```

3. **Test**:
   - Verify color displays correctly
   - Check in both themes

### Updating Theme

1. **Edit dark theme** in `css/tokens.css`:
   ```css
   [data-theme="dark"] {
     --color-name: #dark-value;
   }
   ```

2. **Test**:
   - Toggle theme
   - Verify colors are readable
   - Check contrast ratios

## Troubleshooting

### Playground Not Loading

**Symptom**: Blank page or errors

**Solution**:
1. Check browser console for errors
2. Verify all CSS/JS files are linked correctly
3. Check file paths (case-sensitive on some servers)
4. Ensure MIME types are set correctly

### Theme Not Switching

**Symptom**: Theme toggle doesn't work

**Solution**:
1. Check `theme-toggle.js` is loaded
2. Verify localStorage is enabled in browser
3. Check console for JavaScript errors
4. Clear browser cache and reload

### Code Copy Not Working

**Symptom**: Copy button doesn't copy code

**Solution**:
1. Check browser clipboard permissions
2. Use HTTPS (clipboard API requires secure context)
3. Verify `code-viewer.js` is loaded correctly

### Styles Not Applying

**Symptom**: Components look unstyled

**Solution**:
1. Check CSS files are linked in correct order
2. Verify CSS custom properties are defined
3. Check for CSS syntax errors
4. Clear browser cache

### Responsive Preview Not Working

**Symptom**: Viewport buttons don't resize components

**Solution**:
1. Check `responsive-preview.js` is loaded
2. Verify CSS is responsive (uses media queries or percentage widths)
3. Check console for JavaScript errors

## Performance Optimization

### Loading Speed

- Minify CSS and JS files
- Inline critical CSS in `<head>`
- Defer non-critical JavaScript
- Enable gzip compression on server

### Browser Caching

Add to server configuration:
```
Cache-Control: public, max-age=31536000
```

For static assets (CSS, JS).

### Image Optimization

If images added in future:
- Use WebP format
- Compress images
- Lazy load images

## Security

### Content Security Policy

Add to `index.html` `<head>`:
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self';">
```

### HTTPS

Always serve over HTTPS in production:
- Prevents man-in-the-middle attacks
- Required for clipboard API
- Improves SEO

## Monitoring

### Analytics (Optional)

Add Google Analytics or similar:
```html
<!-- Analytics code -->
```

### Error Tracking

Add error tracking:
```javascript
window.onerror = function(msg, url, line) {
  // Send to logging service
};
```

## Backup and Recovery

### Version Control

- All files in Git repository
- Tag releases: `git tag -a v1.0.0 -m "Release v1.0.0"`
- Push tags: `git push --tags`

### Rollback

```bash
git revert <commit-hash>
# or
git reset --hard <previous-commit>
```

## Support

### Common Questions

**Q: Can I use this playground with my framework?**
A: Yes, copy the HTML/CSS and adapt to your framework's syntax.

**Q: How do I add my own components?**
A: Follow "Adding New Components" section above.

**Q: Can I customize the theme?**
A: Yes, edit CSS custom properties in `tokens.css`.

**Q: Is this accessible?**
A: Yes, built with accessibility in mind. ARIA labels and keyboard navigation included.

### Contact

For issues or questions:
- Open GitHub issue
- Check documentation in `/specs/projects/design-system-playground/`
- Review code comments in source files

## Changelog

### v1.0.0 (Initial Release)
- Core playground infrastructure
- Token visualization
- Component gallery
- Theme toggle
- Code viewer
- Responsive preview
