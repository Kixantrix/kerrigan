# Self-Hosted Runner Setup for SDK Agent Service

This guide details the setup and configuration of a self-hosted GitHub Actions runner with persistent Copilot CLI authentication for the SDK Agent service.

## Overview

The SDK Agent service requires a self-hosted runner because:
- **Persistent Authentication**: Copilot CLI auth must persist between workflow runs
- **Long-Running Support**: Agent processes may require extended execution time
- **State Management**: Auth cache and session state need persistent storage
- **Resource Control**: Better control over compute resources and costs

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Self-Hosted Runner (VM or Container)           │
│  ┌─────────────────────────────────────────┐    │
│  │  Copilot CLI (installed, authenticated) │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │  GitHub Actions Runner Service          │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │  SDK Agent Service (Node.js)            │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │  Auth Cache (~/.copilot/credentials)    │    │
│  │  Persistent Storage (Volume Mount)       │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

## Prerequisites

### Required Resources

- **Compute**: 
  - Minimum: 2 vCPU, 4 GB RAM
  - Recommended: 4 vCPU, 8 GB RAM
  - Storage: 50 GB minimum (persistent)

- **Operating System**:
  - Ubuntu 22.04 LTS (recommended)
  - Ubuntu 20.04 LTS (supported)
  - Debian 11 (supported)

- **Network**:
  - Outbound HTTPS (443) access to:
    - github.com
    - api.github.com
    - *.actions.githubusercontent.com
    - copilot.github.com

### Required Accounts

- **GitHub User with Copilot License**:
  - GitHub Copilot Individual ($10/month) or
  - GitHub Copilot Business (organization-managed)
  - Must have access to the repository

- **GitHub Repository**:
  - Admin access to Kixantrix/kerrigan
  - Ability to register self-hosted runners

## Infrastructure Options

### Option A: Cloud VM (Recommended for Production)

**Providers:**
- AWS EC2 (t3.medium or larger)
- Azure Virtual Machine (B2s or larger)
- Google Cloud Compute Engine (e2-medium or larger)
- DigitalOcean Droplet (4GB or larger)

**Advantages:**
- Full control over environment
- Easy to backup and restore
- Predictable performance
- Simple networking

**Setup Steps:**
1. Provision VM with Ubuntu 22.04
2. Configure persistent storage volumes
3. Set up automatic backups
4. Configure firewall rules (allow outbound HTTPS)

### Option B: Container (Advanced)

**Platforms:**
- Docker on dedicated host
- Azure Container Instances
- AWS ECS
- Google Cloud Run (with persistent storage)

**Advantages:**
- Easier to version and replicate
- Better resource isolation
- Simpler dependency management

**Considerations:**
- Requires volume mounts for persistent storage
- More complex networking setup
- May need container orchestration

### Option C: Dedicated Server

**Setup:**
- Physical or dedicated virtual server
- On-premises or co-located
- Direct control over hardware

**Advantages:**
- Maximum control
- No cloud costs
- Potential for better performance

**Considerations:**
- Requires physical infrastructure
- More complex maintenance
- Network configuration complexity

## Installation Steps

### Step 1: Provision Infrastructure

#### For Cloud VM (AWS EC2 Example):

```bash
# Create EC2 instance (using AWS CLI)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-keypair \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=kerrigan-sdk-runner}]'

# Connect to instance
ssh -i your-keypair.pem ubuntu@<instance-ip>
```

#### For Docker Container:

```dockerfile
# See infrastructure/runner/Dockerfile for complete configuration
FROM ubuntu:22.04

# Install dependencies, configure runner, etc.
# (Full Dockerfile provided in infrastructure directory)
```

### Step 2: Install Dependencies

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
  curl \
  git \
  jq \
  build-essential \
  libssl-dev \
  python3 \
  python3-pip

# Install Node.js 20.x (required for SDK Agent)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installations
node --version  # Should be v20.x
npm --version
git --version
```

### Step 3: Install GitHub CLI

```bash
# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
  sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
  sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt-get update
