# Automation Configuration

This directory contains configuration files for Kerrigan's GitHub automation features.

## Files

- **reviewers.json**: Maps role labels to reviewers/teams for auto-assignment and auto-triage

## Quick Start

Agent roles (spec, architect, swe, etc.) work via **labels**, not @mentions. 

**Two-way automation:**
1. **Label → Assignment**: Apply a role label (e.g., `role:swe`) to auto-assign users
2. **Assignment → Labels** (New!): Assign copilot to auto-add role labels for triaging

📖 **Full guide**: [Agent Assignment Pattern](../../docs/agent-assignment.md)  
📖 **Automation capabilities & limits**: [Automation Limits](../../docs/automation-limits.md)

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

### 2. Configure Auto-Triage (New!)

Enable reverse assignment: when specific users are assigned, automatically add role labels.

```json
{
  "triage_mappings": {
    "copilot": ["role:swe"],
    "alice": ["role:spec", "role:architect"]
  },
  "auto_triage_on_assign": true,
  "comment_on_triage": true
}
```

**Use case**: When copilot is assigned to an issue, automatically add `role:swe` label to indicate which agent should handle the work.

### 3. Enable Issue Generation

Issue generation is triggered by:
- Pushing changes to any `tasks.md` file in `specs/projects/*/`
- Manual workflow dispatch from Actions tab

To enable a task for auto-generation, add this comment:
```markdown
## Task: Implement user authentication
<!-- AUTO-ISSUE: role:swe priority:high -->

**Description**: Add JWT-based authentication...
```

### 4. Sprint Mode

When a tracking issue has the `agent:sprint` label:
- PRs linked to that issue automatically get `agent:go` label
- This reduces manual label management during active sprints

## Automation Workflows

The following workflows are available:

- `auto-assign-reviewers.yml`: Runs on PR opened/labeled (label → assignment)
- `auto-assign-issues.yml`: Runs on issue labeled (label → assignment)
- `auto-triage-on-assign.yml`: Runs on issue assigned (assignment → labels, NEW!)
- `auto-generate-issues.yml`: Runs on push to tasks.md or manual trigger  
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
