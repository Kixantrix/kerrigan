# Tasks: Hello Multi-App Frontend

## Phase 1: Frontend Implementation

- [x] Create HTML structure
  - Done when: index.html has complete markup and styling
  - Dependencies: None

- [x] Implement API integration JavaScript
  - Done when: Frontend can call API endpoints and handle responses
  - Dependencies: HTML structure complete
  - Cross-repo: Requires hello-multiapp-api endpoints

- [x] Add error handling
  - Done when: Connection failures display helpful error messages
  - Dependencies: API integration complete

- [x] Style the interface
  - Done when: Responsive design works on mobile and desktop
  - Dependencies: HTML structure complete

- [x] Add automatic API check on load
  - Done when: Frontend automatically checks API when page loads
  - Dependencies: API integration complete
  - Cross-repo: Requires hello-multiapp-api running

## Phase 2: Containerization

- [x] Create Dockerfile
  - Done when: Docker image builds successfully with nginx
  - Dependencies: Frontend implementation complete
  - Cross-repo: Used by hello-multiapp-infra

- [x] Create nginx configuration
  - Done when: Nginx serves static files correctly
  - Dependencies: Dockerfile created

- [x] Add .gitignore
  - Done when: Unnecessary files excluded from git
  - Dependencies: None

## Phase 3: Documentation

- [ ] Create README.md
  - Done when: Setup, usage, and integration documented
  - Dependencies: Frontend and Docker complete

- [x] Create specs/spec.md
  - Done when: Complete specification with cross-repo references
  - Dependencies: None

- [x] Create specs/tasks.md
  - Done when: Tasks include cross-repo dependencies
  - Dependencies: spec.md complete

- [ ] Create specs/architecture.md
  - Done when: Architecture documents API integration
  - Dependencies: spec.md complete
  - Cross-repo: References hello-multiapp-api, hello-multiapp-infra

- [ ] Create specs/runbook.md
  - Done when: Deployment procedures documented
  - Dependencies: architecture.md complete
  - Cross-repo: References hello-multiapp-infra deployment

- [ ] Create specs/cost-plan.md
  - Done when: Cost breakdown includes shared infrastructure
  - Dependencies: architecture.md complete
  - Cross-repo: Coordinates with shared infrastructure costs

## Phase 4: Integration & Testing

- [ ] Test with API locally
  - Done when: Frontend connects to local API successfully
  - Dependencies: Frontend complete, API running
  - Cross-repo: Requires hello-multiapp-api

- [ ] Test with docker-compose
  - Done when: Frontend starts via infra's docker-compose.yml
  - Dependencies: Dockerfile complete
  - Cross-repo: Requires hello-multiapp-infra

- [ ] Test in multiple browsers
  - Done when: Works in Chrome, Firefox, Safari, Edge
  - Dependencies: Frontend complete

- [ ] Test responsive design
  - Done when: Works well on mobile and desktop viewports
  - Dependencies: Frontend complete

- [ ] Validate error scenarios
  - Done when: API down shows helpful error message
  - Dependencies: Error handling implemented
  - Cross-repo: Test with API stopped

## Cross-Repository Dependencies

**Blocks:**
- None (frontend is a leaf service in dependency graph)

**Blocked by:**
- hello-multiapp-api implementation (needs API endpoints)
- hello-multiapp-api CORS configuration (needs cross-origin access)

**Coordinates with:**
- hello-multiapp-api: API contract (endpoints, response formats, CORS)
- hello-multiapp-infra: Container configuration, networking, deployment
- hello-multiapp-infra: Environment variable configuration (API_URL)

## Task Dependencies

```
spec.md → tasks.md → architecture.md
                  ↓
              runbook.md
              cost-plan.md
                  ↓
            README.md

Frontend code → Dockerfile → docker-compose (in infra repo)
    ↓
API integration tests (requires API)
```

## Multi-Repo Handoffs

### From hello-multiapp-api
**Receives:**
- API endpoint contracts (/health, /version)
- CORS configuration
- API response formats

**Status Check:**
- API health endpoint returns 200
- CORS allows frontend origin
- API documented in API's README

### To hello-multiapp-infra
**Provides:**
- Dockerfile for building frontend container
- Port configuration (80)
- API_URL environment variable requirement

**Status Check:**
- Dockerfile builds successfully
- nginx serves index.html correctly
- Container documented in infra's docker-compose
