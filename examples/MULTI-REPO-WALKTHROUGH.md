# Hello Multi-App: Multi-Repository Example Project

Complete example demonstrating API + Frontend + Infrastructure coordination across three repositories.

## Overview

This example project showcases how Kerrigan handles multi-repository coordination through three interconnected repositories:

1. **hello-multiapp-api** - Python FastAPI backend service
2. **hello-multiapp-frontend** - Static HTML/JS web interface
3. **hello-multiapp-infra** - Docker Compose infrastructure

Each repository contains a complete Kerrigan artifact set (spec.md, tasks.md, architecture.md, runbook.md, cost-plan.md) with cross-repository references demonstrating coordination patterns.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  hello-multiapp-infra (Infrastructure)              │
│  ├── docker-compose.yml (orchestrates services)    │
│  └── specs/ (coordination artifacts)               │
│                                                     │
│  ┌──────────────────┐      ┌────────────────────┐ │
│  │                  │      │                    │ │
│  │  API Service     │◄─────┤  Frontend Service  │ │
│  │  (Port 8000)     │ CORS │  (Port 3000)       │ │
│  │                  │      │                    │ │
│  └──────────────────┘      └────────────────────┘ │
│         ▲                           ▲              │
│         │                           │              │
│         └───────────────────────────┘              │
│              multiapp-network                      │
└─────────────────────────────────────────────────────┘

    hello-multiapp-api          hello-multiapp-frontend
    ├── main.py                 ├── index.html
    ├── Dockerfile              ├── Dockerfile
    └── specs/                  └── specs/
        ├── spec.md                 ├── spec.md
        ├── tasks.md                ├── tasks.md
        ├── architecture.md         ├── architecture.md
        ├── runbook.md              ├── runbook.md
        └── cost-plan.md            └── cost-plan.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git
- Modern web browser

### Setup All Repositories

Since these are example directories within the Kerrigan repository, they're already in the correct structure:

```bash
cd examples/
ls -la
# You should see:
# - hello-multiapp-api/
# - hello-multiapp-frontend/
# - hello-multiapp-infra/
```

### Deploy the Multi-App System

```bash
cd examples/hello-multiapp-infra
docker-compose up --build
```

This will:
1. Build the API container from `../hello-multiapp-api`
2. Build the frontend container from `../hello-multiapp-frontend`
3. Create a bridge network between them
4. Start both services with health checks
5. Make the system available at:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Test the System

1. **Open the frontend**: http://localhost:3000
   - The page automatically checks API connectivity
   - Shows API health status
   - Displays API version information

2. **Test API directly**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/version
   ```

3. **View logs**:
   ```bash
   docker-compose logs api
   docker-compose logs frontend
   ```

### Cleanup

```bash
docker-compose down
```

## Demonstration Scenarios

### Scenario 1: Kickoff - Multi-Repo Initialization

**Goal**: Show how a spec agent initializes all three repos with cross-repo references.

**Artifacts Created**:

Each repository contains a `specs/` folder with:
- `spec.md` - Includes `## Repositories` section listing all three repos
- `tasks.md` - Includes cross-repo dependencies
- `architecture.md` - Documents integration points with other repos
- `runbook.md` - References deployment coordination
- `cost-plan.md` - Allocates shared infrastructure costs

**Cross-Repo References**:

1. **API spec.md** references:
   - Frontend (as consumer of API endpoints)
   - Infra (as deployment orchestrator)

2. **Frontend spec.md** references:
   - API (as dependency for endpoints)
   - Infra (as deployment orchestrator)

3. **Infra spec.md** references:
   - Both API and Frontend (as services to orchestrate)

**Key Pattern**: Each repo knows about the others through artifact documentation, not code dependencies.

**Try It**:
```bash
# View cross-repo references
grep -r "hello-multiapp" examples/hello-multiapp-*/specs/spec.md

# Expected: Each spec.md mentions the other repos
```

### Scenario 2: Implementation - Coordinated Development

**Goal**: Show how multiple SWE agents work on different repos with coordination.

**Workflow**:

1. **SWE Agent works on API** (hello-multiapp-api):
   - Implements FastAPI endpoints
   - Configures CORS for frontend
   - Creates Dockerfile for infra
   - Updates tasks.md marking "Blocks frontend implementation"

2. **SWE Agent works on Frontend** (hello-multiapp-frontend):
   - Checks API tasks.md for "ready" status
   - Implements API integration
   - Creates Dockerfile for infra
   - Updates tasks.md marking "Blocks infra integration"

3. **SWE Agent works on Infra** (hello-multiapp-infra):
   - Checks both API and Frontend tasks.md
   - Creates docker-compose.yml referencing both
   - Configures networking and dependencies
   - Tests end-to-end integration

**Key Pattern**: Task dependencies create coordination without tight coupling.