sudo apt-get install -y gh

# Verify installation
gh --version
```

### Step 4: Install Copilot CLI Extension

```bash
# Install Copilot CLI extension
gh extension install github/gh-copilot

# Verify installation
gh copilot --version
```

### Step 5: Authenticate Copilot CLI

**Important**: This step requires a user with an active Copilot subscription.

```bash
# Authenticate GitHub CLI
gh auth login
# Follow interactive prompts:
# - Select: GitHub.com
# - Authentication method: Login with a web browser
# - Complete OAuth flow in browser

# Verify authentication
gh auth status

# The Copilot CLI should now be authenticated
# Test it:
gh copilot suggest "list files"
```

**Auth Cache Location:**
```
~/.config/gh/
├── hosts.yml          # GitHub authentication
└── config.yml         # CLI configuration

~/.copilot/
├── credentials        # OAuth tokens (DO NOT commit!)
├── config            # CLI configuration
└── sessions/         # Active session state
```

### Step 6: Configure Persistent Storage

**Create backup of auth cache:**

```bash
# Create backup directory
mkdir -p /opt/kerrigan-runner/auth-backup

# Create backup script
sudo tee /opt/kerrigan-runner/backup-auth.sh > /dev/null << 'EOF'
#!/bin/bash
# Backup Copilot authentication
BACKUP_DIR="/opt/kerrigan-runner/auth-backup"
timestamp=$(date +%Y%m%d-%H%M%S)

# Backup gh config
cp -r ~/.config/gh "$BACKUP_DIR/gh-$timestamp"

# Backup copilot config
cp -r ~/.copilot "$BACKUP_DIR/copilot-$timestamp"

# Keep only last 7 backups
ls -t "$BACKUP_DIR" | tail -n +8 | xargs -I {} rm -rf "$BACKUP_DIR/{}"

echo "Auth backup completed: $timestamp"
EOF

sudo chmod +x /opt/kerrigan-runner/backup-auth.sh

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/kerrigan-runner/backup-auth.sh") | crontab -
```

**For Docker/Container environments:**

Mount persistent volumes:
```yaml
volumes:
  - runner-auth-cache:/home/runner/.config/gh
  - runner-copilot-cache:/home/runner/.copilot
```

### Step 7: Install GitHub Actions Runner

```bash
# Create runner directory
mkdir -p ~/actions-runner
cd ~/actions-runner

# Download latest runner package
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r .tag_name | sed 's/v//')
curl -o actions-runner-linux-x64.tar.gz -L \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"

# Extract package
tar xzf actions-runner-linux-x64.tar.gz

# Get registration token from GitHub
# Go to: https://github.com/Kixantrix/kerrigan/settings/actions/runners/new
# Or use GitHub API with a PAT that has admin:org scope

# Configure runner
./config.sh --url https://github.com/Kixantrix/kerrigan \
  --token YOUR_REGISTRATION_TOKEN \
  --name "kerrigan-sdk-runner" \
  --labels "self-hosted,copilot-enabled,sdk-agent" \
  --work _work \
  --replace

# Install as a service (recommended)
sudo ./svc.sh install
sudo ./svc.sh start

# Verify runner is connected
sudo ./svc.sh status
```

**Runner Labels:**
- `self-hosted`: Indicates self-hosted runner
- `copilot-enabled`: Indicates Copilot CLI is available
- `sdk-agent`: Specific label for SDK agent workflows

### Step 8: Configure Health Checks

See `scripts/runner/health-check.sh` for the health check script.

Install health check as a cron job:

```bash
# Copy health check script
sudo cp scripts/runner/health-check.sh /opt/kerrigan-runner/
sudo chmod +x /opt/kerrigan-runner/health-check.sh

# Schedule health checks every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/kerrigan-runner/health-check.sh") | crontab -

