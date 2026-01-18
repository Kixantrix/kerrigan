# Multi-Repository Project Management

## Overview

This playbook guides teams through managing projects that span multiple GitHub repositories, enabling coordinated agent work across repos while maintaining clear boundaries and handoffs.

**Target audience**: Project leads, architects, and agents working on multi-repository projects.

**Related documents**:
- `specs/kerrigan/020-artifact-contracts.md` - Multi-repo specification schema
- `playbooks/project-lifecycle.md` - General project management
- `playbooks/handoffs.md` - Agent handoff protocols

## When to use multi-repo

### Use multi-repo when

**Organizational boundaries**:
- Different teams own different services with separate permissions
- Services have distinct security or compliance requirements
- Separate repositories already exist and can't be merged without disruption

**Technical boundaries**:
- Services are deployed independently with separate lifecycles
- Services use incompatible tech stacks or build tooling
- Build times in monorepo would be prohibitive
- Repositories have different release cadences

**Example scenarios**:
- Microservices architecture with independent deployment
- Shared library used by multiple independent applications
- Infrastructure-as-code repository separate from application code
- Frontend and backend with different teams and tech stacks

### Use monorepo when

**Integration priorities**:
- Services are tightly coupled with shared domain logic
- Atomic cross-service changes are frequent
- Single team owns all components
- Shared code reuse is high

**Simplicity priorities**:
- Coordinated releases are the norm
- Single CI/CD pipeline for all components
- Uniform tooling and conventions
- Simplified dependency management

**Default recommendation**: **Start with monorepo**. Multi-repo adds coordination overhead. Only adopt when organizational or technical constraints require it.

## Setting up a multi-repo project

### 1. Create the project specification

Choose one repository as the **primary repository** that contains the central project specification. This is typically:
- The repository that initiated the project
- The most active repository
- The repository that contains shared documentation

Create `specs/projects/<project-name>/spec.md` with YAML frontmatter:

```yaml
---
repositories:
  - name: api
    url: https://github.com/org/myapp-api
    role: backend
  - name: frontend
    url: https://github.com/org/myapp-frontend
    role: client
---

# Spec: Multi-Repo Project Name

## Goal
[Project goal spanning all repositories]

## Architecture

Backend: [api:specs/architecture.md](api:specs/architecture.md)
Frontend: [frontend:specs/architecture.md](frontend:specs/architecture.md)
```

**Required fields**:
- `name`: Short identifier (alphanumeric, hyphens, underscores only)
- `url`: Full HTTPS GitHub URL
- `role`: Semantic purpose (backend, frontend, client, deployment, shared-lib, docs)

**Constraints**:
- Maximum 5 repositories per project
- All repositories must be in the same GitHub organization
- Repository names must be unique within the project

### 2. Create linked specifications in each repository

Each repository should have its own specification that links back to the central project spec:

**In api repository** (`specs/architecture.md`):
```markdown
# Architecture: MyApp API

This service is part of the [MyApp project](https://github.com/org/myapp-project/blob/main/specs/projects/myapp/spec.md).

## Service Overview
[API-specific architecture]

## Dependencies
- Frontend integration: See central project spec
```

**In frontend repository** (`specs/architecture.md`):
```markdown
# Architecture: MyApp Frontend

This application is part of the [MyApp project](https://github.com/org/myapp-project/blob/main/specs/projects/myapp/spec.md).

## Application Overview
[Frontend-specific architecture]

## API Integration
API documentation: [api:docs/api-spec.md](api:docs/api-spec.md)
```

### 3. Set up consistent status tracking

Each repository tracks its own status, but uses consistent phases:

**api repository** (`status.json`):
```json
{
  "status": "active",
  "current_phase": "implementation",
  "last_updated": "2026-01-15T10:30:00Z",
  "notes": "Working on v2.1 API endpoints for frontend integration"
}
```

**frontend repository** (`status.json`):
```json
{
  "status": "active",
  "current_phase": "implementation",
  "last_updated": "2026-01-15T11:00:00Z",
  "notes": "Waiting for API v2.1 endpoints (see api:tasks.md#issue-42)"
}
```

### 4. Verify permissions

Ensure agents have access to all repositories:
- Same access level (read/write) across all repos
- GitHub tokens with appropriate scopes
- Organization membership if required

Test with:
```bash
# Clone all repositories to verify access
git clone https://github.com/org/myapp-api
git clone https://github.com/org/myapp-frontend
```

## Cross-repository references

### Reference syntax

Use `reponame:path/to/file.md` format:

**In markdown links**:
```markdown
API documentation: [api:docs/api-spec.md](api:docs/api-spec.md)
Frontend architecture: [see frontend](frontend:specs/architecture.md)
```

**In plain text**:
```markdown
- Frontend depends on API v2.1+ (see api:spec.md#versioning)
- Deployment runbook: infra:runbook.md
```

