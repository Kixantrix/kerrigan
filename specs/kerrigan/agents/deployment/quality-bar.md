# Quality Bar: Deployment Agent

## Definition of Done

Operational readiness documentation is "done" when:
- [ ] runbook.md exists with all required sections: Deployment, Operations, Monitoring, Troubleshooting, Rollback
- [ ] cost-plan.md exists for projects using paid resources with: Estimated Costs, Cost Tracking, Guardrails, Optimization Opportunities
- [ ] All procedures are actionable (specific commands and tools, not abstractions)
- [ ] Deployment procedures include prerequisites, expected duration, and verification steps for each environment
- [ ] Operations procedures cover start/stop/restart, health checks, log viewing, scaling, and maintenance tasks
- [ ] Monitoring section defines key metrics with thresholds, dashboard links, and escalation procedures
- [ ] Troubleshooting section includes common issues with symptoms, causes, and solutions
- [ ] Rollback procedures are documented with verification steps
- [ ] Secret management strategy documented with tools, rotation procedures, and examples
- [ ] CI/CD pipeline includes or documents: build, test, security scan, deploy, smoke test automation
- [ ] Cost estimates include ranges, assumptions, and component breakdown
- [ ] Cost guardrails include spending limits, auto-scaling constraints, and budget alerts
- [ ] Documentation links to relevant artifacts (architecture.md, plan.md)
- [ ] status.json was checked before starting work
- [ ] All examples use realistic values (not just placeholders)

## Structural Standards

### Runbook Structure Requirements

**Required Sections** (in order):
1. **Deployment**
   - Procedures for each environment (dev, staging, prod)
   - Prerequisites (dependencies, credentials, tools)
   - Step-by-step deployment commands
   - Expected deployment time
   - Verification steps (health checks, smoke tests)
   
2. **Operations**
   - How to start/stop/restart the service
   - How to check service health (endpoints, commands, expected responses)
   - How to view logs (locations, tools, filters)
   - How to scale up/down (manual and auto-scaling)
   - Common maintenance tasks (cache clearing, data cleanup, etc.)
   
3. **Monitoring**
   - Key metrics to monitor (uptime, latency, error rate, resource usage)
   - Alert thresholds with rationale
   - Dashboard links or creation instructions
   - On-call escalation procedures
   - Log aggregation and analysis tools
   
4. **Troubleshooting**
   - Common issues organized by symptom or component
   - For each issue: symptom, cause, diagnostic commands, solution
   - Log locations and interpretation guidance
   - Emergency contacts and escalation paths
   - Decision trees for complex scenarios
   
5. **Rollback**
   - How to identify last good version
   - Step-by-step rollback procedure
   - Data migration rollback (if applicable)
   - Verification steps after rollback
   - When to roll back vs. roll forward
   - Expected rollback time

### Cost Plan Structure Requirements

**Required Sections** (in order):
1. **Estimated Costs**
   - Infrastructure costs (compute, storage, networking)
   - Third-party service costs (APIs, monitoring, logging)
   - Data transfer and bandwidth costs
   - Development/maintenance costs (if applicable)
   - Ranges with assumptions clearly stated
   
2. **Cost Tracking**
   - Tools for monitoring costs (AWS Cost Explorer, Datadog, etc.)
   - Dashboard links or creation instructions
   - Cost breakdown by component, environment, or team
   - Review frequency (daily/weekly/monthly)
   - Budget alerts and notification thresholds
   
3. **Guardrails**
   - Spending limits per environment
   - Auto-scaling limits to prevent runaway costs
   - Resource quotas and constraints
   - Budget alert thresholds
   - Review and approval process for cost increases
   
4. **Optimization Opportunities**
   - Areas where costs could be reduced
   - Right-sizing recommendations
   - Reserved instance or commitment options
   - Caching opportunities
   - Cost vs. performance tradeoffs
   - Implementation priority (quick wins vs. complex optimizations)

