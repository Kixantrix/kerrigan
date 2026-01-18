# Runbook: Hello Multi-App Frontend

## Overview

Operational guide for deploying, monitoring, and troubleshooting the hello-multiapp-frontend service. This runbook covers local development, Docker deployment, multi-repo orchestration, and cross-service integration.

**Service Information:**
- **Name**: hello-multiapp-frontend
- **Type**: Static web application (nginx)
- **Port**: 80 (container), 3000 (exposed)
- **Dependencies**: hello-multiapp-api (required)
- **Health Check**: HTTP GET to `/` (200 OK)

## Quick Reference

### Common Commands

```bash
# Local development (Python HTTP server)
python3 -m http.server 3000

# Docker build and run
docker build -t frontend:latest .
docker run -p 3000:80 frontend:latest

# Multi-repo deployment
cd ../hello-multiapp-infra
docker-compose up -d frontend

# View logs
docker logs frontend
docker logs -f frontend  # Follow mode

# Stop services
docker-compose down
```

### Service Endpoints

- **Frontend**: http://localhost:3000
- **nginx Health**: http://localhost:3000/ (returns index.html)
- **API (from frontend)**: http://api:8000 (Docker) or http://localhost:8000 (local)

## Local Development

### Prerequisites

**Required:**
- Web browser (Chrome, Firefox, Safari)
- Text editor (VS Code, Sublime, vim)
- Python 3.x (for local HTTP server) OR any web server

**Optional:**
- Docker Desktop (for container testing)
- curl (for API testing)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/your-org/hello-multiapp-frontend.git
cd hello-multiapp-frontend
```

2. **Start local web server**
```bash
# Option 1: Python HTTP server (simplest)
python3 -m http.server 3000

# Option 2: PHP built-in server
php -S localhost:3000

# Option 3: Node.js http-server
npx http-server -p 3000

# Option 4: nginx (if installed locally)
nginx -c nginx.conf -p $(pwd)
```

3. **Start API service** (required for full functionality)
```bash
# In separate terminal
cd ../hello-multiapp-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

4. **Open browser**
```bash
# Linux/macOS
open http://localhost:3000

# Windows
start http://localhost:3000
```

### Development Workflow

**File Changes:**
1. Edit `index.html` in your favorite editor
2. Save the file
3. Refresh browser (Ctrl/Cmd + R)
4. No build step required!

**API Integration Testing:**
1. Ensure API is running on port 8000
2. Click "Check API Status" button
3. Verify success message appears
4. Check browser console for network logs (F12)

**CSS Changes:**
- Styles are embedded in `<style>` tag
- Edit lines 7-83 in `index.html`
- Changes visible on refresh

**JavaScript Changes:**
- Code is in `<script>` tag (lines 107-167)
- Use browser DevTools for debugging
- Console.log for debugging: `console.log('Debug:', variable)`

### Troubleshooting Local Development

**Issue: API connection fails**
```
Symptom: Red error banner "API Connection Failed"
Cause: API not running or wrong port

Solution:
1. Check API is running: curl http://localhost:8000/health
2. Verify port in index.html matches API port
3. Check browser console for CORS errors
4. Ensure API has CORS enabled
```

**Issue: Port 3000 already in use**
```
Symptom: "Address already in use" error
Cause: Another service using port 3000

Solution:
1. Find process: lsof -i :3000
2. Kill process: kill -9 <PID>
3. Or use different port: python3 -m http.server 3001
```

**Issue: Changes not visible**
```
Symptom: Edits to index.html not reflected
Cause: Browser cache

Solution:
1. Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Open DevTools → Disable cache (Network tab)
```

## Docker Deployment

### Build and Run

**Build image:**
```bash
cd hello-multiapp-frontend
docker build -t hello-multiapp-frontend:latest .

# Tag with version
docker build -t hello-multiapp-frontend:1.0.0 .

# Build with custom name
docker build -t frontend:dev .
```

**Run container:**
```bash
# Basic run
docker run -p 3000:80 hello-multiapp-frontend:latest

# With custom API URL
docker run -p 3000:80 \
  -e API_URL=http://localhost:8000 \
  hello-multiapp-frontend:latest

# Detached mode with name
docker run -d \
  --name frontend \
  -p 3000:80 \
  hello-multiapp-frontend:latest

# With API container linked
docker run -d \
  --name frontend \
  --link api:api \
  -p 3000:80 \
  hello-multiapp-frontend:latest
```

**Verify deployment:**
```bash
# Check container is running
docker ps | grep frontend

# Check logs
docker logs frontend

# Test endpoint
curl http://localhost:3000

# Test API connectivity (from host)
curl http://localhost:8000/health
```

### Container Management

