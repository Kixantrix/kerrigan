# Automation Configuration

This directory contains configuration files for Kerrigan's GitHub automation features.

## Files

- **reviewers.json**: Maps role labels to reviewers/teams for auto-assignment, auto-triage, and auto-autonomy grants

## Quick Start

Agent roles (spec, architect, swe, etc.) work via **labels**, not @mentions. 

**Multi-way automation:**
1. **Label → Assignment**: Apply a role label (e.g., `role:swe`) to auto-assign users
2. **Assignment → Labels**: Assign copilot to auto-add role labels for triaging
3. **Auto-Autonomy**: Issues with role labels automatically receive `agent:go` (NEW!)
4. **Auto-Ready PRs**: Draft PRs marked ready when CI passes (NEW!)
5. **Dependency Chain**: Dependent issues auto-triggered when parent closes (NEW!)

📖 **Full guide**: [Agent Assignment Pattern](../../docs/agent-assignment.md)  
📖 **Automation capabilities & limits**: [Automation Limits](../../docs/automation-limits.md)  
📖 **Auto-merge setup**: [Auto-Merge Guide](../../docs/auto-merge-setup.md)

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

### 2. Configure Auto-Triage

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

### 3. Configure Auto-Autonomy (NEW!)

Enable automatic `agent:go` label for qualifying issues:

```json
{
  "auto_grant_autonomy": true,
  "comment_on_auto_grant": true,
  "trusted_users": ["alice", "bob"]
}
```

**Criteria for auto-grant** (any one triggers):
- Issue has a role label (role:swe, role:testing, etc.)
- Issue has `tier:auto` label
- Issue has `kerrigan` label
- Issue created by a trusted user

**Safety**: Auto-grant is disabled by default. Set `auto_grant_autonomy: true` to enable.

### 4. Enable Issue Generation

Issue generation is triggered by:
- Pushing changes to any `tasks.md` file in `specs/projects/*/`
- Manual workflow dispatch from Actions tab

To enable a task for auto-generation, add this comment:
```markdown
## Task: Implement user authentication
<!-- AUTO-ISSUE: role:swe priority:high -->

**Description**: Add JWT-based authentication...
```

### 5. Sprint Mode

When a tracking issue has the `agent:sprint` label:
- PRs linked to that issue automatically get `agent:go` label
- This reduces manual label management during active sprints

### 6. Tier System (NEW!)

Label issues with autonomy tiers:
- **`tier:auto`**: Fully autonomous - auto-gets `agent:go`, minimal gates
- **`tier:standard`**: Standard workflow - acceptance gate only (default)
- **`tier:strategic`**: High-touch - direction + acceptance gates

See [GitHub Labels](../../docs/github-labels.md) for label creation instructions.

## Automation Workflows

The following workflows are available:

### Label Management
- `auto-grant-autonomy.yml`: Automatically adds `agent:go` to qualifying issues (NEW!)
- `auto-assign-copilot.yml`: Assigns Copilot when `agent:go` is added (NEW!)

### Assignment & Triage
- `auto-assign-reviewers.yml`: Runs on PR opened/labeled (label → assignment)
- `auto-assign-issues.yml`: Runs on issue labeled (label → assignment)
- `auto-triage-on-assign.yml`: Runs on issue assigned (assignment → labels)

### PR Automation
- `auto-ready-pr.yml`: Marks draft PRs ready when CI passes (NEW!)
- `auto-generate-issues.yml`: Create issues from tasks.md
- `agent-gates.yml`: Autonomy gate enforcement with sprint mode

### Dependency Management
- `auto-trigger-dependents.yml`: Triggers dependent issues when parent closes (NEW!)

## Autonomous Workflow Example

With full automation enabled:

```
1. Issue Created (has role:swe label)
   ↓
2. Auto-grant agent:go (auto-grant-autonomy.yml)
   ↓
3. Auto-assign Copilot (auto-assign-copilot.yml)
   ↓
4. Copilot creates PR
   ↓
5. CI runs automatically
   ↓
6. Auto-mark ready (auto-ready-pr.yml, if CI passes)
   ↓
7. Auto-assign reviewers (auto-assign-reviewers.yml)
   ↓
8. Human reviews & approves
   ↓
9. [Optional] Auto-merge after approval
   ↓
10. Issue closes
   ↓
11. Trigger dependents (auto-trigger-dependents.yml)
```

## Disabling Automation

To disable a specific automation:
1. Set the corresponding flag to `false` in `reviewers.json`:
   - `auto_assign_on_label: false` - Disable auto-assignment
   - `auto_triage_on_assign: false` - Disable auto-triage
   - `auto_grant_autonomy: false` - Disable auto-autonomy grants
2. Or delete/rename the workflow file (change `.yml` to `.yml.disabled`)

Manual assignments and labels always override automation.

## Troubleshooting

**Reviewers not assigned**: Check that usernames/teams exist and are spelled correctly in reviewers.json

**Issues not generated**: Ensure tasks.md has the `<!-- AUTO-ISSUE -->` comment marker

**Sprint mode not working**: Verify the tracking issue has `agent:sprint` label and PR body links to it

**Auto-grant not working**: Check `auto_grant_autonomy: true` in reviewers.json and verify issue meets criteria

**Copilot not assigned**: Ensure Copilot is a valid user with repository access

**PR not auto-ready**: Verify PR has `agent:go` label and CI workflow completed successfully

**Dependents not triggered**: Check issue body for dependency keywords ("Depends on #N", "Blocked by #N")

**Permissions errors**: Workflows use `GITHUB_TOKEN` which has permissions from the repository settings