# View logs
tail -f /var/log/kerrigan-runner-health.log
```

### Step 9: Configure Auth Refresh

See `scripts/runner/refresh-auth.sh` for the auth refresh script.

**Note**: This script can detect expired tokens but cannot automatically re-authenticate (requires human interaction for OAuth flow).

```bash
# Copy auth refresh script
sudo cp scripts/runner/refresh-auth.sh /opt/kerrigan-runner/
sudo chmod +x /opt/kerrigan-runner/refresh-auth.sh

# Schedule auth checks every hour
(crontab -l 2>/dev/null; echo "0 * * * * /opt/kerrigan-runner/refresh-auth.sh") | crontab -
```

### Step 10: Test the Setup

```bash
# Test GitHub Actions runner
cd ~/actions-runner
./run.sh  # Run interactively to see logs

# In another terminal, verify Copilot CLI
gh copilot suggest "create a hello world file"

# Check health status
/opt/kerrigan-runner/health-check.sh

# View logs
cat /var/log/kerrigan-runner-health.log
```

## Monitoring and Maintenance

### Health Monitoring

**Key metrics to monitor:**
- Runner service status (should be running)
- Copilot CLI authentication status
- Available disk space (min 20% free)
- System resources (CPU, memory)
- Network connectivity

**Alerting:**
Set up alerts for:
- Runner service stops
- Auth expiration detected
- Disk space < 20%
- Failed health checks (3+ consecutive)

### Authentication Management

**Auth token lifetime:**
- GitHub CLI tokens: ~30-90 days (varies)
- Copilot CLI tokens: Tied to GitHub token

**Manual re-authentication required when:**
- Health check reports auth failure
- Workflows fail with auth errors
- After token expiration

**Re-authentication procedure:**
1. SSH into runner host
2. Run: `gh auth refresh`
3. Complete OAuth flow in browser
4. Verify: `gh auth status`
5. Test: `gh copilot suggest "test"`

### Regular Maintenance

**Daily:**
- Review health check logs
- Monitor runner status on GitHub

**Weekly:**
- Review workflow success rates
- Check disk space and clean up if needed
- Review system logs

**Monthly:**
- Update system packages: `sudo apt-get update && sudo apt-get upgrade`
- Update GitHub CLI: `sudo apt-get install --only-upgrade gh`
- Update Actions runner: Download and install latest version
- Rotate auth backups (automatic via cron)

### Backup and Recovery

**Backup strategy:**
- Daily automatic auth cache backups (via cron)
- Manual backups before major changes
- Store backups in separate location/volume

**Recovery procedure:**
1. Provision new runner host (or restore VM from snapshot)
2. Install dependencies (Steps 2-4)
3. Restore auth cache:
   ```bash
   cp -r /opt/kerrigan-runner/auth-backup/gh-TIMESTAMP ~/.config/gh
   cp -r /opt/kerrigan-runner/auth-backup/copilot-TIMESTAMP ~/.copilot
   ```
4. Verify auth: `gh auth status`
5. Install and configure Actions runner (Step 7)
6. Verify health checks

## Security Considerations

### Secrets Management

**Never commit or expose:**
- GitHub auth tokens
- Copilot CLI credentials
- Runner registration tokens
- Private keys

**Secure storage:**
- Auth cache stored in user home directory (restricted permissions)
- Backups stored with restricted permissions (600)
- Use encrypted volumes for sensitive data

### Access Control

**Principle of least privilege:**
- Runner user has minimal system permissions
- Runner can only access assigned repositories
- Copilot CLI uses user's permissions (not elevated)

**Network security:**
- Restrict inbound traffic (only SSH for management)
- Allow outbound HTTPS to required GitHub domains
- Use VPC/private networks if available
- Enable firewall rules

### Audit Logging

**Logs maintained:**
- GitHub Actions workflow logs (90-day retention)
- Runner service logs
- Health check logs
- Auth refresh logs
- System audit logs

**Review regularly:**
- Check logs for unauthorized access attempts
- Monitor for unusual activity patterns
- Track workflow execution history

## Troubleshooting

### Runner Not Connecting

**Symptoms:**
- Runner shows as offline in GitHub Settings
- Workflows queue but don't start

**Solutions:**
1. Check runner service: `sudo ./svc.sh status`
2. View runner logs: `journalctl -u actions.runner.*`
3. Verify network connectivity: `curl https://api.github.com`
4. Check registration token hasn't expired
5. Re-register runner if needed

