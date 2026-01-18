# Architecture: Hello Multi-App Infrastructure

## Overview

Infrastructure orchestration layer for a multi-repository application. This repository demonstrates how to coordinate deployment of separate API and frontend services using Docker Compose, providing a practical example of infrastructure-as-code patterns in a multi-repo architecture.

**Technology Stack:**
- **Orchestration**: Docker Compose 3.8
- **Container Runtime**: Docker Engine
- **Networking**: Docker bridge networking
- **Service Discovery**: Docker DNS
- **Configuration**: Environment variables via docker-compose.yml

## Components & Interfaces

### 1. Docker Compose Orchestration (`docker-compose.yml`)

Central configuration file that coordinates all services:

**Services Managed:**
- `api` - Backend API service (FastAPI)
- `frontend` - Web frontend service (nginx)

**Network Configuration:**
- Network name: `multiapp-network`
- Driver: bridge
- DNS: Automatic service name resolution

**Volume Management:**
- No persistent volumes (stateless services)
- Build contexts reference sibling repositories

### 2. API Service Configuration

**Build Configuration:**
```yaml
build:
  context: ../hello-multiapp-api
  dockerfile: Dockerfile
```

**Runtime Configuration:**
- Port mapping: 8000:8000 (host:container)
- Environment variables:
  - `PORT=8000` - API listening port
  - `ENVIRONMENT=docker` - Environment identifier

**Health Check:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 10s
  timeout: 5s
  retries: 3
```

**Network:**
- Connected to: multiapp-network
- Service name: `api`
- Accessible from frontend as: `http://api:8000`

### 3. Frontend Service Configuration

**Build Configuration:**
```yaml
build:
  context: ../hello-multiapp-frontend
  dockerfile: Dockerfile
```

**Runtime Configuration:**
- Port mapping: 3000:80 (host:container)
- Environment variables:
  - `API_URL=http://api:8000` - Backend API endpoint
- Dependencies:
  - `depends_on: api` - Waits for API container

**Network:**
- Connected to: multiapp-network
- Service name: `frontend`
- Accessible from host as: `http://localhost:3000`

## Multi-Repo Orchestration Design

### Repository Coordination Pattern

**Physical Layout:**
```
hello-multiapp/                    # Parent directory
├── hello-multiapp-api/            # API repository
│   ├── main.py                    # API application
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # API container definition
│   └── specs/                     # API documentation
├── hello-multiapp-frontend/       # Frontend repository
│   ├── index.html                 # Web UI
│   ├── nginx.conf                 # Web server config
│   ├── Dockerfile                 # Frontend container definition
│   └── specs/                     # Frontend documentation
└── hello-multiapp-infra/          # Infrastructure repository (this one)
    ├── docker-compose.yml         # *** Orchestration configuration ***
    ├── README.md                  # Setup instructions
    └── specs/                     # Infrastructure documentation
```

**Key Pattern**: Infrastructure repository references sibling directories using relative paths (`../`).

### Build Coordination

**Build Order:**
1. Docker Compose reads configuration
2. API image builds from `../hello-multiapp-api/Dockerfile`
3. Frontend image builds from `../hello-multiapp-frontend/Dockerfile`
4. Both images tagged locally

**Build Context:**
- API context: `../hello-multiapp-api` (entire directory)
- Frontend context: `../hello-multiapp-frontend` (entire directory)
- No shared build artifacts between services

**Build Time:**
- API: ~30 seconds (Python dependencies installation)
- Frontend: ~10 seconds (copy static files)
- Total: ~40 seconds for clean build

### Startup Coordination

**Startup Sequence:**
```
1. docker-compose up
   ↓
2. Create multiapp-network (bridge)
   ↓
3. Start API container
   ↓
4. API health check begins (10s interval)
   ↓ (waits for healthy status)
5. Start frontend container
   ↓
6. Both services running
```

**Dependency Management:**
- `depends_on: api` ensures API starts first
- Health check ensures API is ready before frontend starts
- Graceful failure if health check fails (retries 3x)

