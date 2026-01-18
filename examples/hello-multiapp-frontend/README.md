# Hello Multi-App Frontend

A lightweight static web application that demonstrates multi-repository coordination and API integration. This frontend connects to [hello-multiapp-api](https://github.com/your-org/hello-multiapp-api) and is deployed using [hello-multiapp-infra](https://github.com/your-org/hello-multiapp-infra).

## Overview

**Technology Stack:**
- Vanilla HTML5, CSS3, JavaScript (ES6+)
- nginx:alpine web server
- Docker containerization
- RESTful API integration

**Key Features:**
- ✅ Zero dependencies (no npm, no build step)
- ✅ Real-time API health checking
- ✅ Responsive design with error handling
- ✅ Production-ready nginx configuration
- ✅ Multi-repo coordination example

## Multi-Repo Architecture

This project is part of a three-repository system demonstrating microservices coordination:

```
hello-multiapp-frontend  (this repo)
    ↓ Consumes API
hello-multiapp-api
    ↓ Deployed by
hello-multiapp-infra
```

**Repository Responsibilities:**
- **frontend** (this): User interface and API client
- **api**: Backend REST API service
- **infra**: Docker Compose orchestration and deployment

Each repository is independently deployable but designed to work together as a cohesive system.

## Quick Start

### Local Development

**Prerequisites:**
- Python 3.x or any HTTP server
- hello-multiapp-api running on port 8000

**Steps:**
```bash
# 1. Clone repository
git clone https://github.com/your-org/hello-multiapp-frontend.git
cd hello-multiapp-frontend

# 2. Start web server
python3 -m http.server 3000

# 3. Open browser
open http://localhost:3000
```

The frontend will automatically attempt to connect to the API at `http://localhost:8000`.

### Docker Deployment

**Single service:**
```bash
# Build image
docker build -t hello-multiapp-frontend:latest .

# Run container
docker run -p 3000:80 hello-multiapp-frontend:latest

# Access frontend
open http://localhost:3000
```

**With API (manual linking):**
```bash
# Start API container first
docker run -d --name api -p 8000:8000 hello-multiapp-api:latest

# Start frontend with link
docker run -d \
  --name frontend \
  --link api:api \
  -p 3000:80 \
  hello-multiapp-frontend:latest
```

### Multi-Repo Deployment (Recommended)

**Full stack with docker-compose:**
```bash
# Clone infra repository
git clone https://github.com/your-org/hello-multiapp-infra.git
cd hello-multiapp-infra

# Ensure frontend and api repos are in parent directory:
# ../hello-multiapp-frontend
# ../hello-multiapp-api
# ./hello-multiapp-infra (current)

# Start all services
docker-compose up -d

# Access services
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

This is the recommended approach as it:
- Handles service dependencies automatically
- Configures networking correctly
- Manages environment variables
- Ensures proper startup order

## Features

### API Integration

**Automatic Health Check:**
- Runs on page load
- Displays connection status
- Shows API version information

**Manual Testing:**
- "Check API Status" button
- Real-time status updates
- Detailed error messages

**Endpoints Used:**
- `GET /health` - API availability check
- `GET /version` - Version and environment info

### Error Handling

**Connection Failures:**
- Clear error messages
- API URL displayed for troubleshooting
- Suggestions for resolution

**CORS Issues:**
- Detected automatically
- Instructions provided
- API configuration guidance

**Network Timeouts:**
- Browser-handled timeouts
- Retry capability via button
- Status persistence between checks

### User Interface

**Responsive Design:**
- Mobile-first CSS approach
- Adapts to screen sizes
- System font stack for performance

**Status Visualization:**
- Loading state (yellow)
- Success state (green)
- Error state (red)
- Version information display

**Accessibility:**
- Semantic HTML structure
- Proper heading hierarchy
- Color contrast compliance
- Keyboard navigation support

## Project Structure

```
hello-multiapp-frontend/
├── Dockerfile              # Container build configuration
├── index.html              # Single-page application (HTML + CSS + JS)
├── nginx.conf              # nginx web server configuration
├── specs/                  # Documentation
│   ├── architecture.md     # System design and integration
│   ├── cost-plan.md        # Cost analysis and budgeting
│   ├── runbook.md          # Operations and troubleshooting
│   ├── spec.md             # Original requirements
│   └── tasks.md            # Implementation tasks
└── README.md               # This file
```

### Key Files

**index.html** (170 lines)
- Complete single-page application
- Embedded styles (lines 7-83)
- Embedded JavaScript (lines 107-167)
- No external dependencies

**nginx.conf** (14 lines)
- Minimal production configuration
- gzip compression enabled
- SPA routing support
- Static file serving optimized

**Dockerfile** (11 lines)
- Based on nginx:alpine (~25MB)
- Copies static files
- Configures nginx
- Production-ready

## API Integration Details

### Configuration

**API URL:**
```javascript
const API_URL = window.API_URL || 'http://localhost:8000';
```

**Override via Environment:**
```bash
# In docker-compose.yml
environment:
  - API_URL=http://api:8000
```

### CORS Requirements

The API must enable CORS to allow frontend access:

```python
# In hello-multiapp-api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Network Connectivity

**Local Development:**
- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- Direct HTTP connection

**Docker Deployment:**
- Frontend: `http://localhost:3000` (host access)
- API: `http://api:8000` (container-to-container via Docker DNS)
- Bridge network: `multiapp-network`

## Multi-Repo Coordination

### Development Workflow

**Working on frontend only:**
```bash
# 1. Ensure API is running
cd ../hello-multiapp-api
docker run -d -p 8000:8000 hello-multiapp-api:latest

# 2. Develop frontend
cd ../hello-multiapp-frontend
python3 -m http.server 3000

# 3. Make changes and refresh browser
```

**Testing integration changes:**
```bash
# 1. Make changes in both repos
cd ../hello-multiapp-api
# Edit files, commit changes

cd ../hello-multiapp-frontend
# Edit files, commit changes

# 2. Deploy both services
cd ../hello-multiapp-infra
docker-compose up -d --build
```

### Deployment Coordination

**Service Dependencies:**
- Frontend requires API to be running
- Managed by `depends_on` in docker-compose.yml
- API must have CORS configured
- Network must be shared

**Version Compatibility:**
- Frontend displays API version
- No strict version checking (yet)
- Breaking API changes require frontend updates
- Coordinated releases recommended

### Repository Links

**Related Repositories:**
- **API**: [hello-multiapp-api](https://github.com/your-org/hello-multiapp-api)
  - Backend REST API service
  - Health and version endpoints
  - CORS configuration

- **Infrastructure**: [hello-multiapp-infra](https://github.com/your-org/hello-multiapp-infra)
  - Docker Compose orchestration
  - Network configuration
  - Multi-service deployment

## Development

### Local Changes

**Edit HTML:**
```bash
# 1. Open index.html in editor
vim index.html

# 2. Refresh browser to see changes
# No build step required!
```

**Test API Integration:**
```bash
# 1. Start local API
cd ../hello-multiapp-api
uvicorn main:app --reload --port 8000

# 2. Start frontend
cd ../hello-multiapp-frontend
python3 -m http.server 3000

# 3. Open browser and click "Check API Status"
```

### Docker Development

**Rebuild and test:**
```bash
# Build new image
docker build -t frontend:dev .

# Test locally
docker run --rm -p 3000:80 frontend:dev

# If working, tag as latest
docker tag frontend:dev hello-multiapp-frontend:latest
```

### Testing

**Manual Testing:**
1. Load page → Should see title and button
2. Click button → Should show green success (if API running)
3. Stop API → Click button → Should show red error
4. Check browser console → Should be error-free

**API Connection Testing:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test version endpoint
curl http://localhost:8000/version

# Test CORS
curl -X OPTIONS http://localhost:8000/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**Container Testing:**
```bash
# Check nginx is running
docker exec frontend ps aux | grep nginx

# Check files are present
docker exec frontend ls -la /usr/share/nginx/html

# Test from inside container
docker exec frontend wget -O- http://localhost/
```

## Troubleshooting

### Common Issues

**Issue: API Connection Failed**
```
Symptom: Red error banner in UI
Cause: API not running or wrong URL

Solution:
1. Check API is running: curl http://localhost:8000/health
2. Verify API_URL in index.html matches API port
3. Check CORS is enabled in API
4. Check browser console for errors (F12)
```

**Issue: CORS Error in Console**
```
Symptom: "blocked by CORS policy" in browser console
Cause: API CORS not configured

Solution:
1. Verify CORS middleware in API (main.py)
2. Ensure allow_origins includes frontend origin
3. Restart API after changes
4. Clear browser cache
```

**Issue: Changes Not Visible**
```
Symptom: Edited index.html but browser shows old version
Cause: Browser cache

Solution:
1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Open DevTools → Disable cache (Network tab)
```

**Issue: Container Won't Start**
```
Symptom: docker ps shows no frontend container
Cause: Port conflict or configuration error

Solution:
1. Check port availability: lsof -i :3000
2. Check logs: docker logs frontend
3. Verify nginx config: docker run --rm frontend nginx -t
4. Try different port: docker run -p 3001:80 frontend
```

### Getting Help

**Documentation:**
- [Architecture](specs/architecture.md) - System design
- [Runbook](specs/runbook.md) - Operations guide
- [Cost Plan](specs/cost-plan.md) - Budget analysis

**Related Documentation:**
- [API Documentation](../hello-multiapp-api/README.md)
- [Infra Documentation](../hello-multiapp-infra/README.md)

**Support:**
- Open an issue in this repository
- Check API repository for backend issues
- Check infra repository for deployment issues

## Monitoring

### Health Checks

**Frontend Health:**
```bash
# HTTP check
curl -f http://localhost:3000/ || echo "Frontend unhealthy"

# Docker health
docker inspect frontend | grep -A 5 Health
```

**Integration Health:**
```bash
# Check API from frontend container
docker exec frontend wget -O- http://api:8000/health
```

### Logs

**Access logs:**
```bash
# View all logs
docker logs frontend

# Follow logs
docker logs -f frontend

# Filter by status code
docker logs frontend | grep "HTTP/1.1 200"
```

**Error logs:**
```bash
# nginx errors
docker logs frontend 2>&1 | grep "error"

# JavaScript errors
# Open browser DevTools (F12) → Console tab
```

### Metrics

**Resource usage:**
```bash
# Real-time stats
docker stats frontend

# Memory and CPU
docker stats --no-stream frontend | awk '{print $3, $4}'
```

## Production Considerations

### Security

**Recommendations:**
1. Enable HTTPS with TLS 1.3
2. Add Content-Security-Policy headers
3. Restrict CORS origins (not wildcard)
4. Implement rate limiting
5. Use security headers (HSTS, X-Frame-Options)

**nginx Security Headers:**
```nginx
# Add to nginx.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### Performance

**Optimizations:**
- gzip compression enabled by default
- Static file caching (add Cache-Control headers)
- CDN integration (CloudFlare, CloudFront)
- HTTP/2 support (nginx 1.9.5+)

**Scaling:**
- Horizontal: Deploy multiple instances behind load balancer
- Vertical: Current container size is minimal (<10MB RAM)
- CDN: Offload static content to edge locations

### High Availability

**Multi-instance Deployment:**
```bash
# Scale with docker-compose
docker-compose up -d --scale frontend=3

# Add load balancer (nginx, HAProxy, AWS ALB)
```

**Zero-Downtime Updates:**
```bash
# Rolling update
docker-compose up -d --no-deps --scale frontend=2 frontend
docker-compose up -d --no-deps --scale frontend=1 frontend
```

## Contributing

### Development Guidelines

1. Keep vanilla JS (no framework dependencies)
2. Maintain single-file architecture
3. Test with API integration
4. Update documentation for changes
5. Follow existing code style

### Testing Changes

```bash
# 1. Make changes
vim index.html

# 2. Test locally
python3 -m http.server 3000

# 3. Test with Docker
docker build -t frontend:test .
docker run -p 3000:80 frontend:test

# 4. Test multi-repo
cd ../hello-multiapp-infra
docker-compose up -d --build frontend
```

### Documentation Updates

When making changes, update:
- This README.md
- specs/architecture.md (if design changes)
- specs/runbook.md (if operations change)
- specs/cost-plan.md (if cost implications)

## License

[Your License Here]

## Contact

- **Repository**: https://github.com/your-org/hello-multiapp-frontend
- **API Repository**: https://github.com/your-org/hello-multiapp-api
- **Infra Repository**: https://github.com/your-org/hello-multiapp-infra
- **Issues**: https://github.com/your-org/hello-multiapp-frontend/issues

---

**Part of the Hello Multi-App Project** - Demonstrating multi-repository microservices coordination with Docker and modern DevOps practices.