### Authentication Failures

**Symptoms:**
- Copilot CLI commands fail
- Workflows fail with "not authenticated" errors
- Health checks report auth failure

**Solutions:**
1. Check auth status: `gh auth status`
2. Check token expiration: `gh auth refresh --help`
3. Re-authenticate: `gh auth login`
4. Verify Copilot subscription is active
5. Test CLI: `gh copilot suggest "test"`

### Disk Space Issues

**Symptoms:**
- Runner fails to start workflows
- Build artifacts fill disk
- Health checks report low disk space

**Solutions:**
1. Check disk usage: `df -h`
2. Clean workflow artifacts: `cd ~/actions-runner/_work && rm -rf */`
3. Clean package caches: `sudo apt-get clean`
4. Review and clean logs: `sudo journalctl --vacuum-time=7d`
5. Increase disk size if needed

### Performance Issues

**Symptoms:**
- Workflows run slowly
- High CPU or memory usage
- System becomes unresponsive

**Solutions:**
1. Check resource usage: `top` or `htop`
2. Review running processes
3. Check for memory leaks in long-running processes
4. Increase VM resources if needed
5. Review workflow job concurrency settings

## Cost Estimation

### Infrastructure Costs (Monthly)

**AWS EC2 (t3.medium, us-east-1):**
- Compute: ~$30/month (on-demand)
- Storage: ~$5/month (50 GB GP3)
- Data transfer: ~$5/month (estimated)
- **Total: ~$40/month**

**Azure VM (B2s, East US):**
- Compute: ~$30/month
- Storage: ~$5/month (50 GB SSD)
- **Total: ~$35/month**

**DigitalOcean (4 GB Droplet):**
- Compute + Storage: $24/month
- Bandwidth: Included (1 TB)
- **Total: ~$24/month**

### Additional Costs

- **GitHub Copilot License**: $10-39/user/month
- **Backup storage**: ~$2-5/month (optional)
- **Monitoring tools**: $0-20/month (optional)

### Cost Optimization

- Use spot/preemptible instances for non-critical workloads
- Schedule runner to stop during off-hours (if workload permits)
- Use smaller instance sizes for light workloads
- Leverage free tier offerings (AWS free tier, Azure credits, etc.)

## Integration with Workflows

### Updated Workflow Configuration

The `sdk-agent-service.yml` workflow has been updated to support both GitHub-hosted and self-hosted runners:

```yaml
runs-on: ${{ matrix.runner }}
strategy:
  matrix:
    runner: [ubuntu-latest, self-hosted]
```

To use only the self-hosted runner:

```yaml
runs-on: self-hosted
```

To require specific labels:

```yaml
runs-on: [self-hosted, copilot-enabled, sdk-agent]
```

### Health Check Integration

Workflows include a health check step that verifies:
- Copilot CLI is available
- Authentication is valid
- Required dependencies are installed

## Related Documentation

- [SDK Agent Setup Guide](./sdk-agent-setup.md) - SDK Agent service setup
- [SDK Agent Operations](./sdk-agent-operations.md) - Operational procedures
- [Research Findings](../specs/projects/copilot-sdk-integration/research-findings.md) - Technical research

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review health check logs: `/var/log/kerrigan-runner-health.log`
3. Review runner logs: `journalctl -u actions.runner.*`
4. Create issue with label `self-hosted-runner`

## Changelog

- **2026-01-29**: Initial documentation created
