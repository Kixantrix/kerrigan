# Cost Plan: Hello Multi-App API

## Overview

Cost analysis for the hello-multiapp-api service within the multi-repository architecture.

## Development Costs

### One-Time Costs

| Item | Hours | Rate | Cost | Notes |
|------|-------|------|------|-------|
| Initial API development | 2 | $150/hr | $300 | FastAPI implementation |
| Docker containerization | 1 | $150/hr | $150 | Dockerfile, testing |
| Documentation | 1.5 | $150/hr | $225 | README, specs artifacts |
| Testing & validation | 1 | $150/hr | $150 | Local and Docker testing |
| **Total Development** | **5.5** | | **$825** | |

### Maintenance Costs (Annual)

| Item | Hours/Year | Rate | Annual Cost | Notes |
|------|------------|------|-------------|-------|
| Dependency updates | 4 | $150/hr | $600 | Security patches, Python/FastAPI updates |
| Bug fixes | 2 | $150/hr | $300 | Minor issues |
| Documentation updates | 1 | $150/hr | $150 | Keep specs current |
| **Total Maintenance** | **7** | | **$1,050** | |

## Infrastructure Costs

### Compute Resources

**Development/Testing:**
- Local development: $0 (developer machines)
- Docker resources: Minimal (part of development environment)

**Production (Small Scale):**

| Resource | Specification | Monthly Cost | Annual Cost | Notes |
|----------|--------------|--------------|-------------|-------|
| Container instance | 0.25 vCPU, 512MB RAM | $10 | $120 | Serverless container service |
| Load balancer | Basic tier | $15 | $180 | Optional for HA |
| **Total Infrastructure** | | **$25/month** | **$300/year** | Single instance |

**Production (Medium Scale with HA):**

| Resource | Specification | Monthly Cost | Annual Cost | Notes |
|----------|--------------|--------------|-------------|-------|
| Container instances (3x) | 0.5 vCPU, 1GB RAM each | $60 | $720 | High availability |
| Load balancer | Standard tier | $25 | $300 | Health checks, SSL |
| Container registry | 100GB storage | $5 | $60 | Docker image storage |
| **Total Infrastructure** | | **$90/month** | **$1,080/year** | HA deployment |

### Networking

| Item | Monthly Cost | Annual Cost | Notes |
|------|--------------|-------------|-------|
| Data transfer (outbound) | $5-20 | $60-240 | Depends on usage |
| API Gateway (if used) | $3.50 per million requests | Variable | Optional |

## Shared Costs with Multi-Repo Project

These costs are shared across all three repositories:

### Infrastructure (via hello-multiapp-infra)

| Item | Total Cost | API Share (33%) | Notes |
|------|-----------|----------------|-------|
| Container orchestration | $30/month | $10/month | Kubernetes/ECS cluster base cost |
| Monitoring & logging | $45/month | $15/month | CloudWatch, Datadog, etc. |
| CI/CD pipeline | $20/month | $7/month | GitHub Actions, build minutes |
| Domain & SSL | $15/year | $5/year | Shared domain costs |
| **Total Shared** | **$95/month** | **$32/month** | **$384/year** |

### Coordination Overhead

| Item | Hours/Year | Rate | Annual Cost | Notes |
|------|------------|------|-------------|-------|
| Cross-repo coordination | 8 | $150/hr | $1,200 | Sync changes across repos |
| Integration testing | 6 | $150/hr | $900 | Test multi-repo interactions |
| Multi-repo documentation | 4 | $150/hr | $600 | Maintain coordination docs |
| **Total Coordination** | **18** | | **$2,700** | Divided among 3 repos = $900/repo |

## AI Agent Costs

### Kerrigan Workflow Costs

| Phase | Agent Role | Estimated Tokens | Cost per Run | Notes |
|-------|-----------|------------------|--------------|-------|
| Specification | @role.spec | 50k | $1.00 | Create specs/ artifacts |
| Implementation | @role.swe | 100k | $2.00 | Write API code |
| Operations | @role.ops | 30k | $0.60 | Deploy and monitor |
| Review | @role.reviewer | 40k | $0.80 | Code review |
| **Total per Iteration** | | **220k** | **$4.40** | |

**Annual AI Costs** (assuming 4 major iterations):
- Iterations: 4 × $4.40 = $17.60
- Ad-hoc changes: ~$20
- **Total**: ~$40/year

## Total Cost Summary

### Year 1 (Including Development)

| Category | Cost | Notes |
|----------|------|-------|
| Development (one-time) | $825 | Initial implementation |
| Infrastructure (production) | $300 | Small scale single instance |
| Shared infrastructure | $384 | API's share of multi-repo costs |
| Coordination overhead | $900 | API's share of multi-repo coordination |
| AI agent usage | $40 | Kerrigan workflow |
| **Total Year 1** | **$2,449** | |

### Ongoing (Annual after Year 1)

| Category | Cost | Notes |
|----------|------|-------|
| Maintenance | $1,050 | Updates and fixes |
| Infrastructure (production) | $300 | Small scale |
| Shared infrastructure | $384 | Multi-repo share |
| Coordination overhead | $900 | Multi-repo sync |
| AI agent usage | $40 | Kerrigan workflow |
| **Total Ongoing** | **$2,674/year** | |

## Cost Optimization Opportunities

### Short-term
- Use serverless containers (pay per execution)
- Leverage free tier for development/testing
- Share container registry across all repos
- Use managed services to reduce maintenance

### Long-term
- Optimize container image size (faster deploy, less storage)
- Implement caching to reduce compute time
- Automate updates to reduce maintenance hours
- Consider consolidating repos if coordination overhead high

## Cost Allocation

Within the multi-repo architecture:
- **API Repository**: 33% of shared costs (this document)
- **Frontend Repository**: 33% of shared costs
- **Infrastructure Repository**: 34% of shared costs (slightly higher for orchestration)

## Budget Alerts

Recommended alerts:
- Infrastructure costs exceed $40/month (small scale) or $120/month (HA)
- Shared infrastructure costs exceed $120/month
- AI agent costs exceed $10/month
- Data transfer costs exceed $30/month

## Cost Tracking

Track costs through:
- Cloud provider billing dashboards
- Infrastructure-as-Code cost estimation tools
- AI API usage dashboards (OpenAI, Anthropic)
- Time tracking for development/maintenance

## Multi-Repo Cost Considerations

**Advantages:**
- Clear cost attribution per service
- Independent scaling (only scale what needs it)
- Can decommission API without affecting frontend

**Disadvantages:**
- Coordination overhead ($900/year)
- Shared infrastructure management complexity
- Integration testing infrastructure costs

**Break-even Analysis:**
- Multi-repo overhead: ~$900/year
- Worth it if: Services scale independently OR different teams own services
- Not worth it if: Always deployed together AND no team boundaries

## Related Documents

- Infrastructure costs: `../hello-multiapp-infra/specs/cost-plan.md`
- Frontend costs: `../hello-multiapp-frontend/specs/cost-plan.md`
- Shared costs breakdown: See "Shared Costs" section above
