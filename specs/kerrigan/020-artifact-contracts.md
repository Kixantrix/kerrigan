# Artifact contracts

Artifacts are the API between agents. Handoffs are not complete until required artifacts exist.

## Per-project required files (minimum)

For each project under `specs/projects/<project-name>/`:

1) `spec.md`
   - Goal
   - Scope / Non-goals
   - Users & scenarios
   - Constraints
   - Acceptance criteria (measurable)
   - Risks & mitigations
   - Success metrics
   - Optional YAML frontmatter for multi-repository projects (see below)

2) `acceptance-tests.md`
   - Human-readable checks (Given/When/Then or checklist)
   - Edge cases / failure modes

3) `architecture.md`
   - Proposed approach
   - Key components + interfaces
   - Data flows (conceptual)
   - Tradeoffs
   - Security & privacy notes (lightweight)

4) `plan.md`
   - Milestones (each ends with green CI)
   - Dependencies
   - Rollback strategy (if relevant)

5) `tasks.md`
   - Executable work items with clear “done” criteria
   - Links to relevant artifacts

6) `test-plan.md`
   - Test levels (unit/integration/e2e)
   - Tooling strategy
   - Coverage focus and risk areas

7) `runbook.md` (if deployable)
   - How to deploy
   - How to operate
   - How to debug
   - Oncall/incident basics (even if “none”)

8) `cost-plan.md` (if deployable / uses paid resources)
   - Expected cost drivers
   - Guardrails (budgets/alerts/tags)
   - Scale assumptions

9) `status.json` (optional, for workflow control)
   - Tracks project state and agent workflow progress
   - Enables pause/resume control for human oversight
   - See schema below

## status.json schema

The `status.json` file provides runtime control over agent workflow. It is optional but recommended for multi-agent projects requiring human oversight.

**Location**: `specs/projects/<project-name>/status.json`

**Schema**:
```json
{
  "status": "active|blocked|completed|on-hold",
  "current_phase": "spec|architecture|implementation|testing|deployment",
  "last_updated": "ISO 8601 timestamp",
  "blocked_reason": "optional: explanation if status=blocked",
  "notes": "optional: human notes or context"
}
```

**Field definitions**:
- `status` (required): Current workflow state
  - `active`: Agents may proceed with work
  - `blocked`: Agents must pause; human intervention needed
  - `completed`: Project work is done
  - `on-hold`: Temporarily paused; may resume later
- `current_phase` (required): Where the project is in the workflow lifecycle
- `last_updated` (required): ISO 8601 timestamp of last status change
- `blocked_reason` (optional but recommended when status=blocked): Explains why work is paused
- `notes` (optional): Free-form text for human context

**Agent behavior**:
- Agents MUST check status.json before starting work
- If status=blocked or on-hold, agents MUST NOT proceed
- Agents SHOULD update last_updated when changing phases
- Agents MAY add notes but MUST NOT change status from active to blocked

## Multi-repository project specification

Projects that span multiple repositories require additional coordination mechanisms. This section defines the schema and conventions for multi-repo projects.

### When to use multi-repo vs monorepo

**Use multi-repo when**:
- Services are deployed independently with separate lifecycles
- Different teams own different services with separate permissions
- Repositories have distinct security or compliance requirements
- Services use incompatible tech stacks or build tooling
- Existing repositories can't be merged without significant disruption

**Use monorepo when**:
- Services are tightly coupled with shared domain logic
- Single team owns all components
- Coordinated releases are the norm
- Shared code reuse is high
- Atomic cross-service changes are frequent

**Default recommendation**: Start with monorepo. Only adopt multi-repo when organizational or technical constraints require it.

### repositories field in spec.md

Multi-repository projects MUST declare all participating repositories in the spec.md frontmatter using YAML:

```yaml
---
repositories:
  - name: api
    url: https://github.com/org/myapp-api
    role: backend
  - name: frontend
    url: https://github.com/org/myapp-frontend
    role: client
  - name: infra
    url: https://github.com/org/myapp-infrastructure
    role: deployment
---

# Spec: Multi-Repo Project Name

## Goal
...
```

**Field definitions**:
- `name` (required): Short identifier for the repository (alphanumeric, hyphens, underscores only)
- `url` (required): Full HTTPS GitHub repository URL
- `role` (required): Semantic role describing the repository's purpose in the project (e.g., backend, frontend, client, deployment, shared-lib, docs)

**Constraints**:
- Maximum 5 repositories per project
- All repositories MUST be in the same GitHub organization
- Repository names MUST be unique within the project
- Uniform permission model: agents must have same access level to all repositories
- The repository containing the spec.md is implicitly included (no need to list it in the array unless cross-referencing it)

### Cross-repository artifact references

When referencing artifacts in other repositories, use the `repo:path` syntax:

```markdown
## Architecture

Backend API architecture: [see api repo](api:specs/architecture.md)
Frontend architecture: [see frontend repo](frontend:specs/architecture.md)

## Dependencies

- Frontend depends on API v2.1+ (see api:spec.md)
- Both depend on shared infrastructure (see infra:runbook.md)
- API documentation: api:docs/api-spec.md
```

