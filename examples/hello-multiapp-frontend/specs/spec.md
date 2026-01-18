# Spec: Hello Multi-App Frontend

## Goal

Create a simple static web frontend that demonstrates multi-repository coordination by consuming backend API endpoints and showcasing cross-repo integration patterns.

## Scope

- Static HTML/JavaScript frontend
- Integration with hello-multiapp-api service
- Visual demonstration of multi-repo coordination
- Nginx-based containerization
- Complete artifact set with cross-repo references
- Responsive UI showing API connection status

## Non-goals

- Complex frontend framework (React/Vue/Angular)
- State management or routing
- Authentication/authorization
- Backend data persistence
- Advanced styling or animations

## Users & scenarios

**Primary users**: Developers learning multi-repo coordination with Kerrigan

**Key scenarios**:
1. **API integration**: Frontend calls backend API to demonstrate cross-repo communication
2. **Health monitoring**: Frontend verifies API health and displays status
3. **Version checking**: Frontend fetches and displays API version information
4. **Visual feedback**: Users see multi-repo coordination working in real-time
5. **Learning example**: Developers understand frontend-backend coordination

## Constraints

- Must be simple enough for tutorial purposes (no build step required)
- Should work seamlessly with hello-multiapp-api
- Must be deployable via hello-multiapp-infra
- All coordination through artifact files
- Keep dependencies minimal (vanilla JS, no npm packages)
- Works in modern browsers without polyfills

## Acceptance criteria

### Functional
- [ ] Frontend displays multi-repo coordination information
- [ ] Button triggers API health check
- [ ] Displays API connection status (success/failure)
- [ ] Fetches and displays API version information
- [ ] Handles API connection errors gracefully
- [ ] Automatically checks API on page load
- [ ] Works with both local and containerized API

### Multi-repo coordination
- [ ] specs/ folder contains complete artifact set
- [ ] spec.md references API and infra repositories
- [ ] tasks.md includes cross-repo dependencies
- [ ] architecture.md documents API integration
- [ ] runbook.md references infra deployment

### Non-functional
- [ ] Responsive design (works on mobile/desktop)
- [ ] Fast page load (< 1 second)
- [ ] Clear error messages when API unavailable
- [ ] Docker image builds successfully
- [ ] Works with docker-compose from infra repo
- [ ] README includes setup instructions

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API not available during demo | High | Show clear error message, make API URL configurable |
| CORS issues block API calls | High | API must configure CORS properly, test integration early |
| Container networking confusion | Medium | Document in runbook, use docker-compose networking |
| Browser compatibility | Low | Use standard JavaScript features, test in major browsers |
| Cross-repo sync issues | Medium | Clear documentation in each repo's artifacts |

## Success metrics

- All acceptance criteria met
- Successfully integrates with API and infra repos
- Example demonstrates clear multi-repo patterns
- Users can follow setup in < 5 minutes
- Error messages help debug connection issues

## Repositories

This project is part of a multi-repository architecture:

- **hello-multiapp-api**
  - Role: Backend API service
  - Repository: `examples/hello-multiapp-api`
  - Dependencies: None
  - Integration: Frontend consumes API endpoints

- **hello-multiapp-frontend** (this repository)
  - Role: Web frontend
  - Dependencies: hello-multiapp-api (requires API endpoints)
  - Dependents: None

- **hello-multiapp-infra**
  - Role: Infrastructure and deployment
  - Repository: `examples/hello-multiapp-infra`
  - Dependencies: hello-multiapp-api, hello-multiapp-frontend
  - Integration: Orchestrates both services

## Cross-repo integration points

1. **API Endpoints**: Frontend consumes
   - `GET /health` - Check API availability
   - `GET /version` - Get API version info

2. **Container**: Built and deployed by infra repo
   - Dockerfile defines container image
   - Exposed on port 80 (mapped to 3000)

3. **Configuration**: Coordinated through infra
   - API_URL environment variable
   - Network configuration in docker-compose

4. **Dependencies**: Frontend depends on API
   - Cannot function without API running
   - Must wait for API health check in orchestration
