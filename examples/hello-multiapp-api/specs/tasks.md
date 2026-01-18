# Tasks: Hello Multi-App API

## Phase 1: API Implementation

- [x] Create FastAPI application structure
  - Done when: main.py implements FastAPI app with basic setup
  - Dependencies: None

- [x] Implement health endpoint
  - Done when: GET /health returns {"status": "ok", "service": "hello-multiapp-api"}
  - Dependencies: API structure complete

- [x] Implement version endpoint
  - Done when: GET /version returns version, service name, and environment
  - Dependencies: API structure complete

- [x] Implement root endpoint
  - Done when: GET / returns service info and endpoint list
  - Dependencies: API structure complete

- [x] Configure CORS middleware
  - Done when: Frontend can make cross-origin requests to API
  - Dependencies: API endpoints implemented
  - Cross-repo: Required by hello-multiapp-frontend

- [x] Add logging configuration
  - Done when: All endpoints log requests at INFO level
  - Dependencies: API endpoints implemented

## Phase 2: Containerization

- [x] Create Dockerfile
  - Done when: Docker image builds successfully
  - Dependencies: API implementation complete
  - Cross-repo: Used by hello-multiapp-infra

- [x] Create requirements.txt
  - Done when: All Python dependencies listed with pinned versions
  - Dependencies: None

- [x] Add .gitignore
  - Done when: Python artifacts excluded from git
  - Dependencies: None

## Phase 3: Documentation

- [ ] Create README.md
  - Done when: Setup, usage, and API documentation complete
  - Dependencies: API and Docker complete

- [x] Create specs/spec.md
  - Done when: Complete specification with cross-repo references
  - Dependencies: None

- [x] Create specs/tasks.md
  - Done when: Tasks include cross-repo dependencies
  - Dependencies: spec.md complete

- [ ] Create specs/architecture.md
  - Done when: Architecture documents integration with frontend and infra
  - Dependencies: spec.md complete
  - Cross-repo: References hello-multiapp-frontend, hello-multiapp-infra

- [ ] Create specs/runbook.md
  - Done when: Deployment procedures documented
  - Dependencies: architecture.md complete
  - Cross-repo: References hello-multiapp-infra deployment

- [ ] Create specs/cost-plan.md
  - Done when: Cost breakdown includes shared infrastructure
  - Dependencies: architecture.md complete
  - Cross-repo: Coordinates with hello-multiapp-infra costs

## Phase 4: Integration & Testing

- [ ] Test with frontend locally
  - Done when: Frontend successfully calls API endpoints
  - Dependencies: API running, frontend implemented
  - Cross-repo: Requires hello-multiapp-frontend

- [ ] Test with docker-compose
  - Done when: API starts via infra's docker-compose.yml
  - Dependencies: Dockerfile complete
  - Cross-repo: Requires hello-multiapp-infra

- [ ] Validate health checks
  - Done when: Docker health check succeeds
  - Dependencies: Health endpoint, docker-compose setup
  - Cross-repo: Used by hello-multiapp-infra

## Cross-Repository Dependencies

**Blocks:**
- hello-multiapp-frontend implementation (frontend needs API endpoints)
- hello-multiapp-infra integration testing (needs API container)

**Blocked by:**
- None (API is the foundation service)

**Coordinates with:**
- hello-multiapp-infra: Container configuration, networking, deployment
- hello-multiapp-frontend: API contract (endpoints, CORS, response formats)