### Secret Management Requirements

**Must Document**:
- All required secrets (database passwords, API keys, certificates, etc.)
- Secret management tool (AWS Secrets Manager, HashiCorp Vault, Kubernetes Secrets, etc.)
- How to reference secrets in code (environment variables, SDK calls)
- Rotation frequency per secret type
- Rotation procedure (step-by-step)
- Emergency rotation procedure for compromised secrets
- Access control (who can access which secrets)
- Warnings against committing secrets to version control

### CI/CD Pipeline Requirements

**Must Include or Document**:
- Build automation (compile, bundle, containerize)
- Test automation (run all tests on each build)
- Security scanning (dependency vulnerabilities, container scanning, SAST)
- Deployment automation for each environment
- Approval gates (who must approve production deployments)
- Smoke tests post-deployment
- Rollback automation or manual procedure
- Deployment notifications (Slack, email, etc.)

## Content Quality Standards

### Good vs. Bad Runbook Examples

#### Deployment Procedures
✅ **Good** (actionable):
```markdown
## Deployment to Production

### Prerequisites
- Kubectl configured for production cluster: `kubectl config use-context prod`
- AWS credentials with deployment role: `aws sts get-caller-identity`
- Release tagged in git: `git tag v1.2.3 && git push origin v1.2.3`

### Steps
1. Trigger CI/CD pipeline (automatic on tag push) or deploy manually:
   ```bash
   kubectl apply -f k8s/production/deployment.yaml
   kubectl rollout status deployment/api-server -n production
   ```

2. Wait for rollout to complete (~5 minutes)

3. Verify deployment:
   ```bash
   # Health check should return 200
   curl -i https://api.example.com/health
   # Expected: HTTP/1.1 200 OK, {"status":"healthy","version":"1.2.3"}
   
   # Check pod status
   kubectl get pods -n production -l app=api-server
   # Expected: All pods Running with READY 1/1
   ```

4. Monitor for 10 minutes:
   - Check dashboard: https://grafana.example.com/d/api-server
   - Watch for error rate spikes or latency increases
   - Review logs for unexpected errors: `kubectl logs -n production -l app=api-server --tail=100`

**Expected Duration**: 15 minutes (5 min deploy + 10 min monitoring)

**Rollback**: If issues occur, see "Rollback Procedure" section below.
```

❌ **Bad** (too abstract):
```markdown
## Deployment to Production

Deploy the application to production using the CI/CD pipeline or manually. Verify that it's working correctly. If something goes wrong, roll back.
```

#### Troubleshooting Guide
✅ **Good** (specific symptoms and solutions):
```markdown
## Troubleshooting

### Service Won't Start

**Symptom**: 
- Pods in CrashLoopBackOff state
- Logs show: `Error: connect ECONNREFUSED 10.0.1.50:5432`
- Health check returns 503

**Cause**: Database connection failed (network issue or incorrect credentials)

**Diagnostic Commands**:
```bash
# Check pod logs
kubectl logs -n production -l app=api-server --tail=50

# Check database pod status
kubectl get pods -n production -l app=postgres

# Test database connectivity from pod
kubectl exec -n production api-server-abc123 -- nc -zv postgres-service 5432

# Verify database secret exists
kubectl get secret postgres-credentials -n production
```

**Solution**:
1. Verify database is running:
   ```bash
   kubectl get pods -n production -l app=postgres
   # All postgres pods should be Running
   ```

2. Check database credentials in secret:
   ```bash
   kubectl get secret postgres-credentials -n production -o yaml
   # Verify data keys: username, password, host, port
   ```

3. Verify network policy allows connection:
   ```bash
   kubectl get networkpolicy -n production
   # Should allow api-server -> postgres traffic
   ```

4. If credentials are incorrect, update secret and restart:
   ```bash
   kubectl delete secret postgres-credentials -n production
   kubectl create secret generic postgres-credentials \
     --from-literal=username=<user> \
     --from-literal=password=<password> \
     -n production
   kubectl rollout restart deployment/api-server -n production
   ```

**Escalation**: If issue persists after 30 minutes, contact Database Team (#db-oncall on Slack)
```

