# Architecture: Hello Multi-App Frontend

## Overview

A static single-page application (SPA) that provides a web interface for the multi-repository application. This frontend demonstrates how to build a lightweight, containerized web UI that integrates with a separate backend API and is deployed using shared infrastructure configurations.

**Technology Stack:**
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Web Server**: nginx:alpine
- **Containerization**: Docker with nginx base image
- **API Integration**: Fetch API with CORS support

## Components & Interfaces

### 1. Static Web Application (`index.html`)

Single-page application with embedded styles and JavaScript:

**Features:**
- Responsive design with mobile-first CSS
- Real-time API connectivity testing
- Automatic API health check on page load
- Error handling and status visualization
- Version information display

**API Integration Points:**
- `GET /health` - Health check endpoint
  - Validates API connectivity
  - Displays service status
  
- `GET /version` - Version information
  - Shows API version, service name, environment
  - Used for compatibility verification

**JavaScript Configuration:**
```javascript
const API_URL = window.API_URL || 'http://localhost:8000';
```
- Default: Local development (localhost:8000)
- Override: Set window.API_URL in production
- Docker: Configured via environment injection

**State Management:**
- Loading state: Yellow banner during API calls
- Success state: Green banner with API details
- Error state: Red banner with troubleshooting info

### 2. nginx Web Server (`nginx.conf`)

Minimal nginx configuration optimized for static content:

**Configuration:**
- Listen port: 80 (internal container port)
- Root directory: `/usr/share/nginx/html`
- Default file: `index.html`
- SPA routing: Falls back to `index.html` for all routes

**Optimizations:**
- gzip compression enabled for text assets
- Efficient static file serving
- Minimal memory footprint (~5MB)

### 3. Docker Container (`Dockerfile`)

Multi-stage build optimized for size and security:

**Base Image:**
- `nginx:alpine` - Minimal Linux distribution
- Size: ~25MB compressed
- Security: Reduced attack surface

**Build Steps:**
1. Copy `index.html` to nginx web root
2. Copy custom `nginx.conf` configuration
3. Expose port 80
4. Run nginx in foreground mode

## Multi-Repo Integration

### Integration with hello-multiapp-api

**API Dependency:**
- Protocol: HTTP REST
- Endpoints: `/health`, `/version`
- CORS: API configured with `allow_origins=["*"]`
- Network: Connected via Docker bridge network in multi-repo deployment

**CORS Configuration:**
The API must enable CORS for frontend access:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Connectivity Patterns:**
- Development: Frontend → `http://localhost:8000` → API
- Docker: Frontend → `http://api:8000` → API (Docker DNS)
- Production: Frontend → `https://api.example.com` → API (via reverse proxy)

**Error Handling:**
- Network failures: Display connection error with API URL
- API errors: Show HTTP status and error details
- Timeout handling: Fetch API default timeout (browser-dependent)

### Integration with hello-multiapp-infra

**Deployment Configuration:**
The infra repository orchestrates both services:

```yaml
frontend:
  build:
    context: ../hello-multiapp-frontend
    dockerfile: Dockerfile
  ports:
    - "3000:80"
  depends_on:
    - api
  environment:
    - API_URL=http://api:8000
  networks:
    - multiapp-network
```

**Key Integration Points:**
- Build context: Relative path to frontend repository
- Port mapping: External 3000 → Internal 80
- Service dependency: Waits for API service
- Network: Shared bridge network for service discovery
- Environment: API URL injected at runtime

**Service Discovery:**
- Docker DNS resolves `api` hostname to API container
- No hardcoded IP addresses required
- Automatic failover if API container restarts

## Technology Choices

### Why Vanilla JavaScript?

**Pros:**
- Zero dependencies (no npm, no build step)
- Instant load time (~2KB HTML file)
- No security vulnerabilities from dependencies
- Easy to understand and modify
- Perfect for simple UI requirements

**Cons:**
- Not suitable for complex SPAs
- No component reusability
- Manual DOM manipulation
- No TypeScript type safety

**Use Case Fit:**
This is a demonstration app with minimal UI requirements. Vanilla JS provides the fastest time-to-value without framework overhead.

### Why nginx?

**Pros:**
- Industry-standard static file server
- Extremely efficient (handles 10,000+ req/s)
- Minimal memory footprint (~5-10MB)
- Battle-tested security
- Alpine variant is tiny (~25MB image)

**Cons:**
- Overkill for single HTML file
- More complex than `python -m http.server`

**Alternatives Considered:**
- Apache httpd: Heavier, more features than needed
- Caddy: Great for HTTPS but unnecessary here
- Node.js/Express: Requires Node runtime, more overhead
- Python SimpleHTTPServer: Not production-ready

**Use Case Fit:**
nginx is the industry standard for production static file serving. Using it here demonstrates best practices for real-world deployments.

## Data Flow

### User Request Flow