**In task lists**:
```markdown
- [ ] Implement API endpoint
  - Repository: api
  - Handoff to: frontend:tasks.md#integrate-api
  - Artifacts: api:docs/api-spec.md
```

### Validation

The `check_artifacts.py` validator checks:
- Repository names exist in the repositories array
- Basic syntax correctness
- Organization consistency

**Note**: Validators do NOT currently verify that cross-repo files exist (future enhancement).

## Agent coordination across repositories

### Discovery workflow

**Step 1**: Agent reads project spec and identifies repositories:
```markdown
Project has 3 repositories:
- api (backend) at github.com/org/myapp-api
- frontend (client) at github.com/org/myapp-frontend  
- infra (deployment) at github.com/org/myapp-infra
```

**Step 2**: Agent determines which repository contains needed artifacts:
```markdown
Need architecture docs:
- API architecture: api:specs/architecture.md
- Frontend architecture: frontend:specs/architecture.md
```

**Step 3**: Agent accesses artifacts using repository name:
```bash
# Clone needed repository
git clone https://github.com/org/myapp-api
cd myapp-api
cat specs/architecture.md
```

### Handoff protocol

**When work moves from one repository to another**, follow this protocol:

**1. Document the handoff in source repository**:

In `api:tasks.md`:
```markdown
- [x] Task: Implement user authentication API
  - Done: Endpoints implemented and tested
  - Artifacts created:
    - api:docs/auth-api.md (API documentation)
    - api:CHANGELOG.md (v2.1 release notes)
  - Handoff to: frontend:tasks.md#integrate-auth
  - Next steps: Frontend team integrates authentication
```

**2. Create corresponding task in target repository**:

In `frontend:tasks.md`:
```markdown
- [ ] Task: Integrate user authentication
  - Depends on: api v2.1 (api:CHANGELOG.md)
  - Documentation: api:docs/auth-api.md
  - Acceptance: Users can log in via frontend
```

**3. Link via GitHub issues (optional but recommended)**:
- Create issue in frontend repository
- Reference API PR or issue: "Depends on org/myapp-api#123"
- Use labels: `multi-repo`, `blocked`, `dependency:api`

**4. Update status across repositories**:
- API repository: Mark phase complete, note handoff
- Frontend repository: Update status to reflect new work

### Tracking dependencies

**Explicit dependency declarations**:

In `frontend:tasks.md`:
```markdown
## Dependencies

- **API v2.1+** (api:spec.md#versioning)
  - Status: ✅ Released 2026-01-15
  - Required endpoints: api:docs/auth-api.md
  - Health check: api:runbook.md#health-check

- **Infrastructure** (infra:terraform/README.md)
  - Status: ⏳ In progress
  - Blocking: Deployment to staging
  - Contact: @infra-team
```

**Version pinning**:
```markdown
- Frontend depends on API v2.1.0+
  - Breaking changes: api:CHANGELOG.md#v2.0.0
  - Migration guide: api:docs/migration-v2.md
```

### Status coordination

**Phase transitions**:
When moving between phases (spec → architecture → implementation), coordinate timing:

```markdown
## Phase Transition: Architecture → Implementation

**Blockers**:
- [ ] API architecture reviewed (api:specs/architecture.md)
- [ ] Frontend architecture reviewed (frontend:specs/architecture.md)
- [ ] Interface contracts agreed (api:docs/api-spec.md)

**Transition order**:
1. API moves to implementation first (provides endpoints)
2. Frontend begins implementation after API v2.1 beta available
3. Infrastructure provisions staging environment in parallel
```

**Coordinating via status.json**:
- All repos should update `last_updated` when making significant progress
- Use `notes` field to reference cross-repo dependencies
- Set `status: blocked` if waiting on another repository

## Common patterns

### Pattern 1: API + Frontend (Two repos)

**Structure**:
```
org/myapp-api           (Backend service)
org/myapp-frontend      (Web application)
```

**Central spec**: In api or separate project repository

**Workflow**:
1. API spec agent defines API contracts
2. API and frontend architects work in parallel
3. API SWE implements endpoints first
4. Frontend SWE integrates once API is stable
5. Both services deployed independently

**Key artifacts**:
- `api:docs/openapi.yaml` - API contract (source of truth)
- `api:CHANGELOG.md` - Version history
- `frontend:docs/integration.md` - How frontend uses API

### Pattern 2: Microservices (Multiple backends + Frontend)

**Structure**:
```
org/users-service       (User management)
org/orders-service      (Order processing)
org/storefront          (Web frontend)
```

**Central spec**: Separate project repository or in storefront

**Workflow**:
1. Define service boundaries and contracts
2. Services implement independently in parallel
3. Frontend integrates with all services
4. Service mesh handles inter-service communication

