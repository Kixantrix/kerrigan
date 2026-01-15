# Automation Limits and Capabilities

This document analyzes the limits of automation in the Issues → PRs → Issues workflow and documents what can be automated within GitHub constraints.

## Executive Summary

**What CAN be automated** (✅ Implemented):
- Issue creation from task definitions
- Role-based reviewer/assignee assignment
- Sprint mode autonomy grants
- PR status checks and gates
- Issue triaging based on assignments

**What REQUIRES human intervention** (⚠️ Fundamental limits):
- Triggering GitHub Copilot to work on issues
- Local development environment setup
- GitHub account authentication for Copilot
- Code generation and PR creation (requires local execution)
- Final PR approval and merge decisions
- Security-sensitive operations

**Key Finding**: GitHub Actions can automate issue management and workflow orchestration, but **GitHub Copilot cannot be directly triggered or invoked from GitHub Actions**. This requires a human with a GitHub account and Copilot access to work locally or through the web interface.

---

## Investigation Findings

### 1. GitHub Actions Triggering

**Current Capabilities** (✅ Implemented):
- Auto-trigger on push to `tasks.md` files
- Manual workflow dispatch for on-demand execution
- PR event triggers (opened, labeled, synchronized)
- Issue event triggers (opened, labeled, assigned)
- Scheduled triggers (cron-based, not yet implemented)

**Limitations**:
- Cannot directly trigger GitHub Copilot sessions
- Cannot invoke local development tools remotely
- Rate limits apply (documented in GitHub Actions docs)
- Workflow execution time limited to 6 hours per job
- Concurrent workflow limits based on GitHub plan

**Configuration Required**:
```yaml
# Example: Enable scheduled issue generation
on:
  schedule:
    - cron: '0 0 * * MON'  # Weekly on Monday
  workflow_dispatch:      # Also allow manual triggers
```

---

### 2. Copilot Integration with Actions

**GitHub Copilot Execution Model**:

GitHub Copilot operates in two modes:
1. **IDE Integration** (VS Code, JetBrains, etc.) - Requires local environment
2. **Copilot in GitHub** (PR reviews, issue responses) - Web-based, triggered by @-mentions

**What CANNOT be automated**:
- ❌ Starting a Copilot coding session from Actions
- ❌ Triggering Copilot to create PRs automatically
- ❌ Invoking Copilot IDE features via CI/CD
- ❌ Scheduling Copilot work programmatically

**What CAN be semi-automated**:
- ✅ Request Copilot PR reviews via `gh pr edit --add-reviewer Copilot`
- ✅ @-mention @copilot in comments to trigger responses
- ✅ Use PR review script to systematically request Copilot reviews
- ✅ Auto-assign role labels that signal which agent should work

**Why**: GitHub Copilot requires:
- Authenticated GitHub user session (cannot use `GITHUB_TOKEN`)
- Local development environment for code generation
- Interactive session for agent work
- Human-in-the-loop for safety and quality control

**Workaround**: The `tools/review-prs.ps1` script provides semi-automation:
```powershell
# Run locally with your GitHub credentials
.\tools\review-prs.ps1 -MarkReadyForReview
```

This script:
- Lists all open PRs
- Adds Copilot as reviewer automatically
- Notifies @copilot on PRs needing changes
- Reports PR status for human triage

**Recommendation**: Run this script manually or schedule it locally (not in GitHub Actions) since it requires authenticated GitHub CLI access.

---

### 3. Authentication Methods

**GitHub Actions Authentication**:
- ✅ `GITHUB_TOKEN` - Automatically provided, limited scope
  - Can: Create issues, add labels, request reviews, comment
  - Cannot: Trigger Copilot sessions, push to protected branches (without config)
  - Lifespan: Duration of workflow run
  - Permissions: Configured per workflow or repository-wide

**Personal Access Token (PAT)**:
- ⚠️ Not recommended for automation
- Security risk if committed to repository
- Requires manual rotation and management
- Kerrigan intentionally avoids PAT requirement

**GitHub CLI Authentication** (for local scripts):
- ✅ Used by `review-prs.ps1`
- Requires: `gh auth login` (one-time setup)
- Provides: Full user permissions
- Use case: Local automation scripts, not CI/CD