❌ **Bad** (vague):
```markdown
## Troubleshooting

### Service Won't Start

If the service won't start, check the logs and make sure the database is accessible. Fix any connection issues or credential problems.
```

#### Operations Procedures
✅ **Good** (complete operations reference):
```markdown
## Operations

### Service Health Check

**Manual Check**:
```bash
# HTTP health endpoint
curl -i https://api.example.com/health
# Expected: HTTP/1.1 200 OK, {"status":"healthy","version":"1.2.3"}

# Check all pods are running
kubectl get pods -n production -l app=api-server
# Expected: All pods with STATUS=Running, READY=1/1
```

**Automated Health Checks**:
- Kubernetes liveness probe: GET /health every 30 seconds (timeout 5s)
- Kubernetes readiness probe: GET /ready every 10 seconds (timeout 3s)
- Uptime monitoring: Pingdom checks every 1 minute from 5 locations

### Viewing Logs

**Real-time logs** (last 100 lines, follow new entries):
```bash
kubectl logs -n production -l app=api-server --tail=100 -f
```

**Search logs** (last 1 hour, filter for errors):
```bash
kubectl logs -n production -l app=api-server --since=1h | grep ERROR
```

**Aggregated logs** (Kibana):
- Dashboard: https://kibana.example.com/app/logs
- Filter: `kubernetes.namespace:production AND kubernetes.labels.app:api-server`
- Retention: 30 days

### Scaling

**Manual scaling**:
```bash
# Scale to 5 replicas
kubectl scale deployment/api-server -n production --replicas=5

# Verify scaling
kubectl get pods -n production -l app=api-server
```

**Auto-scaling** (configured):
- HPA enabled: 2-10 replicas
- Target: 70% CPU utilization
- Check current status: `kubectl get hpa -n production`
```

❌ **Bad** (incomplete):
```markdown
## Operations

Check health using the health endpoint. View logs with kubectl. Scale using kubectl or the autoscaler.
```

### Good vs. Bad Cost Plan Examples

#### Cost Estimates
✅ **Good** (ranges with assumptions):
```markdown
## Estimated Costs

### Infrastructure Costs (Monthly)

**Compute** (AWS EKS + EC2):
- 3 t3.medium nodes (baseline): $75-90/month
- Auto-scaling to 10 nodes (peak load): $250-300/month
- Assumption: Average 5 nodes, 50% utilization
- **Estimate: $150-180/month**

**Database** (RDS PostgreSQL):
- db.t3.small (development): $30/month
- db.r5.large (production): $180/month
- Multi-AZ enabled: +100% cost
- Automated backups (7 days): ~$20/month
- **Estimate: $400/month (prod + backups)**

**Storage**:
- EBS volumes (500GB): $50/month
- S3 (file uploads, 1TB): $23/month
- S3 data transfer (outbound, 500GB): $45/month
- **Estimate: $120/month**

**Networking**:
- Load balancer: $20/month
- NAT gateway: $35/month
- Data transfer (inter-AZ, 200GB): $20/month
- **Estimate: $75/month**

**Total Infrastructure**: $745-875/month

### Third-Party Services (Monthly)

**Datadog** (monitoring and logs):
- 5 hosts: $75/month
- Log ingestion (50GB): $50/month
- **Estimate: $125/month**

**SendGrid** (transactional email):
- 100k emails/month: $90/month
- **Estimate: $90/month**

**Total Third-Party**: $215/month

### Total Estimated Monthly Cost: $960-1090/month

**Assumptions**:
- Production environment only (dev/staging costs ~30% additional)
- Average traffic: 1M requests/month
- Data growth: 10GB/month
- US-East-1 region pricing
- Estimated as of: 2024-01-15

**Cost per request**: ~$0.001 (at 1M requests/month)
```

