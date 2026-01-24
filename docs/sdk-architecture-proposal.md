# Kerrigan SDK Architecture Proposal

**Version**: 1.0  
**Date**: January 2026  
**Status**: Proposal  

---

## Executive Summary

This document proposes an architecture for autonomous agent triggering in Kerrigan using the GitHub Copilot SDK. The architecture supports both single-repo (Kerrigan itself) and multi-repo (Kerrigan as a service) patterns.

**Key Benefits**:
- ✅ Issues automatically trigger agent work (no @-mention required)
- ✅ Service account authentication (no user OAuth)
- ✅ Minimal per-repo setup (one config file)
- ✅ Central management of prompts and workflows
- ✅ No workflow file pollution in target repos

---

## Architecture Option 1: Hybrid (Recommended for Kerrigan)

**Use Case**: Enhance Kerrigan repository with autonomous triggering while keeping existing automation

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kerrigan Repository                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GitHub Actions (Keep)                                   │  │
│  │  ├─ ci.yml (artifact validation)                         │  │
│  │  ├─ agent-gates.yml (autonomy control)                   │  │
│  │  ├─ auto-generate-issues.yml (issue creation)            │  │
│  │  └─ auto-assign-reviewers.yml (reviewer assignment)      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Kerrigan SDK Service (New)                              │  │
│  │  ├─ Webhook endpoint: /webhook/issues                    │  │
│  │  ├─ Copilot SDK client                                   │  │
│  │  ├─ GitHub App authentication                            │  │
│  │  └─ Agent orchestrator                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  External Service     │
                    │  (Railway/Render)     │
                    │                       │
                    │  Node.js + SDK        │
                    │  Port: 3000          │
                    └───────────────────────┘
```

### Flow: Issue to PR

```
┌──────────────┐
│ User creates │
│ issue #123   │
└──────┬───────┘
       │
       ▼
┌──────────────┐        ┌─────────────────────┐
│ User adds    │───────▶│ GitHub webhook      │
│ "agent:go"   │        │ fires to service    │
└──────────────┘        └──────────┬──────────┘
                                   │
       ┌───────────────────────────┘
       │
       ▼
┌──────────────────────┐
│ SDK Service          │
│ 1. Verify signature  │
│ 2. Parse event       │
│ 3. Load issue        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Copilot SDK          │
│ 1. Create session    │
│ 2. Read issue + repo │
│ 3. Plan solution     │
│ 4. Generate code     │
│ 5. Run tests         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ GitHub API           │
│ 1. Create branch     │
│ 2. Commit changes    │
│ 3. Create PR         │
│ 4. Link to issue     │
└──────────────────────┘
```

### Components

#### 1. Webhook Handler

**Responsibilities**:
- Receive webhooks from GitHub
- Verify webhook signatures
- Filter events (only process relevant ones)
- Trigger agent sessions

**Code Structure**:
```javascript
// src/webhook/handler.js
export class WebhookHandler {
  async handle(req, res) {
    // 1. Verify signature
    if (!this.verifySignature(req)) {
      return res.status(401).send('Invalid signature');
    }

    // 2. Parse event
    const event = this.parseEvent(req.body);
    
    // 3. Check if we should process
    if (!this.shouldProcess(event)) {
      return res.status(200).send('Skipped');
    }

    // 4. Trigger agent (async)
    this.triggerAgent(event).catch(console.error);
    
    return res.status(202).send('Processing');
  }

  shouldProcess(event) {
    // Only process issue labeled with agent:go
    return event.action === 'labeled' && 
           event.label?.name === 'agent:go';
  }
}
```

#### 2. Agent Orchestrator

**Responsibilities**:
- Load appropriate agent prompt
- Create Copilot SDK session
- Monitor session progress
- Handle errors and retries

**Code Structure**:
```javascript
// src/agent/orchestrator.js
export class AgentOrchestrator {
  async triggerAgent(issue, repo) {
    // 1. Determine agent type from labels
    const agentType = this.determineAgentType(issue.labels);
    
    // 2. Load agent prompt
    const prompt = await this.loadPrompt(agentType);
    
    // 3. Create context
    const context = {
      repo: repo.full_name,
      issue: issue.number,
      title: issue.title,
      body: issue.body,
      labels: issue.labels.map(l => l.name)
    };

    // 4. Create SDK session
    const session = await this.sdk.createSession({
      model: 'gpt-5',
      context: context
    });

    // 5. Send prompt
    await session.send({
      prompt: this.buildPrompt(prompt, context)
    });

    // 6. Monitor progress
    this.monitorSession(session, issue);
  }