**Try It**:
```bash
# View task dependencies
grep -A5 "Cross-repo" examples/hello-multiapp-*/specs/tasks.md

# See how tasks reference other repos:
# - API: "Blocks: hello-multiapp-frontend implementation"
# - Frontend: "Blocked by: hello-multiapp-api implementation"
# - Infra: "Blocked by: Both API and Frontend containers"
```

### Scenario 3: Deployment - Ops Coordination

**Goal**: Show how an ops agent deploys using all three repos' runbooks.

**Workflow**:

1. **Ops Agent reads Infra runbook** (hello-multiapp-infra/specs/runbook.md):
   - Primary deployment instructions
   - References API and Frontend runbooks for details

2. **Ops Agent checks API runbook** (hello-multiapp-api/specs/runbook.md):
   - API-specific configuration
   - Health check endpoints
   - Troubleshooting API issues

3. **Ops Agent checks Frontend runbook** (hello-multiapp-frontend/specs/runbook.md):
   - Frontend-specific configuration
   - CORS requirements
   - Troubleshooting frontend issues

4. **Ops Agent executes deployment**:
   ```bash
   cd hello-multiapp-infra
   docker-compose up --build
   ```

5. **Ops Agent validates deployment**:
   - API health: `curl http://localhost:8000/health`
   - Frontend: Open http://localhost:3000
   - Integration: Frontend successfully calls API

6. **Ops Agent updates status** across all repos:
   - Could update status.json in each repo
   - Documents deployment in each runbook
   - Tracks issues in each repository

**Key Pattern**: Runbooks coordinate deployment across repos while staying decentralized.

**Try It**:
```bash
# Follow the multi-repo deployment
cd examples/hello-multiapp-infra
docker-compose up --build

# In another terminal, monitor all services
docker-compose logs -f

# Validate each service
curl http://localhost:8000/health    # API
curl http://localhost:8000/version   # API version
open http://localhost:3000            # Frontend

# Check cross-repo integration
# Frontend should show "API Connected Successfully!"
```

## Multi-Repo Coordination Patterns

### Pattern 1: Repository References in Specs

Each `spec.md` includes a `## Repositories` section:

```markdown
## Repositories

- **hello-multiapp-api**
  - Role: Backend service
  - Dependencies: None
  - Dependents: hello-multiapp-frontend

- **hello-multiapp-frontend**
  - Role: Web interface
  - Dependencies: hello-multiapp-api
  - Dependents: None

- **hello-multiapp-infra**
  - Role: Deployment orchestration
  - Dependencies: Both API and Frontend
  - Dependents: None
```

### Pattern 2: Cross-Repo Task Dependencies

Each `tasks.md` includes cross-repo dependency markers:

```markdown
## Cross-Repository Dependencies

**Blocks:**
- hello-multiapp-frontend implementation

**Blocked by:**
- None

**Coordinates with:**
- hello-multiapp-infra: Container deployment
```

### Pattern 3: Integration Points in Architecture

Each `architecture.md` documents integration:

```markdown
## Multi-Repo Integration

### Integration with hello-multiapp-api
- API endpoints consumed
- CORS configuration required
- Network connectivity needed

### Integration with hello-multiapp-infra
- Docker container orchestration
- Environment variables
- Health checks
```

### Pattern 4: Cost Allocation

Each `cost-plan.md` allocates shared costs:

```markdown
## Shared Infrastructure Costs

| Component | Total | This Repo | Notes |
|-----------|-------|-----------|-------|
| Orchestration | $30/mo | $10/mo | 33% allocation |
| Monitoring | $45/mo | $15/mo | 33% allocation |
| CI/CD | $20/mo | $7/mo | 33% allocation |
```

### Pattern 5: Runbook Coordination

Each `runbook.md` references other repos:

```markdown
## Multi-Repo Deployment

See hello-multiapp-infra/specs/runbook.md for orchestration.

This service requires:
- hello-multiapp-api running (check API health)
- Network configuration from infra repo
```

## Learning Paths

### For New Users

1. **Start with infrastructure**:
   ```bash
   cd examples/hello-multiapp-infra
   cat README.md
   ```

2. **Deploy the system**:
   ```bash
   docker-compose up --build
   ```

3. **Explore while running**:
   - Test frontend at http://localhost:3000
   - Read API docs at http://localhost:8000/docs
   - Review logs: `docker-compose logs`

4. **Study the artifacts**:
   ```bash
   # Compare how each repo documents the same integration
   diff examples/hello-multiapp-api/specs/spec.md \
        examples/hello-multiapp-frontend/specs/spec.md
   ```

### For Agent Developers

1. **Study cross-repo references**:
   ```bash
   grep -r "repositories:" examples/hello-multiapp-*/specs/
   ```

2. **Understand task dependencies**:
   ```bash
   grep -r "Cross-repo" examples/hello-multiapp-*/specs/tasks.md
   ```

3. **Review coordination patterns**:
   - How does API know about Frontend? (Through specs)
   - How does Frontend depend on API? (Through tasks)
   - How does Infra orchestrate both? (Through docker-compose)

