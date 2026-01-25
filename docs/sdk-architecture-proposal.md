# SDK-Based Autonomous Agent Service Architecture

## Executive Summary

This document proposes an SDK-based autonomous agent service that enables fully automated issue-to-PR workflows without manual @-mention or assignment. The investigation in PR #127 validated that GitHub App installation tokens successfully authenticate the Copilot SDK, enabling headless operation.

## Architecture Overview

```
┌─────────────────┐
│  Issue Created  │
│  (with label)   │
└────────┬────────┘
         │ Webhook (issues.labeled)
         ▼
┌─────────────────────────────┐
│  GitHub Actions Workflow    │
│  (webhook-triggered)        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  SDK Agent Service          │
│  - Webhook validation       │
│  - GitHub App auth          │
│  - Copilot SDK invocation   │
│  - Agent orchestration      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Agent Execution            │
│  - Fetch issue & specs      │
│  - Load role prompt         │
│  - Execute with SDK         │
│  - Create PR with results   │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│   PR Created    │
│  (autonomous)   │
└─────────────────┘
```

## Key Components

### 1. Webhook Handler

**Responsibility**: Receive and validate GitHub webhook events

**Triggers**:
- `issues.labeled` - Issue labeled with `agent:go`
- `issues.assigned` - Issue assigned to agent
- Filter by role labels: `role:spec`, `role:architect`, `role:swe`, etc.

**Validation**:
- Webhook signature verification (HMAC SHA-256)
- Event type filtering
- Label validation (autonomy gates)
- Rate limiting

### 2. GitHub App Authentication

**Responsibility**: Manage GitHub App installation tokens

**Features**:
- JWT generation from GitHub App private key
- Installation token retrieval (1-hour lifetime)
- Automatic token refresh before expiry
- Secure key storage (GitHub Secrets)

**Permissions Required**:
- `issues: read/write` - Read issue details, post comments
- `pull_requests: write` - Create PRs
- `contents: write` - Push to branches
- `metadata: read` - Access repository metadata

### 3. SDK Client Wrapper

**Responsibility**: Interface with GitHub Copilot SDK

**Features**:
- Authenticate using GitHub App token
- Load and inject role-specific prompts
- Execute code generation tasks
- Handle SDK errors and retries
- Context management (specs, architecture, conventions)

**Context Injection**:
```javascript
{
  issue: { title, body, labels, number },
  repository: { name, owner, default_branch },
  role: "swe" | "architect" | "spec" | "deploy",
  artifacts: {
    spec: "specs/projects/*/spec.md",
    architecture: "specs/projects/*/architecture.md",
    plan: "specs/projects/*/plan.md",
    constitution: "specs/constitution.md"
  },
  prompt: "contents of .github/agents/role.{role}.md"
}
```

### 4. Agent Orchestrator

**Responsibility**: Route issues to appropriate agent roles

**Routing Logic**:
```
IF issue has role:spec → Spec Agent (kickoff-spec.md prompt)
IF issue has role:architect → Architect Agent (architecture-design.md prompt)
IF issue has role:swe → SWE Agent (implementation-swe.md prompt)
IF issue has role:deploy → Deploy Agent (deployment-ops.md prompt)
IF issue has role:security → Security Agent (security-review.md prompt)
IF issue has role:triage → Triage Agent (triage-analysis.md prompt)
ELSE → Default to SWE Agent
```

**Autonomy Gates**:
- Check for `agent:go` or `agent:sprint` label
- Verify no blocking status (`status.json`)
- Skip if PR already exists for issue
- Log all gate checks for audit trail

### 5. PR Creation Service

**Responsibility**: Create pull requests with proper linking

**Features**:
- Create branch from default branch (`sdk-agent/issue-{number}`)
- Commit generated code
- Create PR with issue reference (`Fixes #{number}`)
- Apply appropriate labels (copy role labels)
- Add PR description with checklist
- Link to issue for traceability

### 6. Status & Error Handling

**Responsibility**: Provide visibility and handle failures

**Success Flow**:
1. Post comment to issue: "🤖 Agent started working..."
2. Execute agent with SDK
3. Create PR
4. Post comment: "✅ PR created: #{pr_number}"

**Error Flow**:
1. Catch and log exception
2. Post comment to issue: "❌ Agent failed: {error_summary}"
3. Include retry instructions
4. Alert monitoring (if available)

