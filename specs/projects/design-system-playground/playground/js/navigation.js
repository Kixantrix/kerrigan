// Navigation Functionality

(function() {
  'use strict';

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
      const sectionHeight = section.clientHeight;
      
      if (window.pageYOffset >= sectionTop - 100) {
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
    
    if (!navLinks.contains(event.target) && !menuToggle.contains(event.target)) {
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
    
    // Update active link on scroll
    window.addEventListener('scroll', updateActiveLink);
    
    // Initial active link update
    updateActiveLink();
    
    // Check for hash in URL on load
    if (window.location.hash) {
      setTimeout(() => {
        scrollToSection(window.location.hash);
      }, 100);
    }
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
