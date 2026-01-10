# Agent Assignment Pattern

This guide explains how to assign work to Kerrigan agents using GitHub's label-based automation.

## TL;DR

**Agents are not GitHub accounts** — they're role-based prompts. Work is assigned using **role labels** (like `role:swe`, `role:spec`), which automatically trigger assignment to configured users or teams.

## How It Works

### 1. Agent Roles Are Labels, Not Accounts

Kerrigan's agents (Spec, Architect, SWE, Testing, Security, Deployment, Debugging) are defined as prompts in `.github/agents/`. They are **not** GitHub user accounts or bot accounts, so you cannot:
- ❌ @mention them (e.g., `@kerrigan-swe`)
- ❌ Directly assign them to issues
- ❌ Add them as PR reviewers

### 2. Assignment Via Labels

Instead, use **role labels** to indicate which agent role should handle the work:

| Label | Agent Role | Purpose |
|-------|-----------|---------|
| `role:spec` | Spec Agent | Define project goals and acceptance criteria |
| `role:architect` | Architect Agent | Design system architecture and roadmap |
| `role:swe` | SWE Agent | Implement features with tests |
| `role:testing` | Testing Agent | Strengthen test coverage |
| `role:security` | Security Agent | Security review and hardening |
| `role:deployment` | Deployment Agent | Production readiness and operations |
| `role:debugging` | Debugging Agent | Bug investigation and fixes |

### 3. Automated Assignment Workflow

When you apply a role label to an issue or PR:

1. **GitHub Actions workflow** (`auto-assign-issues.yml` or `auto-assign-reviewers.yml`) detects the label
2. **Configuration lookup** in `.github/automation/reviewers.json` finds mapped users/teams
3. **Automatic assignment** adds those users as assignees (issues) or reviewers (PRs)
4. **Optional comment** notifies assigned users

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│ Apply Label │ ───▶ │ Workflow     │ ───▶ │ Config      │ ───▶ │ Auto-assign  │
│ role:swe    │      │ Triggered    │      │ Lookup      │      │ to alice     │
└─────────────┘      └──────────────┘      └─────────────┘      └──────────────┘
```

## Configuration

### Setting Up Assignment Mappings

Edit `.github/automation/reviewers.json`:

```json
{
  "role_mappings": {
    "role:spec": ["alice", "team:product"],
    "role:architect": ["bob"],
    "role:swe": ["alice", "bob", "team:engineering"],
    "role:testing": ["charlie", "team:qa"],
    "role:security": ["david", "team:security"],
    "role:deployment": ["eve", "team:devops"],
    "role:debugging": ["team:engineering"]
  },
  "default_reviewers": ["team:maintainers"],
  "auto_assign_on_label": true,
  "comment_on_assignment": true,
  "triage_mappings": {
    "copilot": ["role:swe"]
  },
  "auto_triage_on_assign": true,
  "comment_on_triage": true
}
```

**Configuration Options:**
- **role_mappings**: Maps role labels to users/teams for auto-assignment
- **Usernames**: Use plain GitHub usernames (e.g., `"alice"`)
- **Teams**: Use `"team:slug"` format (e.g., `"team:engineering"`)
- **Multiple assignees**: List multiple users/teams in the array
- **Empty arrays**: Leave empty `[]` to disable auto-assignment for that role
- **Default**: `default_reviewers` used when no role label is present

### Setting Up Auto-Triage (New!)

The `triage_mappings` section enables **reverse assignment**: when specified users are assigned to an issue, the system automatically adds appropriate role labels.

**Use case**: When copilot (or any AI assistant) is assigned to an issue, automatically add role labels to indicate which agent should handle the work.

```json
{
  "triage_mappings": {
    "copilot": ["role:swe"],
    "alice": ["role:spec", "role:architect"],
    "bob": ["role:swe", "role:testing"]
  },
  "auto_triage_on_assign": true,
  "comment_on_triage": true
}
```

**How it works:**
1. User assigns copilot (or any configured user) to an issue
2. Workflow detects the assignment
3. Automatically adds configured role labels
4. Labels indicate which agent prompt to use

**Example:**
```bash
gh issue edit 123 --add-assignee copilot
# Automatically adds role:swe label
```

### Disabling Automation

To disable specific automation features:
```json
{
  "auto_assign_on_label": false,     // Disable label → assignment
  "auto_triage_on_assign": false     // Disable assignment → labels
}
```

## Usage Examples

### Example 1: Assign Issue to SWE Agent

```bash
# Create or label an existing issue
gh issue create --title "Implement user authentication" \
  --body "Add JWT-based auth" \
  --label "role:swe"

# Result: Automatically assigns users configured for role:swe
```

### Example 2: Request Architect Review on PR

```bash
# Open PR and add role label
gh pr create --title "Add OAuth support" \
  --body "Implements OAuth2 flow" \
  --label "role:architect"

# Result: Requests review from architect role users
```

### Example 3: Multi-Role Assignment

```bash
# Issue requires both SWE and Security review
gh issue create --title "Add payment processing" \
  --label "role:swe,role:security"

