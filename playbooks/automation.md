# Automation Playbook

This playbook explains how to use Kerrigan's automation features to reduce manual intervention.

## Overview

Kerrigan includes GitHub-native automation workflows that:
- Auto-assign reviewers based on role labels
- Auto-assign issues to appropriate team members
- Auto-generate issues from task definitions
- Auto-approve PRs in sprint mode

All automations are **opt-in** and configurable.

📖 **For detailed automation analysis**, see: [Automation Limits & Capabilities](../docs/automation-limits.md)  
📖 **For agent assignment details**, see: [Agent Assignment Pattern](../docs/agent-assignment.md)

## Setup

### Step 1: Configure Reviewer Mappings

Edit `.github/automation/reviewers.json`:

```json
{
  "role_mappings": {
    "role:spec": ["alice"],
    "role:swe": ["bob", "charlie"],
    "role:testing": ["team:qa"],
    "role:security": ["team:security"]
  },
  "default_reviewers": [],
  "auto_assign_on_label": true,
  "comment_on_assignment": true
}
```

**Tips**:
- Use GitHub usernames without `@` prefix
- Use team slugs with `team:` prefix (e.g., `team:engineering`)
- Leave empty arrays `[]` to disable auto-assignment for specific roles
- Set `auto_assign_on_label: false` to disable all auto-assignment

### Step 2: Enable Issue Generation

In your project's `tasks.md`, add AUTO-ISSUE markers:

```markdown
## Task: Implement authentication
<!-- AUTO-ISSUE: role:swe priority:high -->

**Description**: Add JWT-based authentication

**Acceptance Criteria**:
- [ ] JWT token generation
- [ ] Token validation middleware
- [ ] Tests for auth flow

**Estimated effort**: medium
---
```

Issues will be auto-generated when:
- You push changes to `specs/projects/*/tasks.md`
- You manually trigger the workflow from Actions tab

### Step 3: Use Sprint Mode

For autonomous sprints:

1. Create a tracking issue for the sprint
2. Add `agent:sprint` label to the tracking issue
3. In PRs, reference the sprint issue: "Related to #123"
4. PR will automatically receive `agent:go` label

## Workflows

### auto-assign-reviewers.yml
**Triggers**: PR opened, labeled  
**What it does**: Assigns reviewers based on role labels  
**Permissions**: Needs `pull-requests: write`

### auto-assign-issues.yml
**Triggers**: Issue opened, labeled  
**What it does**: Assigns issues to users based on role labels  
**Permissions**: Needs `issues: write`

### auto-generate-issues.yml
**Triggers**: Push to tasks.md, manual dispatch  
**What it does**: Creates issues from AUTO-ISSUE markers in tasks.md  
**Permissions**: Needs `issues: write`, `contents: read`

### agent-gates.yml (enhanced)
**Triggers**: PR opened, labeled  
**What it does**: Validates autonomy gates + auto-applies agent:go in sprint mode  
**Permissions**: Needs `pull-requests: write`, `issues: read`

### PR Review Script (tools/review-prs.ps1)
**Type**: Local PowerShell script (not GitHub Actions)  
**What it does**: Systematically manages Copilot reviews on all open PRs  
**Usage**: Run locally with `.\tools\review-prs.ps1`  
**Automation potential**: Can be scheduled locally but NOT in GitHub Actions due to authentication requirements

