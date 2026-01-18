// Navigation Functionality

(function() {
  'use strict';

  // Constants
  const NAV_SCROLL_OFFSET = 100; // Offset in pixels to account for sticky nav height
  const HASH_SCROLL_DELAY = 100; // Delay in ms for hash navigation to complete before scrolling
  
  // Throttle helper for scroll events
  let scrollThrottleTimer;
  const throttle = (callback, delay) => {
    if (scrollThrottleTimer) return;
    scrollThrottleTimer = setTimeout(() => {
      callback();
      scrollThrottleTimer = null;
    }, delay);
  };

  // Smooth scroll to sections
  function scrollToSection(sectionId) {
    const section = document.querySelector(sectionId);
    if (!section) return;
    
    // Smooth scroll to section
    section.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }

  // Update active nav link
  function updateActiveLink() {
    const sections = document.querySelectorAll('.section');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let currentSection = '';
    
    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      
      if (window.scrollY >= sectionTop - NAV_SCROLL_OFFSET) {
        currentSection = section.getAttribute('id');
      }
    });
    
    navLinks.forEach(link => {
      link.classList.remove('active');
      
      if (link.getAttribute('href') === `#${currentSection}`) {
        link.classList.add('active');
      }
    });
  }

  // Toggle mobile menu
  function toggleMobileMenu() {
    const navLinks = document.getElementById('nav-links');
    navLinks.classList.toggle('open');
  }

  // Close mobile menu when clicking outside
  function closeMobileMenuOnClickOutside(event) {
    const navLinks = document.getElementById('nav-links');
    const menuToggle = document.getElementById('mobile-menu-toggle');
    
    // Only close if menu is open
    if (navLinks.classList.contains('open') && 
        !navLinks.contains(event.target) && 
        !menuToggle.contains(event.target)) {
      navLinks.classList.remove('open');
    }
  }

  // Initialize navigation
  function init() {
    // Add smooth scroll to nav links
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = link.getAttribute('href');
        scrollToSection(targetId);
        
        // Close mobile menu after clicking
        const navLinksContainer = document.getElementById('nav-links');
        navLinksContainer.classList.remove('open');
        
        // Update URL hash without jumping
        history.pushState(null, null, targetId);
      });
    });
    
    // Mobile menu toggle
    const menuToggle = document.getElementById('mobile-menu-toggle');
    if (menuToggle) {
      menuToggle.addEventListener('click', toggleMobileMenu);
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', closeMobileMenuOnClickOutside);
    
    // Update active link on scroll with throttling for performance
    window.addEventListener('scroll', () => {
      throttle(updateActiveLink, 100);
    });
    
    // Initial active link update
    updateActiveLink();
    
    // Check for hash in URL on load
    if (window.location.hash) {
      setTimeout(() => {
        scrollToSection(window.location.hash);
      }, HASH_SCROLL_DELAY);
    }
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