**GitHub App Authentication** (advanced):
- ⚠️ Complex setup, not yet implemented
- Could provide elevated permissions
- Better security model than PAT
- Overkill for current Kerrigan use case

**Current Setup**:
```yaml
# .github/workflows/auto-generate-issues.yml
permissions:
  issues: write      # Create and label issues
  contents: read     # Read tasks.md files
```

**Security Best Practice**:
- Minimal permissions per workflow
- No PAT storage in repository
- Human authentication for sensitive operations
- Regular permission audits

---

### 4. PR Review Script Automation

**Current Implementation**: `tools/review-prs.ps1` (PowerShell script)

**What It Does**:
1. Lists all open PRs using `gh pr list`
2. Checks if Copilot is assigned as reviewer
3. Adds Copilot reviewer if missing
4. Checks review status and decisions
5. Notifies @copilot on PRs with requested changes
6. Reports PRs ready to merge

**Automation Level**: ⚠️ Semi-automated (requires local execution)

**Why Not Fully Automated**:
- Requires GitHub CLI authentication (`gh auth login`)
- `GITHUB_TOKEN` from Actions has limited scope
- Adding reviewers via API requires specific permissions
- @-mentioning @copilot only works with user auth

**Current Usage Pattern**:
```powershell
# Developer runs locally (daily/weekly)
.\tools\review-prs.ps1

# Or schedule locally with Windows Task Scheduler:
# Daily at 9 AM: pwsh.exe -File "path\to\review-prs.ps1"
```

**Potential Action-Based Alternative** (⚠️ Limited functionality):
```yaml
# Could implement subset of features in Actions
name: Check PR Review Status
on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      issues: write
    steps:
      - name: Request Copilot reviews
        uses: actions/github-script@v7
        with:
          script: |
            # Can request reviews but cannot @-mention effectively
            # GITHUB_TOKEN limitations apply
```

**Recommendation**: 
- Keep current PowerShell script for local use
- Document setup for team members
- Consider scheduled local execution (Task Scheduler/cron)
- Do NOT attempt full Actions migration due to auth limitations

**Enhancement Opportunities**:
- ✅ Add dry-run mode (already implemented)
- ✅ Add duplicate comment prevention (already implemented)
- ⚠️ Could add Slack/email notifications (requires integration)
- ⚠️ Could add PR metrics dashboard (requires additional tooling)

---

### 5. Issue Generation Loop

**Current Implementation**: ✅ Fully automated

The `auto-generate-issues.yml` workflow provides a complete issue generation loop:

**Triggers**:
- Push to `specs/projects/*/tasks.md`
- Manual workflow dispatch

**Process**:
1. Detects changed `tasks.md` files
2. Parses `<!-- AUTO-ISSUE: ... -->` markers
3. Extracts task title, description, labels
4. Checks for duplicate issues (by title)
5. Creates issues with appropriate labels and metadata
6. Links back to project and source file

**Configuration in tasks.md**:
```markdown
## Task: Implement user authentication
<!-- AUTO-ISSUE: role:swe priority:high -->

**Description**: Add JWT-based authentication

**Acceptance Criteria**:
- [ ] JWT token generation
- [ ] Token validation middleware
- [ ] Tests for auth flow
---
```

**Automation Features**:
- ✅ Duplicate detection (prevents re-creating existing issues)
- ✅ Dry-run mode for testing
- ✅ Batch processing (multiple tasks per file)
- ✅ Project metadata tracking
- ✅ Label inheritance from markers

**Manual Steps Required**:
1. ⚠️ Human must write task definitions in `tasks.md`
2. ⚠️ Human must commit and push changes
3. ⚠️ Human must add `agent:go` label to enable agent work
4. ⚠️ Human must assign or trigger Copilot to work on issues

**Self-Chaining Pattern** (Documented in `specs/kerrigan/060-self-chaining-issues.md`):

Issues can include "On Completion" instructions for agents:
```markdown
## On Completion

When this issue is complete, create the next issue:
- Title: "Milestone 3: Add integration tests"
- Labels: agent:go, role:testing, kerrigan
- Body: [template]
```

**Automation Level**: 🔄 Semi-autonomous loop
- Issue generation: Fully automated
- Issue assignment: Automated via role labels
- Issue work: Requires human-triggered Copilot
- Next issue creation: Agent can do via `gh issue create` command
- Loop continuation: Requires human oversight

