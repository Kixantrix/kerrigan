# Runbook: Hello Multi-App API

## Service Overview

**Service**: hello-multiapp-api  
**Type**: REST API (FastAPI)  
**Port**: 8000  
**Health Check**: http://localhost:8000/health

## Quick Reference

### Status Check
```bash
curl http://localhost:8000/health
```

### View Logs
```bash
# Docker Compose
docker-compose logs api

# Docker
docker logs <container-id>
```

### Restart Service
```bash
# Docker Compose (from infra repo)
docker-compose restart api

# Docker
docker restart <container-id>
```

## Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

1. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run locally**:
   ```bash
   python main.py
   ```
   Service available at: http://localhost:8000

3. **Test endpoints**:
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Version info
   curl http://localhost:8000/version
   
   # Service info
   curl http://localhost:8000/
   
   # API docs (automatic)
   open http://localhost:8000/docs
   ```

### Configuration

Environment variables:
```bash
export PORT=8000
export ENVIRONMENT=development
export LOG_LEVEL=INFO
```

## Docker Deployment

### Build Image

```bash
docker build -t hello-multiapp-api .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e ENVIRONMENT=docker \
  hello-multiapp-api
```

### Health Check

Docker includes automatic health checking:
```bash
docker inspect --format='{{.State.Health.Status}}' <container-id>
```

## Multi-Repo Deployment

### Using Infrastructure Repository

This is the **recommended deployment method** as it coordinates all services.

**Prerequisites:**
- hello-multiapp-api (this repo)
- hello-multiapp-frontend
- hello-multiapp-infra

**Steps:**

1. **Clone all repositories** side by side:
   ```bash
   mkdir hello-multiapp
   cd hello-multiapp
   git clone <api-repo> hello-multiapp-api
   git clone <frontend-repo> hello-multiapp-frontend
   git clone <infra-repo> hello-multiapp-infra
   ```

2. **Deploy via infrastructure**:
   ```bash
   cd hello-multiapp-infra
   docker-compose up --build
   ```

3. **Verify deployment**:
   ```bash
   # API health
   curl http://localhost:8000/health
   
   # Frontend (will call API)
   open http://localhost:3000
   ```

### Startup Order

The infrastructure repository ensures proper startup:
1. API container starts first
2. Health check validates API ready
3. Frontend container starts (depends on API)
4. System fully operational

## Monitoring

### Health Checks

**Endpoint**: `GET /health`

**Expected Response**:
```json
{
  "status": "ok",
  "service": "hello-multiapp-api"
}
```

**Failure Conditions**:
- HTTP 500: Internal server error
- Timeout: Service not responding
- Connection refused: Service not running

### Version Information

**Endpoint**: `GET /version`

**Expected Response**:
```json
{
  "version": "1.0.0",
  "service": "hello-multiapp-api",
  "environment": "docker"
}
```

### Logs

**Log Location**: stdout (captured by Docker)

**Log Format**: `TIMESTAMP - LOGGER - LEVEL - MESSAGE`

**Key Log Messages**:
- `Starting Hello Multi-App API on port 8000` - Service starting
- `Health check requested` - Health endpoint called
- `Version requested` - Version endpoint called

## Troubleshooting

### Service Won't Start

**Symptom**: Container exits immediately

**Checks**:
1. Verify Python dependencies installed:
   ```bash
   docker-compose logs api | grep "error"
   ```

2. Check port availability:
   ```bash
   lsof -i :8000  # Should be empty before starting
   ```

3. Verify environment variables:
   ```bash
   docker-compose config | grep environment -A 5
   ```

### Health Check Failing

**Symptom**: Docker reports unhealthy status

**Checks**:
1. Test health endpoint manually:
   ```bash
   docker exec <container-id> curl -f http://localhost:8000/health
   ```

2. Check application logs:
   ```bash
   docker-compose logs api
   ```

3. Verify service is listening:
   ```bash
   docker exec <container-id> netstat -tlnp | grep 8000
   ```

### CORS Issues (Frontend Can't Connect)

**Symptom**: Frontend shows connection errors despite API running

**Checks**:
1. Verify CORS configuration in main.py
2. Check browser console for CORS errors
3. Test API directly:
   ```bash
   curl -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" \
        -X OPTIONS http://localhost:8000/health -v
   ```

4. Ensure frontend using correct API URL

### Performance Issues

**Symptom**: Slow response times

**Checks**:
1. Check resource usage:
   ```bash
   docker stats <container-id>
   ```

2. Review logs for errors:
   ```bash
   docker-compose logs api | grep -i error
   ```

3. Test endpoint performance:
   ```bash
   time curl http://localhost:8000/health
   ```

## Rollback Procedures

### Rollback Container

```bash
# Stop current version
docker-compose down

# Pull previous version
docker pull hello-multiapp-api:<previous-tag>

# Update docker-compose.yml with previous tag
# Restart
docker-compose up -d
```

### Rollback Code

```bash
git checkout <previous-commit>
docker-compose up --build
```

## Cross-Repository Coordination

### With hello-multiapp-frontend

**Integration Point**: API endpoints

**Coordination**:
- Frontend depends on API being healthy
- API must enable CORS for frontend origin
- Version endpoint allows compatibility checking

**Handoff**:
1. API deployed and health check passing
2. Frontend configured with API URL
3. Test frontend → API communication

### With hello-multiapp-infra

**Integration Point**: Docker Compose orchestration

**Coordination**:
- Infra defines container configuration
- Infra manages networking between services
- Infra coordinates startup order

**Handoff**:
1. API Dockerfile maintained in this repo
2. Infra references Dockerfile in docker-compose
3. Changes to API require rebuilding via infra

## Emergency Contacts

- **Service Owner**: Platform Team
- **On-Call**: [Monitoring alert system]
- **Documentation**: `specs/` folder in this repository
- **Related Services**: hello-multiapp-frontend, hello-multiapp-infra
