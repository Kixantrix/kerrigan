# Architecture: Hello Multi-App API

## Overview

A lightweight FastAPI service that provides backend functionality for a multi-repository application. This service demonstrates how to build an API that coordinates with separate frontend and infrastructure repositories.

**Technology Stack:**
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with ASGI
- **Language**: Python 3.11+
- **Containerization**: Docker with python:3.11-slim base

## Components & interfaces

### 1. FastAPI Application (`main.py`)

Core application with three endpoints:

**Endpoints:**
- `GET /` - Service information and endpoint discovery
  - Returns: Service metadata, available endpoints
  - Use case: API discovery and documentation

- `GET /health` - Health check endpoint
  - Returns: `{"status": "ok", "service": "hello-multiapp-api"}`
  - Use case: Container orchestration health checks, monitoring

- `GET /version` - Version information
  - Returns: Version, service name, environment
  - Use case: Frontend version compatibility checks

**CORS Configuration:**
- Allows all origins (configurable for production)
- Enables credentials, all methods, all headers
- Required for: hello-multiapp-frontend cross-origin requests

**Logging:**
- Format: Timestamp, logger name, level, message
- Level: INFO (configurable via LOG_LEVEL env var)
- Output: stdout (captured by Docker)

### 2. Configuration

**Environment Variables:**
- `PORT`: Listening port (default: 8000)
- `ENVIRONMENT`: Environment name (development, docker, production)
- `LOG_LEVEL`: Logging level (default: INFO)

## Multi-Repo Integration

### Integration with hello-multiapp-frontend

**Contract:**
- Frontend expects JSON responses from all endpoints
- CORS must allow frontend origin
- `/health` endpoint confirms API availability
- `/version` endpoint for compatibility checking

**Network:**
- Docker: Accessible via service name `api` on port 8000
- Local dev: Accessible via localhost:8000

**Dependencies:**
- Frontend depends on API being available
- API must start before frontend makes requests
- Health check ensures API readiness

### Integration with hello-multiapp-infra

**Container Configuration:**
- Dockerfile exposes port 8000
- Health check: `curl -f http://localhost:8000/health`
- Environment variables set via docker-compose

**Deployment:**
- Built as Docker image by infra repo
- Orchestrated via docker-compose.yml
- Networked with frontend container

**Monitoring:**
- Health checks every 10 seconds
- 3 retries with 5-second timeout
- Logs accessible via `docker-compose logs api`

## Data Flows

### Flow 1: Health Check (Monitoring)
```
Infrastructure → GET /health → API returns status → Health confirmed
```
Used by Docker health checks and external monitoring.

### Flow 2: Version Check (Frontend)
```
Frontend → GET /version → API returns version info → Compatibility validated
```
Frontend uses this to ensure API version compatibility.

### Flow 3: Service Discovery
```
Client → GET / → API returns endpoint list → Client knows available APIs
```
Provides self-documentation of available endpoints.

### Flow 4: Container Orchestration
```
docker-compose up → Builds API image → Starts container → 
Health check verifies → Frontend container starts → System ready
```
Demonstrates multi-repo container coordination.

## Project Structure

```
hello-multiapp-api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container definition
├── .gitignore          # Git exclusions
├── README.md           # Setup and usage
└── specs/              # Kerrigan artifact set
    ├── spec.md         # This specification
    ├── tasks.md        # Implementation tasks
    ├── architecture.md # Architecture (this file)
    ├── runbook.md      # Deployment procedures
    └── cost-plan.md    # Cost analysis
```

## Technology Choices

### Why FastAPI over Flask?

**Pros:**
- Modern async/await support
- Automatic OpenAPI documentation
- Type hints for validation
- Better performance for async workloads

**Cons:**
- More complex than Flask for simple cases
- Requires understanding of async patterns

**Decision:** FastAPI provides better documentation and performance for this example.

### Why Python over Go/Node?

**Pros:**
- Clear, readable syntax for examples
- Excellent ecosystem
- Easy containerization

**Cons:**
- Larger container images
- Slower cold start than Go

**Decision:** Python's clarity outweighs performance concerns for this example.

## Security & Privacy

- **Input validation**: FastAPI provides automatic validation
- **CORS**: Configure for specific origins in production
- **Secrets**: No secrets in this stateless API
- **Container**: Runs as non-root user (Python image default)
- **Dependencies**: Pin exact versions, scan for CVEs

## Scalability

**Current design:**
- Stateless (horizontal scaling ready)
- No database connections
- Each request is independent
- Docker enables easy replication

**For production:**
- Add multiple API instances behind load balancer
- Configure appropriate worker count in Uvicorn
- Implement rate limiting if needed
- Add caching layer for version endpoint

## Monitoring & Observability

**Health Checks:**
- `/health` endpoint for liveness probes
- Docker health check configuration
- Fast response time for monitoring

**Logging:**
- Structured logs to stdout
- Request logging at INFO level
- Container logs accessible via docker-compose

**Metrics (future):**
- Request count, latency, error rate
- Integration with Prometheus/monitoring tools

## Cross-Repository References

**Depends on:**
- None (foundational service)

**Depended on by:**
- **hello-multiapp-frontend**: Consumes API endpoints, requires CORS
- **hello-multiapp-infra**: Builds and deploys container

**Coordination artifacts:**
- `specs/spec.md`: Documents repository relationships
- `specs/tasks.md`: Cross-repo task dependencies
- `specs/runbook.md`: Deployment coordination with infra
- `Dockerfile`: Contract with infra for containerization

## Deployment Strategy

See `specs/runbook.md` for detailed deployment procedures.

**Summary:**
1. API built first (no dependencies)
2. Frontend built after API (depends on API contract)
3. Infra orchestrates both services
4. Health checks ensure proper startup order
