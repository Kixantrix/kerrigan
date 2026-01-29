# Self-Hosted Runner Infrastructure

This directory contains infrastructure configuration for deploying a self-hosted GitHub Actions runner with persistent Copilot CLI authentication.

## Contents

- **Dockerfile** - Container image definition for the runner
- **docker-compose.yml** - Docker Compose configuration for easy deployment
- **entrypoint.sh** - Container entrypoint script

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- GitHub runner registration token
- (Optional) GitHub CLI authenticated for Copilot

### Deploy with Docker Compose

1. **Get a runner registration token:**
   ```bash
   # Via GitHub UI:
   # Go to: https://github.com/Kixantrix/kerrigan/settings/actions/runners/new
   
   # Or via GitHub CLI:
   gh api repos/Kixantrix/kerrigan/actions/runners/registration-token --jq .token
   ```

2. **Set environment variables:**
   ```bash
   export RUNNER_TOKEN="your-registration-token"
   export RUNNER_NAME="kerrigan-runner"
   ```

3. **Start the runner:**
   ```bash
   cd infrastructure/runner
   docker-compose up -d
   ```

4. **Authenticate Copilot CLI (one-time setup):**
   ```bash
   # Enter the running container
   docker exec -it kerrigan-runner /bin/bash
   
   # Authenticate GitHub CLI
   gh auth login
   # Follow the OAuth flow in your browser
   
   # Verify authentication
   gh auth status
   gh copilot suggest "test"
   
   # Exit container
   exit
   ```

5. **Verify runner is connected:**
   - Visit: https://github.com/Kixantrix/kerrigan/settings/actions/runners
   - You should see "kerrigan-runner" with status "Idle"

### Deploy with Docker

```bash
# Build image
docker build -t kerrigan-runner -f infrastructure/runner/Dockerfile .

# Run container
docker run -d \
  --name kerrigan-runner \
  -e RUNNER_TOKEN="your-token" \
  -e RUNNER_NAME="kerrigan-runner" \
  -v runner-gh-auth:/home/runner/.config/gh \
  -v runner-copilot-auth:/home/runner/.copilot \
  kerrigan-runner
```

## Configuration

### Environment Variables

#### Required

- `RUNNER_TOKEN` - GitHub Actions runner registration token (get from GitHub Settings)

#### Optional

- `RUNNER_NAME` - Name for the runner (default: `kerrigan-runner`)
- `RUNNER_LABELS` - Additional labels, comma-separated (default: `self-hosted,copilot-enabled,sdk-agent`)
- `RUNNER_GROUP` - Runner group name (optional)
- `GITHUB_REPOSITORY` - Repository URL (default: `https://github.com/Kixantrix/kerrigan`)

### Volumes

The following volumes should be mounted for persistent data:

- `/home/runner/.config/gh` - GitHub CLI authentication
- `/home/runner/.copilot` - Copilot CLI authentication and cache
- `/home/runner/actions-runner/_work` - Workflow working directory
- `/home/runner/logs` - Application logs

### Resource Limits

Recommended resource limits:

```yaml
resources:
  limits:
    cpus: '4'
    memory: 8G
  reservations:
    cpus: '2'
    memory: 4G
```

Adjust based on your workload.

## Persistent Authentication

The container uses Docker volumes to persist authentication between restarts:

1. **Initial authentication** (one-time):
   - Enter container: `docker exec -it kerrigan-runner /bin/bash`
   - Run: `gh auth login`
   - Complete OAuth flow
   - Exit container

2. **Authentication persists** across:
   - Container restarts
   - Container recreation (as long as volumes are preserved)
   - Host reboots (if volumes are on persistent storage)

3. **Re-authentication needed** when:
   - Token expires (typically 30-90 days)
   - Volumes are deleted
   - Auth cache is corrupted

## Monitoring

### Health Checks

```bash
# Docker health check
docker ps

# Manual health check
docker exec kerrigan-runner bash /home/runner/scripts/health-check.sh

# View logs
docker logs kerrigan-runner
docker logs -f kerrigan-runner  # Follow logs
```