**View logs:**
```bash
# View all logs
docker logs frontend

# Follow logs (live tail)
docker logs -f frontend

# Last 100 lines
docker logs --tail 100 frontend

# Logs since 10 minutes ago
docker logs --since 10m frontend
```

**Restart container:**
```bash
# Restart (preserves container)
docker restart frontend

# Stop and start (recreates)
docker stop frontend
docker start frontend

# Remove and recreate
docker rm -f frontend
docker run -d --name frontend -p 3000:80 hello-multiapp-frontend:latest
```

**Inspect container:**
```bash
# View configuration
docker inspect frontend

# View resource usage
docker stats frontend

# Execute commands in container
docker exec frontend ls /usr/share/nginx/html
docker exec frontend cat /etc/nginx/conf.d/default.conf

# Interactive shell
docker exec -it frontend sh
```

### Troubleshooting Docker

**Issue: Container starts but crashes immediately**
```
Symptom: Container exits after starting
Diagnosis: docker logs frontend

Common causes:
1. nginx configuration error
2. Port already in use
3. Permission issues

Solution:
1. Check logs: docker logs frontend
2. Test config: docker run --rm frontend nginx -t
3. Verify port: netstat -an | grep 3000
```

**Issue: Cannot access frontend from browser**
```
Symptom: Connection refused on http://localhost:3000
Diagnosis: docker ps (is container running?)

Solution:
1. Verify container: docker ps | grep frontend
2. Check port mapping: docker port frontend
3. Test from host: curl http://localhost:3000
4. Check firewall: sudo ufw status
5. On Mac: use 127.0.0.1 instead of localhost
```

**Issue: API calls fail in Docker**
```
Symptom: Frontend loads but API check fails
Diagnosis: docker logs frontend (check nginx errors)

Solution:
1. Check network: docker network inspect bridge
2. Verify API container: docker ps | grep api
3. Test API from frontend container:
   docker exec frontend wget -O- http://api:8000/health
4. Check CORS in API logs
```

## Multi-Repo Deployment

### Using hello-multiapp-infra

**Full stack deployment:**
```bash
# Navigate to infra repository
cd ../hello-multiapp-infra

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Check status
docker-compose ps
```

**Service-specific operations:**
```bash
# Rebuild and restart frontend only
docker-compose up -d --build frontend

# Stop frontend only
docker-compose stop frontend

# View frontend logs
docker-compose logs frontend

# Scale frontend (if load balancer configured)
docker-compose up -d --scale frontend=3
```

**Network testing:**
```bash
# Test frontend → API connectivity
docker-compose exec frontend wget -O- http://api:8000/health

# Test API → health check
docker-compose exec api curl http://frontend/

# View network configuration
docker network inspect hello-multiapp-infra_multiapp-network
```

### Cross-Repo Coordination

**Update workflow:**

1. **Frontend changes only:**
```bash
# 1. Make changes in frontend repo
cd hello-multiapp-frontend
# Edit index.html

# 2. Test locally
python3 -m http.server 3000

# 3. Commit changes
git add index.html
git commit -m "Update UI styling"
git push origin main

# 4. Rebuild in infra repo
cd ../hello-multiapp-infra
docker-compose up -d --build frontend
```

2. **Frontend + API changes:**
```bash
# 1. Update API first
cd hello-multiapp-api
# Make changes, commit, push

# 2. Update frontend
cd ../hello-multiapp-frontend
# Make changes, commit, push

# 3. Deploy both
cd ../hello-multiapp-infra
docker-compose down
docker-compose up -d --build
```

3. **Configuration changes:**
```bash
# Update docker-compose.yml in infra repo
cd hello-multiapp-infra
# Edit docker-compose.yml (ports, environment, etc.)

# Apply changes
docker-compose up -d
```

### Troubleshooting Multi-Repo

**Issue: Frontend can't find API**
```
Symptom: API Connection Failed in UI
Diagnosis: Check docker-compose.yml network configuration

Solution:
1. Verify services in same network:
   docker-compose config | grep -A 5 networks
2. Check API service name matches:
   API_URL should be http://api:8000 (not localhost)
3. Check depends_on in docker-compose.yml:
   frontend:
     depends_on:
       - api
4. Restart both services:
   docker-compose restart api frontend
```

**Issue: Old version of frontend deployed**
```
Symptom: Changes not reflected after rebuild
Cause: Docker cache

Solution:
1. Force rebuild: docker-compose build --no-cache frontend
2. Remove old images: docker images | grep frontend
3. Clean rebuild: docker-compose down && docker-compose up -d --build
```

