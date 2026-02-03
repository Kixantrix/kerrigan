# Self-Hosted Runner Operations Guide

This guide provides operational procedures for managing the self-hosted GitHub Actions runner with persistent Copilot CLI authentication.

## Overview

The self-hosted runner enables the SDK Agent service to execute with persistent Copilot CLI authentication, supporting fully autonomous agent workflows.

## Quick Reference

### Status Checks

```bash
# Check runner service
sudo systemctl status actions.runner.*

# Check GitHub CLI auth
gh auth status

# Check Copilot CLI
gh copilot suggest "test"

# Run full health check
bash ~/scripts/health-check.sh

# Check auth refresh logs
cat /var/log/kerrigan-runner-auth.log
```

### Common Operations

```bash
# Start runner
sudo systemctl start actions.runner.*

# Stop runner
sudo systemctl stop actions.runner.*

# Restart runner
sudo systemctl restart actions.runner.*

# View runner logs
journalctl -u actions.runner.* -f

# Re-authenticate GitHub CLI
gh auth login

# Refresh auth
bash ~/scripts/refresh-auth.sh
```

## Daily Operations

### Morning Checklist

1. **Check runner status**
   ```bash
   sudo systemctl status actions.runner.*
   ```
   - Should show "active (running)"
   - If not, investigate logs and restart

2. **Review health check logs**
   ```bash
   tail -20 /var/log/kerrigan-runner-health.log
   ```
   - Look for any failures or warnings
   - Address any auth issues immediately

3. **Check recent workflow runs**
   - Visit: https://github.com/Kixantrix/kerrigan/actions
   - Look for failed SDK Agent Service runs
   - Investigate failures

4. **Verify disk space**
   ```bash
   df -h /
   ```
   - Should have at least 20% free
   - Clean up if needed

### End of Day Checklist

1. **Review metrics**
   - Count of workflow runs today
   - Success/failure rate
   - Average execution time

2. **Check for alerts**
   - Email alerts for auth failures
   - System monitoring alerts
   - GitHub notifications

3. **Verify backups**
   ```bash
   ls -lh /opt/kerrigan-runner/auth-backup/
   ```
   - Should see recent backup directories
   - Latest backup should be from today

## Weekly Operations

### Weekly Maintenance (Every Monday)

1. **Review last week's metrics**
   ```bash
   # Get workflow run stats
   gh run list --workflow="SDK Agent Service" --limit 100 --json conclusion,createdAt
   ```

2. **Check system updates**
   ```bash
   sudo apt-get update
   sudo apt-get list --upgradable
   ```

3. **Clean up disk space**
   ```bash
   # Clean workflow artifacts
   cd ~/actions-runner/_work
   du -sh */
   # Remove old work directories if needed
   
   # Clean package caches
   sudo apt-get clean
   sudo apt-get autoremove
   ```

4. **Review and rotate logs**
   ```bash
   # Check log sizes
   du -sh /var/log/*.log
   
   # Rotate old logs (older than 7 days)
   sudo journalctl --vacuum-time=7d
   ```

5. **Test runner functionality**
   - Create a test issue with label `agent:go` and `sdk-test`
   - Verify workflow runs successfully
   - Check that Copilot CLI works

## Monthly Operations

### Monthly Maintenance (First Monday of Month)

1. **Update system packages**
   ```bash
   sudo apt-get update
   sudo apt-get upgrade -y
   ```

2. **Update GitHub CLI**
   ```bash
   sudo apt-get install --only-upgrade gh
   gh --version
   ```

3. **Update Copilot CLI extension**
   ```bash
   gh extension upgrade github/gh-copilot
   gh copilot --version
   ```

4. **Update Actions runner**
   ```bash
   cd ~/actions-runner
   
   # Check current version
   ./config.sh --version
   
   # Check for updates
   LATEST_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r .tag_name | sed 's/v//')
   echo "Latest version: $LATEST_VERSION"
   
   # Download and install if newer version available
   # See: https://github.com/actions/runner/releases
   ```

5. **Review security**
   - Check for security updates
   - Review auth logs for suspicious activity
   - Verify firewall rules
   - Review access logs

