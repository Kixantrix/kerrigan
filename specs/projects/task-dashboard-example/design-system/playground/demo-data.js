// Demo Data and Interactive Functionality for Technical Precision Design System Playground

// Sample task data
const tasks = [
  { id: 'TASK-123', title: 'Fix login bug', status: 'in-progress', assignee: 'Alice', due: '2026-01-20' },
  { id: 'TASK-124', title: 'Update documentation', status: 'todo', assignee: 'Bob', due: '2026-01-22' },
  { id: 'TASK-125', title: 'Deploy to production', status: 'done', assignee: 'Charlie', due: '2026-01-18' },
  { id: 'TASK-126', title: 'Code review PR #456', status: 'in-progress', assignee: 'Alice', due: '2026-01-19' },
  { id: 'TASK-127', title: 'Update dependencies', status: 'todo', assignee: 'Bob', due: '2026-01-25' },
  { id: 'TASK-128', title: 'Fix database migration', status: 'blocked', assignee: 'David', due: '2026-01-21' },
  { id: 'TASK-129', title: 'Implement search feature', status: 'in-progress', assignee: 'Eve', due: '2026-01-23' },
  { id: 'TASK-130', title: 'Write unit tests', status: 'todo', assignee: 'Frank', due: '2026-01-24' },
];

// Status badge HTML generator
function createStatusBadge(status) {
  const statusMap = {
    'todo': 'todo',
    'in-progress': 'in-progress',
    'done': 'done',
    'blocked': 'blocked'
  };
  
  const statusClass = statusMap[status] || 'todo';
  const statusLabel = status.replace('-', ' ');
  
  return `
    <span class="status-badge status-badge--${statusClass}" role="status" aria-label="Task status: ${statusLabel}">
      <span class="status-badge__dot"></span>
      ${status}
    </span>
  `;
}

// Populate DataTable
function populateDataTable() {
  const tableBody = document.getElementById('table-body');
  if (!tableBody) return;
  
  tableBody.innerHTML = tasks.map(task => `
    <div class="data-table__row" role="row" tabindex="0" data-task-id="${task.id}">
      <div class="data-table__cell" role="cell">${task.id}</div>
      <div class="data-table__cell" role="cell">${task.title}</div>
      <div class="data-table__cell" role="cell">${createStatusBadge(task.status)}</div>
      <div class="data-table__cell" role="cell">${task.assignee}</div>
      <div class="data-table__cell" role="cell">${task.due}</div>
    </div>
  `).join('');
  
  // Add keyboard navigation
  addTableKeyboardNavigation();
}

// DataTable sorting functionality
let currentSort = { column: null, direction: 'none' };

function sortTable(column, direction) {
  if (direction === 'none') return;
  
  const sortedTasks = [...tasks].sort((a, b) => {
    const aVal = a[column];
    const bVal = b[column];
    
    if (direction === 'ascending') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });
  
  const tableBody = document.getElementById('table-body');
  if (!tableBody) return;
  
  tableBody.innerHTML = sortedTasks.map(task => `
    <div class="data-table__row" role="row" tabindex="0" data-task-id="${task.id}">
      <div class="data-table__cell" role="cell">${task.id}</div>
      <div class="data-table__cell" role="cell">${task.title}</div>
      <div class="data-table__cell" role="cell">${createStatusBadge(task.status)}</div>
      <div class="data-table__cell" role="cell">${task.assignee}</div>
      <div class="data-table__cell" role="cell">${task.due}</div>
    </div>
  `).join('');
  
  addTableKeyboardNavigation();
}

// Add sorting to table headers
function initTableSorting() {
  document.querySelectorAll('.data-table__cell--header').forEach(header => {
    header.addEventListener('click', () => {
      const column = header.getAttribute('data-column');
      const currentSortState = header.getAttribute('aria-sort');
      
      let newSort;
      if (currentSortState === 'none' || currentSortState === 'descending') {
        newSort = 'ascending';
      } else {
        newSort = 'descending';
      }
      
      // Clear other headers
      document.querySelectorAll('.data-table__cell--header').forEach(h => {
        h.setAttribute('aria-sort', 'none');
      });
      
      // Set new sort
      header.setAttribute('aria-sort', newSort);
      currentSort = { column, direction: newSort };
      
      // Sort table
      sortTable(column, newSort);
    });
  });
}