**Recommendation**: 
- Current implementation is optimal balance
- Self-chaining pattern enables momentum
- Human-in-loop prevents runaway automation
- Could enhance with parent/child issue relationships

---

### 6. Workflow Permissions

**Permission Model**: Least privilege principle

**Current Workflow Permissions**:

**auto-generate-issues.yml**:
```yaml
permissions:
  issues: write      # Create and modify issues
  contents: read     # Read repository files
```

**auto-assign-reviewers.yml**:
```yaml
permissions:
  pull-requests: write  # Assign reviewers
  contents: read        # Read configuration
```

**auto-assign-issues.yml**:
```yaml
permissions:
  issues: write      # Assign users to issues
  contents: read     # Read configuration
```

**auto-triage-on-assign.yml**:
```yaml
permissions:
  issues: write      # Add labels to issues
  contents: read     # Read configuration
```

**agent-gates.yml**:
```yaml
permissions:
  pull-requests: write  # Add labels (sprint mode)
  issues: read          # Check linked issue labels
```

**ci.yml**:
```yaml
permissions:
  contents: read        # Read code and run validators
  pull-requests: read   # Access PR context
```

**Repository-Level Configuration**:

Settings → Actions → General → Workflow permissions:
- ✅ Recommended: "Read and write permissions"
- ⚠️ Alternative: "Read repository contents and packages permissions" + manual grants

**Permission Limitations**:
- ❌ Cannot modify protected branches without additional config
- ❌ Cannot access organization secrets without explicit grant
- ❌ Cannot trigger other workflows directly (security)
- ❌ Cannot perform user-authenticated actions (like @-mentions)
- ❌ Cannot approve PRs (by design, prevents automation abuse)

**Security Considerations**:
- ✅ Workflows only run on PRs from same repository (not forks, by default)
- ✅ Each workflow has explicit, minimal permissions
- ✅ No PAT usage (reduces attack surface)
- ✅ Configuration files in `.github/automation/` separate from code
- ✅ Manual overrides always take precedence

**Branch Protection Compatibility**:
- ✅ Status checks work with branch protection
- ✅ Agent gates integrate with required checks
- ⚠️ Auto-merge would require elevated permissions (not recommended)
- ⚠️ Auto-approval conflicts with human review philosophy

**Troubleshooting Permission Issues**:

1. **"Resource not accessible by integration"**:
   - Check workflow `permissions:` block
   - Verify repository-wide permissions setting
   - Ensure `GITHUB_TOKEN` has not been restricted

2. **"Reviewers not assigned"**:
   - Verify usernames/teams exist
   - Check team permissions (teams must have repo access)
   - Ensure `pull-requests: write` permission

3. **"Issues not created"**:
   - Check `issues: write` permission
   - Verify label existence (labels must be pre-created)
   - Check workflow logs for detailed errors

**Recommendation**:
- Current permission setup is optimal
- No changes needed for Kerrigan use case
- Document repository settings requirement in setup guide

---

## What Can Be Automated: Summary Matrix

### Issue Management
| Task | Automation Level | Implementation | Human Required |
|------|------------------|----------------|----------------|
| Create issues from tasks.md | ✅ Full | auto-generate-issues.yml | Write tasks, commit |
| Assign issues by role | ✅ Full | auto-assign-issues.yml | Apply labels |
| Auto-triage issues | ✅ Full | auto-triage-on-assign.yml | Assign users |
| Close completed issues | ⚠️ Manual | N/A | Merge PR |

### PR Management
| Task | Automation Level | Implementation | Human Required |
|------|------------------|----------------|----------------|
| Create PRs | ❌ No | Requires Copilot/human | Full |
| Assign reviewers by role | ✅ Full | auto-assign-reviewers.yml | Apply labels |
| Request Copilot review | ⚠️ Semi | review-prs.ps1 (local) | Run script |
| Check autonomy gates | ✅ Full | agent-gates.yml | Add labels |
| Sprint mode auto-approval | ✅ Full | agent-gates.yml | Set sprint label |
| Merge PRs | ⚠️ Manual | N/A | Human approval |