6. **Backup validation**
   - Test restoring from backup
   - Verify backup integrity
   - Update backup procedures if needed

## Authentication Management

### Checking Auth Status

```bash
# GitHub CLI status
gh auth status

# Test Copilot CLI
gh copilot suggest "create hello world file"

# Run auth health check
bash ~/scripts/refresh-auth.sh
```

### Re-authenticating

**When needed:**
- Health check reports auth failure
- Workflows fail with authentication errors
- After token expiration (typically 30-90 days)

**Procedure:**

1. SSH into runner host
   ```bash
   ssh user@runner-host
   ```

2. Stop runner temporarily (optional but recommended)
   ```bash
   sudo systemctl stop actions.runner.*
   ```

3. Re-authenticate GitHub CLI
   ```bash
   gh auth login
   ```
   - Select: GitHub.com
   - Authentication method: Login with a web browser
   - Complete OAuth flow in browser
   - Select scopes: All (repo, workflow, admin:org)

4. Verify authentication
   ```bash
   gh auth status
   ```

5. Test Copilot CLI
   ```bash
   gh copilot suggest "test command"
   ```

6. Restart runner
   ```bash
   sudo systemctl start actions.runner.*
   ```

7. Verify with test workflow
   - Create test issue with `agent:go` label
   - Verify workflow runs successfully

### Auth Token Expiration

**Symptoms:**
- Workflows fail with "authentication required" errors
- `gh auth status` shows expired token
- Health check reports auth failure

**Prevention:**
- Monitor auth age via health checks
- Set calendar reminder for 60 days after auth
- Enable email alerts for auth failures

**Recovery:**
Follow re-authentication procedure above.

## Troubleshooting

### Runner Not Starting Workflows

**Symptoms:**
- Issues labeled but no workflow runs
- Runner shows as offline in GitHub

**Diagnosis:**
```bash
# Check runner service
sudo systemctl status actions.runner.*

# Check runner logs
journalctl -u actions.runner.* -n 100

# Check network connectivity
curl -v https://api.github.com
```

**Solutions:**
1. Restart runner service
   ```bash
   sudo systemctl restart actions.runner.*
   ```

2. If still offline, check runner registration
   ```bash
   cd ~/actions-runner
   cat .runner
   ```

3. Re-register if needed
   ```bash
   # Get new token from GitHub Settings
   ./config.sh remove
   ./config.sh --url https://github.com/Kixantrix/kerrigan --token NEW_TOKEN --name kerrigan-runner
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```

### Authentication Failures

**Symptoms:**
- Workflows fail immediately after checkout
- Error messages about authentication
- Copilot CLI commands fail

**Diagnosis:**
```bash
# Check GitHub CLI auth
gh auth status

# Check Copilot CLI
gh copilot explain "test"

# Check auth cache
ls -la ~/.config/gh/
ls -la ~/.copilot/
```

**Solutions:**
1. Refresh auth
   ```bash
   gh auth refresh
   ```

2. If refresh fails, re-authenticate
   ```bash
   gh auth login
   ```

3. Verify Copilot subscription
   - Check GitHub account has active Copilot subscription
   - Verify at: https://github.com/settings/copilot

### Disk Space Issues

**Symptoms:**
- Runner fails to start workflows
- Health check reports low disk space
- Workflows fail with "No space left on device"

**Diagnosis:**
```bash
# Check disk usage
df -h

# Find large directories
du -sh /* | sort -h

# Check workflow artifacts
du -sh ~/actions-runner/_work/*
```

**Solutions:**
1. Clean workflow artifacts
   ```bash
   cd ~/actions-runner/_work
   rm -rf */
   ```

2. Clean package caches
   ```bash
   sudo apt-get clean
   sudo apt-get autoremove
   ```

3. Clean old logs
   ```bash
   sudo journalctl --vacuum-time=7d
   ```

4. If still low, increase disk size
   - Stop runner
   - Expand volume/disk in cloud console
   - Resize filesystem: `sudo resize2fs /dev/xvda1`
   - Restart runner

### Performance Issues

**Symptoms:**
- Workflows run slowly
- High CPU or memory usage
- System becomes unresponsive

