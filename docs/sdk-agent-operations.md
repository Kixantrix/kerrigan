# SDK Agent Service - Operations Guide

## Overview

This guide provides operational procedures for the SDK Agent Service, including monitoring, troubleshooting, and maintenance tasks.

## Daily Operations

### Morning Checklist

1. **Check workflow status**
   ```bash
   gh run list --workflow="SDK Agent Service" --limit 20
   ```
   
2. **Review failed runs**
   ```bash
   gh run list --workflow="SDK Agent Service" --status=failure --limit 10
   ```

3. **Check recent issue activity**
   - Review issues with `agent:go` label
   - Verify issue comments were posted
   - Confirm PRs were created

### Monitoring Metrics

Track these key metrics daily:

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Workflow success rate | > 95% | < 90% |
| Average execution time | < 5 minutes | > 10 minutes |
| Issue-to-PR time | < 5 minutes | > 15 minutes |
| Error rate | < 5% | > 10% |

## Incident Response

### Workflow Failures

**Severity: High**

1. **Identify the issue**
   ```bash
   gh run view <run-id> --log
   ```

2. **Common causes**:
   - Authentication failure (expired/invalid secrets)
   - SDK timeout (Copilot API issues)
   - GitHub API rate limiting
   - Network connectivity issues

3. **Immediate actions**:
   - Check GitHub status: https://www.githubstatus.com/
   - Verify secrets are not expired
   - Review error logs
   - Post comment to affected issue

4. **Resolution steps**:
   - For auth errors: Rotate secrets (see Maintenance section)
   - For timeouts: Increase `SDK_TIMEOUT_MS`
   - For rate limits: Add retry logic or wait
   - For network: Retry workflow

### Multiple Consecutive Failures

**Severity: Critical**

1. **Disable workflow temporarily**
   ```bash
   # Comment out workflow triggers in .github/workflows/sdk-agent-service.yml
   # Or disable via GitHub UI: Settings → Actions → Disable workflow
   ```

2. **Investigate root cause**
   - Check recent code changes
   - Review system logs
   - Test in staging environment

3. **Communication**
   - Post status update to repository discussions
   - Notify team in Slack/Teams
   - Update incident log

4. **Recovery**
   - Fix root cause
   - Test in isolation
   - Enable workflow gradually
   - Monitor closely for 24 hours

### Issue Not Processed

**Severity: Medium**

**Symptoms**: Issue labeled with `agent:go` but no workflow run

**Diagnosis**:
1. Check workflow is enabled: Actions → SDK Agent Service
2. Verify issue has required labels
3. Check workflow triggers in yaml file

**Resolution**:
1. Ensure workflow file exists and is valid
2. Remove and re-add `agent:go` label
3. Check Actions permissions: Settings → Actions → General

## Maintenance Tasks

### Weekly Maintenance

1. **Review logs**
   - Check for patterns in failures
   - Identify slow operations
   - Look for warnings

2. **Update dependencies**
   ```bash
   cd services/sdk-agent
   npm outdated
   npm update
   npm audit
   ```

3. **Analyze metrics**
   - Success/failure rate trend
   - Average execution time trend
   - Cost analysis (if applicable)

### Monthly Maintenance

1. **Rotate GitHub App secrets** (if policy requires)
   ```bash
   # 1. Generate new private key in GitHub App settings
   # 2. Update SDK_AGENT_PRIVATE_KEY secret
   # 3. Test with sample issue
   # 4. Revoke old key
   ```

2. **Review and update documentation**
   - Update runbooks with lessons learned
   - Document new error patterns
   - Update troubleshooting guides

3. **Capacity planning**
   - Review usage trends
   - Forecast future needs
   - Plan for scaling if needed

### Quarterly Maintenance

1. **Security audit**
   - Review GitHub App permissions
   - Audit secret access logs
   - Check for unauthorized access attempts
   - Review dependency vulnerabilities

2. **Performance review**
   - Analyze execution time trends
   - Identify optimization opportunities
   - Review cost efficiency

3. **Disaster recovery test**
   - Verify backup procedures
   - Test recovery from secret loss
   - Validate rollback procedures

## Troubleshooting Playbook

### Authentication Errors

**Error**: `GitHub App credentials are invalid`

**Steps**:
1. Verify `SDK_AGENT_APP_ID` matches GitHub App
2. Check `SDK_AGENT_PRIVATE_KEY` format (includes BEGIN/END lines)
3. Confirm GitHub App is installed on repository
4. Test authentication locally:
   ```bash
   cd services/sdk-agent
   npm run dev -- \
     --event-type "test" \
     --issue-number 1 \
     --repository "owner/repo"
   ```

### SDK Timeout

**Error**: `SDK execution timed out`

