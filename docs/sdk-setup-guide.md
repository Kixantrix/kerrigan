# Kerrigan SDK Setup Guide

**Version**: 1.0  
**Audience**: Developers implementing autonomous agent triggering  
**Prerequisites**: GitHub account, Node.js 18+, basic command line knowledge

---

## Quick Start (15 minutes)

This guide walks you through setting up autonomous agent triggering using the GitHub Copilot SDK.

### What You'll Build

A service that:
1. Receives webhooks when issues are labeled
2. Triggers a Copilot agent to work on the issue
3. Agent creates a PR automatically
4. No human intervention required

### Architecture Overview

```
GitHub Issue (labeled) → Webhook → Your Service → Copilot SDK → GitHub PR
```

---

## Part 1: GitHub App Setup (5 minutes)

### Step 1: Create GitHub App

1. Go to **Settings → Developer settings → GitHub Apps**
2. Click **New GitHub App**

3. Fill in basic information:
   - **GitHub App name**: `kerrigan-agent-dev` (must be unique)
   - **Homepage URL**: `https://github.com/yourusername/kerrigan`
   - **Webhook URL**: `https://your-service.railway.app/webhook` (get after deploying)
   - **Webhook secret**: Generate a random string: `openssl rand -hex 32`

4. Set permissions:
   ```
   Repository permissions:
   - Contents: Read & write
   - Issues: Read & write
   - Pull requests: Read & write
   - Metadata: Read only (automatic)
   ```

5. Subscribe to events:
   - ✅ Issues
   - ✅ Pull request

6. **Where can this GitHub App be installed?**
   - Select: "Only on this account"

7. Click **Create GitHub App**

### Step 2: Generate Private Key