**Diagnosis:**
```bash
# Check resource usage
top
htop  # if installed

# Check load average
uptime

# Check memory
free -h

# Check running workflows
cd ~/actions-runner/_work
ps aux | grep node
```

**Solutions:**
1. Check for runaway processes
   ```bash
   ps aux --sort=-%cpu | head -10
   ps aux --sort=-%mem | head -10
   ```

2. Kill stuck workflows if needed
   ```bash
   # Find workflow process
   ps aux | grep "npm start"
   
   # Kill specific process (replace PID)
   kill PID
   ```

3. Increase VM resources if consistently overloaded
   - Stop runner
   - Resize VM in cloud console
   - Start runner

### Network Connectivity Issues

**Symptoms:**
- Workflows fail to checkout repository
- Cannot reach GitHub API
- Timeout errors

**Diagnosis:**
```bash
# Test GitHub connectivity
curl -v https://api.github.com

# Test GitHub Actions
curl -v https://pipelines.actions.githubusercontent.com

# Check DNS resolution
nslookup github.com

# Check routes
traceroute github.com
```

**Solutions:**
1. Check firewall rules
   - Ensure outbound HTTPS (443) is allowed
   - Verify no proxy configuration issues

2. Restart networking
   ```bash
   sudo systemctl restart networking
   ```

3. Check with cloud provider for network issues

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Runner Availability**
   - Uptime: Should be > 99%
   - Status: Online/Offline
   - Alert: If offline for > 5 minutes

2. **Authentication Status**
   - GitHub CLI: Authenticated
   - Copilot CLI: Working
   - Alert: On auth failure

3. **Workflow Success Rate**
   - Target: > 95% success rate
   - Alert: If < 90% for 24 hours

4. **Resource Usage**
   - Disk: < 80% full
   - Memory: < 80% used
   - CPU: < 70% average
   - Alert: If exceeded for > 1 hour

5. **System Health**
   - Health check: Passing
   - Last auth refresh: < 24 hours ago
   - Last backup: < 24 hours ago

### Setting Up Alerts

**Email Alerts:**
```bash
# Configure in refresh-auth.sh
export ALERT_EMAIL="ops@example.com"
```