**Steps**:
1. Check Copilot API status
2. Increase timeout in workflow:
   ```yaml
   env:
     SDK_TIMEOUT_MS: 600000  # Increase to 10 minutes
   ```
3. Review issue complexity (large codebase?)
4. Consider breaking into smaller tasks

### PR Creation Failed

**Error**: `Failed to create PR`

**Steps**:
1. Check for existing PR with same branch name
2. Verify write permissions on repository
3. Check for branch protection rules
4. Review merge conflicts on base branch
5. Test manually:
   ```bash
   git checkout -b test-branch
   gh pr create --title "Test" --body "Test PR"
   ```

### Rate Limiting

**Error**: `API rate limit exceeded`

**Steps**:
1. Check current rate limit status:
   ```bash
   gh api rate_limit
   ```
2. If using installation token, limits should be high (5000/hour)
3. Consider:
   - Adding retry with exponential backoff
   - Caching responses where possible
   - Batching operations

## Emergency Procedures

### Total Service Outage

1. **Immediate actions** (first 5 minutes):
   - Disable SDK Agent Service workflow
   - Post status update to repository
   - Notify team
   - Start incident log

2. **Assessment** (next 15 minutes):
   - Identify scope (all issues or specific types?)
   - Determine root cause
   - Estimate time to resolution
   - Decide: fix forward or rollback?

3. **Resolution** (variable):
   - Apply fix
   - Test thoroughly
   - Enable gradually
   - Monitor continuously

4. **Post-incident** (within 24 hours):
   - Complete incident report
   - Update runbooks
   - Schedule post-mortem
   - Implement preventive measures

### Secret Compromise

1. **Immediate actions**:
   - Revoke compromised secrets immediately
   - Generate new GitHub App private key
   - Update repository secrets
   - Audit recent activity for unauthorized access

2. **Investigation**:
   - Review access logs
   - Identify scope of compromise
   - Document timeline
   - Report to security team

3. **Recovery**:
   - Rotate all related secrets
   - Review and tighten permissions
   - Update security policies
   - Monitor for suspicious activity

## Escalation Procedures

### Level 1: Standard Issues
- **Handler**: On-call engineer
- **Response time**: Within 4 hours
- **Examples**: Single workflow failure, minor errors

### Level 2: Service Degradation
- **Handler**: Senior engineer
- **Response time**: Within 1 hour
- **Examples**: Multiple failures, authentication issues

### Level 3: Service Outage
- **Handler**: Engineering manager + team
- **Response time**: Immediate
- **Examples**: Complete service failure, security incident

## Metrics and Reporting

### Daily Report Template

```markdown
## SDK Agent Service - Daily Report
**Date**: YYYY-MM-DD

### Summary
- Workflows run: X
- Success rate: Y%
- Average execution time: Z minutes

### Issues
- Failed runs: N
- Most common error: [error type]

### Actions Taken
- [Action 1]
- [Action 2]

### Open Items
- [ ] Item 1
- [ ] Item 2
```

### Weekly Report Template

```markdown
## SDK Agent Service - Weekly Report
**Week of**: YYYY-MM-DD

### Metrics
- Total workflows: X
- Success rate: Y% (target: >95%)
- Average time: Z min (target: <5 min)
- Cost: $X (target: <$50/mo)

### Incidents
- Critical: N
- High: N
- Medium: N

### Improvements
- [Improvement 1]
- [Improvement 2]

### Next Week
- [ ] Action 1
- [ ] Action 2
```

## Useful Commands

### View recent runs
```bash
gh run list --workflow="SDK Agent Service" --limit 20
```

### View specific run logs
```bash
gh run view <run-id> --log
```

### Rerun failed workflow
```bash
gh run rerun <run-id>
```

### List issues with agent:go label
```bash
gh issue list --label "agent:go" --state open
```

### Check GitHub Actions status
```bash
curl https://www.githubstatus.com/api/v2/status.json
```

### View repository secrets (names only)
```bash
gh secret list
```

### Update a secret
```bash
gh secret set SDK_AGENT_APP_ID --body "123456"
```

## Contacts

- **Primary**: [Team email/Slack]
- **Secondary**: [Backup contact]
- **Escalation**: [Manager/Lead]
- **Security**: [Security team contact]

## Related Documentation

- [SDK Architecture Proposal](sdk-architecture-proposal.md)
- [Setup Guide](sdk-agent-setup.md)
- [Service README](../services/sdk-agent/README.md)
- [Kerrigan Architecture](architecture.md)

## Version History

- **2026-01-25**: Initial operations guide created
- **TBD**: Update after PR #127 SDK integration

---

**Last Updated**: 2026-01-25
**Maintained By**: Kerrigan DevOps Team