**Startup Time:**
- API startup: ~3 seconds
- Health check validation: ~10 seconds
- Frontend startup: ~2 seconds
- Total: ~15 seconds to full operation

## Container Networking

### Bridge Network Architecture

**Network Name**: multiapp-network  
**Driver**: bridge (default Docker network)  
**Subnet**: Auto-assigned by Docker (typically 172.x.x.x/16)

**Service Discovery:**
- Docker provides automatic DNS resolution
- Service name = hostname (e.g., `api` resolves to API container IP)
- No manual IP configuration required

**Communication Paths:**

1. **External → Frontend** (User access)
   ```
   Browser → localhost:3000 → Docker port mapping → Frontend container:80
   ```

2. **External → API** (Direct API access)
   ```
   Browser → localhost:8000 → Docker port mapping → API container:8000
   ```

3. **Frontend → API** (Internal communication)
   ```
   Frontend container → api:8000 → Docker DNS → API container:8000
   ```

**Network Isolation:**
- Services only accessible within multiapp-network (plus exposed ports)
- No access to host network services unless explicitly exposed
- Isolated from other Docker networks on same host

### Port Mapping Strategy

**API Service:**
- Container port: 8000 (FastAPI default)
- Host port: 8000 (matches container for simplicity)
- Mapping: `8000:8000`
- Rationale: Direct mapping, no confusion

**Frontend Service:**
- Container port: 80 (nginx default)
- Host port: 3000 (standard frontend port)
- Mapping: `3000:80`
- Rationale: 80 often restricted/in-use on host, 3000 is conventional

**Port Conflict Handling:**
- If ports in use, docker-compose fails with clear error
- User must stop conflicting services or modify mappings
- Documented in README troubleshooting section

## Health Check Strategy

### API Health Check

**Configuration:**
```yaml
test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
interval: 10s
timeout: 5s
retries: 3
```

**Behavior:**
- Checks every 10 seconds
- Fails if no response in 5 seconds
- Retries 3 times before marking unhealthy
- Failure threshold: 15 seconds (3 retries × 5s timeout)

**Health States:**
- `starting` - Container launched, health check not yet passed
- `healthy` - Health check passing
- `unhealthy` - Health check failed 3+ times

**Impact on Orchestration:**
- Frontend `depends_on` waits for API container start (not health)
- Health status visible in `docker-compose ps`
- Can be used by external monitoring systems

### Frontend Health Check

**Configuration:** None explicit

**Rationale:**
- nginx starts very quickly (~2 seconds)
- Static content serving is reliable
- Failure would be immediately obvious (container exits)
- Health check adds minimal value

**Alternative Monitoring:**
- Monitor via container status (running/exited)
- Check frontend port accessibility from host
- End-to-end test via browser

## Environment Configuration

### API Environment Variables

**Set by Infrastructure:**
- `PORT=8000` - API listens on this port
- `ENVIRONMENT=docker` - Identifies Docker environment

**Used by API:**
- Port binding in FastAPI startup
- Environment-specific logging or behavior
- Displayed in `/version` endpoint

### Frontend Environment Variables

**Set by Infrastructure:**
- `API_URL=http://api:8000` - Backend API endpoint

**Used by Frontend:**
- JavaScript API calls use this URL
- Injected into nginx config or HTML
- Enables frontend to find API via Docker DNS

### Configuration Strategy

**Benefits:**
- Centralized configuration in docker-compose.yml
- No hardcoded values in application code
- Easy to modify for different environments
- Clear separation of concerns

**Limitations:**
- Not suitable for secrets (use Docker secrets in production)
- Changes require container restart
- No runtime reconfiguration

## Integration with Application Repositories

### Integration with hello-multiapp-api

**Dependencies:**
- Requires: `Dockerfile` in API repository
- Requires: `/health` endpoint for health checks
- Requires: API listens on port configured via `PORT` env var

**Coordination Points:**
1. **Build**: Infrastructure builds API using API's Dockerfile
2. **Configuration**: Infrastructure sets PORT and ENVIRONMENT
3. **Networking**: Infrastructure adds API to shared network
4. **Health**: Infrastructure monitors API /health endpoint
5. **Exposure**: Infrastructure exposes API on host port 8000

