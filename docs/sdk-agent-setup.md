# SDK Agent Service Setup Guide

This guide walks through setting up the SDK-based autonomous agent service for Kerrigan.

## Overview

The SDK Agent Service enables fully automated issue-to-PR workflows. When an issue is labeled with `agent:go`, the service automatically:

1. Validates permissions and autonomy gates
2. Determines the appropriate agent role
3. Executes the agent using GitHub Copilot SDK
4. Creates a pull request with results
5. Posts status updates

## Prerequisites

### Required

- **GitHub Repository**: Access to Kixantrix/kerrigan repository
- **Admin Access**: Ability to create GitHub Apps and manage secrets
- **GitHub Actions**: Enabled on the repository
- **Node.js 20+**: For local development/testing

### Optional

- **Self-hosted Runner**: For faster execution and caching (recommended for high volume)
- **Monitoring Tool**: For production monitoring and alerting

## Step 1: Create GitHub App

### 1.1 Navigate to GitHub App Settings

1. Go to GitHub Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"

### 1.2 Configure App Settings

**Basic Information:**
- **GitHub App name**: `kerrigan-sdk-agent` (or your preferred name)
- **Homepage URL**: `https://github.com/Kixantrix/kerrigan`
- **Webhook URL**: Leave blank (we're using GitHub Actions, not webhooks)
- **Webhook secret**: Leave blank

**Permissions:**

Repository permissions:
- **Contents**: Read and write
- **Issues**: Read and write
- **Pull requests**: Read and write
- **Metadata**: Read only

Organization permissions: None required

User permissions: None required

**Subscribe to events:**
- Uncheck all events (GitHub Actions handles triggers)

**Where can this GitHub App be installed?**
- Select "Only on this account"

### 1.3 Create and Install

1. Click "Create GitHub App"
2. Note the **App ID** (you'll need this later)
3. Click "Generate a private key" and download the `.pem` file
4. Click "Install App" and select the `Kixantrix/kerrigan` repository

## Step 2: Configure GitHub Secrets

### 2.1 Add Secrets to Repository

Navigate to: Repository Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

**SDK_AGENT_APP_ID**
```
Value: <Your GitHub App ID from Step 1.3>
Example: 123456
```

**SDK_AGENT_PRIVATE_KEY**
```
Value: <Contents of the .pem file from Step 1.3>
Format: Include the entire key with headers:
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA...
(multiple lines)
...
-----END RSA PRIVATE KEY-----

⚠️ Important: 
- Include the BEGIN and END lines
- Preserve all line breaks
- Do not add extra spaces or characters
```

### 2.2 Verify Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Verify both secrets are listed:
   - `SDK_AGENT_APP_ID`
   - `SDK_AGENT_PRIVATE_KEY`

## Step 3: Deploy Service Code

### 3.1 Ensure Code is in Repository

The service code should already be in the repository at:
```
services/sdk-agent/
├── src/
├── package.json
├── tsconfig.json
└── README.md
```

### 3.2 Enable GitHub Actions Workflow

The workflow file is located at:
```
.github/workflows/sdk-agent-service.yml
```

It's automatically enabled when the file is committed to the repository.

### 3.3 Verify Workflow

1. Go to repository Actions tab
2. Look for "SDK Agent Service" in the workflows list
3. It should be listed but not yet run (will trigger on issue events)

## Step 4: Test the Service

### 4.1 Create a Test Issue

1. Go to Issues → New issue
2. Create an issue with:
   - **Title**: "Test SDK Agent Service"
   - **Body**: "This is a test issue to verify the SDK agent service is working."
   - **Labels**: Add `agent:go` and `role:swe`

### 4.2 Monitor Execution

1. Go to Actions tab immediately after labeling
2. Watch for "SDK Agent Service" workflow to start
3. Click on the running workflow to see logs

### 4.3 Expected Behavior

**Success indicators:**
- ✅ Workflow starts within seconds of labeling
- ✅ Issue gets a comment: "🤖 SDK Agent Started"
- ✅ Workflow completes (may fail with SDK placeholder error - expected)

**Currently expected error:**
```
❌ SDK integration not yet implemented - awaiting PR #127 merge
```

This is normal! The service infrastructure is complete, but the actual Copilot SDK integration is pending PR #127.

**Issue comment should appear:**
```
❌ Agent Failed
The SDK agent encountered an error while processing this issue:
SDK integration not yet implemented - awaiting PR #127 merge
```

## Step 5: Configure Monitoring (Optional)

### 5.1 GitHub Actions Monitoring

**Default monitoring:**
- Workflow run history in Actions tab
- Email notifications on workflow failures (if enabled in your GitHub settings)

**Enhanced monitoring:**
1. Enable notifications: Settings → Notifications → Actions
2. Set up status checks: Settings → Branches → Branch protection rules
3. Monitor via GitHub CLI: `gh run list --workflow="SDK Agent Service"`

### 5.2 External Monitoring

For production use, consider:

**Uptime monitoring:**
- Monitor GitHub Actions status: https://www.githubstatus.com/
- Set up alerts for workflow failures

**Cost monitoring:**
- Track Actions minutes usage: Settings → Billing → Actions
- Set up spending limits if using private repositories

## Step 6: Production Rollout

### 6.1 Pilot Phase (Recommended)

1. **Limited testing**:
   - Use only on test issues (label: `sdk-test`)
   - Monitor logs and errors
   - Collect feedback

2. **Controlled rollout**:
   - Enable for specific issue types (e.g., only `role:swe`)
   - Run parallel with manual workflow
   - Compare quality and speed

3. **Full deployment**:
   - Enable for all issue types
   - Document operational procedures
   - Train team on new workflow

### 6.2 Update Documentation

Once SDK integration is complete (PR #127):

1. Update service documentation
2. Update architecture diagrams
3. Document operational procedures
4. Create runbooks for common issues

### 6.3 Establish Operational Procedures

**Daily:**
- Review failed workflow runs
- Check issue comments for errors
- Monitor cost (if private repo)

**Weekly:**
- Review success/failure rates
- Analyze performance metrics
- Update documentation as needed

**Monthly:**
- Review and rotate secrets
- Update dependencies
- Assess cost vs. value

## Troubleshooting

### Workflow Doesn't Start

**Symptoms:**
- Issue labeled with `agent:go` but no workflow runs

**Solutions:**
1. Check GitHub Actions is enabled: Settings → Actions → Allow all actions
2. Verify workflow file exists: `.github/workflows/sdk-agent-service.yml`
3. Check workflow syntax: Actions → SDK Agent Service → "..." → View workflow file
4. Ensure issue has autonomy label: `agent:go`, `agent:sprint`, or `autonomy:override`

### Authentication Failed

**Symptoms:**
```
❌ GitHub App credentials are invalid
```

**Solutions:**
1. Verify `SDK_AGENT_APP_ID` secret matches your App ID
2. Verify `SDK_AGENT_PRIVATE_KEY` includes BEGIN/END lines
3. Check GitHub App is installed on the repository
4. Ensure private key hasn't expired (regenerate if needed)

### Workflow Times Out

**Symptoms:**
- Workflow runs for 6+ hours (default timeout)
- No progress in logs

**Solutions:**
1. Check GitHub Actions status: https://www.githubstatus.com/
2. Verify network connectivity (rare in GitHub-hosted runners)
3. Reduce `SDK_TIMEOUT_MS` to fail faster
4. Add timeout to workflow: `timeout-minutes: 30`

### Permission Denied

**Symptoms:**
```
❌ Resource not accessible by integration
```

**Solutions:**
1. Verify GitHub App has required permissions (Contents, Issues, PRs)
2. Check App is installed on the repository
3. Verify workflow permissions match requirements
4. Reinstall GitHub App if permissions were changed

## Advanced Configuration

### Custom Timeouts

Edit `.github/workflows/sdk-agent-service.yml`:

```yaml
jobs:
  invoke-sdk-agent:
    timeout-minutes: 30  # Add this line
    runs-on: ubuntu-latest
```

### Self-Hosted Runner

For better performance:

```yaml
jobs:
  invoke-sdk-agent:
    runs-on: self-hosted  # Change from ubuntu-latest
```

### Conditional Execution

To test on specific issues only:

```yaml
if: |
  contains(github.event.issue.labels.*.name, 'agent:go') &&
  contains(github.event.issue.labels.*.name, 'sdk-test')
```

### Multiple Environments

For staging/production separation:

```yaml
jobs:
  invoke-sdk-agent:
    environment: production  # Add environment gate
    runs-on: ubuntu-latest
```

## Security Considerations

### Secret Rotation

**Recommended schedule:**
- Rotate GitHub App private key: Quarterly
- Rotate installation tokens: Automatic (1-hour lifetime)

**Rotation procedure:**
1. Generate new private key in GitHub App settings
2. Update `SDK_AGENT_PRIVATE_KEY` secret
3. Test with a sample issue
4. Revoke old private key

### Access Control

**Who has access:**
- Repository admins: Full access to secrets and workflows
- Repository collaborators: Can trigger workflows by labeling issues
- GitHub App: Limited to configured permissions

**Least privilege:**
- GitHub App has minimum required permissions
- Workflow uses scoped `GITHUB_TOKEN`
- Secrets are encrypted at rest

### Audit Logging

**What's logged:**
- All workflow runs (90-day retention)
- All issue comments (permanent)
- All PR creations (permanent)
- Git history (permanent)

**Monitoring recommendations:**
- Review Actions logs weekly
- Audit issue comments for anomalies
- Track PR creation patterns

## Support and Resources

### Documentation

- [SDK Architecture Proposal](../docs/sdk-architecture-proposal.md)
- [Service README](../services/sdk-agent/README.md)
- [Kerrigan Architecture](../docs/architecture.md)

### Getting Help

1. **Check logs**: Actions tab → SDK Agent Service → Click run → View logs
2. **Check issue comments**: Service posts errors to issues
3. **Search issues**: Existing issues may have solutions
4. **Open issue**: Create new issue with `sdk-agent-service` label

### Useful Commands

```bash
# View recent workflow runs
gh run list --workflow="SDK Agent Service" --limit 10

# View logs for a specific run
gh run view <run-id> --log

# View workflow file
gh workflow view sdk-agent-service.yml

# Trigger workflow manually (if configured)
gh workflow run sdk-agent-service.yml
```

## Next Steps

After completing this setup:

1. ✅ Verify test issue triggers workflow
2. ✅ Review workflow logs
3. ✅ Monitor first few successful runs
4. ⏳ Wait for PR #127 (SDK integration)
5. 🚀 Deploy to production after SDK integration

## Changelog

- **2026-01-25**: Initial setup guide created
- **TBD**: Update after PR #127 SDK integration

---

**Questions?** Open an issue with the `sdk-agent-service` label.