### Check Runner Status

```bash
# Check if runner process is running
docker exec kerrigan-runner pgrep -f "Runner.Listener"

# Check GitHub CLI auth
docker exec kerrigan-runner gh auth status

# Check Copilot CLI
docker exec kerrigan-runner gh copilot suggest "test"
```

## Troubleshooting

### Runner Not Connecting

**Problem**: Container starts but runner doesn't show in GitHub

**Solutions**:
1. Check logs: `docker logs kerrigan-runner`
2. Verify token: Make sure `RUNNER_TOKEN` is valid (tokens expire)
3. Check network: Ensure container can reach GitHub (https://github.com)

### Authentication Failed

**Problem**: Copilot CLI commands fail with auth errors

**Solutions**:
1. Check auth status: `docker exec kerrigan-runner gh auth status`
2. Re-authenticate: Enter container and run `gh auth login`
3. Verify Copilot subscription is active

### Container Keeps Restarting

**Problem**: Container restarts continuously

**Solutions**:
1. Check logs: `docker logs kerrigan-runner`
2. Verify runner isn't already registered (remove old registration first)
3. Check for resource limits (may need more memory/CPU)

## Maintenance

### Update Runner

```bash
# Pull latest image
docker-compose pull

# Recreate container (preserves volumes)
docker-compose up -d

# Or manually:
docker stop kerrigan-runner
docker rm kerrigan-runner
docker build -t kerrigan-runner -f infrastructure/runner/Dockerfile .
docker-compose up -d
```

### Update Dependencies

Rebuild the image with latest dependencies:

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Backup Authentication

```bash
# Create backup of authentication volumes
docker run --rm \
  -v runner-gh-auth:/source/gh \
  -v runner-copilot-auth:/source/copilot \
  -v $(pwd)/backup:/backup \
  ubuntu \
  tar czf /backup/runner-auth-$(date +%Y%m%d).tar.gz -C /source .

# Restore from backup
docker run --rm \
  -v runner-gh-auth:/target/gh \
  -v runner-copilot-auth:/target/copilot \
  -v $(pwd)/backup:/backup \
  ubuntu \
  tar xzf /backup/runner-auth-YYYYMMDD.tar.gz -C /target
```

### Clean Up

```bash
# Stop and remove container
docker-compose down

# Remove all data (WARNING: loses authentication!)
docker-compose down -v

# Remove images
docker rmi kerrigan-runner
```

## Security Considerations

1. **Protect tokens**: Never commit `RUNNER_TOKEN` to git
2. **Secure volumes**: Authentication volumes contain sensitive data
3. **Network isolation**: Use Docker networks to isolate runner
4. **Regular updates**: Keep base image and dependencies updated
5. **Monitor access**: Review runner logs regularly

## Production Deployment

For production use:

1. **Use secrets management**:
   - Store `RUNNER_TOKEN` in secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
   - Inject at runtime

2. **Set up monitoring**:
   - Container health checks
   - Log aggregation (ELK, Splunk, CloudWatch)
   - Alerting on failures

3. **Implement backup strategy**:
   - Regular automated backups of auth volumes
   - Test restore procedures
   - Off-site backup storage

4. **Use orchestration**:
   - Deploy with Kubernetes, ECS, or similar
   - Auto-restart on failure
   - Rolling updates

5. **Harden security**:
   - Run container as non-root (already configured)
   - Use read-only filesystem where possible
   - Implement network policies
   - Regular security scans

## Related Documentation

- [Self-Hosted Runner Setup Guide](../../docs/self-hosted-runner-setup.md) - Detailed setup for VM deployment
- [Self-Hosted Runner Operations](../../docs/self-hosted-runner-operations.md) - Operational procedures
- [SDK Agent Setup](../../docs/sdk-agent-setup.md) - SDK Agent service configuration

## Support

For issues or questions:
1. Check logs: `docker logs kerrigan-runner`
2. Review troubleshooting section above
3. Create issue with label `self-hosted-runner`

---

**Last Updated**: 2026-01-29  
**Version**: 1.0
