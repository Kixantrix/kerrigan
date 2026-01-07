# Automation Contracts

This document defines generic automation contracts that enable platform-agnostic agent workflows while providing concrete GitHub implementations.

## Design Philosophy

**Platform abstraction**: Define automation needs as contracts, not implementation details.
**GitHub-first, portable-ready**: Implement with GitHub Actions but design for future portability.
**Opt-in control**: All automations respect manual overrides and configuration.

## Core Automation Contracts

### 1. Reviewer Assignment Contract

**Need**: Automatically assign reviewers based on role labels when PRs are opened.

**Inputs**:
- PR metadata (labels, project folder, linked issues)
- Role-to-reviewer mapping configuration

**Outputs**:
- Reviewer assignments to PR
- Optional review team assignments

**GitHub Implementation**: Workflow using `actions/github-script@v7`

**Configuration file**: `.github/automation/reviewers.json`

**Schema**:
```json
{
  "role_mappings": {
    "role:spec": ["username1", "team:specs"],
    "role:architect": ["username2", "team:architecture"],
    "role:swe": ["username3", "team:engineering"],
    "role:testing": ["username4", "team:qa"],
    "role:security": ["username5", "team:security"],
    "role:deployment": ["username6", "team:ops"]
  },
  "default_reviewers": ["team:maintainers"],
  "require_code_owner_review": true
}
```

---

### 2. Issue Generation Contract

**Need**: Auto-generate issues from project task definitions to reduce manual work.

**Inputs**:
- Project `tasks.md` file with structured task definitions
- Issue template configuration
- Sprint/milestone context

**Outputs**:
- Created issues with appropriate labels and assignments
- Linked to project folder and parent tracking issue

**GitHub Implementation**: Workflow triggered on push to tasks.md or manual dispatch

**Task Format in tasks.md**:
```markdown
## Task: [Task title]
<!-- AUTO-ISSUE: role:swe priority:high -->

**Description**: Clear description of work

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2

**Dependencies**: #123, #456

**Estimated effort**: [small|medium|large]

---
```

The `<!-- AUTO-ISSUE: ... -->` comment enables auto-generation with specified labels.

---

### 3. Sprint Mode Automation Contract

**Need**: When sprint mode is active, automatically apply autonomy grants to reduce friction.

**Inputs**:
- Sprint tracking issue (labeled with `agent:sprint`)
- PRs linked to sprint tracking issue

**Outputs**:
- Automatic `agent:go` label on PRs within sprint scope
- Status comments explaining auto-approval

**GitHub Implementation**: Enhanced agent-gates.yml workflow

**Configuration**: Labels on sprint tracking issue control behavior

---

### 4. Role-Based Assignment Contract

**Need**: Auto-assign issues to appropriate agents/teams based on role labels.

**Inputs**:
- Issue role labels (role:spec, role:swe, etc.)
- Role-to-assignee mapping

**Outputs**:
- Issue assignments
- Project board placement (optional)

**GitHub Implementation**: Workflow on issue creation/label events

**Configuration**: Uses same `.github/automation/reviewers.json` for consistency

---

## Configuration Structure

All automation configuration lives in `.github/automation/` to:
- Separate automation from core workflows
- Make it easy to enable/disable
- Facilitate future platform migrations

### Directory Layout
```
.github/
├── automation/
│   ├── reviewers.json          # Role-to-reviewer mappings
│   ├── issue-generation.yml    # Issue generation config
│   └── README.md              # Automation documentation
├── workflows/
│   ├── auto-assign-reviewers.yml
│   ├── auto-generate-issues.yml
│   ├── auto-assign-issues.yml
│   └── agent-gates.yml (enhanced)
```

---

## Portability Notes

To adapt these contracts to another platform (GitLab, Bitbucket, etc.):

1. **Reviewer Assignment**: Map to platform's reviewer/approver API
2. **Issue Generation**: Use platform's issue creation API with same task.md format
3. **Sprint Mode**: Adapt label-based logic to platform's label/tag system
4. **Role Assignment**: Use platform's assignment API

The task.md format, role labels, and configuration schemas remain the same.

---

## Disabling Automation

To disable specific automations:
- Comment out or delete the workflow file
- Or add a workflow condition checking for a config flag
- Manual labels/assignments always take precedence over automation

---

## Security Considerations

- All automations run with `GITHUB_TOKEN` (no PAT required)
- Automations cannot override human-applied labels
- Autonomy gates still enforce final approval
- Reviewer requirements from CODEOWNERS still apply