❌ **Bad** (vague and incomplete):
```markdown
## Estimated Costs

Cloud infrastructure will cost around $1000/month. This includes servers, databases, and storage. Third-party services will add some additional costs.
```

#### Cost Guardrails
✅ **Good** (specific limits and alerts):
```markdown
## Guardrails

### Spending Limits (per environment)

**Development**:
- Hard limit: $200/month
- Alert threshold: $150/month (75%)
- Auto-shutdown: Nights and weekends (save ~50%)
- AWS Budget alert to: dev-team@example.com

**Staging**:
- Hard limit: $300/month
- Alert threshold: $225/month (75%)
- Auto-shutdown: Weekends only
- AWS Budget alert to: dev-team@example.com

**Production**:
- Soft limit: $1200/month (requires approval to exceed)
- Warning threshold: $900/month (75%)
- Critical threshold: $1500/month (125% - investigate immediately)
- AWS Budget alerts to: ops-team@example.com, finance@example.com

### Auto-Scaling Limits

**Kubernetes HPA**:
- Minimum replicas: 2 (production), 1 (dev/staging)
- Maximum replicas: 10 (production), 3 (dev/staging)
- Rationale: Prevents runaway scaling from attack or bug

**Database**:
- Read replicas: Max 2 (production)
- Auto-scaling disabled (manual approval required)
- Rationale: Database scaling is expensive; needs architectural review

**Storage**:
- S3 lifecycle policy: Move to Glacier after 90 days
- Delete old backups after 30 days
- Rationale: Prevents unbounded storage growth

### Resource Quotas

**Kubernetes ResourceQuotas** (per namespace):
```yaml
# Production namespace
limits.cpu: "20"
limits.memory: "40Gi"
requests.storage: "500Gi"

# Development namespace
limits.cpu: "4"
limits.memory: "8Gi"
requests.storage: "100Gi"
```

### Cost Increase Review Process

**For increases >20% of budget**:
1. Document business justification
2. Analyze cost drivers (what changed?)
3. Evaluate alternatives (right-sizing, architectural changes)
4. Get approval from Engineering Manager + Finance
5. Update budget and alert thresholds
6. Schedule follow-up review in 30 days
```

❌ **Bad** (no specifics):
```markdown
## Guardrails

Set spending limits for each environment. Configure auto-scaling limits to prevent runaway costs. Monitor spending and get approval for significant increases.
```

### Good vs. Bad Secret Management Examples

#### Secret Documentation
✅ **Good** (specific and actionable):
```markdown
## Secret Management

### Tool: AWS Secrets Manager

All secrets are stored in AWS Secrets Manager and injected into pods via Kubernetes External Secrets Operator.

### Required Secrets

**Production**:
1. `prod/api-server/database-url`
   - PostgreSQL connection string
   - Format: `postgresql://username:password@host:5432/dbname`
   - Rotation: Quarterly (every 90 days)
   - Access: api-server pods only

2. `prod/api-server/jwt-secret`
   - Token signing key (256-bit random string)
   - Rotation: Semi-annually (every 180 days)
   - Access: api-server pods only

3. `prod/api-server/sendgrid-api-key`
   - Email service API key
   - Rotation: Annually or on compromise
   - Access: api-server pods only

### Referencing Secrets in Code

**Environment variables** (injected by ExternalSecret):
```python
import os

database_url = os.environ['DATABASE_URL']
jwt_secret = os.environ['JWT_SECRET']
sendgrid_key = os.environ['SENDGRID_API_KEY']
```

**Never do this**:
```python
# ❌ Hardcoded secret (NEVER commit this)
jwt_secret = "my-super-secret-key-12345"
```

### Rotation Procedure (Normal)