**Reference syntax**:
- Format: `reponame:path/to/artifact.md`
- `reponame`: Must match a `name` field from the `repositories` array in spec.md
- `path`: Relative path from repository root
- Use in markdown links: `[description](reponame:path)`
- Use in plain text: `(see reponame:path)` or `reponame:path`

**Validation**:
- Repository name must exist in the repositories array
- Path should point to a valid artifact type
- Agents should verify cross-repo references resolve to actual files (when access permits)

### Cross-repository handoff protocol

When agent work spans multiple repositories, handoffs follow this protocol:

**1. Document the handoff in tasks.md**:
```markdown
- [ ] Task: Implement API endpoint
  - Repository: api
  - Done when: Endpoint deployed and documented
  - Handoff to: Frontend team via frontend:tasks.md
  - Artifacts: api:docs/api-spec.md, api:CHANGELOG.md
```

**2. Update status across repositories**:
- Each repository tracks its own status.json
- Use consistent `current_phase` values across repos
- Coordinate phase transitions via PR comments or linked issues

**3. Link artifacts across repositories**:
- Update the project's central spec.md with cross-repo references
- Each repo's tasks.md links back to central spec
- Use GitHub issues to track cross-repo dependencies

**4. Agent coordination**:
- Agents check the repositories field before starting work
- Agents discover which repo contains the artifact they need
- Agents reference cross-repo artifacts using `repo:path` syntax
- Agents document cross-repo dependencies in handoff notes

### Multi-repository examples

#### Example 1: Two-repository project (API + Frontend)

**Project**: specs/projects/todo-fullstack/spec.md
```yaml
---
repositories:
  - name: api
    url: https://github.com/acme/todo-api
    role: backend
  - name: web
    url: https://github.com/acme/todo-web
    role: frontend
---

# Spec: Todo Fullstack

## Goal
Build a full-stack todo application with REST API backend and React frontend.

## Architecture

Backend: [api:specs/architecture.md](api:specs/architecture.md)
Frontend: [web:specs/architecture.md](web:specs/architecture.md)

## Dependencies

- Frontend depends on API v1.0+ (see api:spec.md#versioning)
- Both share API contract: api:docs/openapi.yaml
```

#### Example 2: Three-repository project (Microservices)

**Project**: specs/projects/ecommerce-platform/spec.md
```yaml
---
repositories:
  - name: users
    url: https://github.com/shop/users-service
    role: backend
  - name: orders
    url: https://github.com/shop/orders-service
    role: backend
  - name: web
    url: https://github.com/shop/storefront
    role: frontend
---

# Spec: E-commerce Platform

## Goal
Multi-service e-commerce platform with user management, order processing, and web storefront.

## Architecture

- Users service: [users:specs/architecture.md](users:specs/architecture.md)
- Orders service: [orders:specs/architecture.md](orders:specs/architecture.md)
- Storefront: [web:specs/architecture.md](web:specs/architecture.md)
- Service mesh: [orders:specs/service-mesh.md](orders:specs/service-mesh.md)

## Cross-service dependencies

- Orders service depends on Users service v2.0+ for authentication
  - Contract: users:docs/auth-api.md
  - Health check: users:runbook.md#health-endpoints
- Web storefront calls both services
  - Users API: users:docs/api-spec.md
  - Orders API: orders:docs/api-spec.md
```

#### Example 3: Infrastructure + Application

**Project**: specs/projects/myapp-production/spec.md
```yaml
---
repositories:
  - name: app
    url: https://github.com/company/myapp
    role: application
  - name: infra
    url: https://github.com/company/myapp-infrastructure
    role: deployment
---

# Spec: MyApp Production Deployment

## Goal
Deploy MyApp to production with infrastructure as code.

## Deployment Architecture

Application: [app:specs/architecture.md](app:specs/architecture.md)
Infrastructure: [infra:terraform/README.md](infra:terraform/README.md)

## Runbooks

- Deploy application: [app:runbook.md](app:runbook.md)
- Provision infrastructure: [infra:runbook.md](infra:runbook.md)
- Disaster recovery: [infra:docs/dr-plan.md](infra:docs/dr-plan.md)
```

### Limitations and future work

**Current limitations** (Milestone 7a):
- Maximum 5 repositories per project
- All repositories must be in same GitHub organization
- Uniform permission model (same access for all repos)
- No automated validation of cross-repo references (manual check required)
- No dependency version tracking (manual documentation only)

**Future enhancements** (Milestone 7b+):
- Cross-repo reference validation in CI
- Dependency graph visualization
- Cross-repo status dashboard
- Automated synchronization checks
- Support for repositories in different organizations (with explicit permission grants)

## Kerrigan-wide artifacts
- `specs/constitution.md` governs all work.
- `specs/kerrigan/030-quality-bar.md` defines definition-of-done and heuristics.

## Naming and linking
- Each PR must link the project folder it advances (e.g., `specs/projects/foo/`).
- Each artifact should link to adjacent artifacts (spec ↔ plan ↔ tasks).