**Key artifacts**:
- Each service: `service:docs/api-spec.md`
- Central: Service dependency graph
- Central: Cross-service communication patterns

### Pattern 3: Application + Infrastructure

**Structure**:
```
org/myapp               (Application code)
org/myapp-infra         (Terraform/K8s configs)
```

**Central spec**: In application repository

**Workflow**:
1. Application defines infrastructure requirements
2. Infrastructure provisions environments
3. Application deployed to infrastructure
4. Runbooks span both repositories

**Key artifacts**:
- `app:specs/infrastructure-requirements.md`
- `infra:terraform/README.md` - Infrastructure overview
- `infra:runbook.md` - Deployment procedures

### Pattern 4: Shared Library + Applications

**Structure**:
```
org/shared-lib          (Reusable library)
org/app-one             (Application using library)
org/app-two             (Application using library)
```

**Central spec**: In shared library or separate

**Workflow**:
1. Library defines public API
2. Library releases versioned artifacts
3. Applications depend on specific library versions
4. Breaking changes coordinated via migration guides

**Key artifacts**:
- `shared-lib:CHANGELOG.md` - Version history
- `shared-lib:docs/api.md` - Public API documentation
- Each app: Dependency version pinning

## Troubleshooting

### Issue: Agent can't find cross-repo artifact

**Symptoms**:
- Agent references `api:docs/spec.md` but file doesn't exist
- Build fails with "artifact not found"

**Solutions**:
1. Verify repository name matches `repositories` array
2. Check path is relative to repository root
3. Verify file exists in target repository
4. Check agent has access to target repository
5. Use absolute GitHub URLs as fallback

### Issue: Repository not in same organization

**Symptoms**:
- Validator fails with "repositories must be in same org"

**Solutions**:
1. Move repositories to same organization, OR
2. Use separate single-repo projects with manual coordination, OR
3. Document as limitation and link repos via GitHub issues only

### Issue: Circular dependencies between repos

**Symptoms**:
- API depends on frontend, frontend depends on API
- Can't determine implementation order

**Solutions**:
1. Define clear interface contracts first
2. Use API mocking/stubs to break cycle
3. Reconsider repository boundaries (might be one service)
4. Version APIs to allow incremental integration

### Issue: Inconsistent status across repositories

**Symptoms**:
- API says "implementation done" but frontend says "waiting for API"

**Solutions**:
1. Use GitHub issues to track cross-repo handoffs
2. Update status.json notes with handoff details
3. Establish handoff checklist (docs, tests, notification)
4. Use semantic versioning to communicate readiness

## Best practices

### Documentation

- **DRY principle**: Don't duplicate information across repos
- **Link, don't copy**: Use cross-repo references instead of duplicating
- **Central contracts**: API specs, interface definitions in single source of truth
- **Changelog discipline**: Document breaking changes in CHANGELOG.md

### Communication

- **Handoff checklist**: Define what "done" means for handoffs
- **Status updates**: Update status.json when making significant progress
- **Issue linking**: Use GitHub issues to track cross-repo dependencies
- **Notification**: Mention teams when handoff is ready

### Versioning

- **Semantic versioning**: Use semver for API versions
- **Pin dependencies**: Specify minimum/maximum versions
- **Migration guides**: Document breaking changes
- **Beta releases**: Let dependent services test before GA

### Testing

- **Contract tests**: Verify interface boundaries
- **Integration tests**: Test cross-repo interactions
- **Mock external services**: Don't require all repos running locally
- **CI coordination**: Run integration tests across repos

## Limitations

### Current limitations (Milestone 7a)

- Maximum 5 repositories per project
- All repositories must be in same GitHub organization
- Uniform permission model (same access for all repos)
- Basic automated validation of cross-repo reference syntax (repository name validation only; file existence checks are future work)
- No dependency version tracking (manual documentation only)

### Manual workarounds

**Cross-repo reference validation**:
```bash
# Manually verify references
grep -r "reponame:" specs/projects/myapp/*.md
# Check each file exists in target repo
```

**Dependency tracking**:
- Document in tasks.md manually
- Use GitHub issues with labels
- Create dependency matrix in architecture.md

### Future enhancements (Milestone 7b+)

- Automated cross-repo reference validation in CI
- Dependency graph visualization
- Cross-repo status dashboard
- Automated synchronization checks
- Support for repositories in different organizations

## Examples

See `specs/kerrigan/020-artifact-contracts.md` for detailed examples:
- Example 1: Two-repository project (API + Frontend)
- Example 2: Three-repository project (Microservices)
- Example 3: Infrastructure + Application

## Related playbooks

- `playbooks/project-lifecycle.md` - Managing project states
- `playbooks/handoffs.md` - Agent handoff protocols
- `playbooks/autonomy-modes.md` - Controlling agent autonomy