  determineAgentType(labels) {
    if (labels.some(l => l.name === 'role:swe')) return 'swe';
    if (labels.some(l => l.name === 'role:architect')) return 'architect';
    if (labels.some(l => l.name === 'role:testing')) return 'testing';
    return 'swe'; // default
  }
}
```

#### 3. Prompt Manager

**Responsibilities**:
- Store agent prompts
- Load prompts by type
- Template prompt with context

**Prompt Storage**:
```
kerrigan-service/
├── prompts/
│   ├── swe.md           # Software engineer agent
│   ├── architect.md     # Architecture agent
│   ├── testing.md       # Testing agent
│   └── default.md       # Default agent
```

**Code Structure**:
```javascript
// src/prompts/manager.js
export class PromptManager {
  async loadPrompt(type) {
    const path = `./prompts/${type}.md`;
    return await fs.readFile(path, 'utf-8');
  }

  buildPrompt(template, context) {
    return template
      .replace('{{repo}}', context.repo)
      .replace('{{issue}}', context.issue)
      .replace('{{title}}', context.title)
      .replace('{{body}}', context.body);
  }
}
```

#### 4. Authentication Manager

**Responsibilities**:
- Generate GitHub App installation tokens
- Refresh tokens before expiry
- Provide tokens to SDK

**Code Structure**:
```javascript
// src/auth/manager.js
import { App } from 'octokit';

export class AuthManager {
  constructor() {
    this.app = new App({
      appId: process.env.APP_ID,
      privateKey: process.env.PRIVATE_KEY
    });
  }

  async getToken(installationId) {
    // Check cache
    if (this.isTokenValid(installationId)) {
      return this.tokenCache.get(installationId);
    }

    // Generate new token
    const token = await this.app.getInstallationAccessToken({
      installationId
    });

    // Cache token (expires in 1 hour)
    this.tokenCache.set(installationId, {
      token,
      expiresAt: Date.now() + 3600000
    });

    return token;
  }

  isTokenValid(installationId) {
    const cached = this.tokenCache.get(installationId);
    return cached && cached.expiresAt > Date.now() + 300000; // 5 min buffer
  }
}
```

### Deployment

**Option 1: Railway (Recommended)**
- Simple deployment from GitHub
- Auto-scaling
- Built-in monitoring
- Cost: ~$5-20/month

**Steps**:
1. Create Railway project
2. Connect to GitHub repo
3. Set environment variables
4. Deploy

**Option 2: Self-hosted**
- Full control
- Can run on existing infrastructure
- Cost: Variable (infrastructure cost)

**Steps**:
1. Clone service repo
2. Install dependencies: `npm install`
3. Set environment variables
4. Run with PM2 or systemd
5. Configure reverse proxy (nginx)

### Configuration

**Environment Variables**:
```bash
# GitHub App
APP_ID=123456
PRIVATE_KEY_PATH=/path/to/private-key.pem
INSTALLATION_ID=7890123

# Webhook
WEBHOOK_SECRET=your-secret

# Service
PORT=3000
NODE_ENV=production