### Code Generation
| Task | Automation Level | Implementation | Human Required |
|------|------------------|----------------|----------------|
| Generate code changes | ❌ No | Requires Copilot | Full |
| Run tests | ✅ Full | ci.yml | Push code |
| Run linters | ✅ Full | ci.yml | Push code |
| Fix failing tests | ❌ No | Requires Copilot | Full |

### Workflow Orchestration
| Task | Automation Level | Implementation | Human Required |
|------|------------------|----------------|----------------|
| Label-based routing | ✅ Full | Multiple workflows | Define labels |
| Status tracking | ⚠️ Semi | status.json | Update file |
| Next issue creation | ⚠️ Semi | Agent via gh CLI | Agent execution |
| Progress reporting | ⚠️ Manual | N/A | Update issues |

**Legend**:
- ✅ Full: Completely automated via GitHub Actions
- ⚠️ Semi: Partially automated, requires human trigger/input
- ❌ No: Cannot be automated, requires human/Copilot interaction

---

## Maximum Safe Automation: Recommendations

### Current State (✅ Implemented)

The repository already implements maximum safe automation within GitHub constraints:

1. **Issue Generation**: Fully automated from task definitions
2. **Role-Based Assignment**: Automatic based on labels
3. **Sprint Mode**: Auto-applies autonomy grants
4. **Autonomy Gates**: Enforced via CI checks
5. **Quality Validation**: Automated artifact and quality checks

### Enhancement Opportunities

#### 1. PR Review Script Scheduling (⚠️ Requires local setup)

**Option A: Local Task Scheduler (Recommended)**
```powershell
# Windows Task Scheduler
# Run daily at 9 AM on developer's machine
schtasks /create /tn "Kerrigan PR Review" /tr "pwsh.exe -File C:\path\to\review-prs.ps1" /sc daily /st 09:00
```

**Option B: Cron on macOS/Linux**
```bash
# Add to crontab (crontab -e)
0 9 * * * /usr/local/bin/pwsh /path/to/review-prs.ps1
```

**Option C: GitHub Actions (⚠️ Limited functionality)**
- Can check PR status
- Cannot effectively @-mention Copilot
- Not recommended due to auth limitations

#### 2. Scheduled Issue Generation (🔄 Could implement)

```yaml
# Add to auto-generate-issues.yml
on:
  schedule:
    - cron: '0 0 * * MON'  # Weekly on Monday
  push:
    paths:
      - 'specs/projects/*/tasks.md'
  workflow_dispatch:
```

**Use case**: Periodic check for new tasks even without pushes

#### 3. Status Monitoring Dashboard (🔄 Could implement)

Create a simple workflow to report project status:
```yaml
name: Status Report
on:
  schedule:
    - cron: '0 8 * * MON'  # Weekly Monday morning
jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - name: Generate status report
        uses: actions/github-script@v7
        with:
          script: |
            // Count open issues by label
            // Check blocked status.json files
            // Report in issue comment or Slack
```

#### 4. Auto-Merge for Trusted PRs (⚠️ Not recommended)

**Could** implement auto-merge for:
- Documentation-only changes
- Bot-generated dependency updates
- PRs with `autonomy:override` + all checks passing

**Should NOT** because:
- Conflicts with human-in-loop philosophy
- Removes safety net
- GitHub provides native auto-merge feature if needed

#### 5. Cross-Repository Automation (🔄 Advanced)

For organizations using Kerrigan across multiple repos:
- Centralized automation configuration
- Shared issue templates
- Workflow reuse via composite actions

**Implementation**:
```yaml
# Use composite actions from central repo
- uses: org/kerrigan-automation/.github/actions/assign-reviewers@v1
```

### Security and Safety Guardrails

**DO automate**:
- ✅ Issue creation and labeling
- ✅ Assignment based on predefined rules
- ✅ Status checks and gates
- ✅ Notification generation
- ✅ Configuration validation

**DO NOT automate**:
- ❌ Code generation (requires Copilot)
- ❌ PR approval and merge
- ❌ Security-sensitive operations
- ❌ Changing protected branch rules
- ❌ User authentication/permissions