1. Generate new secret value:
   ```bash
   # For random secrets (JWT, API keys)
   new_secret=$(openssl rand -base64 32)
   ```

2. Create new version in AWS Secrets Manager:
   ```bash
   aws secretsmanager put-secret-value \
     --secret-id prod/api-server/jwt-secret \
     --secret-string "$new_secret"
   ```

3. Trigger secret sync to Kubernetes:
   ```bash
   kubectl annotate externalsecret api-server-secrets \
     force-sync=$(date +%s) -n production
   ```

4. Perform rolling restart:
   ```bash
   kubectl rollout restart deployment/api-server -n production
   ```

5. Verify pods picked up new secret:
   ```bash
   kubectl logs -n production -l app=api-server --tail=10 | grep "Secret loaded"
   ```

6. Monitor for authentication errors for 10 minutes

**Duration**: ~15 minutes

### Emergency Rotation (Compromised Secret)

If a secret is compromised:

1. **Immediately** create new secret version (same steps as above)
2. Perform **immediate** restart (not rolling):
   ```bash
   kubectl delete pods -n production -l app=api-server
   # All pods recreated immediately with new secret
   ```
3. Revoke compromised secret from external services (if applicable)
4. Document incident in post-mortem
5. Review access logs to determine compromise scope

**Contact**: security-team@example.com or #security-oncall on Slack

### Best Practices

✅ **Do**:
- Store all secrets in AWS Secrets Manager (never in git)
- Use environment variables to access secrets
- Rotate secrets on schedule
- Use least-privilege IAM roles for secret access
- Audit secret access regularly
- Enable secret versioning
- Monitor for secret changes (CloudWatch alarms)

❌ **Don't**:
- Commit secrets to version control
- Share secrets via email, Slack, or unencrypted channels
- Use the same secret across environments (dev/staging/prod)
- Grant overly broad secret access
- Store secrets in plain text files
- Log secret values (mask them in logs)
```

❌ **Bad** (too vague):
```markdown
## Secret Management

