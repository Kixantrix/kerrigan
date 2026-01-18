// Responsive Preview Functionality

(function() {
  'use strict';

  // Get layout max-width from CSS custom property
  const getMaxWidth = () => {
    return getComputedStyle(document.documentElement)
      .getPropertyValue('--layout-max-width').trim();
  };

  const viewportSizes = {
    mobile: { width: '375px', label: 'Mobile (375px)' },
    tablet: { width: '768px', label: 'Tablet (768px)' },
    desktop: { width: '', label: 'Desktop (1200px)' } // Empty width means use max-width
  };

  let currentViewport = 'desktop';

  // Get viewport controls
  const viewportButtons = document.querySelectorAll('.viewport-btn');
  const viewportInfo = document.getElementById('current-viewport');
  const mainContent = document.querySelector('.playground-content');

  // Apply viewport size
  function applyViewport(viewport) {
    currentViewport = viewport;
    const size = viewportSizes[viewport];
    
    // Update active button
    viewportButtons.forEach(btn => {
      if (btn.dataset.viewport === viewport) {
        btn.classList.add('active');
        btn.setAttribute('aria-pressed', 'true');
      } else {
        btn.classList.remove('active');
        btn.setAttribute('aria-pressed', 'false');
      }
    });
    
    // Update viewport info display
    if (viewportInfo) {
      viewportInfo.textContent = size.label;
    }
    
    // Apply visual indicator (max-width to main content)
    if (viewport === 'mobile' || viewport === 'tablet') {
      mainContent.style.cssText = `
        max-width: ${size.width};
        margin-left: auto;
        margin-right: auto;
        border: 1px solid var(--color-border);
        transition: all 0.3s ease;
      `;
    } else {
      const maxWidth = getMaxWidth();
      mainContent.style.cssText = `
        max-width: ${maxWidth};
        border: none;
      `;
    }
  }

  // Initialize responsive preview
  function init() {
    // Add click handlers to viewport buttons
    viewportButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const viewport = btn.dataset.viewport;
        applyViewport(viewport);
      });
    });
    
    // Set initial viewport
    applyViewport('desktop');
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