**Safety Principles**:
1. **Manual override always available**: Labels, assignments can be changed manually
2. **Fail-safe defaults**: Workflows fail gracefully, don't block legitimate work
3. **Audit trail**: All automation logged in GitHub Actions
4. **Least privilege**: Minimal permissions per workflow
5. **Human checkpoints**: Critical decisions require human approval

---

## Setup Requirements Guide

### For Repository Owners/Admins

**Required (One-time setup)**:

1. **Create GitHub Labels** (see `docs/github-labels.md`):
   ```bash
   # Role labels
   gh label create "role:spec" --color "0075ca"
   gh label create "role:architect" --color "0075ca"
   gh label create "role:swe" --color "0075ca"
   gh label create "role:testing" --color "0075ca"
   
   # Autonomy labels
   gh label create "agent:go" --color "28a745"
   gh label create "agent:sprint" --color "28a745"
   gh label create "autonomy:override" --color "d93f0b"
   
   # Special labels
   gh label create "allow:large-file" --color "fbca04"
   gh label create "kerrigan" --color "7057ff"
   ```

2. **Configure Workflow Permissions**:
   - Settings → Actions → General → Workflow permissions
   - Select: "Read and write permissions"
   - Enable: "Allow GitHub Actions to create and approve pull requests" (if using auto-assignment)

3. **Configure Reviewer Mappings** (`.github/automation/reviewers.json`):
   ```json
   {
     "role_mappings": {
       "role:swe": ["your-github-username"],
       "role:testing": ["team:qa"]
     },
     "auto_assign_on_label": true,
     "auto_triage_on_assign": true
   }
   ```

4. **Enable GitHub Copilot** (if using AI assistance):
   - Organization/user settings → Copilot → Enable
   - Grant access to team members
   - Note: Cannot be triggered from Actions

**Optional**:

5. **Configure Branch Protection**:
   - Require status checks: "Agent Gates", "CI / validate"
   - Require pull request reviews
   - Do NOT enable auto-merge unless desired

6. **Set up PR Review Script Scheduling** (local):
   - Install GitHub CLI: `gh auth login`
   - Install PowerShell 7+ (if not on Windows)
   - Schedule script execution (see Enhancement Opportunities)

### For Individual Contributors

**Required**:

1. **Authenticate GitHub CLI** (for PR review script):
   ```bash
   gh auth login
   # Follow prompts, grant required permissions
   ```

2. **Install PowerShell** (if not on Windows):
   ```bash
   # macOS
   brew install --cask powershell
   
   # Linux
   # See: https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-linux
   ```

3. **Enable GitHub Copilot** (if available):
   - Install in IDE (VS Code, JetBrains)
   - OR use via GitHub.com interface

**Workflow**:

1. **Create issues**:
   - Add to `specs/projects/*/tasks.md` with AUTO-ISSUE markers
   - Commit and push → automation creates issues

2. **Work on issues**:
   - Issues auto-assigned based on role labels
   - Use Copilot locally or @-mention @copilot in GitHub
   - Create PRs with "Fixes #N" in description

3. **Review PRs**:
   - Run `.\tools\review-prs.ps1` to manage reviews
   - Or manually add Copilot as reviewer
   - Address feedback and merge

### Troubleshooting Common Issues

**"Workflow not triggering"**:
- Check workflow file syntax (YAML)
- Verify trigger conditions match event
- Check Actions tab for errors
- Ensure workflows are enabled in repository settings

**"Permissions denied"**:
- Review workflow permissions in YAML
- Check repository-wide permissions setting
- Verify user/team has repository access

**"Labels not applied"**:
- Ensure labels exist (case-sensitive)
- Check configuration file syntax (valid JSON)
- Review workflow logs for errors

**"Copilot not responding"**:
- Verify Copilot is enabled for user/org
- Check @-mention syntax (must be `@copilot`)
- Ensure PR is not in draft state
- Remember: Cannot trigger Copilot from Actions

**"Duplicate issues created"**:
- Check issue titles (must match exactly for duplicate detection)
- Review workflow logs for detection logic
- Manually close duplicates if created

---

## Limitations and Constraints

### GitHub Platform Limits

1. **API Rate Limits**:
   - `GITHUB_TOKEN`: 1,000 requests/hour per repository
   - Authenticated requests: 5,000/hour per user
   - Affects: Bulk operations, frequent polling