**Error Categories**:
- **Authentication errors**: GitHub App token issues
- **SDK errors**: Copilot API failures, rate limits
- **Repository errors**: Branch conflicts, push failures
- **Validation errors**: Missing artifacts, invalid specs

## Hosting Platform: GitHub Actions (Preferred)

### Why GitHub Actions?

1. **No external infrastructure** - Fully contained in repository
2. **Native GitHub integration** - Direct access to GitHub API
3. **Secrets management** - Built-in secrets store
4. **Cost-effective** - Free for public repos, ~$0.008/min for private
5. **Event-driven** - Triggered directly by GitHub webhooks
6. **No additional deployment** - Just commit workflow files

### Implementation Approach

**Workflow Structure**:
```yaml
# .github/workflows/sdk-agent-service.yml
name: SDK Agent Service
on:
  issues:
    types: [labeled, assigned]
  
permissions:
  issues: write
  pull-requests: write
  contents: write

jobs:
  invoke-agent:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          cd services/sdk-agent
          npm ci
      
      - name: Run SDK agent
        env:
          GITHUB_APP_ID: ${{ secrets.SDK_AGENT_APP_ID }}
          GITHUB_APP_PRIVATE_KEY: ${{ secrets.SDK_AGENT_PRIVATE_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cd services/sdk-agent
          npm start -- \
            --event-type "${{ github.event_name }}" \
            --issue-number "${{ github.event.issue.number }}" \
            --repository "${{ github.repository }}"
```

### Alternative: Self-Hosted Runner

For organizations with existing runners:
- Runner pre-authenticated with Copilot CLI
- Faster startup (no dependency installation)
- Can cache SDK responses
- Better for high-volume usage

## Service Directory Structure

```
services/sdk-agent/
├── package.json              # Node.js dependencies
├── tsconfig.json             # TypeScript configuration
├── src/
│   ├── index.ts             # Entry point
│   ├── webhook-handler.ts   # Webhook validation & routing
│   ├── github-app-auth.ts   # GitHub App authentication
│   ├── sdk-client.ts        # Copilot SDK wrapper
│   ├── agent-orchestrator.ts # Role-based routing
│   ├── pr-creator.ts        # PR creation service
│   ├── status-reporter.ts   # Issue comments & logging
│   └── types.ts             # TypeScript type definitions
├── tests/
│   ├── webhook-handler.test.ts
│   ├── github-app-auth.test.ts
│   └── agent-orchestrator.test.ts
├── .env.example             # Example environment variables
└── README.md                # Service documentation
```

## Configuration

### GitHub App Setup

1. **Create GitHub App** (Settings → Developer settings → GitHub Apps)
   - Name: `kerrigan-sdk-agent`
   - Webhook URL: (Not used - using Actions instead)
   - Permissions:
     - Repository permissions:
       - Contents: Read & write
       - Issues: Read & write
       - Pull requests: Read & write
       - Metadata: Read
   - Subscribe to events: None (handled by Actions)

2. **Install App** on Kerrigan repository

3. **Generate Private Key** and store in GitHub Secrets:
   - `SDK_AGENT_APP_ID`: App ID (from app settings)
   - `SDK_AGENT_PRIVATE_KEY`: Private key (PEM format)

### Environment Variables

```bash
# Required
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
GITHUB_TOKEN=ghp_...  # Provided by Actions

# Optional
LOG_LEVEL=info
RETRY_ATTEMPTS=3
RETRY_DELAY_MS=1000
SDK_TIMEOUT_MS=300000  # 5 minutes
```

## Security Considerations

### Secret Management
- ✅ GitHub App private key stored in GitHub Secrets
- ✅ Never logged or exposed in outputs
- ✅ Rotated regularly (recommended: quarterly)
- ✅ Scoped to minimum required permissions

### Webhook Validation
- ✅ Signature verification using HMAC SHA-256
- ✅ Event type filtering (only process expected events)
- ✅ Label validation (autonomy gates)
- ✅ Rate limiting (prevent abuse)

### Code Execution
- ✅ All code runs in isolated GitHub Actions runner
- ✅ No execution of arbitrary user code
- ✅ SDK responses validated before committing
- ✅ All changes go through PR review process

### Audit Trail
- ✅ All agent invocations logged to issue comments
- ✅ GitHub Actions logs retained (default: 90 days)
- ✅ Git history tracks all code changes
- ✅ PR links back to triggering issue

