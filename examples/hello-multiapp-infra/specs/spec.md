# Spec: Hello Multi-App Infrastructure

## Goal

Create infrastructure orchestration that demonstrates multi-repository coordination by managing deployment configurations for both API and frontend services in a unified Docker Compose environment.

## Scope

- Docker Compose orchestration for multi-service architecture
- Container networking and service discovery
- Health check configuration and startup dependencies
- Environment variable management
- Cross-repository build coordination
- Complete artifact set demonstrating infrastructure-as-code patterns

## Non-goals

- Production Kubernetes configurations (keep it simple with Docker Compose)
- CI/CD pipeline implementation (focus on deployment configuration)
- Secrets management or advanced security (basic configuration only)
- Monitoring infrastructure (basic health checks only)
- Multi-environment configurations (demonstrate patterns, not full implementation)

## Users & scenarios

**Primary users**: Developers learning multi-repo coordination with Kerrigan

**Key scenarios**:
1. **Multi-repo orchestration**: Deploy all services with single command
2. **Development environment**: Local development setup for full stack
3. **Service coordination**: Manage startup order and dependencies
4. **Network management**: Configure inter-service communication
5. **Infrastructure as code**: Demonstrate declarative deployment patterns

## Constraints

- Must coordinate with hello-multiapp-api and hello-multiapp-frontend repositories
- Should work on developer machines (Docker Desktop)
- All three repositories must be cloned side-by-side
- No external orchestration tools (keep dependencies minimal)
- Must be simple enough for tutorial purposes
- All coordination through Docker Compose and environment variables

## Acceptance criteria

### Functional
- [ ] docker-compose.yml successfully builds both API and frontend
- [ ] API service starts first with health checks
- [ ] Frontend service starts after API is healthy
- [ ] Services communicate over Docker bridge network
- [ ] Health checks validate service availability
- [ ] All services accessible from host machine
- [ ] Single command starts entire stack

### Multi-repo coordination
- [ ] specs/ folder contains complete artifact set
- [ ] spec.md references both API and frontend repositories
- [ ] tasks.md includes cross-repo build dependencies
- [ ] architecture.md documents orchestration design
- [ ] runbook.md provides deployment procedures
- [ ] cost-plan.md includes all shared infrastructure costs

### Non-functional
- [ ] Services start in < 30 seconds
- [ ] Logs accessible via docker-compose logs
- [ ] Clean shutdown with docker-compose down
- [ ] Works on Linux, macOS, and Windows with Docker Desktop
- [ ] README provides clear setup instructions
- [ ] Graceful error handling for missing repositories

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Repository layout confusion | High | Clear documentation of required directory structure |
| Network configuration issues | High | Use Docker Compose networking with service names |
| Build failures from missing repos | High | Document repository cloning requirements |
| Port conflicts on developer machines | Medium | Use standard ports, document conflicts in troubleshooting |
| Health check timeouts | Medium | Configure appropriate intervals and retries |
| Cross-repo version mismatches | Medium | Document versioning strategy, consider tags |

## Success metrics

- All acceptance criteria met
- Developers can clone and run in < 5 minutes
- Example demonstrates clear multi-repo orchestration patterns
- Documentation enables self-service deployment
- Zero manual configuration required

## Repositories

This project coordinates a multi-repository architecture:

- **hello-multiapp-api**
  - Role: Backend API service
  - Repository: `examples/hello-multiapp-api`
  - Dependencies: None
  - Integration: Built and orchestrated by this infra repo

- **hello-multiapp-frontend**
  - Role: Web frontend
  - Repository: `examples/hello-multiapp-frontend`
  - Dependencies: hello-multiapp-api (runtime dependency)
  - Integration: Built and orchestrated by this infra repo

- **hello-multiapp-infra** (this repository)
  - Role: Infrastructure orchestration and deployment
  - Dependencies: Both API and frontend repositories
  - Dependents: None
  - Responsibility: Coordinates all services, manages shared infrastructure

## Cross-repo integration points

1. **Docker Compose Configuration**: Orchestrates both services
   - Build contexts point to sibling repositories
   - Manages service dependencies (frontend depends_on api)
   - Configures shared networking

2. **Container Networking**: Provides service discovery
   - Bridge network: `multiapp-network`
   - Service names: `api`, `frontend`
   - DNS resolution for inter-service communication

3. **Environment Configuration**: Injects runtime configuration
   - API: PORT, ENVIRONMENT variables
   - Frontend: API_URL pointing to api service
   - Coordinated through docker-compose.yml

4. **Health Checks**: Ensures proper startup order
   - API health endpoint monitored
   - Frontend waits for API availability
   - Graceful failure handling

5. **Port Mappings**: Exposes services to host
   - API: localhost:8000 → container:8000
   - Frontend: localhost:3000 → container:80

## Deployment architecture

### Repository Layout
```
hello-multiapp/                  # Parent directory
├── hello-multiapp-api/          # API repository
│   ├── main.py
│   ├── Dockerfile
│   └── specs/
├── hello-multiapp-frontend/     # Frontend repository
│   ├── index.html
│   ├── Dockerfile
│   └── specs/
└── hello-multiapp-infra/        # Infrastructure repository (this one)
    ├── docker-compose.yml       # Orchestration config
    ├── README.md
    └── specs/
```

### Startup Sequence
1. User runs `docker-compose up` in infra directory
2. Docker Compose builds API image from ../hello-multiapp-api
3. API container starts, health checks begin
4. Docker Compose builds frontend image from ../hello-multiapp-frontend
5. Frontend container waits for API (depends_on)
6. Both services running, accessible from host

### Service Communication
- External: Host browser → localhost:3000 → Frontend container
- Internal: Frontend container → api:8000 → API container
- Health: Docker → localhost:8000/health → API health check

## Integration testing

### Prerequisites Validation
- Verify all three repositories cloned correctly
- Check Docker and Docker Compose installed
- Validate ports 3000 and 8000 available

### Integration Test Cases
1. **Build Test**: Both images build successfully
2. **Startup Test**: Services start in correct order
3. **Health Test**: API health check passes
4. **Network Test**: Frontend can reach API via service name
5. **End-to-End Test**: Browser can access frontend, frontend calls API
6. **Shutdown Test**: Clean shutdown without errors

### Success Criteria
- All containers running (`docker-compose ps` shows "healthy")
- API responds to health check
- Frontend loads in browser
- Frontend successfully calls API endpoints
- Logs show no errors
