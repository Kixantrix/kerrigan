# Acceptance tests: Deployment Agent

## Runbook Creation

- [ ] **Given** a deployable project, **When** Deployment Agent starts work, **Then** runbook.md is created with all required sections
- [ ] **Given** runbook.md exists, **When** checking structure, **Then** it includes: Deployment, Operations, Monitoring, Troubleshooting, Rollback sections
- [ ] **Given** deployment procedures, **When** reviewing, **Then** each procedure includes prerequisites, expected duration, and verification steps
- [ ] **Given** runbook commands, **When** checking, **Then** commands are specific and actionable (not abstract descriptions)
- [ ] **Given** runbook sections, **When** validating, **Then** all section headings match artifact contract requirements

## Cost Plan Creation

- [ ] **Given** a project using paid resources, **When** Deployment Agent starts work, **Then** cost-plan.md is created
- [ ] **Given** cost-plan.md exists, **When** checking structure, **Then** it includes: Estimated Costs, Cost Tracking, Guardrails, Optimization Opportunities sections
- [ ] **Given** cost estimates, **When** reviewing, **Then** estimates cover infrastructure, third-party services, data transfer, and maintenance
- [ ] **Given** cost guardrails, **When** checking, **Then** guardrails include spending limits, auto-scaling constraints, and budget alerts
- [ ] **Given** cost tracking, **When** reviewing, **Then** documentation specifies tools, dashboards, and review frequency
- [ ] **Given** cost estimates, **When** validating, **Then** assumptions and ranges are documented clearly

## Deployment Procedures

- [ ] **Given** deployment section in runbook, **When** checking, **Then** procedures exist for each environment (dev, staging, prod)
- [ ] **Given** deployment procedure, **When** reviewing, **Then** prerequisites are clearly listed
- [ ] **Given** deployment procedure, **When** checking, **Then** expected deployment time is documented
- [ ] **Given** deployment procedure, **When** validating, **Then** verification steps are included
- [ ] **Given** multi-step deployment, **When** checking, **Then** steps are numbered and sequential
- [ ] **Given** deployment automation, **When** reviewing, **Then** both automated and manual procedures are documented
- [ ] **Given** deployment procedure, **When** checking dependencies, **Then** external dependencies are clearly noted

## Operations Procedures

- [ ] **Given** operations section, **When** reviewing, **Then** it includes how to start/stop the service
- [ ] **Given** operations section, **When** checking, **Then** it includes how to check service health
- [ ] **Given** operations section, **When** validating, **Then** it includes how to view logs
- [ ] **Given** operations section, **When** reviewing, **Then** it includes how to scale up/down
- [ ] **Given** operations section, **When** checking, **Then** common maintenance tasks are documented
- [ ] **Given** operational commands, **When** validating, **Then** commands include full syntax and options

## Monitoring Documentation

- [ ] **Given** monitoring section, **When** reviewing, **Then** key metrics are defined (uptime, latency, errors, resource usage)
- [ ] **Given** monitoring metrics, **When** checking, **Then** alert thresholds are specified with rationale
- [ ] **Given** monitoring section, **When** validating, **Then** dashboard links are provided
- [ ] **Given** monitoring setup, **When** reviewing, **Then** on-call escalation procedures are documented
- [ ] **Given** monitoring alerts, **When** checking, **Then** alert meanings and expected responses are explained
- [ ] **Given** health checks, **When** validating, **Then** endpoints, expected responses, and frequencies are specified

## Troubleshooting Documentation

- [ ] **Given** troubleshooting section, **When** reviewing, **Then** common issues are documented with symptoms, causes, and solutions
- [ ] **Given** troubleshooting guide, **When** checking, **Then** issues are organized by symptom or component
- [ ] **Given** troubleshooting issue, **When** validating, **Then** diagnostic commands are provided
- [ ] **Given** troubleshooting issue, **When** reviewing, **Then** resolution steps are actionable and specific
- [ ] **Given** troubleshooting section, **When** checking, **Then** emergency contacts and escalation paths are included
- [ ] **Given** debugging procedures, **When** validating, **Then** log locations and interpretation guidance are provided

## Rollback Procedures

- [ ] **Given** rollback section, **When** reviewing, **Then** procedure includes how to roll back to previous version
- [ ] **Given** rollback procedure, **When** checking, **Then** it includes how to identify the last good version
- [ ] **Given** rollback procedure, **When** validating, **Then** verification steps after rollback are documented
- [ ] **Given** rollback documentation, **When** reviewing, **Then** guidance on "when to roll back vs. roll forward" is included
- [ ] **Given** data migration rollback, **When** checking, **Then** database rollback procedures are documented (if applicable)
- [ ] **Given** rollback procedure, **When** validating, **Then** expected rollback time is documented
- [ ] **Given** rollback steps, **When** reviewing, **Then** rollback is tested or includes validation criteria

## Secret Management

- [ ] **Given** secret management documentation, **When** reviewing, **Then** it specifies tools used (e.g., AWS Secrets Manager, HashiCorp Vault)
- [ ] **Given** secret management, **When** checking, **Then** it documents all required secrets for the project
- [ ] **Given** secret rotation procedure, **When** validating, **Then** rotation frequency and process are documented
- [ ] **Given** secret management, **When** reviewing, **Then** it includes examples of how to reference secrets in code
- [ ] **Given** secret documentation, **When** checking, **Then** it explicitly warns against committing secrets to version control
- [ ] **Given** secret access, **When** validating, **Then** least-privilege access principles are documented
- [ ] **Given** emergency secret rotation, **When** reviewing, **Then** emergency rotation procedure is documented

