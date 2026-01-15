# Processed Feedback Directory

This directory contains feedback that has been reviewed and acted upon by the Kerrigan agent.

## Structure

Feedback files are moved here from `../agent-feedback/` after review and action.

## Status Values

- **reviewed**: Feedback has been reviewed and categorized
- **implemented**: Changes have been made to address the feedback
- **wont_fix**: Feedback noted but no changes planned (with explanation in notes)

## Archive Organization

Files maintain their original names but include updated metadata:
- `status`: Updated to reflect current state
- `reviewed_by`: GitHub username of reviewer
- `reviewed_date`: When feedback was reviewed
- `implementation_pr`: PR number where fix was implemented (if applicable)
- `notes`: Summary of actions taken

## Learning from History

This directory serves as a knowledge base of:
- Common issues and their solutions
- Patterns in agent friction points
- Successful improvements made
- Evolution of the Kerrigan system

## Example

```yaml
# Original feedback from agent
timestamp: "2026-01-15T10:00:00Z"
issue_number: 42
agent_role: "swe"
category: "prompt_clarity"
severity: "high"
title: "Validator heading names not specified in prompt"
description: |
  The role.swe.md prompt doesn't mention that validators expect
  exact heading names (case-sensitive). I spent 20 minutes debugging
  why "Acceptance Criteria" failed validation when it should be
  "Acceptance criteria".

# Added during processing
status: "implemented"
reviewed_by: "kerrigan-agent"
reviewed_date: "2026-01-16T09:00:00Z"
implementation_pr: 44
notes: |
  Updated role.swe.md with specific heading examples.
  Also updated handoffs.md to document this learning.
  Cross-checked other agent prompts for same issue.
```
