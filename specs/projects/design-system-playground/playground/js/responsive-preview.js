// Responsive Preview Functionality

(function() {
  'use strict';

  // Get layout max-width from CSS custom property
  const getMaxWidth = () => {
    return getComputedStyle(document.documentElement)
      .getPropertyValue('--layout-max-width').trim();
  };

  // Get viewport width from CSS custom property with a fallback
  const getViewportWidth = (varName, fallback) => {
    const value = getComputedStyle(document.documentElement)
      .getPropertyValue(varName)
      .trim();
    return value || fallback;
  };

  // Define viewport sizes - read from CSS tokens if available
  const mobileWidth = getViewportWidth('--viewport-mobile-width', '375px');
  const tabletWidth = getViewportWidth('--viewport-tablet-width', '768px');

  const viewportSizes = {
    mobile: { width: mobileWidth, label: `Mobile (${mobileWidth})` },
    tablet: { width: tabletWidth, label: `Tablet (${tabletWidth})` },
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
    
    // Apply visual indicator by setting individual style properties
    if (viewport === 'mobile' || viewport === 'tablet') {
      mainContent.style.maxWidth = size.width;
      mainContent.style.marginLeft = 'auto';
      mainContent.style.marginRight = 'auto';
      mainContent.style.border = '1px solid var(--color-border)';
      mainContent.style.transition = 'all var(--transition-base) ease';
    } else {
      const maxWidth = getMaxWidth();
      mainContent.style.maxWidth = maxWidth;
      mainContent.style.marginLeft = '';
      mainContent.style.marginRight = '';
      mainContent.style.border = 'none';
      mainContent.style.transition = '';
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