**Why not in Actions**: GitHub Copilot requires user authentication and cannot be triggered via `GITHUB_TOKEN`. The script uses GitHub CLI (`gh`) which requires `gh auth login`. See [Automation Limits](../docs/automation-limits.md#4-pr-review-script-automation) for details.

**Local scheduling options**:
- Windows: Task Scheduler
- macOS/Linux: cron
- Recommended: Run manually or daily

## Disabling Automation

To disable a workflow:
1. Rename `.github/workflows/auto-*.yml` to `.github/workflows/auto-*.yml.disabled`
2. Or delete the workflow file
3. Or add a condition that always skips: `if: false`

## Platform Portability

The automation contracts are documented in `specs/kerrigan/070-automation-contracts.md`.

To port to another platform (GitLab, Bitbucket, Azure DevOps):
1. Keep the same task.md format and role label conventions
2. Reimplement workflows using the platform's CI/CD system
3. Use platform-specific APIs for issue/PR assignment
4. Configuration files remain similar (JSON/YAML)

The core contracts (role labels, task format, autonomy modes) are platform-agnostic.

## Troubleshooting

**Reviewers not assigned**
- Check that usernames/teams in reviewers.json are correct
- Verify workflow has `pull-requests: write` permission
- Check Actions logs for error messages

**Issues not generated**
- Verify `<!-- AUTO-ISSUE: ... -->` comment is present
- Check that tasks.md follows the required format
- Look for existing issues with same title (workflow skips duplicates)

**Sprint mode not working**
- Confirm tracking issue has `agent:sprint` label
- Verify PR body links to the sprint issue
- Check Actions logs for the agent-gates workflow

**Permission errors**
- Workflows use `GITHUB_TOKEN` which inherits repo permissions
- Go to Settings > Actions > General > Workflow permissions
- Ensure "Read and write permissions" is enabled

## Best Practices

1. **Start simple**: Enable auto-assignment first, add issue generation later
2. **Test in dry-run**: Use workflow_dispatch with dry_run=true for issue generation
3. **Review assignments**: Manual assignments always override automation
4. **Sprint mode discipline**: Only use `agent:sprint` for focused sprint work
5. **Keep config updated**: Review `.github/automation/reviewers.json` as team changes
6. **Validate JSON**: Use JSON validators before committing config changes to avoid workflow errors
7. **Test with a dry-run first**: For issue generation, use manual dispatch with dry_run mode to preview changes
8. **Monitor workflow logs**: Check Actions tab periodically for warnings or configuration issues
9. **Use consistent label names**: Role labels are case-sensitive; maintain consistent naming
10. **Document team slugs**: Keep a reference of team slugs as they may differ from display names

## Testing Results

The automation infrastructure has been thoroughly tested with 47+ automated tests covering:

- ✅ Configuration validation
- ✅ Workflow trigger conditions  
- ✅ Permission requirements
- ✅ Error handling
- ✅ Integration between workflows
- ✅ Edge case scenarios

**Status**: All tests passing, CI green

For detailed testing results, edge cases, and troubleshooting guide, see: [Automation Testing Documentation](../docs/automation-testing.md)

### Key Edge Cases Documented

1. **Team Assignment Limitation**: Teams cannot be assigned to issues (GitHub API limitation), only to PR reviews. Use individual usernames for issue assignment.

2. **Label Case Sensitivity**: All labels and usernames are case-sensitive. Ensure exact matches in configuration.

3. **Duplicate Issue Prevention**: Issue generation checks for duplicates by title. Similar issues must have different titles.

4. **Cross-Repo Links**: Sprint mode detects cross-repo issue references but only checks issues in the current repository.

5. **Configuration Validation**: Workflows validate configuration and log detailed errors but don't fail the workflow to avoid blocking legitimate work.

### Tested Scenarios

**Auto-Assignment**:
- ✅ Role labels trigger assignment to configured users/teams
- ✅ Multiple role labels assign all mapped reviewers
- ✅ Empty role mappings disable assignment for specific roles
- ✅ Duplicate assignments prevented
- ✅ Issue author not assigned to own issue

**Auto-Triage**:
- ✅ User assignment triggers role label addition
- ✅ Multiple labels can be auto-applied
- ✅ Existing labels not duplicated
- ✅ Invalid configurations handled gracefully

**Issue Generation**:
- ✅ AUTO-ISSUE markers parsed correctly
- ✅ Duplicate issues prevented (by title matching)
- ✅ Dry-run mode works without creating issues
- ✅ Multiple tasks per file handled

**Sprint Mode**:
- ✅ agent:sprint label detected on linked issues
- ✅ agent:go auto-applied to linked PRs
- ✅ Multiple link patterns supported (Fixes #N, Closes #N, #N)
- ✅ Fallback to PR labels when issues inaccessible

## Security Considerations

- All workflows run with `GITHUB_TOKEN` (no PAT required)
- Automations cannot override human-applied labels
- Autonomy gates still enforce final approval
- CODEOWNERS file still applies if present
- Workflows only have write access to PRs/issues, not code