1. **User loads page** (http://localhost:3000)
   - Browser → nginx → Serve index.html
   - nginx compresses response (gzip)
   - Browser renders HTML/CSS

2. **Page load event triggers API check**
   - JavaScript executes `checkAPI()` function
   - Fetch API calls `${API_URL}/health`
   - Browser handles CORS preflight (OPTIONS request)
   - API responds with CORS headers
   - Frontend displays status

3. **User clicks "Check API Status"**
   - Same flow as automatic check
   - Fetches both `/health` and `/version` endpoints
   - Updates UI based on response

### Network Architecture

```
User Browser (http://localhost:3000)
    ↓
nginx Container (port 80)
    ↓
Static HTML + JavaScript
    ↓
Fetch API Request (http://api:8000)
    ↓
Docker Bridge Network (multiapp-network)
    ↓
API Container (port 8000)
    ↓
FastAPI Application
```

## Security Considerations

### Frontend Security

**Content Security:**
- No user input (no XSS risk)
- No dynamic content injection
- Inline styles and scripts (no external resources)

**API Security:**
- CORS validation by browser
- No authentication (demo app)
- API URL configurable (no hardcoded secrets)

**Container Security:**
- Alpine base image (minimal attack surface)
- nginx runs as non-root user
- No shell access needed
- Read-only root filesystem possible

### Production Hardening

**Recommendations:**
1. Use HTTPS with TLS 1.3
2. Implement Content-Security-Policy headers
3. Restrict CORS origins to specific domains
4. Add rate limiting at nginx level
5. Enable nginx security headers
6. Use Docker secrets for sensitive config

## Performance

### Frontend Performance

**Size:**
- HTML file: ~6KB uncompressed
- gzip compressed: ~2KB
- Total download: <3KB
- Time to interactive: <100ms

**nginx Performance:**
- Static file serving: 10,000+ req/s
- Memory usage: ~5-10MB
- CPU usage: Negligible (<1%)

**Browser Compatibility:**
- Modern browsers (ES6+ required)
- Chrome 60+, Firefox 60+, Safari 12+
- No polyfills included

### Scalability

**Horizontal Scaling:**
- Stateless design (scales linearly)
- No session management
- Can deploy 100+ instances easily
- Load balancer required for HA

**CDN Integration:**
- Static assets can be cached
- Cache-Control headers configurable
- CloudFlare, AWS CloudFront compatible

## Monitoring & Observability

### Frontend Monitoring

**Available Metrics:**
- nginx access logs (request count, latency)
- nginx error logs (4xx, 5xx errors)
- Container resource usage (CPU, memory)

**User-Visible Errors:**
- API connection failures (displayed in UI)
- Network timeouts (browser console)
- CORS errors (browser console)

### Integration Points

**Health Checks:**
- Docker: nginx process liveness
- Infrastructure: HTTP GET to `/` (200 OK)
- API: Validated via frontend health check button

**Logs:**
- nginx access logs: stdout
- nginx error logs: stderr
- Collected by Docker logging driver
- Viewable via `docker logs frontend`

## Development Workflow

### Local Development

**File Changes:**
1. Edit `index.html`
2. Refresh browser (instant feedback)
3. No build step required

**API Integration:**
- Run API locally on port 8000
- Frontend connects to `localhost:8000`
- CORS enabled in API for local development

### Docker Development

**Rebuild Workflow:**
```bash
cd hello-multiapp-frontend
docker build -t frontend:dev .
docker run -p 3000:80 frontend:dev
```

**Fast Iteration:**
- Image builds in ~5 seconds
- No dependencies to install
- Minimal layer caching needed

### Multi-Repo Development

**Full Stack Testing:**
```bash
cd hello-multiapp-infra
docker-compose up --build
```

**Service Updates:**
- Changes to frontend require infra rebuild
- API changes automatically picked up
- Network configuration managed by infra

## Cross-Repo Coordination

### Version Compatibility

**API Version Check:**
- Frontend displays API version from `/version` endpoint
- No strict version validation
- Breaking changes require frontend updates

**Deployment Coordination:**
- Infra repository pins service versions
- Frontend and API deployed together
- Rolling updates possible with backward compatibility

### Documentation Cross-References

**Related Documentation:**
- **API Architecture**: `../hello-multiapp-api/specs/architecture.md`
  - CORS configuration details
  - Endpoint specifications
  - API authentication (future)

- **Infra Runbook**: `../hello-multiapp-infra/specs/runbook.md`
  - Multi-repo deployment procedures
  - Service orchestration
  - Network configuration

- **API Runbook**: `../hello-multiapp-api/specs/runbook.md`
  - API troubleshooting
  - Performance tuning
  - Monitoring setup

### Change Management

**Impact Analysis:**
- Frontend changes: Isolated, no API impact
- API endpoint changes: May require frontend updates
- Infra changes: Can affect both frontend and API

**Testing Strategy:**
- Unit: Not applicable (no logic to test)
- Integration: Test API connectivity
- E2E: Manual testing via browser
- Contract: Validate API endpoint expectations

## Future Enhancements

### Potential Improvements

**Features:**
- Add more API endpoints (POST /messages)
- WebSocket support for real-time updates
- User authentication and sessions
- Progressive Web App (PWA) capabilities

**Technical:**
- Environment-specific builds (dev/prod)
- Build step with minification
- TypeScript migration
- React/Vue framework upgrade

**Operations:**
- Health check endpoint for frontend
- Metrics endpoint (Prometheus)
- Structured logging
- Distributed tracing integration

### Migration Path to React

**When to Migrate:**
- UI complexity exceeds vanilla JS capabilities
- Need component reusability
- Team familiar with React ecosystem
- Performance optimization needed

**Migration Strategy:**
1. Add build step (webpack/vite)
2. Convert HTML to JSX components
3. Add state management (Context API)
4. Implement routing (react-router)
5. Add testing (Jest + React Testing Library)

**Cost-Benefit Analysis:**
- Current: 0 dependencies, instant updates
- React: Better DX, worse deployment complexity
- Recommendation: Keep vanilla JS until complexity demands it