**API Responsibilities:**
- Provide working Dockerfile
- Implement /health endpoint
- Listen on port from PORT env var
- Enable CORS for frontend
- Log to stdout/stderr for Docker logs

**Infrastructure Responsibilities:**
- Build API image from correct context
- Configure appropriate environment variables
- Monitor API health
- Provide network connectivity
- Expose API to host and frontend

### Integration with hello-multiapp-frontend

**Dependencies:**
- Requires: `Dockerfile` in frontend repository
- Requires: nginx serves content on port 80
- Requires: Frontend uses API_URL for backend calls

**Coordination Points:**
1. **Build**: Infrastructure builds frontend using frontend's Dockerfile
2. **Configuration**: Infrastructure sets API_URL
3. **Networking**: Infrastructure adds frontend to shared network
4. **Dependencies**: Infrastructure ensures API starts first
5. **Exposure**: Infrastructure exposes frontend on host port 3000

**Frontend Responsibilities:**
- Provide working Dockerfile
- Serve content on port 80
- Use API_URL for backend requests
- Handle API unavailability gracefully
- Log to stdout/stderr for Docker logs

**Infrastructure Responsibilities:**
- Build frontend image from correct context
- Configure API_URL to point to API service
- Ensure API available before frontend starts
- Provide network connectivity to API
- Expose frontend to host

## Technology Choices

### Why Docker Compose over Kubernetes?

**Pros:**
- Simple, single-file configuration
- Runs on developer machines (no cluster required)
- Perfect for local development
- Minimal learning curve
- Fast iteration cycle

**Cons:**
- Not suitable for production at scale
- No auto-scaling or self-healing
- Single-host limitation
- Less sophisticated orchestration features

**Decision:** Docker Compose is ideal for this example project, focusing on multi-repo patterns rather than production orchestration complexity.

### Why Bridge Network over Host Network?

**Pros:**
- Service isolation
- DNS-based service discovery
- No port conflicts between services
- More realistic production simulation

**Cons:**
- Slight performance overhead (minimal)
- Additional network layer

**Decision:** Bridge networking provides better isolation and demonstrates production patterns, worth the minimal overhead.

### Why Relative Paths over Git Submodules?

**Pros:**
- Simple directory structure
- No Git submodule complexity
- Easy to understand
- Each repo independently cloneable

**Cons:**
- Requires manual cloning of all repos
- No version coordination mechanism
- Relies on directory naming convention

**Decision:** Simplicity wins for tutorial purposes. Production could use submodules or monorepo.

## Deployment Workflows

### Local Development Workflow

**First Time Setup:**
```bash
# 1. Clone all repositories
mkdir hello-multiapp
cd hello-multiapp
git clone <api-repo> hello-multiapp-api
git clone <frontend-repo> hello-multiapp-frontend
git clone <infra-repo> hello-multiapp-infra

# 2. Start all services
cd hello-multiapp-infra
docker-compose up --build
```

**Daily Development:**
```bash
# Start services
cd hello-multiapp-infra
docker-compose up

# Make changes to API or frontend in their repos
# Rebuild only changed service
docker-compose up --build api  # or frontend
```

**Cleanup:**
```bash
docker-compose down
docker-compose down -v  # Also remove volumes (if any)
```

### Troubleshooting Workflow

**View Logs:**
```bash
docker-compose logs           # All services
docker-compose logs api       # API only
docker-compose logs frontend  # Frontend only
docker-compose logs -f        # Follow mode
```

**Check Service Status:**
```bash
docker-compose ps                           # Service status
docker inspect <container-id>               # Detailed info
docker exec -it <container-id> /bin/sh      # Shell access
```

**Rebuild Services:**
```bash
docker-compose build --no-cache    # Clean rebuild
docker-compose up --force-recreate # Force recreate containers
```

## Scalability Considerations

### Current Architecture
- Single instance of each service
- No load balancing
- No redundancy
- Suitable for: Development, demos, small-scale deployments