**Slack Alerts:**
```bash
# Configure in refresh-auth.sh
export ALERT_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**GitHub Issues:**
- Consider creating issues automatically for repeated failures
- Use GitHub CLI to create issues from scripts

### Monitoring Dashboard

Consider setting up a monitoring dashboard with:
- Runner status (online/offline)
- Recent workflow runs (success/failure)
- System resources (CPU, memory, disk)
- Auth status (valid/expired)
- Alerts history

**Tools:**
- Grafana + Prometheus
- Datadog
- New Relic
- CloudWatch (AWS)
- Azure Monitor

## Disaster Recovery

### Backup Procedures

**What to backup:**
- Auth cache (`~/.config/gh`, `~/.copilot`)
- Runner configuration (`~/actions-runner/.runner`)
- Custom scripts and configuration
- Logs (for forensics)

**Backup schedule:**
- Daily: Auth cache (automatic via cron)
- Weekly: Full system backup
- Monthly: Backup verification

**Backup locations:**
- Local: `/opt/kerrigan-runner/auth-backup`
- Remote: S3, Azure Blob, or similar
- Offsite: Separate region/availability zone

### Recovery Procedures

**Scenario 1: Runner host failure**

1. Provision new host (see setup guide)
2. Install dependencies
3. Restore auth cache from backup
4. Register runner
5. Verify functionality

**Scenario 2: Auth corruption**

1. Stop runner
2. Remove corrupted auth cache
3. Restore from latest backup
4. Verify auth status
5. Start runner

**Scenario 3: Complete data loss**

1. Provision new host
2. Install all dependencies
3. Manual re-authentication (no backup available)
4. Register runner
5. Document lessons learned

### Recovery Time Objectives

- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 24 hours (daily backups)

## Security Best Practices

1. **Keep system updated**
   - Apply security patches promptly
   - Update GitHub CLI and Copilot CLI regularly

2. **Restrict access**
   - Limit SSH access to authorized users
   - Use SSH keys, not passwords
   - Implement IP allowlist if possible

3. **Protect credentials**
   - Never commit auth cache to git
   - Use encrypted volumes for sensitive data
   - Rotate tokens regularly

4. **Monitor access**
   - Review auth logs regularly
   - Monitor for unusual activity
   - Set up intrusion detection

5. **Audit regularly**
   - Review who has access
   - Check runner permissions
   - Verify security configurations

## Cost Optimization

### Current Costs

- Cloud VM: ~$24-40/month (varies by provider)
- GitHub Copilot: $10-39/user/month
- Bandwidth: Typically included
- Storage: Minimal (~$2-5/month for backups)

### Optimization Strategies

1. **Use smaller instance when possible**
   - Monitor actual resource usage
   - Downsize if consistently underutilized

2. **Use spot/preemptible instances**
   - For non-critical workloads
   - Can save 60-90% on compute costs

3. **Schedule runner downtime**
   - Stop runner during off-hours if workflows are predictable
   - Save ~50% on compute costs

4. **Optimize storage**
   - Clean up artifacts regularly
   - Use lifecycle policies for backups
   - Compress logs before archiving

## Support and Escalation

### Support Levels

**Level 1: Self-service**
- Check health check logs
- Review troubleshooting guide
- Run diagnostic scripts

**Level 2: Team support**
- Post in team chat
- Create internal ticket
- Review with team member

**Level 3: External support**
- GitHub Support (for runner issues)
- Cloud provider support (for infrastructure)
- Community forums

### Escalation Criteria

**Escalate immediately if:**
- Runner offline for > 1 hour
- Auth failures affecting production workflows
- Security incident detected
- Data loss or corruption
- System completely unresponsive

**Escalate within 24 hours if:**
- Persistent auth issues
- Performance degradation > 50%
- Disk space critical
- Repeated health check failures

## Change Management

### Making Changes

**Always:**
1. Test in non-production environment first
2. Create backup before changes
3. Document changes
4. Have rollback plan
5. Schedule during maintenance window

**For major changes:**
- Get approval from team
- Notify stakeholders
- Schedule announcement
- Prepare rollback procedure
- Monitor closely after change

### Change Log

Maintain a change log for the runner:
- Date of change
- What was changed
- Why it was changed
- Who made the change
- Rollback procedure if needed

## Related Documentation

- [Self-Hosted Runner Setup](./self-hosted-runner-setup.md) - Initial setup
- [SDK Agent Setup](./sdk-agent-setup.md) - SDK Agent configuration
- [Health Check Script](../scripts/runner/health-check.sh) - Health monitoring
- [Auth Refresh Script](../scripts/runner/refresh-auth.sh) - Auth management

## Appendix

### Useful Commands Reference

```bash
# Runner service management
sudo systemctl start actions.runner.*
sudo systemctl stop actions.runner.*
sudo systemctl restart actions.runner.*
sudo systemctl status actions.runner.*

# View logs
journalctl -u actions.runner.* -f
journalctl -u actions.runner.* -n 100
journalctl -u actions.runner.* --since "1 hour ago"

# GitHub CLI
gh auth status
gh auth login
gh auth refresh
gh extension list
gh extension upgrade --all

# Copilot CLI
gh copilot suggest "command"
gh copilot explain "command"

# System diagnostics
df -h                    # Disk usage
free -h                  # Memory usage
top                      # Process monitor
htop                     # Interactive process monitor
uptime                   # System uptime and load
nproc                    # CPU count
lsblk                    # Block devices

# Network diagnostics
curl -v https://api.github.com
ping github.com
traceroute github.com
nslookup github.com

# Runner diagnostics
cd ~/actions-runner
./config.sh --version
cat .runner
ps aux | grep Runner

# Health checks
bash ~/scripts/health-check.sh
bash ~/scripts/refresh-auth.sh

# Cleanup
sudo apt-get clean
sudo apt-get autoremove
sudo journalctl --vacuum-time=7d
cd ~/actions-runner/_work && rm -rf */
```

### Contact Information

- Repository: https://github.com/Kixantrix/kerrigan
- Issues: Create issue with label `self-hosted-runner`
- Documentation: `/docs/self-hosted-runner-*.md`

---

**Last Updated**: 2026-01-29  
**Version**: 1.0