## CI/CD Pipeline

- [ ] **Given** CI/CD pipeline, **When** checking, **Then** build automation is configured
- [ ] **Given** CI/CD pipeline, **When** validating, **Then** test automation runs on each build
- [ ] **Given** CI/CD pipeline, **When** reviewing, **Then** security scanning is included (dependencies, containers)
- [ ] **Given** CI/CD pipeline, **When** checking, **Then** deployment automation exists or is documented
- [ ] **Given** CI/CD pipeline, **When** validating, **Then** smoke tests run after deployment
- [ ] **Given** pipeline configuration, **When** reviewing, **Then** rollback automation exists or is documented
- [ ] **Given** pipeline stages, **When** checking, **Then** approval gates are documented for production deployments

## Cost Awareness

- [ ] **Given** cost-plan.md, **When** reviewing cost tracking, **Then** tools or dashboards for monitoring costs are specified
- [ ] **Given** cost guardrails, **When** checking, **Then** spending limits are defined per environment
- [ ] **Given** cost guardrails, **When** validating, **Then** auto-scaling limits to prevent runaway costs are documented
- [ ] **Given** cost plan, **When** reviewing, **Then** budget alerts and notification thresholds are configured or documented
- [ ] **Given** optimization opportunities, **When** checking, **Then** specific areas for cost reduction are identified
- [ ] **Given** cost estimates, **When** validating, **Then** right-sizing recommendations are included
- [ ] **Given** cost optimization, **When** reviewing, **Then** reserved instance or commitment options are documented (if applicable)
- [ ] **Given** cost tracking, **When** checking, **Then** cost breakdown by component or service is explained

## Status and Workflow

- [ ] **Given** project with status.json, **When** Deployment Agent starts work, **Then** agent checks status is "active" or file doesn't exist
- [ ] **Given** status.json shows "blocked", **When** Deployment Agent starts work, **Then** agent stops and reports blocked_reason
- [ ] **Given** deployment work, **When** referencing artifacts, **Then** runbook links to architecture.md and plan.md

## Verification and Validation

- [ ] **Given** deployment procedure, **When** reviewing verification steps, **Then** health check commands are provided
- [ ] **Given** deployment verification, **When** checking, **Then** expected outputs or responses are documented
- [ ] **Given** smoke tests, **When** validating, **Then** critical functionality checks are defined
- [ ] **Given** post-deployment verification, **When** reviewing, **Then** monitoring period duration is specified
- [ ] **Given** verification failures, **When** checking, **Then** failure response procedures are documented

## Environment-Specific Configuration

- [ ] **Given** multi-environment deployment, **When** reviewing, **Then** environment-specific configurations are documented
- [ ] **Given** environment procedures, **When** checking, **Then** differences between dev, staging, and prod are clearly noted
- [ ] **Given** environment access, **When** validating, **Then** access control and permissions are documented per environment
- [ ] **Given** environment monitoring, **When** reviewing, **Then** environment-specific thresholds are documented (if different)

## Documentation Quality

- [ ] **Given** runbook procedures, **When** checking clarity, **Then** procedures are written for operators unfamiliar with the system
- [ ] **Given** operational commands, **When** validating, **Then** all commands include examples with actual values
- [ ] **Given** troubleshooting documentation, **When** reviewing, **Then** error messages are quoted verbatim for searchability
- [ ] **Given** cost documentation, **When** checking, **Then** currency and time periods are explicitly stated
- [ ] **Given** all documentation, **When** validating, **Then** last updated dates or version information is included

## Security Considerations

- [ ] **Given** deployment procedures, **When** reviewing security, **Then** TLS/HTTPS requirements are documented
- [ ] **Given** secret management, **When** checking security, **Then** encryption at rest requirements are documented
- [ ] **Given** access control, **When** validating, **Then** who can deploy to each environment is clearly defined
- [ ] **Given** deployment audit, **When** reviewing, **Then** audit logging requirements are documented
- [ ] **Given** secure communication, **When** checking, **Then** internal communication security requirements are documented

## Edge Cases

- [ ] **Given** project without paid resources, **When** checking, **Then** cost-plan.md may be omitted with justification
- [ ] **Given** non-deployable library project, **When** checking, **Then** runbook.md focuses on release procedures and versioning
- [ ] **Given** simple project, **When** reviewing runbook, **Then** still includes all required sections (even if brief)
- [ ] **Given** complex multi-service deployment, **When** checking, **Then** service dependencies and deployment order are documented
- [ ] **Given** disaster recovery scenario, **When** validating, **Then** complete system restore procedures are documented

## Continuous Improvement

- [ ] **Given** production incidents, **When** reviewing documentation, **Then** learnings are incorporated into troubleshooting section
- [ ] **Given** cost actuals vs. estimates, **When** checking, **Then** cost-plan.md includes update process and review frequency
- [ ] **Given** deployment failures, **When** validating, **Then** failure modes and prevention are documented
- [ ] **Given** operational changes, **When** reviewing, **Then** documentation update process is defined