### Scaling Options

**Horizontal Scaling (Docker Compose):**
```bash
docker-compose up --scale api=3 --scale frontend=2
```
- Requires: Remove port mappings or use port ranges
- Requires: Load balancer container (nginx, HAProxy)
- Limitation: Single host only

**Production Scaling:**
- Migrate to Kubernetes for multi-host orchestration
- Use managed container services (ECS, GKE, AKS)
- Add load balancer service
- Implement health checks at load balancer
- Configure auto-scaling policies

## Security Considerations

### Current Security Posture

**Strengths:**
- Service isolation via Docker networks
- No exposed volumes with sensitive data
- Minimal attack surface
- Containers run as non-root users (API, frontend defaults)

**Weaknesses:**
- No TLS encryption (HTTP only)
- No authentication/authorization
- Permissive CORS (allow all origins)
- Environment variables visible in config
- No secrets management

### Production Hardening

**Required for Production:**
1. **TLS/HTTPS**: Add reverse proxy with TLS termination
2. **Secrets Management**: Use Docker secrets or vault
3. **CORS**: Restrict to specific origins
4. **Network Policies**: Limit inter-service communication
5. **Image Scanning**: Scan for vulnerabilities before deployment
6. **Least Privilege**: Run containers as specific non-root users
7. **Read-Only Filesystem**: Where possible
8. **Resource Limits**: Prevent DoS via resource exhaustion

## Monitoring & Observability

### Current Monitoring

**Container Status:**
- `docker-compose ps` - Service status
- `docker stats` - Resource usage
- Health check status (API only)

**Logging:**
- All logs to stdout/stderr
- Captured by Docker logging driver
- Accessible via `docker-compose logs`

**Limitations:**
- No metrics aggregation
- No alerting
- No distributed tracing
- Logs not persisted

### Production Monitoring

**Recommendations:**
1. **Metrics**: Prometheus + Grafana
2. **Logging**: ELK stack or CloudWatch
3. **Tracing**: Jaeger or Zipkin
4. **Alerts**: PagerDuty or OpsGenie
5. **Health Checks**: Uptime monitoring service

## Cross-Repository Coordination

### Version Management

**Current Approach:**
- No explicit versioning
- Uses latest code from each repo
- Relies on compatible changes

**Production Approach:**
- Tag releases in each repo
- Reference specific tags in docker-compose:
  ```yaml
  image: api:v1.2.3
  image: frontend:v2.0.1
  ```
- Coordinate breaking changes across repos
- Maintain compatibility matrix

### Change Coordination

**Breaking Changes:**
1. Identify breaking change (e.g., API endpoint change)
2. Update API repository
3. Update frontend repository to match
4. Update infrastructure docs if needed
5. Test integration
6. Deploy both together

**Non-Breaking Changes:**
- Can deploy independently
- Infrastructure doesn't need updates
- Rebuild specific service only

### Documentation Cross-References

**Related Documentation:**
- **API Architecture**: `../hello-multiapp-api/specs/architecture.md`
  - API endpoints, CORS configuration
  - Container specifications
  
- **Frontend Architecture**: `../hello-multiapp-frontend/specs/architecture.md`
  - API integration approach
  - Container specifications

- **API Runbook**: `../hello-multiapp-api/specs/runbook.md`
  - API deployment procedures
  - Troubleshooting

- **Frontend Runbook**: `../hello-multiapp-frontend/specs/runbook.md`
  - Frontend deployment procedures
  - Troubleshooting

## Future Enhancements

### Potential Improvements

**Configuration Management:**
- Add .env file support
- Environment-specific configs (dev, staging, prod)
- Configuration validation

**Development Experience:**
- Hot reload for development
- Volume mounts for live editing
- Development vs production Docker Compose files

**Production Readiness:**
- Kubernetes manifests (Helm charts)
- CI/CD pipeline definitions
- Infrastructure as Code (Terraform)
- Secrets management integration

**Monitoring:**
- Prometheus metrics exporters
- Centralized logging configuration
- Distributed tracing setup
- Alert definitions
