# Runbook: Hello Multi-App Infrastructure

## Service Overview

**Service**: hello-multiapp-infra  
**Type**: Multi-service orchestration (Docker Compose)  
**Services Managed**: API (port 8000), Frontend (port 3000)  
**Health Check**: http://localhost:8000/health (API)

## Quick Reference

### Start All Services
```bash
cd hello-multiapp-infra
docker-compose up --build
```

### Stop All Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
```

### Check Status
```bash
docker-compose ps
```

### Restart Service
```bash
docker-compose restart api      # API only
docker-compose restart frontend # Frontend only
docker-compose restart          # All services
```

## Prerequisites

### Software Requirements

**Required:**
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

**Check Versions:**
```bash
docker --version
docker-compose --version
git --version
```

### Repository Structure

**Required Layout:**
```
hello-multiapp/                  # Parent directory (any name)
├── hello-multiapp-api/          # Must be named exactly this
├── hello-multiapp-frontend/     # Must be named exactly this
└── hello-multiapp-infra/        # Must be named exactly this (current dir)
```

**Validate Structure:**
```bash
cd hello-multiapp-infra
ls ../hello-multiapp-api/Dockerfile       # Should exist
ls ../hello-multiapp-frontend/Dockerfile  # Should exist
```

### Port Availability

**Required Ports:**
- 3000 - Frontend
- 8000 - API

**Check Port Usage:**
```bash
# Linux/macOS
lsof -i :3000
lsof -i :8000

# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

If ports are in use, stop the conflicting services before proceeding.

## Initial Setup

### First-Time Deployment

**Step 1: Clone All Repositories**
```bash
# Create parent directory
mkdir hello-multiapp
cd hello-multiapp

# Clone all three repositories side-by-side
git clone <api-repo-url> hello-multiapp-api
git clone <frontend-repo-url> hello-multiapp-frontend
git clone <infra-repo-url> hello-multiapp-infra
```

**Step 2: Verify Structure**
```bash
ls -la
# Should show three directories:
# hello-multiapp-api/
# hello-multiapp-frontend/
# hello-multiapp-infra/
```

**Step 3: Start Services**
```bash
cd hello-multiapp-infra
docker-compose up --build
```

**Step 4: Verify Deployment**
```bash
# In another terminal
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"hello-multiapp-api"}

# Open in browser
open http://localhost:3000
# Expected: Frontend UI with API status
```

### Configuration Options

**Environment Variables (optional):**

Create `.env` file in hello-multiapp-infra directory:
```bash
# API Configuration
API_PORT=8000
API_ENVIRONMENT=docker

# Frontend Configuration
FRONTEND_PORT=3000
API_URL=http://api:8000
```

**Custom Port Mapping:**

Edit `docker-compose.yml` ports section:
```yaml
api:
  ports:
    - "8080:8000"  # Map to different host port

frontend:
  ports:
    - "8080:80"    # Map to different host port
```

## Operations

### Starting Services

**Development Mode (attached logs):**
```bash
docker-compose up
```
- Logs stream to terminal
- Ctrl+C stops services
- Good for: Active development, debugging

**Production Mode (detached):**
```bash
docker-compose up -d
```
- Runs in background
- No log output to terminal
- Good for: Long-running deployments

**Rebuild and Start:**
```bash
docker-compose up --build
```
- Rebuilds images before starting
- Use when: Code changes in API or frontend

**Force Recreate:**
```bash
docker-compose up --force-recreate
```
- Recreates containers even if config unchanged
- Use when: Troubleshooting container issues

### Stopping Services

**Graceful Stop:**
```bash
docker-compose stop
```
- Stops containers but preserves them
- Can restart quickly with `docker-compose start`

**Stop and Remove:**
```bash
docker-compose down
```
- Stops and removes containers
- Removes networks
- Preserves images (fast restart)

**Full Cleanup:**
```bash
docker-compose down --rmi all --volumes
```
- Stops and removes containers
- Removes images
- Removes volumes (if any)
- Use when: Complete cleanup needed

