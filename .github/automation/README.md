# Automation Configuration

This directory contains configuration files for Kerrigan's GitHub automation features.

## Files

- **reviewers.json**: Maps role labels to reviewers/teams for auto-assignment
- **issue-generation.yml**: Configuration for auto-generating issues from tasks.md

## Setup Instructions

### 1. Configure Reviewer Mappings

Edit `reviewers.json` to map role labels to GitHub usernames or teams:

```json
{
  "role_mappings": {
    "role:spec": ["alice", "team:product"],
    "role:swe": ["bob", "team:engineering"],
    "role:testing": ["charlie", "team:qa"]
  },
  "default_reviewers": ["team:maintainers"],
  "auto_assign_on_label": true
}
```

**Syntax**:
- Use plain usernames: `"alice"`
- Use team slugs with prefix: `"team:engineering"`
- Leave arrays empty to disable auto-assignment for that role

### 2. Enable Issue Generation

Issue generation is triggered by:
- Pushing changes to any `tasks.md` file in `specs/projects/*/`
- Manual workflow dispatch from Actions tab

To enable a task for auto-generation, add this comment:
```markdown
## Task: Implement user authentication
<!-- AUTO-ISSUE: role:swe priority:high -->

**Description**: Add JWT-based authentication...
```

### 3. Sprint Mode

When a tracking issue has the `agent:sprint` label:
- PRs linked to that issue automatically get `agent:go` label
- This reduces manual label management during active sprints

## Automation Workflows

The following workflows are available:

- `auto-assign-reviewers.yml`: Runs on PR opened/labeled
- `auto-generate-issues.yml`: Runs on push to tasks.md or manual trigger  
- `auto-assign-issues.yml`: Runs on issue labeled
- `agent-gates.yml`: Enhanced with sprint mode auto-approval

## Disabling Automation

To disable a specific automation:
1. Delete or rename its workflow file (change `.yml` to `.yml.disabled`)
2. Or edit the workflow to add a condition that always skips

Manual assignments always override automation.

## Troubleshooting

**Reviewers not assigned**: Check that usernames/teams exist and are spelled correctly in reviewers.json

**Issues not generated**: Ensure tasks.md has the `<!-- AUTO-ISSUE -->` comment marker

**Sprint mode not working**: Verify the tracking issue has `agent:sprint` label and PR body links to it

**Permissions errors**: Workflows use `GITHUB_TOKEN` which has permissions from the repository settings