Use a secret management tool like AWS Secrets Manager or HashiCorp Vault. Store secrets securely and rotate them regularly. Never commit secrets to git.
```

## Common Mistakes to Avoid

### Documentation Mistakes
- ❌ Abstract procedures without specific commands
- ❌ Using placeholder values without examples (`<your-value-here>`)
- ❌ Missing prerequisite information (credentials, tools, access)
- ❌ No expected outputs or success criteria
- ❌ Procedures that haven't been validated (incorrect commands)
- ❌ Missing environment-specific differences
- ❌ No links between related procedures (deployment → verification → rollback)
- ❌ Forgetting to update documentation after changes

### Runbook Mistakes
- ❌ Missing verification steps after deployment
- ❌ No expected deployment time documented
- ❌ Rollback procedure without verification steps
- ❌ Troubleshooting without diagnostic commands
- ❌ Monitoring without specific metrics and thresholds
- ❌ Operations procedures without examples
- ❌ No escalation paths or emergency contacts

### Cost Plan Mistakes
- ❌ Point estimates without ranges or assumptions
- ❌ Missing cost drivers (e.g., data transfer)
- ❌ No guardrails or spending limits
- ❌ Cost tracking without specific tools or dashboards
- ❌ No optimization opportunities identified
- ❌ Estimates without "as of" date (pricing changes)
- ❌ No cost breakdown by component
- ❌ Ignoring non-infrastructure costs (third-party APIs, licenses)

### Secret Management Mistakes
- ❌ Exposing actual secret values in documentation
- ❌ Not documenting all required secrets
- ❌ Missing rotation procedures
- ❌ No emergency rotation procedure
- ❌ Not specifying secret management tool
- ❌ Generic guidance without specific examples
- ❌ Not documenting access control
- ❌ Missing examples of how to reference secrets in code

### CI/CD Pipeline Mistakes
- ❌ Missing security scanning in pipeline
- ❌ No smoke tests after deployment
- ❌ Deployment without approval gates for production
- ❌ No rollback automation or documentation
- ❌ Missing deployment notifications
- ❌ Pipeline without test automation
- ❌ No verification steps in pipeline

### Monitoring Mistakes
- ❌ Metrics without thresholds
- ❌ Thresholds without rationale
- ❌ No dashboard links or creation instructions
- ❌ Missing escalation procedures
- ❌ Not defining key metrics (SLIs)
- ❌ No log aggregation documentation
- ❌ Alerts without clear meanings or actions

## Validation Checklist

Before considering operational documentation complete:

### Runbook Validation
- [ ] runbook.md file exists
- [ ] All required sections present: Deployment, Operations, Monitoring, Troubleshooting, Rollback
- [ ] Deployment procedures for each environment (dev, staging, prod)
- [ ] All procedures have specific commands (not abstractions)
- [ ] Prerequisites documented for each procedure
- [ ] Expected durations documented
- [ ] Verification steps included
- [ ] Health check endpoints and expected responses documented
- [ ] Log locations and viewing commands provided
- [ ] Scaling procedures (manual and auto) documented
- [ ] Key metrics defined with thresholds
- [ ] Dashboard links provided
- [ ] Escalation procedures documented
- [ ] Common issues documented with symptoms, causes, solutions
- [ ] Rollback procedure with verification steps
- [ ] Links to architecture.md and other artifacts

### Cost Plan Validation
- [ ] cost-plan.md exists (if project uses paid resources)
- [ ] All required sections present: Estimated Costs, Cost Tracking, Guardrails, Optimization Opportunities
- [ ] Cost estimates include ranges and assumptions
- [ ] Estimates break down by component
- [ ] Infrastructure costs documented (compute, storage, network)
- [ ] Third-party service costs documented
- [ ] Cost tracking tools and dashboards specified
- [ ] Spending limits per environment defined
- [ ] Auto-scaling limits documented
- [ ] Budget alerts configured or documented
- [ ] Optimization opportunities identified with priority
- [ ] Right-sizing recommendations included

### Secret Management Validation
- [ ] All required secrets identified and documented
- [ ] Secret management tool specified (AWS Secrets Manager, Vault, etc.)
- [ ] Secret rotation procedures documented
- [ ] Rotation frequencies specified per secret type
- [ ] Emergency rotation procedure documented
- [ ] Examples of referencing secrets in code provided
- [ ] Access control and least-privilege documented
- [ ] Warnings against committing secrets included

### CI/CD Pipeline Validation
- [ ] Build automation documented or implemented
- [ ] Test automation in pipeline
- [ ] Security scanning in pipeline (dependencies, containers)
- [ ] Deployment automation for each environment
- [ ] Approval gates for production
- [ ] Smoke tests post-deployment
- [ ] Rollback automation or procedure
- [ ] Deployment notifications configured

### Documentation Quality
- [ ] All procedures use specific commands (not abstractions)
- [ ] Examples use realistic values (not just placeholders)
- [ ] Expected outputs documented
- [ ] Error cases documented
- [ ] Environment-specific differences noted
- [ ] Links between related procedures
- [ ] Contact information for escalations
- [ ] Last updated or "as of" dates included

### Completeness Check
- [ ] status.json checked before starting work
- [ ] Project deployability assessed correctly
- [ ] All environments documented (dev, staging, prod as applicable)
- [ ] Documentation links to architecture.md, plan.md
- [ ] Procedures validated or include validation criteria

## Review Standards

### Self-Review
Before submitting documentation, agent should:
1. Validate all required sections exist
2. Check that all procedures are actionable (specific commands)
3. Verify links to other artifacts work
4. Ensure cost estimates include assumptions
5. Confirm secret management is documented without exposing secrets
6. Check that rollback procedures include verification
7. Validate monitoring metrics have thresholds

### Operational Review Criteria (Human or Agent)
Reviewers should validate:
- **Completeness**: All required sections and content present?
- **Actionability**: Can an unfamiliar operator follow the procedures?
- **Accuracy**: Are commands and configurations correct?
- **Specificity**: Are examples specific enough (not just placeholders)?
- **Cost realism**: Are cost estimates plausible and assumptions clear?
- **Security**: Are secrets managed properly without exposure?
- **Maintainability**: Will this documentation be easy to update?

### Operational Acceptance
Good operational documentation passes this test:
- [ ] Can answer: "How do I deploy this?" (complete procedure exists)
- [ ] Can answer: "How do I know it's working?" (health checks and monitoring)
- [ ] Can answer: "What do I do if it breaks?" (troubleshooting guide)
- [ ] Can answer: "How do I undo this deployment?" (rollback procedure)
- [ ] Can answer: "How much will this cost?" (cost estimates with assumptions)
- [ ] Can answer: "How do I manage secrets?" (secret management documented)
- [ ] Can be used by someone unfamiliar with the system (self-contained)

## Examples

### Minimal Deployable Service

Even simple services need operational documentation:
```
# Project: Weather API (single service)

