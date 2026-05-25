// Theme Toggle Functionality

(function() {
  'use strict';

  const THEME_KEY = 'design-system-theme';
  const THEME_LIGHT = 'light';
  const THEME_DARK = 'dark';

  // Get theme toggle button
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = themeToggle.querySelector('.theme-icon');

  // Get current theme from localStorage or default to light
  function getCurrentTheme() {
    return localStorage.getItem(THEME_KEY) || THEME_LIGHT;
  }

  // Apply theme to document
  function applyTheme(theme) {
    if (theme === THEME_DARK) {
      document.documentElement.setAttribute('data-theme', 'dark');
      themeIcon.textContent = '☀️';
      themeToggle.setAttribute('aria-label', 'Switch to light mode');
    } else {
      document.documentElement.removeAttribute('data-theme');
      themeIcon.textContent = '🌙';
      themeToggle.setAttribute('aria-label', 'Switch to dark mode');
    }
  }

  // Toggle theme
  function toggleTheme() {
    const currentTheme = getCurrentTheme();
    const newTheme = currentTheme === THEME_LIGHT ? THEME_DARK : THEME_LIGHT;
    
    // Save to localStorage
    localStorage.setItem(THEME_KEY, newTheme);
    
    // Apply theme
    applyTheme(newTheme);
    
    // Announce to screen readers
    announceThemeChange(newTheme);
  }

  // Announce theme change for accessibility
  function announceThemeChange(theme) {
    const ANNOUNCEMENT_REMOVAL_DELAY = 1000; // Time in ms before removing announcement from DOM
    
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = `Theme changed to ${theme} mode`;
    document.body.appendChild(announcement);
    
    // Remove announcement after brief delay
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, ANNOUNCEMENT_REMOVAL_DELAY);
  }

  // Initialize theme on page load
  function init() {
    const savedTheme = getCurrentTheme();
    applyTheme(savedTheme);
    
    // Add event listener to toggle button
    themeToggle.addEventListener('click', toggleTheme);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
