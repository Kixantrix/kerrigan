# Spec: Hello Multi-App API

## Goal

Create a simple FastAPI service that demonstrates multi-repository coordination by providing backend API endpoints for a multi-repo application architecture.

## Scope

- REST API with health and version endpoints
- CORS support for frontend integration
- Docker containerization
- Complete artifact set for multi-repo coordination
- Cross-repository references and dependencies

## Non-goals

- Complex business logic or data persistence
- Authentication/authorization
- Production-grade monitoring (basic logging only)
- Performance optimization beyond basics

## Users & scenarios

**Primary users**: Developers learning multi-repo coordination with Kerrigan

**Key scenarios**:
1. **Frontend integration**: Frontend service consumes API endpoints
2. **Health monitoring**: Infrastructure monitors service health
3. **Version tracking**: Clients check API version compatibility
4. **Multi-repo coordination**: Demonstrates artifact-driven coordination across repositories

## Constraints

- Must be simple enough for tutorial/example purposes
- Should work seamlessly with hello-multiapp-frontend
- Must be deployable via hello-multiapp-infra configurations
- All coordination through artifact files (no external state)
- Keep dependencies minimal

## Acceptance criteria

### Functional
- [ ] GET /health returns 200 with service status
- [ ] GET /version returns API version and environment info
- [ ] GET / returns service information and available endpoints
- [ ] CORS configured to allow frontend requests
- [ ] Service logs requests appropriately

### Multi-repo coordination
- [ ] specs/ folder contains complete artifact set
- [ ] spec.md references frontend and infra repositories
- [ ] tasks.md includes cross-repo dependencies
- [ ] architecture.md documents integration points
- [ ] runbook.md includes deployment with infra repo

### Non-functional
- [ ] Response time < 100ms for all endpoints
- [ ] Docker image builds successfully
- [ ] Works with docker-compose from infra repo
- [ ] README includes setup instructions

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CORS misconfiguration blocks frontend | High | Test frontend integration early |
| Version inconsistencies across repos | Medium | Document versioning strategy in architecture |
| Docker networking issues | Medium | Use docker-compose from infra repo |
| Cross-repo dependency confusion | Medium | Clear documentation in each repo |

## Success metrics

- All acceptance criteria met
- Successfully integrates with frontend and infra repos
- Example demonstrates clear multi-repo patterns
- Documentation enables self-service learning

## Repositories

This project is part of a multi-repository architecture:

- **hello-multiapp-api** (this repository)
  - Role: Backend API service
  - Dependencies: None
  - Dependents: hello-multiapp-frontend

- **hello-multiapp-frontend**
  - Role: Web frontend
  - Dependencies: hello-multiapp-api (consumes API endpoints)
  - Repository: `examples/hello-multiapp-frontend`

- **hello-multiapp-infra**
  - Role: Infrastructure and deployment
  - Dependencies: hello-multiapp-api, hello-multiapp-frontend (orchestrates both)
  - Repository: `examples/hello-multiapp-infra`

## Cross-repo integration points

1. **API Endpoints**: Consumed by frontend
   - `/health` - Health check
   - `/version` - Version information
   - `/` - Service metadata

2. **Container**: Built and deployed by infra repo
   - Dockerfile defines container image
   - Exposed on port 8000

3. **Configuration**: Coordinated through infra
   - Environment variables set in docker-compose
   - Network configuration managed by infra