// Keyboard navigation for table rows
function addTableKeyboardNavigation() {
  const rows = document.querySelectorAll('.data-table__body .data-table__row');
  
  rows.forEach((row, index) => {
    row.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' && index < rows.length - 1) {
        e.preventDefault();
        rows[index + 1].focus();
      } else if (e.key === 'ArrowUp' && index > 0) {
        e.preventDefault();
        rows[index - 1].focus();
      } else if (e.key === 'Home') {
        e.preventDefault();
        rows[0].focus();
      } else if (e.key === 'End') {
        e.preventDefault();
        rows[rows.length - 1].focus();
      }
    });
  });
}

// CommandBar functionality
let commandBarOpen = false;
let focusedCommandIndex = -1;

function openCommandBar() {
  const commandBar = document.getElementById('command-bar');
  const commandInput = document.getElementById('command-input');
  
  if (!commandBar || !commandInput) return;
  
  commandBar.classList.add('command-bar--open');
  commandInput.focus();
  commandInput.setAttribute('aria-expanded', 'true');
  commandBarOpen = true;
  focusedCommandIndex = -1;
}

function closeCommandBar() {
  const commandBar = document.getElementById('command-bar');
  const commandInput = document.getElementById('command-input');
  
  if (!commandBar || !commandInput) return;
  
  commandBar.classList.remove('command-bar--open');
  commandInput.value = '';
  commandInput.setAttribute('aria-expanded', 'false');
  commandBarOpen = false;
  focusedCommandIndex = -1;
  
  // Clear focused state from commands
  document.querySelectorAll('.command-bar__item').forEach(item => {
    item.classList.remove('command-bar__item--focused');
  });
}

function executeCommand(command) {
  console.log('Executing command:', command);
  alert(`Command executed: ${command}`);
  closeCommandBar();
}

// Initialize CommandBar
function initCommandBar() {
  const commandBar = document.getElementById('command-bar');
  const commandInput = document.getElementById('command-input');
  const backdrop = document.querySelector('.command-bar__backdrop');
  const openButton = document.getElementById('open-command-bar');
  
  if (!commandBar || !commandInput || !backdrop) return;
  
  // Open command bar button
  if (openButton) {
    openButton.addEventListener('click', openCommandBar);
  }
  
  // Keyboard shortcut to open
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      openCommandBar();
    }
  });
  
  // Close on backdrop click
  backdrop.addEventListener('click', closeCommandBar);
  
  // Escape to close
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && commandBarOpen) {
      closeCommandBar();
    }
  });
  
  // Command navigation with arrow keys
  commandInput.addEventListener('keydown', (e) => {
    const commands = document.querySelectorAll('.command-bar__item');
    
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      focusedCommandIndex = Math.min(focusedCommandIndex + 1, commands.length - 1);
      updateFocusedCommand(commands);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      focusedCommandIndex = Math.max(focusedCommandIndex - 1, -1);
      updateFocusedCommand(commands);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (focusedCommandIndex >= 0 && focusedCommandIndex < commands.length) {
        const command = commands[focusedCommandIndex].getAttribute('data-command');
        executeCommand(command);
      }
    }
  });
  
  // Click on command
  document.querySelectorAll('.command-bar__item').forEach(item => {
    item.addEventListener('click', () => {
      const command = item.getAttribute('data-command');
      executeCommand(command);
    });
  });
  
  // Filter commands based on input
  commandInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    document.querySelectorAll('.command-bar__item').forEach(item => {
      const label = item.querySelector('.command-bar__item-label').textContent.toLowerCase();
      if (label.includes(query)) {
        item.style.display = 'flex';
      } else {
        item.style.display = 'none';
      }
    });
  });
}

function updateFocusedCommand(commands) {
  commands.forEach((cmd, index) => {
    if (index === focusedCommandIndex) {
      cmd.classList.add('command-bar__item--focused');
      cmd.scrollIntoView({ block: 'nearest' });
    } else {
      cmd.classList.remove('command-bar__item--focused');
    }
  });
}

// TaskRow checkbox functionality
function initTaskRows() {
  document.querySelectorAll('.task-row__checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      const row = e.target.closest('.task-row');
      if (e.target.checked) {
        row.classList.add('task-row--selected');
      } else {
        row.classList.remove('task-row--selected');
      }
    });
  });
}

// Initialize everything on page load
document.addEventListener('DOMContentLoaded', () => {
  populateDataTable();
  initTableSorting();
  initCommandBar();
  initTaskRows();
  
  console.log('Technical Precision Design System Playground loaded');
  console.log('Press ⌘K (Mac) or Ctrl+K (Windows/Linux) to open the command bar');
});