### Restarting Services

**Restart All:**
```bash
docker-compose restart
```

**Restart Specific Service:**
```bash
docker-compose restart api
docker-compose restart frontend
```

**Restart with Rebuild:**
```bash
docker-compose up --build --force-recreate
```

### Updating Services

**Update API:**
```bash
# 1. Pull latest API code
cd ../hello-multiapp-api
git pull

# 2. Rebuild and restart
cd ../hello-multiapp-infra
docker-compose up --build -d api
```

**Update Frontend:**
```bash
# 1. Pull latest frontend code
cd ../hello-multiapp-frontend
git pull

# 2. Rebuild and restart
cd ../hello-multiapp-infra
docker-compose up --build -d frontend
```

**Update All:**
```bash
# 1. Pull all repositories
cd ../hello-multiapp-api && git pull
cd ../hello-multiapp-frontend && git pull
cd ../hello-multiapp-infra && git pull

# 2. Rebuild and restart
docker-compose up --build -d
```

## Monitoring

### Service Health

**Check Service Status:**
```bash
docker-compose ps
```

Expected output:
```
NAME                  STATUS              PORTS
hello-multiapp-api    Up (healthy)        0.0.0.0:8000->8000/tcp
hello-multiapp-frontend  Up              0.0.0.0:3000->80/tcp
```

**Check API Health:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "hello-multiapp-api"
}
```

**Check Frontend:**
```bash
curl -I http://localhost:3000
```

Expected: `HTTP/1.1 200 OK`

### Resource Usage

**Monitor Resource Consumption:**
```bash
docker stats
```

Shows real-time:
- CPU usage
- Memory usage
- Network I/O
- Block I/O

**Per-Service Stats:**
```bash
docker stats hello-multiapp-api
docker stats hello-multiapp-frontend
```

### Logging

**View All Logs:**
```bash
docker-compose logs
```

**Follow Logs (live tail):**
```bash
docker-compose logs -f
```

**Service-Specific Logs:**
```bash
docker-compose logs api
docker-compose logs frontend
```

**Last N Lines:**
```bash
docker-compose logs --tail=100 api
```

**Logs with Timestamps:**
```bash
docker-compose logs -t
```

**Search Logs:**
```bash
docker-compose logs | grep ERROR
docker-compose logs api | grep "Health check"
```

### Network Inspection

**List Networks:**
```bash
docker network ls | grep multiapp
```

**Inspect Network:**
```bash
docker network inspect hello-multiapp-infra_multiapp-network
```

Shows:
- Connected containers
- IP addresses
- Network configuration

**Test Inter-Service Communication:**
```bash
# From within frontend container
docker exec -it hello-multiapp-frontend sh
wget -O- http://api:8000/health
```

## Troubleshooting

### Services Won't Start

**Symptom:** `docker-compose up` fails immediately

**Diagnosis:**
```bash
# Check for errors
docker-compose up

# Validate docker-compose.yml syntax
docker-compose config
```

**Common Causes:**

1. **Missing Repositories**
   ```bash
   # Check if API and frontend repos exist
   ls ../hello-multiapp-api
   ls ../hello-multiapp-frontend
   ```
   Fix: Clone missing repositories

2. **Port Conflicts**
   ```bash
   # Find process using port
   lsof -i :8000
   lsof -i :3000
   ```
   Fix: Stop conflicting process or change ports

3. **Docker Not Running**
   ```bash
   docker ps
   ```
   Fix: Start Docker Desktop or Docker daemon

### Build Failures

**Symptom:** Image build fails during `docker-compose up --build`

**Diagnosis:**
```bash
# Build specific service
docker-compose build api
docker-compose build frontend