1. Scroll to **Private keys**
2. Click **Generate a private key**
3. Save the `.pem` file securely (you'll need it later)

### Step 3: Install the App

1. Click **Install App** in left sidebar
2. Select your repository
3. Choose: "All repositories" or "Only select repositories"
4. Click **Install**

5. **Save the Installation ID** from the URL:
   ```
   https://github.com/settings/installations/12345678
                                           ^^^^^^^^
   This is your INSTALLATION_ID
   ```

### Step 4: Save Credentials

Create a `.env` file with these values:
```bash
# From GitHub App settings page
APP_ID=123456

# Path to the .pem file you downloaded
PRIVATE_KEY_PATH=/path/to/private-key.pem

# From installation URL
INSTALLATION_ID=12345678

# The webhook secret you generated
WEBHOOK_SECRET=your-secret-here
```

---

## Part 2: Service Setup (5 minutes)

### Step 1: Clone Template

```bash
# Clone the Kerrigan SDK service template
git clone https://github.com/yourusername/kerrigan-sdk-service
cd kerrigan-sdk-service

# Install dependencies
npm install
```

**Note**: If template doesn't exist yet, use the code from Part 3 below to create it manually.

### Step 2: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env
```

Paste your values from Part 1, Step 4.

### Step 3: Test Locally

```bash
# Start service
npm start

# In another terminal, test health endpoint
curl http://localhost:3000/health
```

You should see:
```json
{
  "status": "healthy",
  "uptime": 5.123,
  "sdk": true,
  "github": true
}
```

---

## Part 3: Deploy to Railway (5 minutes)

### Option A: Deploy via Railway CLI (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add environment variables
railway variables set APP_ID=123456
railway variables set INSTALLATION_ID=12345678
railway variables set WEBHOOK_SECRET=your-secret
railway variables set PRIVATE_KEY="$(cat private-key.pem)"

# Deploy
railway up
```

### Option B: Deploy via Railway Dashboard

1. Go to https://railway.app
2. Click **New Project → Deploy from GitHub repo**
3. Select your service repository
4. Add environment variables:
   - `APP_ID`
   - `INSTALLATION_ID`
   - `WEBHOOK_SECRET`
   - `PRIVATE_KEY` (paste entire .pem file content)

5. Click **Deploy**

### Step 2: Get Service URL

After deployment:
```bash
# Get your service URL
railway domain
```

Example output: `kerrigan-agent-dev.up.railway.app`

### Step 3: Update GitHub App Webhook URL

1. Go back to GitHub App settings
2. Update **Webhook URL** to: `https://kerrigan-agent-dev.up.railway.app/webhook`
3. Click **Save changes**

### Step 4: Verify Webhook

```bash
# Trigger a test webhook from GitHub
# Settings → Webhooks → Recent Deliveries → Redeliver
```

Check Railway logs:
```bash
railway logs
```

You should see: `Webhook received` in the logs.

---

## Part 4: Testing (5 minutes)

### Step 1: Create Test Issue

1. Go to your repository
2. Create a new issue:
   ```
   Title: Test autonomous agent
   
   Body:
   Create a simple function that adds two numbers.
   
   Requirements:
   - Function should be in src/utils/math.js
   - Include JSDoc comments
   - Add unit tests
   ```

### Step 2: Trigger Agent

1. Add label `agent:go` to the issue
2. Watch service logs: `railway logs --follow`

You should see:
```
Webhook received: issues.labeled
Issue #1: Test autonomous agent
Triggering agent...
Agent session created: sess_abc123
Agent working...
```

### Step 3: Wait for PR

The agent will:
1. Analyze the issue (~30 seconds)
2. Create code changes (~2 minutes)
3. Run tests (~1 minute)
4. Create PR (~30 seconds)

**Total time**: ~4 minutes

### Step 4: Review PR

1. Check for new PR in your repository
2. PR should have:
   - Title: "Implement test autonomous agent"
   - Description: Links to issue with "Fixes #1"
   - Files changed: `src/utils/math.js`, `tests/math.test.js`
   - All tests passing

### Step 5: Verify

```bash
# Check out the PR branch
gh pr checkout 1

# Run tests
npm test

# Review code
cat src/utils/math.js
```

---

## Part 5: Customization

### Custom Agent Prompts

Edit `prompts/swe.md` to customize agent behavior:

```markdown
# Software Engineer Agent

You are a software engineer working on {{repo}}.

## Your Task

Issue #{{issue}}: {{title}}

{{body}}

## Requirements

1. Create production-ready code
2. Follow repository conventions
3. Write comprehensive tests
4. Add documentation
5. Create PR with "Fixes #{{issue}}"

## Quality Standards

- Max 800 lines per file
- Test coverage > 80%
- All lints must pass
- Clear commit messages

## Process

1. Analyze requirements carefully
2. Plan your changes
3. Implement incrementally
4. Test thoroughly
5. Create detailed PR description
```

### Multiple Agent Types

Create different prompts for different roles:

```bash
prompts/
├── swe.md         # Software engineer (default)
├── architect.md   # Architecture review
├── testing.md     # Test creation
└── spec.md        # Specification writing
```

Map labels to agent types in `src/config/agents.js`:
```javascript
export const AGENT_MAPPING = {
  'role:swe': 'swe',
  'role:architect': 'architect',
  'role:testing': 'testing',
  'role:spec': 'spec'
};
```

### Cost Controls

Limit SDK usage in `src/config/limits.js`:
```javascript
export const LIMITS = {
  // Max sessions per hour (across all repos)
  maxSessionsPerHour: 10,
  
  // Max requests per session
  maxRequestsPerSession: 100,
  
  // Timeout for long-running sessions (minutes)
  sessionTimeout: 15,
  
  // Max file size to process (bytes)
  maxFileSize: 1048576, // 1MB
};
```

### Notifications

Add Slack notifications in `src/notifications/slack.js`:
```javascript
export async function notifyPRCreated(pr) {
  await fetch(process.env.SLACK_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `🎉 PR created: ${pr.title}`,
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*<${pr.url}|${pr.title}>*\n${pr.description}`
          }
        }
      ]
    })
  });
}
```

---

## Troubleshooting

### Issue: Webhook Not Received

**Check**:
1. Railway service is running: `railway status`
2. URL is correct in GitHub App settings
3. Webhook secret matches in both places

**Debug**:
```bash
# Check Railway logs
railway logs

# Test webhook manually
curl -X POST https://your-service.railway.app/webhook \
  -H "Content-Type: application/json" \
  -d '{"action":"labeled","issue":{"number":1}}'
```

### Issue: Agent Not Triggered

**Check**:
1. Issue has `agent:go` label
2. Service received webhook (check logs)
3. SDK authentication working

**Debug**:
```bash
# Check SDK connection
railway run npm run check-sdk

# Test agent manually
railway run npm run test-agent -- --issue 1
```

### Issue: PR Not Created

**Check**:
1. Agent completed successfully (check logs)
2. GitHub App has write permissions
3. No branch protection blocking agent

**Debug**:
```bash
# Check agent session
railway logs --filter "Agent session"

# Check GitHub App permissions
gh api /repos/:owner/:repo/installation
```

### Issue: High Costs

**Check**:
1. Monitor SDK usage: `railway run npm run usage-report`
2. Check for infinite loops in agent sessions
3. Verify cost limits are enforced

**Fix**:
```javascript
// Add to src/config/limits.js
export const COST_LIMITS = {
  maxRequestsPerDay: 500,
  alertThreshold: 400,
  hardLimit: 500
};
```

---

## Monitoring & Maintenance

### View Service Status

```bash
# Railway dashboard
railway open

# Or check health endpoint
curl https://your-service.railway.app/health
```

### Monitor Costs

```bash
# Check SDK usage
railway run npm run sdk-usage

