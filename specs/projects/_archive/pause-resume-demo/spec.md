# Spec: Pause/Resume Demo Project

## Overview
This is a minimal demonstration project created to validate the Milestone 3 pause/resume workflow with real-world usage. It simulates a simple project lifecycle to exercise status.json functionality.

## Purpose
The purpose of this project is to:
1. Validate that status.json pause/resume workflow works in practice
2. Generate real examples for documentation
3. Ensure CI status visibility works correctly
4. Test agent behavior with different status states

## Acceptance criteria
- [ ] Project can transition through multiple phases
- [ ] Status can be paused with 'blocked' state
- [ ] Status can be resumed with 'active' state
- [ ] On-hold status works as expected
- [ ] show_status.py displays project status correctly
- [ ] All transitions documented with timestamps

## Components & interfaces
- status.json file with valid schema
- Minimal spec documentation (this file)
- Documentation of workflow experience

## Security & privacy notes
None. This is a documentation/validation project only.

## Out of scope
- Actual implementation of any software
- Full agent execution
- Integration with external systems

## References
- tools/validators/show_status.py
- tests/validators/test_pause_resume_workflow.py
- playbooks/handoffs.md