# Copilot (auto-set by auth manager)
# COPILOT_GITHUB_TOKEN=<generated>
```

### Monitoring

**Health Check Endpoint**:
```javascript
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    uptime: process.uptime(),
    sdk: sdk.isConnected(),
    github: github.isAuthenticated()
  });
});
```

**Metrics to Track**:
- Webhook events received
- Agent sessions triggered
- PRs created successfully
- Errors encountered
- SDK requests consumed
- Response times

---

## Architecture Option 2: Central Service (Multi-Repo)

**Use Case**: Provide Kerrigan as a service to multiple repositories/organizations

### System Overview

```
                    ┌────────────────────────────┐
                    │  Central Kerrigan Service  │
                    │  (Organization-level)      │
                    │                            │
                    │  ┌──────────────────────┐  │
                    │  │  Webhook Router      │  │
                    │  └──────────┬───────────┘  │
                    │             │              │
                    │  ┌──────────▼───────────┐  │
                    │  │  Config Manager      │  │
                    │  │  (loads repo config) │  │
                    │  └──────────┬───────────┘  │
                    │             │              │
                    │  ┌──────────▼───────────┐  │
                    │  │  Agent Orchestrator  │  │
                    │  │  (routes to agents)  │  │
                    │  └──────────┬───────────┘  │
                    │             │              │
                    │  ┌──────────▼───────────┐  │
                    │  │  Copilot SDK Pool    │  │
                    │  │  (manages sessions)  │  │
                    │  └──────────────────────┘  │
                    └────────────┬───────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
    ┌──────────┐           ┌──────────┐           ┌──────────┐
    │ Repo A   │           │ Repo B   │           │ Repo C   │
    │ config   │           │ config   │           │ config   │
    └──────────┘           └──────────┘           └──────────┘
```

### Per-Repo Configuration

**`kerrigan.json`** (at repository root):
```json
{
  "kerrigan": {
    "version": "1.0",
    "enabled": true,
    
    "triggers": {
      "auto_trigger_label": "agent:go",
      "sprint_label": "agent:sprint"
    },
    
    "roles": {
      "default": "role:swe",
      "labels": {
        "role:swe": "swe",
        "role:architect": "architect",
        "role:testing": "testing",
        "role:spec": "spec"
      }
    },
    
    "quality": {
      "max_lines_per_file": 800,
      "require_tests": true,
      "require_docs": true
    },
    
    "prompts": {
      "source": "default",
      "overrides": {
        "swe": "custom-swe-prompt"
      }
    },
    
    "notifications": {
      "slack_webhook": "https://hooks.slack.com/...",
      "notify_on": ["pr_created", "pr_merged", "error"]
    }
  }
}
```

### Components

#### 1. Config Manager

**Responsibilities**:
- Load `kerrigan.json` from repos
- Cache configurations
- Validate config schemas
- Apply defaults for missing values

**Code Structure**:
```javascript
// src/config/manager.js
export class ConfigManager {
  async loadConfig(repo) {
    // Check cache
    if (this.cache.has(repo)) {
      return this.cache.get(repo);
    }

    try {
      // Fetch from repo
      const { data } = await this.github.repos.getContent({
        owner: repo.owner,
        repo: repo.name,
        path: 'kerrigan.json'
      });

      const config = JSON.parse(
        Buffer.from(data.content, 'base64').toString()
      );

      // Validate and apply defaults
      const validated = this.validateConfig(config);
      
      // Cache for 5 minutes
      this.cache.set(repo, validated, 300000);
      
      return validated;
    } catch (error) {
      // Return default config if file not found
      return this.getDefaultConfig();
    }
  }

  validateConfig(config) {
    // Validate against schema
    // Apply defaults for missing values
    return {
      ...this.defaults,
      ...config.kerrigan
    };
  }
}
```

#### 2. Webhook Router

**Responsibilities**:
- Route webhooks to appropriate handlers
- Load per-repo configuration
- Decide if event should trigger agent

**Code Structure**:
```javascript
// src/webhook/router.js
export class WebhookRouter {
  async route(event) {
    // 1. Load repo config
    const config = await this.configManager.loadConfig(event.repository);

    // 2. Check if Kerrigan is enabled
    if (!config.enabled) {
      return { status: 'disabled' };
    }

    // 3. Check if event matches triggers
    if (!this.matchesTrigger(event, config)) {
      return { status: 'no_match' };
    }

    // 4. Route to orchestrator
    return await this.orchestrator.handle(event, config);
  }

