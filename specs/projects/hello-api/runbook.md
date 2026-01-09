# Runbook: Hello API

This runbook describes how to deploy, operate, debug, and maintain the Hello API service.

## Prerequisites

- Docker installed (for containerized deployment)
- Python 3.11+ (for local development)
- Network access to target deployment environment

## Deployment

### Local Development

1. **Install dependencies**:
   ```bash
   cd examples/hello-api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the service**:
   ```bash
   python app.py
   ```

3. **Verify it's running**:
   ```bash
   curl http://localhost:5000/health
   # Expected: {"status": "ok"}
   ```

### Docker Deployment

1. **Build the image**:
   ```bash
   cd examples/hello-api
   docker build -t hello-api:latest .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name hello-api \
     -p 5000:5000 \
     -e PORT=5000 \
     hello-api:latest
   ```

3. **Verify it's running**:
   ```bash
   curl http://localhost:5000/health
   # Expected: {"status": "ok"}
   ```

### Production Deployment (Example: Docker Compose)

Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  api:
    image: hello-api:latest
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

Deploy:
```bash
docker-compose up -d
```

## Configuration

The service is configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Port the service listens on |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENVIRONMENT` | development | Environment name (development, production) |

Example with custom configuration:
```bash
export PORT=8080
export LOG_LEVEL=DEBUG
python app.py
```

## Operation

### Health Checks

Monitor service health via the `/health` endpoint:
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{"status": "ok"}
```

### Logs

The service logs to stdout. View logs:

**Local development**:
```bash
# Logs appear in terminal where app.py is running
```

**Docker**:
```bash
docker logs hello-api
docker logs -f hello-api  # Follow logs
```

**Docker Compose**:
```bash
docker-compose logs api
docker-compose logs -f api  # Follow logs
```

Log format:
```
[2024-01-09 10:30:45] INFO: GET /health -> 200
[2024-01-09 10:30:50] INFO: GET /greet?name=Alice -> 200
[2024-01-09 10:30:52] ERROR: POST /echo -> 400 (Invalid JSON)
```

### Graceful Shutdown

**Local development**:
- Press `Ctrl+C` to stop the service

**Docker**:
```bash
docker stop hello-api  # Sends SIGTERM, waits 10s, then SIGKILL
```

**Docker Compose**:
```bash
docker-compose down
```

## Debugging

### Common Issues

#### Service won't start
**Symptom**: Error message "Address already in use"
**Cause**: Another process is using port 5000
**Solution**:
```bash
# Find the process using the port
lsof -i :5000  # On Linux/Mac
netstat -ano | findstr :5000  # On Windows

# Either kill that process or use a different port
export PORT=8080
python app.py
```

#### Health check fails
**Symptom**: `curl http://localhost:5000/health` returns connection refused
**Cause**: Service is not running or running on different port
**Solution**:
```bash
# Check if service is running
ps aux | grep python  # Local
docker ps | grep hello-api  # Docker

# Check logs for startup errors
docker logs hello-api
```

#### 400 errors on /greet
**Symptom**: `{"error": "Name parameter is required"}`
**Cause**: Missing or empty `name` query parameter
**Solution**: Include name in the request
```bash
curl "http://localhost:5000/greet?name=Alice"
```

#### 400 errors on /echo
**Symptom**: `{"error": "Invalid JSON body"}`
**Cause**: Malformed JSON or missing Content-Type header
**Solution**: Send valid JSON with correct header
```bash
curl -X POST http://localhost:5000/echo \
  -H "Content-Type: application/json" \
  -d '{"test": "value"}'
```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python app.py
```

This will show detailed request/response information.

### Performance Issues

**Symptom**: Slow response times
**Investigation**:
1. Check system resources: `docker stats hello-api`
2. Review logs for errors or timeouts
3. Test with single request: `time curl http://localhost:5000/health`

**Note**: This is a simple example service. For production high-performance needs, use gunicorn with multiple workers:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

## Monitoring

### Key Metrics to Monitor

1. **Availability**: `/health` endpoint returns 200
2. **Response time**: < 100ms for all endpoints
3. **Error rate**: < 1% of requests should return 5xx errors
4. **Container health**: Container should be running and healthy

### Alerting Recommendations

- Alert if `/health` returns non-200 for > 2 minutes
- Alert if container restarts more than 3 times in 10 minutes
- Alert if error rate exceeds 5%

## Rollback

If a deployment causes issues:

### Docker
```bash
# Stop the problematic container
docker stop hello-api

# Remove it
docker rm hello-api

# Run the previous version
docker run -d --name hello-api -p 5000:5000 hello-api:v1.0.0
```

### Docker Compose
```bash
# Stop the current deployment
docker-compose down

# Update docker-compose.yml to use previous version
# Change: image: hello-api:latest
#     to: image: hello-api:v1.0.0

# Deploy previous version
docker-compose up -d
```

## Incident Response

### Service Down
1. Check if container/process is running
2. Check logs for errors
3. Restart service
4. If restart fails, rollback to previous version
5. Investigate root cause after service is restored

### High Error Rate
1. Check logs for error patterns
2. Verify configuration is correct
3. Test endpoints manually to reproduce issue
4. If isolated to specific endpoint, consider disabling it temporarily
5. Fix issue and redeploy

### No Resources Available

This simple service has no external dependencies or critical resources. Issues are typically:
- Port conflicts (solved by changing PORT)
- Memory exhaustion (unlikely with this simple service)
- Container orchestration issues (check Docker/k8s logs)

## Maintenance

### Updating Dependencies

1. Review `requirements.txt` for outdated packages
2. Update versions carefully, testing after each change
3. Run security scans: `pip install safety && safety check`
4. Update Docker base image to latest Python 3.11 patch

### Backups

This service is stateless - no backups needed. Configuration is in code.

### Scheduled Tasks

No scheduled tasks for this service.

## Oncall / Incident Basics

**Severity**: Low (example/demo service, not critical)

**Escalation**: N/A (example project)

**Response Time SLA**: N/A (example project)

**Key Contacts**: Development team

For a production service, this section would include:
- On-call rotation details
- Escalation contacts and procedures
- Service Level Objectives (SLOs)
- Incident communication protocols
- Postmortem process
