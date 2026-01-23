# Project-Specific Skills Example

This example demonstrates how to configure and use project-specific skills in a Python API project.

**Note**: This example shows the configuration structure. Stack-specific skills (like `stacks/python/testing-pytest`) will be available once they are manually curated from authoritative sources following the process in SKILLS-REGISTRY.md.

## Project Structure

```
specs/projects/my-python-api/
├── spec.md
├── architecture.md
├── plan.md
├── tasks.md
├── skills.json                 # Skills configuration
└── skills/                     # Optional: project-specific skills
    └── api-conventions.md
```

## Step 1: Create Skills Configuration

**specs/projects/my-python-api/skills.json:**
```json
{
  "version": "1.0",
  "description": "Skills for the Python API Gateway project",
  "universal_skills": [
    "meta/artifact-contracts",
    "meta/agent-handoffs",
    "meta/quality-bar"
  ],
  "stack_skills": [
    # Future: Add manually curated stack skills here when available
    # "stacks/python/testing-pytest"
  ],
  "project_skills": [
    "skills/api-conventions"
  ],
  "auto_detect": true
}
```

## Step 2: Create Project-Specific Skill (Optional)

**specs/projects/my-python-api/skills/api-conventions.md:**
```markdown
---
title: API Gateway Error Response Format
version: 1.0.0
source: Project-specific
quality_tier: 3
last_reviewed: 2026-01-23
last_updated: 2026-01-23
reviewed_by: api-team
license: MIT
tags: [api, errors, conventions, project-specific]
applies_to: [my-python-api]
---

# API Gateway Error Response Format

Project-specific conventions for error responses in the API Gateway.

## Standard Error Format

All error responses must follow this structure:

\```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "not-an-email"
    },
    "request_id": "req_abc123"
  }
}
\```

## Error Codes

- `VALIDATION_ERROR` - Input validation failed
- `AUTH_ERROR` - Authentication failed
- `PERMISSION_ERROR` - Authorization failed
- `NOT_FOUND` - Resource not found
- `RATE_LIMIT` - Rate limit exceeded
- `INTERNAL_ERROR` - Server error

## Usage in Python

\```python
from fastapi import HTTPException

def validate_email(email: str):
    if not is_valid_email(email):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid email format",
                    "details": {"field": "email", "value": email}
                }
            }
        )
\```
```

## Step 3: Agent References Skills

When agents work on this project, they see:

### From Agent Prompts
```markdown
## Relevant Skills

Universal (all projects):
- [Artifact Contracts](../../skills/meta/artifact-contracts.md)
- [Agent Handoffs](../../skills/meta/agent-handoffs.md)
- [Quality Bar](../../skills/meta/quality-bar.md)

Project-specific:
- [API Error Response Format](skills/api-conventions.md)
```

**Note**: Stack-specific skills will appear here once they are properly curated from authoritative sources.

### Auto-Detected

System detects:
- `pyproject.toml` → suggests Python skills (when available)
- `fastapi` in dependencies → suggests API patterns (when available)
- Existing `skills.json` → loads configured skills

## Step 4: Agent Uses Skills in Work

**Example commit message:**
```
Add user validation endpoint

Implemented per:
- tasks.md (Task 2.3)
- architecture.md (User Service component)
- skills/api-conventions.md (error response format)

Tests cover happy path and validation errors.
```

**Example PR description:**
```markdown
## Changes
- Added POST /users endpoint with validation
- Error responses follow project conventions (per skills/api-conventions.md)

## Tests
- test_create_user_success (happy path)
- test_create_user_invalid_email (validation)
- test_create_user_duplicate (conflict)

All tests pass: `pytest tests/`
```

## Benefits

1. **Consistent patterns**: All team members follow same conventions
2. **Easy onboarding**: New agents immediately see relevant skills
3. **Stack-appropriate**: Python-specific patterns automatically available
4. **Project conventions**: Custom patterns documented and enforced
5. **Quality assurance**: Skills reference reinforces quality bar

## Alternative Configurations

### Minimal (Universal Only)

```json
{
  "version": "1.0",
  "universal_skills": [
    "meta/artifact-contracts",
    "meta/agent-handoffs",
    "meta/quality-bar"
  ],
  "auto_detect": true
}
```

### Multi-Stack Project

```json
{
  "version": "1.0",
  "universal_skills": ["meta/artifact-contracts", "meta/agent-handoffs", "meta/quality-bar"],
  "stack_skills": [
    # Future: Add when properly curated
    # "stacks/python/testing-pytest",
    # "stacks/typescript/type-safety",
    # "stacks/react/component-patterns"
  ],
  "auto_detect": true
}
```

### Experimental Skills

```json
{
  "version": "1.0",
  "universal_skills": ["meta/artifact-contracts"],
  "stack_skills": ["stacks/python/testing-pytest"],
  "project_skills": [
    "experimental/ai-agent-patterns",
    "skills/custom-deployment"
  ],
  "auto_detect": false
}
```

## See Also

- [Skills Registry](../SKILLS-REGISTRY.md) - Complete registry documentation
- [Skills README](../README.md) - Usage guide
- [Skills Template](../skills.json.template) - Configuration template