# Check build logs
docker-compose build --no-cache api
```

**Common Causes:**

1. **API Build Fails**
   - Check: `../hello-multiapp-api/requirements.txt` exists
   - Check: `../hello-multiapp-api/Dockerfile` is valid
   - Fix: Repair API repository, check API documentation

2. **Frontend Build Fails**
   - Check: `../hello-multiapp-frontend/index.html` exists
   - Check: `../hello-multiapp-frontend/Dockerfile` is valid
   - Fix: Repair frontend repository, check frontend documentation

3. **Network Issues During Build**
   - Symptom: "Failed to download packages"
   - Fix: Check internet connection, retry with `--no-cache`

### Health Check Failures

**Symptom:** API shows as "unhealthy" in `docker-compose ps`

**Diagnosis:**
```bash
# Check API logs
docker-compose logs api

# Manually test health endpoint
docker exec -it hello-multiapp-api curl http://localhost:8000/health

# Check if API is running
docker exec -it hello-multiapp-api ps aux
```

**Common Causes:**

1. **API Not Starting**
   - Check logs: `docker-compose logs api`
   - Look for: Python errors, port binding issues

2. **Health Endpoint Not Responding**
   - Verify API implementation has `/health` endpoint
   - Check API is listening on correct port

3. **curl Not Available in Container**
   - Check Dockerfile installs curl
   - Alternative: Change health check to use Python script

**Temporary Fix:**
```bash
# Restart API
docker-compose restart api

# Rebuild API from scratch
docker-compose up --build --force-recreate api
```

### Frontend Can't Reach API

**Symptom:** Frontend shows "API connection failed"

**Diagnosis:**
```bash
# Check if API is running
docker-compose ps api

# Check API health
curl http://localhost:8000/health

# Check network connectivity
docker exec -it hello-multiapp-frontend wget -O- http://api:8000/health
```

**Common Causes:**

1. **API Not Running**
   - Fix: Start API with `docker-compose up api`

2. **Wrong API_URL**
   - Check: `docker-compose.yml` has `API_URL=http://api:8000`
   - Should use service name `api`, not `localhost`

3. **Network Not Connected**
   - Check: Both services on same network
   ```bash
   docker network inspect hello-multiapp-infra_multiapp-network
   ```

4. **CORS Issues**
   - Check: API logs for CORS errors
   - Verify: API has CORS middleware configured
   - See: `../hello-multiapp-api/specs/architecture.md`

### Port Access Issues

**Symptom:** Can't access services from host browser

**Diagnosis:**
```bash
# Check port mappings
docker-compose ps

# Check if ports are bound
netstat -an | grep 8000
netstat -an | grep 3000

# Test from host
curl http://localhost:8000/health
curl http://localhost:3000
```

**Common Causes:**

1. **Firewall Blocking Ports**
   - Check firewall rules
   - Allow ports 3000 and 8000

2. **Wrong Port in Browser**
   - Use: `http://localhost:3000` (not `http://localhost:80`)
   - Use: `http://localhost:8000` (not `http://localhost:8000/api`)

3. **Docker Network Mode Issues**
   - Verify using bridge network (default)
   - Check `docker-compose.yml` network configuration

### Performance Issues

**Symptom:** Slow response times, high resource usage

**Diagnosis:**
```bash
# Check resource usage
docker stats

# Check logs for errors
docker-compose logs | grep -i error
docker-compose logs | grep -i timeout
```

**Common Causes:**

1. **Insufficient Resources**
   - Check: Docker Desktop resource limits
   - Increase: Docker Desktop > Settings > Resources
   - Recommended: 4 GB RAM, 2 CPUs minimum

2. **Container Thrashing**
   - Restart services: `docker-compose restart`
   - Rebuild: `docker-compose up --build`

3. **Log Volume**
   - Check: `docker inspect <container> | grep LogPath`
   - Clear: `docker-compose down && docker-compose up -d`

### Clean Slate Recovery

**When all else fails:**

```bash
# 1. Stop everything
docker-compose down

# 2. Remove all project containers
docker-compose down --rmi all

# 3. Clean Docker system (careful!)
docker system prune -a

# 4. Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d

# 5. Verify
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:3000
```

## Multi-Repo Coordination

### Synchronized Updates

**Scenario:** API endpoint changed, frontend needs update

