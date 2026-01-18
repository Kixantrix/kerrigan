// Code Viewer Functionality

(function() {
  'use strict';

  // Constants
  const FEEDBACK_TIMEOUT = 2000; // Time in ms to display copy feedback before reverting

  // Toggle code visibility
  function toggleCode(button) {
    const targetId = button.dataset.target;
    const codeBlock = document.getElementById(targetId);
    
    if (!codeBlock) return;
    
    const isVisible = codeBlock.style.display !== 'none';
    
    if (isVisible) {
      codeBlock.style.display = 'none';
      button.textContent = 'View Code';
      button.setAttribute('aria-expanded', 'false');
    } else {
      codeBlock.style.display = 'block';
      button.textContent = 'Hide Code';
      button.setAttribute('aria-expanded', 'true');
      
      // Add copy button if not already present
      addCopyButton(codeBlock);
      
      // Move focus to the copy button for keyboard accessibility
      const copyBtn = codeBlock.querySelector('.copy-btn');
      if (copyBtn) {
        copyBtn.focus();
      }
    }
  }

  // Add copy button to code block
  function addCopyButton(codeBlock) {
    // Check if copy button already exists
    if (codeBlock.querySelector('.copy-btn')) return;
    
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.setAttribute('aria-label', 'Copy code to clipboard');
    
    copyBtn.addEventListener('click', () => {
      copyCode(codeBlock, copyBtn);
    });
    
    // Make code block relative positioned for absolute button
    codeBlock.style.position = 'relative';
    codeBlock.insertBefore(copyBtn, codeBlock.firstChild);
  }

  // Copy code to clipboard
  async function copyCode(codeBlock, button) {
    const code = codeBlock.querySelector('code');
    if (!code) return;
    
    const text = code.textContent;
    
    try {
      // Modern clipboard API (requires HTTPS or localhost)
      // For HTTP development, the fallback method will be used automatically
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        showCopySuccess(button);
      } else {
        // Fallback for older browsers or non-secure contexts (HTTP)
        fallbackCopyToClipboard(text);
        showCopySuccess(button);
      }
    } catch (err) {
      console.error('Failed to copy code:', err);
      showCopyError(button);
    }
  }

  // Fallback copy method
  function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.setAttribute('readonly', '');
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
      document.execCommand('copy');
    } finally {
      document.body.removeChild(textArea);
    }
  }

  // Show success feedback
  function showCopySuccess(button) {
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    button.classList.add('copy-btn--success');
    
    setTimeout(() => {
      button.textContent = originalText;
      button.classList.remove('copy-btn--success');
    }, FEEDBACK_TIMEOUT);
  }

  // Show error feedback
  function showCopyError(button) {
    const originalText = button.textContent;
    button.textContent = 'Failed';
    button.classList.add('copy-btn--error');
    
    setTimeout(() => {
      button.textContent = originalText;
      button.classList.remove('copy-btn--error');
    }, FEEDBACK_TIMEOUT);
  }

  // Initialize code viewer
  function init() {
    // Add click handlers to all code toggle buttons
    const toggleButtons = document.querySelectorAll('.code-toggle');
    
    toggleButtons.forEach(button => {
      button.setAttribute('aria-expanded', 'false');
      button.addEventListener('click', () => {
        toggleCode(button);
      });
    });
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