runbook.md (250 lines):
  - Deployment (to Heroku)
  - Operations (start/stop, logs, scaling)
  - Monitoring (uptime, latency, errors)
  - Troubleshooting (5 common issues)
  - Rollback (Heroku rollback command)
  - Secrets (API key for weather data provider)

cost-plan.md (80 lines):
  - Estimated: $50/month (Heroku dyno + weather API)
  - Tracking: Heroku dashboard + weather API usage dashboard
  - Guardrails: $100/month limit, alerts at $75
  - Optimization: Right-size dyno based on actual traffic

CI/CD:
  - GitHub Actions workflow (already exists)
  - Added: Security scanning step
  - Added: Deployment to Heroku with smoke test
```

### Complex Multi-Service Deployment

```
# Project: E-commerce Platform (microservices)

runbook.md (800 lines):
  - Deployment (6 services, dependencies documented)
    - Deployment order: database → cache → backend → frontend
    - Each service has own deployment procedure
  - Operations (per service and overall health)
  - Monitoring (service-level and business metrics)
  - Troubleshooting (organized by symptom, 20+ issues)
    - Service-specific issues
    - Cross-service issues (cascading failures)
  - Rollback (per service with dependency considerations)
  - Secrets (12 secrets across services, rotation matrix)

cost-plan.md (400 lines):
  - Estimated: $3500-4500/month
    - Compute: $1800/month (Kubernetes cluster)
    - Databases: $1200/month (RDS + Redis)
    - Storage: $300/month (S3 + backups)
    - Networking: $400/month (ALB + CloudFront + data transfer)
    - Third-party: $800/month (Stripe, SendGrid, Datadog, etc.)
  - Tracking: Multi-dimensional (service, environment, team)
  - Guardrails: Tiered by environment and service criticality
  - Optimization: 8 opportunities identified with ROI estimates

CI/CD:
  - Multi-stage pipeline for each service
  - Integration tests across services
  - Canary deployments for production
  - Automated rollback on smoke test failure
```

## Continuous Improvement

The Deployment Agent role should evolve based on:
- Production incidents (update troubleshooting guides)
- Cost actuals vs. estimates (refine estimation models)
- Rollback scenarios (update procedures based on actual rollbacks)
- Operational feedback (operators report what's helpful/missing)
- Security reviews (incorporate security findings)
- Tool changes (update for new CI/CD, monitoring, or secret management tools)

Changes to this quality bar should be proposed via:
1. Issue documenting the operational gap or improvement
2. Examples of current documentation vs. improved approach
3. Update to this quality-bar.md
4. Update to role.deployment.md agent prompt
5. Validation that change improves operational outcomes