**Issue: Port conflicts**
```
Symptom: "Port already in use" error
Diagnosis: docker-compose up shows port conflict

Solution:
1. Check what's using port:
   lsof -i :3000
   netstat -an | grep 3000
2. Stop conflicting service or change port in docker-compose.yml:
   ports:
     - "3001:80"  # Use 3001 instead
3. Update documentation with new port
```

## API Integration

### Health Check Validation

**Manual testing:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","service":"hello-multiapp-api"}

# Test version endpoint
curl http://localhost:8000/version

# Expected response:
# {"version":"1.0.0","service":"hello-multiapp-api","environment":"development"}
```

**Automated testing:**
```bash
# Check API is reachable
if curl -sf http://localhost:8000/health > /dev/null; then
  echo "API is healthy"
else
  echo "API is down"
  exit 1
fi
```

### CORS Configuration

**Verify CORS headers:**
```bash
# Test CORS preflight
curl -X OPTIONS http://localhost:8000/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Expected headers:
# access-control-allow-origin: *
# access-control-allow-methods: GET, POST, ...
# access-control-allow-headers: *
```

**CORS troubleshooting:**
```
Issue: CORS error in browser console
Error: "Access to fetch at 'http://localhost:8000' from origin 
       'http://localhost:3000' has been blocked by CORS policy"

Solution:
1. Check API CORS middleware is enabled (main.py)
2. Verify API allows origin: allow_origins=["*"]
3. Test with curl (bypasses CORS)
4. Clear browser cache
5. Check API logs for CORS errors
```

## Monitoring

### Health Checks

**Container health:**
```bash
# Docker health status
docker inspect frontend | grep -A 5 Health

# Manual health check
curl -f http://localhost:3000/ || echo "Frontend unhealthy"

# Check nginx process
docker exec frontend ps aux | grep nginx
```

**Service health:**
- Frontend loads: http://localhost:3000 returns HTML
- API check button works: Returns green success message
- Version info displays: Shows API version details

### Logs

**Access logs:**
```bash
# nginx access logs (stdout)
docker logs frontend | grep "GET /"

# Filter by status code
docker logs frontend | grep "HTTP/1.1 200"

# Count requests
docker logs frontend | grep "GET" | wc -l
```

**Error logs:**
```bash
# nginx error logs (stderr)
docker logs frontend 2>&1 | grep "error"

# Filter by severity
docker logs frontend 2>&1 | grep "emerg\|alert\|crit"

# JavaScript errors (browser console)
# Open DevTools (F12) → Console tab
```

**Log rotation:**
```bash
# Docker handles log rotation automatically
# Configure in /etc/docker/daemon.json:
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Performance Monitoring

**Resource usage:**
```bash
# Real-time stats
docker stats frontend

# CPU and memory
docker stats --no-stream frontend | awk '{print $3, $4}'

# Network I/O
docker stats --no-stream frontend | awk '{print $8, $9}'
```

**Request metrics:**
```bash
# Request count from logs
docker logs frontend | grep -c "GET /"

# Response times (requires nginx logging configured)
docker logs frontend | awk '{print $NF}' | grep -E '^[0-9]'

# Error rate
docker logs frontend 2>&1 | grep -c "error"
```

## Common Issues

### Frontend Issues

**Issue: Blank page**
```
Symptom: Browser shows empty white page
Diagnosis: Check browser console (F12)

Solutions:
1. JavaScript error: Check console for errors
2. File not found: Verify index.html in /usr/share/nginx/html
3. nginx not running: Check container logs
4. Browser cache: Hard refresh (Ctrl+Shift+R)
```

**Issue: Styles not loading**
```
Symptom: Page loads but no styling
Diagnosis: Check if CSS is embedded or external

Solutions:
1. Verify <style> tag in index.html (lines 7-83)
2. Check for CSS syntax errors
3. Clear browser cache
4. Verify file wasn't corrupted during Docker build
```

### API Connection Issues

**Issue: API connection timeout**
```
Symptom: "API Connection Failed" after long delay
Diagnosis: Network connectivity issue

Solutions:
1. Check API is running: curl http://localhost:8000/health
2. Verify network: ping api (from frontend container)
3. Check firewall rules: sudo iptables -L
4. Verify docker network: docker network inspect multiapp-network
5. Check API logs for errors: docker logs api
```

**Issue: CORS policy error**
```
Symptom: "blocked by CORS policy" in browser console
Diagnosis: CORS not configured in API

Solutions:
1. Verify CORS middleware in API (main.py lines 26-33)
2. Check allowed origins: should include frontend origin
3. Restart API after changes: docker-compose restart api
4. Test with curl: curl -H "Origin: http://localhost:3000" http://localhost:8000/health
```

### Container Issues