**Procedure:**
1. Update API repository
2. Update frontend repository to match
3. Test locally before deploying:
   ```bash
   cd hello-multiapp-infra
   docker-compose up --build
   # Test in browser
   ```
4. Deploy both together:
   ```bash
   docker-compose down
   docker-compose up --build -d
   ```

### Version Management

**Current Approach:**
- Uses latest code from each repository
- No explicit version pinning
- Suitable for: Development, testing

**Production Approach:**
1. Tag releases in each repository:
   ```bash
   cd hello-multiapp-api
   git tag v1.2.3
   git push --tags
   
   cd ../hello-multiapp-frontend
   git tag v2.0.1
   git push --tags
   ```

2. Check out specific versions:
   ```bash
   cd hello-multiapp-api
   git checkout v1.2.3
   
   cd ../hello-multiapp-frontend
   git checkout v2.0.1
   ```

3. Deploy:
   ```bash
   cd ../hello-multiapp-infra
   docker-compose up --build -d
   ```

### Rollback Procedures

**Rollback Single Service:**
```bash
# 1. Check out previous version
cd ../hello-multiapp-api
git log --oneline  # Find previous commit
git checkout <previous-commit>

# 2. Rebuild and deploy
cd ../hello-multiapp-infra
docker-compose up --build -d api
```

**Rollback All Services:**
```bash
# 1. Check out previous versions in all repos
cd ../hello-multiapp-api
git checkout <previous-commit>

cd ../hello-multiapp-frontend
git checkout <previous-commit>

# 2. Rebuild and deploy
cd ../hello-multiapp-infra
docker-compose up --build -d
```

**Emergency Rollback (use old images):**
```bash
# 1. Stop services
docker-compose down

# 2. List old images
docker images | grep hello-multiapp

# 3. Tag old image as latest
docker tag hello-multiapp-api:<old-tag> hello-multiapp-api:latest

# 4. Restart
docker-compose up -d
```

## Production Considerations

### Pre-Production Checklist

- [ ] All three repositories at stable versions (tagged)
- [ ] Health checks passing
- [ ] End-to-end testing completed
- [ ] Documentation updated
- [ ] Monitoring configured
- [ ] Backup plan in place
- [ ] Rollback procedure tested

### Production Hardening

**Security:**
1. Use HTTPS (add reverse proxy with TLS)
2. Restrict CORS origins in API
3. Use Docker secrets for sensitive config
4. Run containers as non-root users
5. Enable read-only root filesystem

**Reliability:**
1. Add restart policies:
   ```yaml
   restart: always
   ```
2. Configure resource limits:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 512M
   ```
3. Implement proper logging driver
4. Add monitoring and alerting

**For Production Scale:**
- Migrate to Kubernetes or managed container service
- Implement load balancing
- Add auto-scaling
- Configure persistent logging
- Set up metrics collection
- Implement distributed tracing

### Monitoring Integration

**Prometheus (example):**
```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  networks:
    - multiapp-network
```

**Grafana (example):**
```yaml
# Add to docker-compose.yml
grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
  networks:
    - multiapp-network
```

## Emergency Contacts

- **Service Owner**: Platform Team
- **On-Call**: [Monitoring/alerting system]
- **Documentation**: 
  - Infrastructure: `specs/` in this repository
  - API: `../hello-multiapp-api/specs/`
  - Frontend: `../hello-multiapp-frontend/specs/`
- **Related Services**: API, Frontend

## Maintenance Windows

### Routine Maintenance

**Weekly:**
- Review logs for errors
- Check resource usage trends
- Update dependencies if needed

**Monthly:**
- Update Docker images to latest
- Review and optimize configurations
- Update documentation

**Quarterly:**
- Security audit
- Performance review
- Disaster recovery test

### Planned Downtime

**Procedure:**
1. Notify users (if applicable)
2. Backup current state (if applicable)
3. Schedule maintenance window
4. Stop services: `docker-compose down`
5. Perform maintenance
6. Test in isolated environment
7. Deploy: `docker-compose up -d`
8. Verify all services healthy
9. Monitor for issues
