# Hello Multi-App Infrastructure

Infrastructure and deployment configurations for the hello-multiapp project.

## Overview

This repository contains:
- Docker Compose configuration for local development
- Container orchestration setup for the multi-app system
- Deployment scripts and configurations

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Access to hello-multiapp-api and hello-multiapp-frontend repositories

### Local Development

1. **Clone all three repositories** side by side:
   ```bash
   mkdir hello-multiapp
   cd hello-multiapp
   git clone <api-repo-url> hello-multiapp-api
   git clone <frontend-repo-url> hello-multiapp-frontend
   git clone <infra-repo-url> hello-multiapp-infra
   ```

2. **Start all services**:
   ```bash
   cd hello-multiapp-infra
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Stopping Services

```bash
docker-compose down
```

## Architecture

The infrastructure orchestrates two services:

- **API Service** (Port 8000)
  - Built from `../hello-multiapp-api`
  - FastAPI application
  - Provides REST endpoints

- **Frontend Service** (Port 3000)
  - Built from `../hello-multiapp-frontend`
  - Static HTML/JS served by Nginx
  - Connects to API service

Both services communicate over a Docker bridge network.

## Configuration

### Environment Variables

**API Service:**
- `PORT`: API listening port (default: 8000)
- `ENVIRONMENT`: Environment name (docker, production, etc.)

**Frontend Service:**
- `API_URL`: API service URL (default: http://api:8000)

### Ports

- `3000`: Frontend (HTTP)
- `8000`: API (HTTP)

## Health Checks

The API service includes a health check that verifies the service is responsive:
- Endpoint: `/health`
- Interval: 10 seconds
- Timeout: 5 seconds
- Retries: 3

## Deployment

For production deployment:

1. Build images with appropriate tags
2. Push to container registry
3. Deploy using your orchestration platform (Kubernetes, ECS, etc.)
4. Configure appropriate environment variables and secrets
5. Set up ingress/load balancing

See `specs/runbook.md` for detailed deployment procedures.

## Multi-Repo Coordination

This infrastructure repository coordinates with:

- **hello-multiapp-api**: Source for API container
- **hello-multiapp-frontend**: Source for frontend container

Changes to either application repository require rebuilding the corresponding container.

## Troubleshooting

### Services won't start
- Ensure ports 3000 and 8000 are not in use
- Check that all three repos are cloned side by side
- Verify Docker is running

### API connection fails
- Check API health: `curl http://localhost:8000/health`
- View API logs: `docker-compose logs api`
- Verify network configuration

### Frontend can't reach API
- Check API_URL environment variable
- Verify both containers are on the same network
- Check frontend logs: `docker-compose logs frontend`

## Documentation

Complete project documentation:
- Specification: `specs/spec.md`
- Architecture: `specs/architecture.md`
- Runbook: `specs/runbook.md`
- Tasks: `specs/tasks.md`
- Cost Plan: `specs/cost-plan.md`