2. **Workflow Limits** (varies by GitHub plan):
   - Free: 2,000 minutes/month, 20 concurrent jobs
   - Pro: 3,000 minutes/month, 40 concurrent jobs
   - Team: 10,000 minutes/month, 60 concurrent jobs
   - Enterprise: 50,000 minutes/month, 180 concurrent jobs

3. **Artifact Storage**:
   - Free: 500 MB
   - Affects: CI artifacts, logs retention

4. **Workflow File Limits**:
   - Max 20 workflows queued per repository
   - Max 6 hours per workflow run
   - Max 72 hours before cancellation if pending

### Copilot Integration Limits

1. **No Direct API Access**:
   - Cannot trigger Copilot programmatically
   - No REST/GraphQL API for code generation
   - Requires human-initiated session

2. **Authentication Requirements**:
   - Requires GitHub user account
   - Cannot use `GITHUB_TOKEN` or PAT
   - Must be enabled per user/organization

3. **Environment Dependencies**:
   - Code generation requires local IDE/environment
   - Cannot run in GitHub Actions context
   - Web-based Copilot limited to PR reviews/comments

### Kerrigan Design Philosophy Limits

These are **intentional design choices**, not platform limitations:

1. **Human-in-Loop**:
   - Agents cannot auto-approve or merge
   - Humans control autonomy grants
   - Safety over speed

2. **No Auto-Merge**:
   - All PRs require human approval
   - Prevents runaway automation
   - Maintains quality control

3. **Minimal External Dependencies**:
   - No custom GitHub Apps
   - No third-party CI/CD integrations
   - Keeps setup simple

4. **Platform-Agnostic Contracts**:
   - Automation designed for portability
   - Core contracts work on any platform
   - GitHub implementation is one option

---

## Conclusion

### What We Achieved

Kerrigan implements **maximum safe automation** within GitHub constraints:

1. ✅ **Full issue lifecycle automation**: From task definition to assignment
2. ✅ **Intelligent routing**: Role-based assignment and triage
3. ✅ **Autonomy control**: Sprint mode and gates
4. ✅ **Quality enforcement**: Automated validation
5. ✅ **Semi-automated reviews**: PR review script

### What Remains Manual (By Design)

1. ⚠️ **Triggering Copilot**: Requires human-initiated session
2. ⚠️ **Code generation**: Cannot automate AI code writing
3. ⚠️ **Final approval**: Human judgment required
4. ⚠️ **Security decisions**: Too sensitive to automate

### Key Insight

The limitation is not GitHub Actions capability, but the **fundamental architecture of GitHub Copilot**:
- Copilot is designed as a **user-facing tool**, not a service API
- This is intentional for safety, quality, and user control
- Attempting workarounds would violate terms of service and create security risks

### Recommendation

**Current implementation is optimal.** The boundary between automated and manual is exactly where it should be:
- Automate: Orchestration, routing, validation, status tracking
- Human: Strategy, code generation (via Copilot), approval, security

This balance provides:
- ✅ Maximum efficiency (reduce manual toil)
- ✅ Human control (strategic decisions)
- ✅ Safety (humans in critical path)
- ✅ Simplicity (no complex workarounds)

### Next Steps for Users

1. **Follow setup guide** above to configure repository
2. **Run PR review script** locally (optional, for convenience)
3. **Use existing automations** - they cover 80% of the workflow
4. **Focus human time** on high-value activities: strategy, review, security

---

## References

- **Automation Setup**: [.github/automation/README.md](../.github/automation/README.md)
- **Automation Playbook**: [playbooks/automation.md](../playbooks/automation.md)
- **Autonomy Modes**: [playbooks/autonomy-modes.md](../playbooks/autonomy-modes.md)
- **Automation Contracts**: [specs/kerrigan/070-automation-contracts.md](../specs/kerrigan/070-automation-contracts.md)
- **Self-Chaining Issues**: [specs/kerrigan/060-self-chaining-issues.md](../specs/kerrigan/060-self-chaining-issues.md)
- **PR Review Script**: [tools/README.md](../tools/README.md)
- **Setup Guide**: [docs/setup.md](./setup.md)
- **Agent Assignment**: [docs/agent-assignment.md](./agent-assignment.md)
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **GitHub Copilot Docs**: https://docs.github.com/en/copilot