# Result: Assigns users from both role mappings
```

### Example 4: Manual Override

You can always manually assign users regardless of automation:
```bash
gh issue edit 123 --add-assignee alice
```

### Example 5: Auto-Triage on Assignment (New!)

When copilot is assigned, role labels are automatically added:
```bash
# Create issue and assign copilot
gh issue create --title "Fix login bug" --assignee copilot

# Result: Automatically adds role:swe label
# This indicates which agent prompt should be used
```

Configured triage mappings:
```json
{
  "triage_mappings": {
    "copilot": ["role:swe"],
    "alice": ["role:spec", "role:architect"]
  }
}
```

## Integration with Agent Workflows

### For Issue Creators

When creating an issue that should be handled by a specific agent:

1. Add the appropriate role label (e.g., `role:spec`, `role:swe`)
2. Add `agent:go` label if you want the agent to start immediately
3. Automation assigns configured users who can then:
   - Copy the agent prompt from `.github/agents/role.*.md`
   - Execute the agent work
   - Submit a PR with results

### For AI Agent Users

If you're using an AI coding assistant (like GitHub Copilot):

1. Find issues assigned to you with a role label
2. Copy the corresponding agent prompt from `.github/agents/`
3. Provide the prompt and issue context to your AI assistant
4. Review and commit the AI-generated output

### For Project Maintainers

Configure `reviewers.json` to map role labels to:
- Your GitHub username for solo projects
- Team members for collaborative projects  
- GitHub teams for organization-wide assignment

## Why Not Real Bot Accounts?

You might wonder: "Why not create actual bot accounts like `@kerrigan-swe`?"

### Challenges with Bot Accounts

1. **Cost**: Requires separate GitHub accounts (potentially paid seats)
2. **Maintenance**: Each bot needs credentials, token management, and monitoring
3. **Complexity**: Requires hosting infrastructure for bot logic
4. **Permissions**: Bots need write access to your repository
5. **GitHub Limitations**: No native auto-complete for bot @mentions

### Benefits of Label-Based Approach

1. ✅ **Zero infrastructure**: Uses GitHub Actions (free for public repos)
2. ✅ **No credentials**: Uses built-in `GITHUB_TOKEN`
3. ✅ **Flexible mapping**: Same label can assign different people per project
4. ✅ **Human-in-loop**: Humans execute agent prompts, review AI outputs
5. ✅ **Transparent**: All assignments visible in issue/PR timeline

## Alternative: GitHub Apps (Advanced)

For organizations wanting bot-like behavior, consider creating a GitHub App:

**Benefits:**
- Can @mention the app (e.g., `@kerrigan-bot`)
- Can comment and interact as a bot
- Fine-grained permissions
- Webhooks for event-driven automation

**Drawbacks:**
- Requires hosting infrastructure
- Complex setup and maintenance
- Costs for hosting/compute
- Overkill for most use cases

See [GitHub Apps documentation](https://docs.github.com/en/apps) for details.

## Troubleshooting

### Issue Not Auto-Assigned

**Symptoms:** Label applied but no assignment happens

**Solutions:**
1. Check that `auto_assign_on_label: true` in `reviewers.json`
2. Verify role label exactly matches a key in `role_mappings`
3. Ensure mapped usernames exist and are collaborators
4. Check GitHub Actions logs for workflow errors
5. Verify workflow has `issues: write` permission

### Wrong People Assigned

**Symptoms:** Assigned users don't match expectations

**Solutions:**
1. Review `reviewers.json` configuration
2. Check for typos in usernames or team slugs
3. Remember: team format is `"team:slug"`, not `"@org/team"`
4. Clear and re-apply label to trigger re-assignment

### Teams Not Assigned

**Symptoms:** Team assignment fails or is skipped

**Solutions:**
1. Teams can only be assigned as PR reviewers, not issue assignees
2. Use individual usernames for issue assignment
3. Verify team slug matches GitHub organization team
4. Check that workflow has `pull-requests: write` permission

### Automation Not Triggering

**Symptoms:** No workflow runs when labels applied

**Solutions:**
1. Check `.github/workflows/auto-assign-*.yml` files exist
2. Verify workflows are enabled (not disabled in repo settings)
3. Check workflow `on:` triggers include `labeled` event
4. Review Actions tab for workflow runs and errors

## FAQ

**Q: Can I use agent names like @kerrigan-swe in comments?**  
A: You can mention them in comments, but they won't receive notifications. Use role labels for assignment.

**Q: Can I have different mappings per project?**  
A: No, `reviewers.json` is repository-wide. Fork the template for project-specific configs.

**Q: Do I need to configure all roles?**  
A: No, leave arrays empty `[]` for roles you don't use.

**Q: Can I disable comments on assignment?**  
A: Yes, set `"comment_on_assignment": false` in `reviewers.json`.

**Q: What if I don't want automation at all?**  
A: Delete or disable the workflow files in `.github/workflows/`, or set `auto_assign_on_label: false`.

## See Also

- [Automation Configuration](../.github/automation/README.md) — Full automation setup
- [Agent Prompts](../.github/agents/README.md) — All agent role definitions  
- [Autonomy Modes](../playbooks/autonomy-modes.md) — Control when agents can work
- [Setup Guide](./setup.md) — Initial repository setup
