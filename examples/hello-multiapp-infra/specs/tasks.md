# Tasks: Hello Multi-App Infrastructure

## Phase 1: Repository Setup

- [x] Create repository structure
  - Done when: README.md, .gitignore, and specs/ folder exist
  - Dependencies: None

- [x] Create .gitignore
  - Done when: Docker and OS artifacts excluded
  - Dependencies: None

## Phase 2: Docker Compose Configuration

- [x] Create docker-compose.yml base structure
  - Done when: Version and services sections defined
  - Dependencies: Repository setup complete
  - Cross-repo: Requires knowledge of API and frontend repositories

- [x] Configure API service
  - Done when: API build context, ports, environment, and health check defined
  - Dependencies: Base docker-compose.yml created
  - Cross-repo: Requires hello-multiapp-api/Dockerfile

- [x] Configure frontend service
  - Done when: Frontend build context, ports, environment, and dependencies defined
  - Dependencies: API service configured
  - Cross-repo: Requires hello-multiapp-frontend/Dockerfile

- [x] Create Docker bridge network
  - Done when: multiapp-network defined with bridge driver
  - Dependencies: Services configured

## Phase 3: Service Orchestration

- [x] Configure service dependencies
  - Done when: Frontend depends_on API service
  - Dependencies: Both services defined

- [x] Configure health checks
  - Done when: API health check validates /health endpoint
  - Dependencies: API service configuration
  - Cross-repo: Requires API /health endpoint implementation

- [x] Configure environment variables
  - Done when: API and frontend have appropriate environment configuration
  - Dependencies: Services defined
  - Cross-repo: Coordinates with API and frontend environment needs

- [x] Configure port mappings
  - Done when: API on 8000, frontend on 3000, no conflicts
  - Dependencies: Services defined

## Phase 4: Documentation

- [x] Create README.md
  - Done when: Setup instructions, architecture overview, troubleshooting complete
  - Dependencies: docker-compose.yml complete

- [x] Create specs/spec.md
  - Done when: Complete specification with cross-repo references
  - Dependencies: None

- [x] Create specs/tasks.md
  - Done when: Tasks include cross-repo dependencies (this file)
  - Dependencies: spec.md complete

- [ ] Create specs/architecture.md
  - Done when: Orchestration design, networking, and integration documented
  - Dependencies: spec.md complete
  - Cross-repo: Documents integration with API and frontend

- [ ] Create specs/runbook.md
  - Done when: Deployment procedures, monitoring, troubleshooting complete
  - Dependencies: architecture.md complete
  - Cross-repo: Coordinates deployment of all services

- [ ] Create specs/cost-plan.md
  - Done when: Shared infrastructure costs and allocation documented
  - Dependencies: architecture.md complete
  - Cross-repo: Includes costs shared across all three repositories

## Phase 5: Testing & Validation

- [ ] Test single service startup
  - Done when: API starts successfully via docker-compose
  - Dependencies: API service configuration complete
  - Cross-repo: Requires hello-multiapp-api repository

- [ ] Test multi-service startup
  - Done when: Both services start in correct order
  - Dependencies: All services configured
  - Cross-repo: Requires both API and frontend repositories

- [ ] Validate service networking
  - Done when: Frontend can reach API via service name
  - Dependencies: Both services running
  - Cross-repo: Tests API and frontend integration

- [ ] Validate health checks
  - Done when: Docker reports API as healthy
  - Dependencies: Health check configured
  - Cross-repo: Requires API /health endpoint

- [ ] Test end-to-end workflow
  - Done when: Browser → frontend → API chain works
  - Dependencies: All services running
  - Cross-repo: Full stack integration test

- [ ] Test clean shutdown
  - Done when: docker-compose down succeeds without errors
  - Dependencies: Services running

## Phase 6: Error Handling & Edge Cases

- [ ] Handle missing repositories
  - Done when: Clear error message if API or frontend not found
  - Dependencies: docker-compose.yml complete

- [ ] Handle port conflicts
  - Done when: README documents port conflict troubleshooting
  - Dependencies: README created

- [ ] Handle build failures
  - Done when: docker-compose errors are clear and actionable
  - Dependencies: All configurations complete

- [ ] Validate cross-platform compatibility
  - Done when: Works on Linux, macOS, and Windows
  - Dependencies: All configurations complete

## Cross-Repository Dependencies

**Blocks:**
- End-to-end testing of entire multi-repo project
- Production deployment preparation
- Cross-repo integration validation

**Blocked by:**
- hello-multiapp-api: Dockerfile and /health endpoint required
- hello-multiapp-frontend: Dockerfile and API integration required

**Coordinates with:**
- hello-multiapp-api: 
  - Uses API Dockerfile for building
  - Configures API environment variables
  - Monitors API health checks
  - Exposes API on port 8000

- hello-multiapp-frontend:
  - Uses frontend Dockerfile for building
  - Configures frontend environment (API_URL)
  - Manages frontend dependencies on API
  - Exposes frontend on port 3000

## Multi-Repo Build Order

The orchestration requires this build order:

1. **API builds first** (no dependencies)
   - Build context: ../hello-multiapp-api
   - Build time: ~30 seconds
   - Output: API container image

2. **Frontend builds second** (logical dependency)
   - Build context: ../hello-multiapp-frontend
   - Build time: ~10 seconds
   - Output: Frontend container image

3. **API starts first** (runtime dependency)
   - Container starts, health checks begin
   - Must be healthy before frontend starts

4. **Frontend starts last** (depends_on API)
   - Waits for API container
   - Connects to API via Docker network

## Coordination Tasks

### Pre-deployment Coordination
- [ ] Verify all repositories at compatible versions
- [ ] Check API contract matches frontend expectations
- [ ] Validate environment variable configurations
- [ ] Ensure Docker Compose version compatibility

### Deployment Coordination
- [ ] Build all images in correct order
- [ ] Start services with proper dependencies
- [ ] Verify health checks pass
- [ ] Validate inter-service communication

### Post-deployment Validation
- [ ] Confirm all containers running
- [ ] Test frontend → API communication
- [ ] Check logs for errors
- [ ] Verify ports accessible from host

## Shared Infrastructure Tasks

- [ ] Document shared network configuration
  - Done when: Bridge network usage documented
  - Used by: Both API and frontend

- [ ] Document shared logging strategy
  - Done when: Log aggregation approach documented
  - Used by: All services for troubleshooting

- [ ] Document shared monitoring approach
  - Done when: Health check strategy documented
  - Used by: All services for availability verification

- [ ] Document cost allocation methodology
  - Done when: Shared cost split documented in cost-plan.md
  - Used by: All three repositories for budgeting