  matchesTrigger(event, config) {
    if (event.action !== 'labeled') return false;
    
    const triggerLabels = [
      config.triggers.auto_trigger_label,
      config.triggers.sprint_label
    ];
    
    return triggerLabels.includes(event.label?.name);
  }
}
```

#### 3. Dashboard

**Purpose**: Provide visibility into all monitored repos

**Features**:
- List all repositories with Kerrigan enabled
- Show active issues and PRs
- Display agent activity in real-time
- Show cost metrics (SDK usage)
- Historical trends

**Tech Stack**: Next.js + React + TailwindCSS

**Example Routes**:
- `/` - Dashboard home (all repos)
- `/repos/:owner/:repo` - Single repo view
- `/agents` - Active agent sessions
- `/metrics` - Usage and cost metrics
- `/settings` - Service configuration

**Screenshot (Conceptual)**:
```
┌────────────────────────────────────────────────────────────┐
│ Kerrigan Dashboard                          🟢 Service OK  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Monitored Repositories: 12                                │
│ Active Agents: 3                                           │
│ Open PRs: 5                                                │
│ SDK Usage: 245/1500 requests this month                   │
│                                                            │
│ ┌────────────────────────────────────────────────────┐   │
│ │ org/project-alpha                           Active │   │
│ │ ├─ Issue #42: Add authentication                  │   │
│ │ │  Agent: 🟢 Working (65% complete)               │   │
│ │ │  ETA: ~5 minutes                                │   │
│ │ └─ PR #41: Fix login bug [ready for review]      │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
│ ┌────────────────────────────────────────────────────┐   │
│ │ org/project-beta                            Idle   │   │
│ │ └─ No active work                                  │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
│ ┌────────────────────────────────────────────────────┐   │
│ │ org/project-gamma                           Active │   │
│ │ ├─ Issue #15: Refactor API [queued]              │   │
│ │ └─ PR #14: Add tests [merged 2h ago]             │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Scaling Considerations

**Database**: Store state for reliability
- Repository configurations (cache)
- Active agent sessions
- Historical metrics
- Error logs

**Queue**: Handle high webhook volume
- Redis or RabbitMQ for job queue
- Ensures no webhook is lost
- Enables rate limiting

**Architecture with Queue**:
```
Webhook → Queue → Workers → SDK Sessions
            ↓
         Database
```

### Cost at Scale

**Assumptions**:
- 20 repositories
- 100 issues/month total
- 40 SDK requests per issue average

**Costs**:
- Copilot Enterprise (5 seats): $195/month
- Infrastructure (Railway Business): $20/month
- Database (Postgres): $5/month
- Monitoring (Betterstack): $10/month
- **Total**: ~$230/month

**Per-Repo Cost**: $11.50/month (~50 cents per issue)

---

## Migration Path

### Phase 1: Prototype (Weeks 1-2)

**Goal**: Validate the concept with minimal investment

**Tasks**:
- ✅ Set up basic Node.js service
- ✅ Implement webhook receiver
- ✅ Integrate Copilot SDK
- ✅ Test with 1-2 simple issues
- ✅ Measure cost per issue

**Success Criteria**:
- Agent successfully creates PR from issue
- Cost per issue < $1
- No security issues identified

### Phase 2: Kerrigan Integration (Weeks 3-4)

**Goal**: Deploy to Kerrigan repository

**Tasks**:
- ✅ Create GitHub App for Kerrigan
- ✅ Deploy service to Railway
- ✅ Configure webhooks
- ✅ Test with real Kerrigan issues
- ✅ Monitor for 1-2 weeks

**Success Criteria**:
- At least 5 issues processed successfully
- No workflow disruptions
- Cost within budget ($50/month)
- Team satisfied with results

### Phase 3: Hardening (Weeks 5-6)

**Goal**: Production-ready service

**Tasks**:
- ✅ Add comprehensive error handling
- ✅ Implement monitoring and alerting
- ✅ Security audit and fixes
- ✅ Performance optimization
- ✅ Documentation complete

**Success Criteria**:
- 99% uptime over 2 weeks
- All security issues resolved
- Documentation allows new team member to deploy

### Phase 4: Multi-Repo (Weeks 7-10)

**Goal**: Support additional repositories

