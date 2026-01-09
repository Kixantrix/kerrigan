# Spec: Hello API

## Goal
Create a simple, well-structured REST API service that demonstrates best practices for API development and serves as a reference example for the Kerrigan agent workflow.

## Scope

- HTTP REST API with 2-3 basic endpoints (health check, greeting, echo)
- JSON request/response handling
- Basic error handling and validation
- Structured logging
- Configuration management (port, environment)
- Docker containerization for deployment
- Comprehensive test coverage

## Non-goals

- Database integration (keep it stateless)
- Authentication/authorization (focus on structure)
- Complex business logic
- Production-grade monitoring/observability (basic logging only)
- Multi-service architecture

## Users & Scenarios

**Primary users**: Developers learning the Kerrigan workflow

**Key scenarios**:
1. **Health check**: System monitoring tools check if service is running
2. **Personalized greeting**: Client sends name, receives greeting message
3. **Echo service**: Client sends arbitrary JSON, receives it back (for testing)

## Constraints

- Must be simple enough to implement in < 4 hours
- Should demonstrate code quality from day one (no prototype exceptions)
- Must work in containerized environment
- Should use a mainstream language/framework (suggest: Python/Flask, Go/net/http, or Node/Express)
- Must include tests from the start
- CI must stay green throughout implementation

## Acceptance criteria

### Functional
- [ ] GET /health returns 200 with {"status": "ok"}
- [ ] GET /greet?name=X returns 200 with {"message": "Hello, X!"}
- [ ] POST /echo with JSON body returns same JSON with 200
- [ ] Invalid requests return appropriate 4xx errors with error messages
- [ ] Service can be started via command line or Docker

### Non-functional
- [ ] Response time < 100ms for all endpoints (unloaded)
- [ ] Test coverage > 80%
- [ ] All endpoints have unit/integration tests
- [ ] Service logs requests at INFO level
- [ ] Configuration can be changed via environment variables
- [ ] Docker image builds successfully
- [ ] README includes setup and usage instructions

### Quality
- [ ] Code passes linting/formatting checks
- [ ] No security vulnerabilities in dependencies
- [ ] CI workflow validates all checks
- [ ] Code is modular (separate files for routing, handlers, config)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Choice of stack creates friction | Medium | Pick widely-used, simple framework; document rationale |
| Over-engineering for simple example | Low | Stick to scope; use checklist to prevent creep |
| Missing quality checks | Medium | Add linting/testing to CI from start |
| Docker complexity | Low | Use minimal base image; keep Dockerfile simple |

## Success Metrics

- All acceptance criteria met
- CI passes on all commits
- Implementation completes in single milestone
- Example is referenced in handoff playbook as "clean implementation"
- Code serves as template for future projects
