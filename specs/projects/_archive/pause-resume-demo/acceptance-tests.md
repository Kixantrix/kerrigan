# Acceptance Tests: Pause/Resume Demo

## Test scenarios

### Scenario 1: Initial active state
**Given** a new project with status.json set to "active"  
**When** show_status.py is run  
**Then** the project appears with green emoji (🟢) and ACTIVE status

### Scenario 2: Pause with blocked status
**Given** status.json is updated to "blocked" with a reason  
**When** show_status.py is run  
**Then** the project appears with red emoji (🔴), BLOCKED status, and displays the blocked reason

### Scenario 3: Resume after blocked
**Given** status.json is updated back to "active"  
**When** show_status.py is run  
**Then** the project appears with green emoji (🟢) and ACTIVE status again

### Scenario 4: On-hold status
**Given** status.json is set to "on-hold"  
**When** show_status.py is run  
**Then** the project appears with yellow emoji (🟡) and ON-HOLD status

### Scenario 5: Phase transitions
**Given** status.json current_phase is updated  
**When** show_status.py is run  
**Then** the displayed phase reflects the new value

## Verification method
All tests are validated by:
1. Manual execution of show_status.py
2. Visual inspection of output
3. Documentation of results in playbooks/handoffs.md