**Tasks**:
- ✅ Implement config manager
- ✅ Create `kerrigan.json` schema
- ✅ Build dashboard UI
- ✅ Test with 2-3 pilot repos
- ✅ Gather feedback and iterate

**Success Criteria**:
- 3+ repos successfully onboarded
- Setup time < 5 minutes per repo
- No conflicts with existing workflows
- Positive feedback from pilot users

### Phase 5: Public Release (Week 11+)

**Goal**: Open-source and promote

**Tasks**:
- ✅ Open-source the service
- ✅ Create onboarding docs
- ✅ Video tutorial
- ✅ Blog post announcement
- ✅ Community support channels

**Success Criteria**:
- 10+ external repos using Kerrigan
- Active community contributions
- Positive feedback and testimonials

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SDK API changes | High | Medium | Monitor releases, maintain version compatibility |
| Service downtime | Medium | Low | Use managed hosting, implement health checks |
| Rate limits hit | Medium | Medium | Implement queuing, monitor usage closely |
| Security breach | Critical | Low | Regular audits, follow best practices |
| High costs | Medium | Medium | Set up alerts, optimize usage patterns |

### Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Poor adoption | Medium | Medium | Start with pilot, gather feedback early |
| Maintenance burden | Medium | Low | Automate deployment, good monitoring |
| Documentation debt | Low | High | Write docs as you build, not after |
| Support overhead | Medium | Medium | Build self-service tools, FAQ |

### Mitigation Strategies

**1. SDK Changes**
- Subscribe to SDK release notifications
- Run automated tests against new versions
- Maintain backward compatibility layer
- Have rollback plan

**2. Cost Overruns**
- Set hard limits in code (max sessions/hour)
- Monitor costs daily
- Alert when approaching limits
- Optimize prompts to reduce requests

**3. Security**
- Regular penetration testing
- Automated security scanning (Dependabot, Snyk)
- Incident response plan
- Regular token rotation

**4. Reliability**
- Use managed services (Railway, Render)
- Implement circuit breakers
- Queue webhooks for retry
- Health check monitoring

---

## Alternative Approaches Considered

### Alternative 1: GitHub Actions + SDK

**Idea**: Run SDK from GitHub Actions instead of external service

**Pros**:
- No external infrastructure
- Integrated with existing workflows
- No webhooks needed

**Cons**:
- ❌ Actions can't trigger on label add (must use Issues API)
- ❌ `GITHUB_TOKEN` has limited scope
- ❌ Cold starts for each run
- ❌ More complex to manage state

**Verdict**: ❌ Not recommended - External service is cleaner

### Alternative 2: Copilot CLI Direct

**Idea**: Use Copilot CLI directly without SDK

**Pros**:
- Simpler (no SDK dependency)
- Direct control

**Cons**:
- ❌ Less programmatic control
- ❌ Harder to integrate
- ❌ No multi-language support
- ❌ More manual work

**Verdict**: ❌ Not recommended - SDK provides better abstraction

### Alternative 3: Custom Agent Implementation

**Idea**: Build our own agent without Copilot

**Pros**:
- Full control
- Potentially lower cost

**Cons**:
- ❌ Massive development effort
- ❌ Need to maintain AI models
- ❌ Lower quality than Copilot
- ❌ Security and compliance burden

**Verdict**: ❌ Not recommended - Reinventing the wheel

---

## Conclusion

The proposed architecture using GitHub Copilot SDK provides a clear path to autonomous agent triggering and multi-repo support. The hybrid approach is recommended for Kerrigan itself, with a clear migration path to central service for multi-repo adoption.

**Next Steps**:
1. Review and approve this proposal
2. Begin Phase 1 prototype (weeks 1-2)
3. Evaluate results and decide on Phase 2

**Decision Point**: After Phase 1, decide whether to:
- ✅ Continue with Phases 2-3 (recommended if prototype succeeds)
- ⚠️ Adjust approach based on learnings
- ❌ Abandon if costs or complexity too high

---

**Document Version**: 1.0  
**Last Updated**: January 24, 2026  
**Next Review**: After Phase 1 completion