### For Teams Adopting Multi-Repo

1. **Assess if multi-repo is right**:
   - Multiple teams owning different services? ✅ Multi-repo
   - Services scale independently? ✅ Multi-repo
   - Always deployed together? ⚠️ Consider monorepo
   - Small project, single team? ⚠️ Consider monorepo

2. **Start with this example**:
   - Clone and deploy it
   - Modify one service and redeploy
   - Add a new endpoint to API, consume in Frontend
   - Practice coordination patterns

3. **Adapt to your needs**:
   - Replace FastAPI with your backend tech
   - Replace static frontend with React/Vue/etc
   - Replace Docker Compose with Kubernetes/ECS
   - Keep the artifact coordination patterns

## Key Takeaways

### What This Example Demonstrates

✅ **Artifact-driven coordination**: No external tools needed, everything in Git  
✅ **Clear dependencies**: Each repo knows what it needs  
✅ **Decentralized but coordinated**: No single point of failure  
✅ **Agent-friendly**: Specs are readable by both humans and AI  
✅ **Scalable pattern**: Works with 2 repos or 20 repos  

### What Makes This Different

Traditional multi-repo approaches:
- ❌ Require external tracking tools (Jira, spreadsheets)
- ❌ Dependencies implicit in code only
- ❌ Coordination happens in meetings
- ❌ Documentation scattered across wikis

Kerrigan multi-repo approach:
- ✅ All coordination in Git artifacts
- ✅ Dependencies explicit in specs
- ✅ Coordination happens through PRs
- ✅ Documentation lives with code

### Success Metrics

This example succeeds if:
- [ ] New users can deploy in < 5 minutes
- [ ] Agents understand cross-repo context
- [ ] Pattern applicable to real projects
- [ ] Coordination scales to 5+ repos
- [ ] No external tools required

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are available
lsof -i :3000  # Frontend
lsof -i :8000  # API

# Check Docker is running
docker ps

# View detailed logs
docker-compose logs
```

### Frontend Can't Connect to API

```bash
# Verify API is healthy
curl http://localhost:8000/health

# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS http://localhost:8000/health -v

# Check network configuration
docker network ls
docker network inspect hello-multiapp-infra_multiapp-network
```

### Changes Not Reflected

```bash
# Rebuild containers
docker-compose up --build

# Or rebuild specific service
docker-compose up --build api
```

## Next Steps

### Extend This Example

1. **Add a database service**:
   - Create hello-multiapp-db repository
   - Update API to use database
   - Update infra to orchestrate all three

2. **Add authentication**:
   - Add auth endpoints to API
   - Update frontend with login UI
   - Coordinate via specs

3. **Add monitoring**:
   - Create hello-multiapp-monitoring repo
   - Add Prometheus/Grafana
   - Update all runbooks

### Apply to Your Project

1. **Identify services**: What can be separate repos?
2. **Define boundaries**: What's the API contract?
3. **Create artifacts**: Spec, tasks, architecture, runbook, cost-plan
4. **Document dependencies**: Who depends on whom?
5. **Test coordination**: Deploy end-to-end

## Documentation

Complete documentation for each repository:

### hello-multiapp-api
- [README](hello-multiapp-api/README.md)
- [Specification](hello-multiapp-api/specs/spec.md)
- [Architecture](hello-multiapp-api/specs/architecture.md)
- [Tasks](hello-multiapp-api/specs/tasks.md)
- [Runbook](hello-multiapp-api/specs/runbook.md)
- [Cost Plan](hello-multiapp-api/specs/cost-plan.md)

### hello-multiapp-frontend
- [README](hello-multiapp-frontend/README.md)
- [Specification](hello-multiapp-frontend/specs/spec.md)
- [Architecture](hello-multiapp-frontend/specs/architecture.md)
- [Tasks](hello-multiapp-frontend/specs/tasks.md)
- [Runbook](hello-multiapp-frontend/specs/runbook.md)
- [Cost Plan](hello-multiapp-frontend/specs/cost-plan.md)

### hello-multiapp-infra
- [README](hello-multiapp-infra/README.md)
- [Specification](hello-multiapp-infra/specs/spec.md)
- [Architecture](hello-multiapp-infra/specs/architecture.md)
- [Tasks](hello-multiapp-infra/specs/tasks.md)
- [Runbook](hello-multiapp-infra/specs/runbook.md)
- [Cost Plan](hello-multiapp-infra/specs/cost-plan.md)

## References

- [Kerrigan Milestone 7 Spec](../../specs/projects/kerrigan/milestone-7-spec.md)
- [Kerrigan Milestone 7 Tasks](../../specs/projects/kerrigan/milestone-7-tasks.md)
- [Multi-Repo Playbook](../../playbooks/multi-repo.md) (to be created)
- [Hello API Example](../hello-api) (single-repo reference)

## License

MIT (see root LICENSE file)