**Issue: Container exits immediately**
```
Symptom: docker ps shows no frontend container
Diagnosis: docker logs frontend

Solutions:
1. nginx config error: docker run --rm frontend nginx -t
2. File permissions: docker exec frontend ls -la /usr/share/nginx/html
3. Port conflict: netstat -an | grep 80
4. Check Dockerfile for errors
```

**Issue: High memory usage**
```
Symptom: docker stats shows >100MB memory
Diagnosis: Memory leak or configuration issue

Solutions:
1. Expected memory: 5-10MB for nginx
2. Check for memory leak: docker stats --no-stream frontend
3. Restart container: docker restart frontend
4. Check nginx config for issues
```

## Deployment Checklist

### Pre-Deployment

- [ ] API service is running and healthy
- [ ] Frontend code tested locally
- [ ] Docker build succeeds without errors
- [ ] API URL configured correctly
- [ ] CORS enabled in API
- [ ] Network configuration verified

### Deployment Steps

1. [ ] Build Docker image: `docker build -t frontend:latest .`
2. [ ] Tag image with version: `docker tag frontend:latest frontend:1.0.0`
3. [ ] Test locally: `docker run -p 3000:80 frontend:latest`
4. [ ] Verify API connectivity works
5. [ ] Deploy via infra: `docker-compose up -d frontend`
6. [ ] Check logs: `docker-compose logs frontend`
7. [ ] Test in browser: http://localhost:3000
8. [ ] Verify API check button works

### Post-Deployment

- [ ] Service is running: `docker ps | grep frontend`
- [ ] Health check passes: `curl http://localhost:3000/`
- [ ] API integration works: Click "Check API Status"
- [ ] Logs are clean: No errors in `docker logs frontend`
- [ ] Resource usage normal: `docker stats frontend`
- [ ] Documentation updated

## Rollback Procedure

**If deployment fails:**

1. **Identify issue:**
```bash
docker logs frontend
docker logs api
```

2. **Rollback to previous version:**
```bash
# Stop current version
docker-compose stop frontend

# Deploy previous version
docker-compose up -d frontend:1.0.0

# Or rebuild from previous commit
git checkout HEAD~1
docker-compose up -d --build frontend
```

3. **Verify rollback:**
```bash
curl http://localhost:3000/
docker logs frontend | tail -20
```

## Cross-Service Dependencies

### Dependency Map

```
hello-multiapp-frontend (this service)
  ↓ Requires
hello-multiapp-api (port 8000)
  ↓ Orchestrated by
hello-multiapp-infra (docker-compose)
```

### Service Startup Order

1. **API starts first** (via `depends_on` in docker-compose.yml)
2. **Frontend starts second** (after API is running)
3. **Frontend automatically checks API** (on page load)

### Related Runbooks

- **API Runbook**: `../hello-multiapp-api/specs/runbook.md`
  - API deployment procedures
  - CORS troubleshooting
  - Performance tuning

- **Infra Runbook**: `../hello-multiapp-infra/specs/runbook.md`
  - Multi-service orchestration
  - Network configuration
  - Full stack deployment

## Emergency Procedures

### Service Down

**If frontend is completely unresponsive:**
```bash
# 1. Check container status
docker ps -a | grep frontend

# 2. If not running, start it
docker start frontend

# 3. If still failing, rebuild
docker-compose up -d --build frontend

# 4. If persistent, check dependencies
docker logs api  # API might be down
docker network inspect multiapp-network  # Network issues
```

### Data Loss

**Note:** This service is stateless. No data loss possible.
- All content is in source control
- No database or persistent storage
- Redeploying restores all functionality

### Performance Degradation

**If frontend is slow:**
```bash
# Check resource usage
docker stats frontend

# Check nginx processes
docker exec frontend ps aux

# Check network latency
docker exec frontend ping api

# Restart if needed
docker restart frontend
```

## Maintenance Windows

### Update Procedure

1. **Announce maintenance** (if production)
2. **Stop service**: `docker-compose stop frontend`
3. **Pull latest code**: `git pull origin main`
4. **Rebuild image**: `docker-compose build frontend`
5. **Start service**: `docker-compose up -d frontend`
6. **Verify health**: Test in browser
7. **Monitor logs**: `docker-compose logs -f frontend`

### Estimated Downtime

- Frontend update: <30 seconds
- Full rebuild: <1 minute
- Multi-repo update: <2 minutes

### Zero-Downtime Update

**With multiple instances:**
```bash
# Scale up
docker-compose up -d --scale frontend=2

# Update first instance
docker-compose stop frontend_1
docker-compose up -d frontend_1

# Update second instance
docker-compose stop frontend_2
docker-compose up -d frontend_2

# Scale back down
docker-compose up -d --scale frontend=1
```