# View cost breakdown
railway run npm run cost-report
```

Expected output:
```
SDK Usage Report
----------------
Period: Last 30 days
Total requests: 245 / 1500
Cost: $0 (within quota)
Average per issue: 24 requests

By Repository:
- org/repo-a: 120 requests
- org/repo-b: 80 requests
- org/repo-c: 45 requests
```

### Update Service

```bash
# Pull latest changes
git pull origin main

# Deploy
railway up
```

### Rotate Credentials

```bash
# 1. Generate new private key in GitHub App settings
# 2. Download new .pem file
# 3. Update Railway
railway variables set PRIVATE_KEY="$(cat new-private-key.pem)"

# 4. Restart service
railway restart
```

---

## Advanced Configuration

### Multi-Repo Support

Add `kerrigan.json` to each repository:

```json
{
  "kerrigan": {
    "enabled": true,
    "labels": {
      "trigger": "agent:go",
      "sprint": "agent:sprint"
    },
    "agent": {
      "default_type": "swe",
      "timeout_minutes": 15
    },
    "quality": {
      "max_lines_per_file": 800,
      "require_tests": true
    }
  }
}
```

Service will automatically load and respect these settings.

### Custom Tools

Add custom tools for agents in `src/tools/`:

```javascript
// src/tools/database.js
export const databaseTool = {
  name: 'query_database',
  description: 'Query the database schema',
  async execute(params) {
    // Connect to DB and return schema
    return await db.query('SELECT * FROM information_schema.tables');
  }
};
```

Register in SDK:
```javascript
const session = await sdk.createSession({
  model: 'gpt-5',
  tools: [databaseTool]
});
```

### Rate Limiting

Implement per-repo rate limiting:

```javascript
// src/ratelimit/manager.js
export class RateLimitManager {
  async checkLimit(repo) {
    const key = `${repo}:${Date.now() / 3600000 | 0}`;
    const count = await redis.get(key);
    
    if (count >= 10) {
      throw new Error('Rate limit: max 10 agents/hour');
    }
    
    await redis.incr(key);
    await redis.expire(key, 3600);
  }
}
```

---

## Security Checklist

Before going to production:

- [ ] Webhook signature verification enabled
- [ ] Private key stored securely (not in code)
- [ ] Environment variables not committed to git
- [ ] Rate limiting implemented
- [ ] Input validation on all webhook data
- [ ] Error messages don't leak sensitive info
- [ ] HTTPS only (no HTTP)
- [ ] Regular dependency updates (Dependabot)
- [ ] Security scanning enabled (Snyk/CodeQL)
- [ ] Incident response plan documented

---

## Cost Optimization

### Tips to Reduce Costs

1. **Filter events early**:
   ```javascript
   // Only process specific labels
   const allowedLabels = ['agent:go', 'agent:sprint'];
   if (!allowedLabels.includes(label.name)) return;
   ```

2. **Cache context**:
   ```javascript
   // Cache repository context for 1 hour
   const context = await cache.get(`repo:${repo.name}`);
   if (!context) {
     context = await loadRepoContext(repo);
     await cache.set(`repo:${repo.name}`, context, 3600);
   }
   ```

3. **Batch requests**:
   ```javascript
   // Process related issues together
   const relatedIssues = await findRelatedIssues(issue);
   await sdk.createSession({
     context: { issues: [issue, ...relatedIssues] }
   });
   ```

4. **Monitor and alert**:
   ```javascript
   // Alert when approaching limits
   if (requestCount > LIMITS.alertThreshold) {
     await notifyAdmin('Approaching SDK limit');
   }
   ```

---

## Next Steps

### After Basic Setup

1. ✅ Test with 5-10 real issues
2. ✅ Monitor costs for 1 week
3. ✅ Gather feedback from team
4. ✅ Adjust agent prompts based on results

### Scale to More Repos

1. ✅ Document setup process
2. ✅ Create `kerrigan.json` template
3. ✅ Install app on additional repos
4. ✅ Build dashboard for monitoring

### Advanced Features

1. ⚠️ Multi-agent workflows
2. ⚠️ Cross-repo dependencies
3. ⚠️ Custom quality gates
4. ⚠️ Advanced analytics

---

## Support

### Resources

- **Main Investigation**: [docs/sdk-investigation.md](./sdk-investigation.md)
- **Architecture Proposal**: [docs/sdk-architecture-proposal.md](./sdk-architecture-proposal.md)
- **Copilot SDK Docs**: https://github.com/github/copilot-sdk
- **GitHub Apps Guide**: https://docs.github.com/en/apps

### Getting Help

1. Check troubleshooting section above
2. Review Railway logs: `railway logs`
3. Check GitHub App webhook deliveries
4. Open issue in Kerrigan repository

---

**Document Version**: 1.0  
**Last Updated**: January 24, 2026  
**Tested With**: GitHub Copilot SDK v1.0, Node.js 20.x, Railway