## Cost Analysis

### GitHub Actions (Preferred)

**Public Repository**: FREE
- Unlimited minutes for public repos
- SDK API usage charged separately (if applicable)

**Private Repository**:
- Free tier: 2,000 minutes/month
- Additional: $0.008/minute
- Estimated per-issue: 5-10 minutes = $0.04-$0.08
- Monthly cost (50 issues): $2-$4

**SDK API Usage** (estimate):
- Copilot charges may apply based on usage
- Need to monitor actual costs in pilot

### Alternative Platforms (for comparison)

**Azure Functions**: $10-35/month (serverless)
**Railway/Render**: $5-25/month (PaaS)
**GitHub Codespaces**: ~$130/month (24/7) - NOT RECOMMENDED

## Rollout Plan

### Phase 1: Development (Week 1-2)
- [x] Architecture documentation (this document)
- [ ] Implement core service components
- [ ] Unit tests for key functions
- [ ] Integration tests with mock SDK

### Phase 2: Pilot (Week 3)
- [ ] Deploy to `feature/sdk-agent-service` branch
- [ ] Test with synthetic issues (label: `sdk-test`)
- [ ] Monitor logs and error rates
- [ ] Collect feedback from test PRs

### Phase 3: Limited Release (Week 4)
- [ ] Deploy to kerrigan repository
- [ ] Enable for select issue types (e.g., only `role:swe`)
- [ ] Run parallel with manual workflow
- [ ] Compare quality and speed

### Phase 4: General Availability (Week 5+)
- [ ] Enable for all issue types
- [ ] Deprecate manual workflow (keep as fallback)
- [ ] Publish documentation
- [ ] Monitor operational metrics

## Success Metrics

### Performance
- **Trigger to PR**: < 5 minutes (95th percentile)
- **Uptime**: > 99% (excluding maintenance)
- **Error Rate**: < 5% of triggered issues

### Quality
- **PR Approval Rate**: > 80% (first submission)
- **CI Pass Rate**: > 90% (before review)
- **Artifact Compliance**: 100% (required files)

### Cost
- **Monthly Cost**: < $50/month
- **Cost per Issue**: < $1/issue

### User Experience
- **Manual Steps Eliminated**: Manual assignment, initial trigger
- **Time Saved**: ~5 minutes per issue (setup time)
- **Human Focus**: Shift from orchestration to decision-making

## Maintenance & Operations

### Monitoring
- GitHub Actions workflow status
- Issue comment success/failure
- SDK API error rates
- GitHub App token refresh failures

### Troubleshooting
1. **Agent doesn't start**: Check `agent:go` label, verify GitHub App installed
2. **Authentication fails**: Verify secrets, check token expiry
3. **SDK timeout**: Increase timeout, check SDK availability
4. **PR creation fails**: Check branch conflicts, verify permissions

### Backup Plan
- Manual workflow remains available (existing Copilot @-mention)
- Can disable SDK workflow by removing workflow file
- All artifacts and conventions remain compatible

## Related Documentation

- [Architecture](architecture.md) - Overall Kerrigan architecture
- [Automation Limits](automation-limits.md) - Current automation gaps
- [Agent Assignment](agent-assignment.md) - Manual agent assignment
- [Autonomy Modes](../playbooks/autonomy-modes.md) - Autonomy controls
- [CI Workflows](ci-workflows.md) - Existing GitHub Actions

## Questions & Answers

**Q: Does this replace the current manual workflow?**
A: No, both coexist. SDK service is additive, not replacing.

**Q: What if PR #127 isn't merged yet?**
A: This architecture assumes validation succeeded. Implementation proceeds in feature branch.

**Q: Can we run this on other repositories?**
A: Yes, with minor config changes. GitHub App can be installed on multiple repos.

**Q: What about multi-repo orchestration?**
A: Out of scope for v1. Future enhancement could coordinate across repos.

**Q: How do we test this safely?**
A: Feature branch + synthetic test issues with `sdk-test` label.

## Next Steps

1. Review and approve this architecture
2. Implement core service (Phase 1)
3. Create GitHub App and configure secrets
4. Deploy to feature branch for testing
5. Run pilot with test issues
6. Iterate based on feedback
7. Promote to production if successful

---

**Status**: Proposal - Awaiting Review
**Last Updated**: 2026-01-25
**Author**: Kerrigan Agent System
