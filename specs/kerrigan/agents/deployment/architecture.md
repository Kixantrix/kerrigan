# Architecture: Deployment Agent

## Overview

The Deployment Agent serves as the operational readiness specialist within the Kerrigan agent swarm. It transforms deployable projects into production-ready systems by creating comprehensive operational documentation, establishing deployment automation, implementing cost tracking mechanisms, and ensuring secure operational practices. The agent bridges the gap between working code and reliable production operations.

The agent's architecture emphasizes actionable documentation over abstract concepts, cost awareness from day one, and operational procedures that can be followed by engineers unfamiliar with the system. Unlike traditional "deploy and pray" approaches, this agent ensures operational knowledge is captured, tested, and maintained as code artifacts alongside the application itself.

The Deployment Agent works in the later stages of project development, after architecture and implementation are substantially complete, but before or during initial production deployment. It collaborates closely with the Architect Agent (for understanding system design) and the Security Agent (for secure operational practices).

## Components & interfaces

### Input Sources
- **architecture.md**: System design, components, deployment topology, and infrastructure requirements
- **plan.md**: Deployment milestones and timeline expectations
- **spec.md**: Requirements and constraints that inform operational procedures
- **test-plan.md**: Testing strategy that informs smoke tests and verification procedures
- **status.json**: Project workflow status (must check before starting work)
- **Existing infrastructure**: Current CI/CD setup, monitoring tools, cost tracking systems
- **Codebase**: Application code, existing deployment scripts, configuration files

### Core Processing Components

**Status Checker**
- Validates project status before starting work
- Reads status.json and checks for "blocked" or "on-hold" states
- Reports blocked_reason and stops if project is not active
- Ensures deployment work only proceeds when project is ready

**Input Analyzer**
- Reads architecture.md to understand deployment topology
- Identifies infrastructure dependencies (databases, caches, queues, etc.)
- Determines if project is deployable (services, APIs, web apps vs. libraries)
- Assesses if project uses paid resources (cloud infrastructure, third-party APIs)
- Identifies environments (dev, staging, production)
- Extracts secret management requirements
- Maps out deployment dependencies and sequencing

**Runbook Generator**
- Creates operational procedures documentation
- Structures content into required sections: Deployment, Operations, Monitoring, Troubleshooting, Rollback
- Generates environment-specific deployment procedures
- Documents start/stop/restart procedures for services
- Creates health check and verification procedures
- Compiles troubleshooting guides from architecture and common failure modes
- Documents log locations and interpretation guidance
- Defines rollback procedures with verification steps
- Ensures all procedures are actionable with specific commands

**Cost Analyzer**
- Identifies cost drivers from architecture (compute, storage, bandwidth, APIs)
- Estimates costs per component with assumptions and ranges
- Creates cost tracking documentation (tools, dashboards, review frequency)
- Defines guardrails: spending limits, auto-scaling constraints, budget alerts
- Identifies optimization opportunities (right-sizing, reserved instances, caching)
- Documents cost breakdown by component, environment, or team
- Plans for cost monitoring and quarterly reviews

**Secret Management Documenter**
- Identifies secrets required by application (API keys, database passwords, certificates)
- Documents secret management tools (AWS Secrets Manager, HashiCorp Vault, Kubernetes Secrets)
- Creates secret rotation procedures with frequencies
- Generates examples of referencing secrets in code (environment variables)
- Establishes least-privilege access principles
- Documents emergency rotation procedures
- Validates that secrets are not committed to version control

**Monitoring Documentation Builder**
- Defines key metrics from architecture (uptime, latency, error rate, resource usage)
- Specifies alert thresholds with rationale
- Documents dashboard creation or links to existing dashboards
- Creates on-call escalation procedures
- Maps metrics to business impact
- Defines service level indicators (SLIs) and objectives (SLOs) where appropriate
- Documents log aggregation and analysis tools

**CI/CD Pipeline Documenter**
- Documents or implements build automation (compile, bundle, containerize)
- Ensures test automation runs in pipeline
- Adds security scanning (dependency vulnerabilities, container scanning)
- Creates deployment automation for each environment
- Implements or documents smoke tests post-deployment
- Establishes approval gates for production deployments
- Documents rollback automation or manual procedures
- Ensures pipeline includes verification steps

**Troubleshooting Guide Builder**
- Compiles common issues from architecture and experience
- Structures issues by symptom or component
- Provides diagnostic commands for each issue
- Documents root causes and resolution steps
- Includes emergency contacts and escalation paths
- References relevant log files and monitoring dashboards
- Creates decision trees for complex troubleshooting scenarios

### Output Artifacts
- **runbook.md**: Complete operational procedures documentation
- **cost-plan.md**: Cost estimates, tracking, and guardrails (for projects with paid resources)
- **CI/CD pipeline configuration**: Updated or new pipeline definitions
- **Monitoring configuration**: Dashboard definitions or documentation
- **Secret management documentation**: Within runbook.md or separate security docs
- **Deployment scripts**: Automation scripts or documented manual procedures
- **Smoke test definitions**: Post-deployment verification tests

### Validation Interface
- Agent output must satisfy:
  - runbook.md exists with all required sections
  - cost-plan.md exists if project uses paid resources
  - All procedures are actionable (specific commands, not abstractions)
  - Secret management strategy documented
  - Rollback procedures defined
  - Monitoring metrics and thresholds specified
  - CI/CD pipeline includes security scanning
  - Documentation links to relevant artifacts

## Data flow (conceptual)

```
[architecture.md, plan.md, spec.md, status.json]
        ↓
[Status Check] → (if blocked) → [Stop & Report]
        ↓
[Input Analyzer] → Determine project type, environments, paid resources
        ↓
[Deployability Assessment]
        ↓
[Parallel Processing:]
        ├─→ [Runbook Generator]
        │       ├─→ Deployment procedures (per environment)
        │       ├─→ Operations procedures (start/stop/scale)
        │       ├─→ Monitoring documentation (metrics/dashboards)
        │       ├─→ Troubleshooting guide (issues/solutions)
        │       └─→ Rollback procedures (verification)
        │
        ├─→ [Cost Analyzer] → (if paid resources)
        │       ├─→ Cost estimates (by component)
        │       ├─→ Tracking mechanisms (tools/dashboards)
        │       ├─→ Guardrails (limits/alerts)
        │       └─→ Optimization opportunities
        │
        ├─→ [Secret Management Documenter]
        │       ├─→ Required secrets inventory
        │       ├─→ Management tools and procedures
        │       └─→ Rotation procedures
        │
        └─→ [CI/CD Pipeline Documenter]
                ├─→ Build automation
                ├─→ Test automation
                ├─→ Security scanning
                ├─→ Deployment automation
                └─→ Smoke tests
        ↓
[Document Integration] → Link artifacts together
        ↓
[Validation] → Check completeness and actionability
        ↓
[Runbook.md + Cost-Plan.md + CI/CD updates]
```

## Tradeoffs

### Comprehensive Documentation vs. Minimal Overhead
**Decision**: Create comprehensive runbook and cost plan even for small projects
- **Pro**: Ensures operational knowledge is captured; reduces MTTR during incidents; new team members can operate service; cost awareness from day one
- **Con**: Upfront documentation overhead; may feel like bureaucracy for simple projects; documentation can become outdated
- **Mitigation**: Use templates for common patterns; keep documentation focused on essentials; establish update triggers (deployment failures, incidents, cost surprises); even small projects benefit during incidents

### Actionable Commands vs. Abstract Guidance
**Decision**: Prioritize specific commands and tools over general concepts
- **Pro**: Operators can copy-paste commands; reduces errors; faster incident response; easier for junior engineers; acts as executable documentation
- **Con**: Commands may become outdated; environment-specific; longer documentation; may not cover all variations
- **Mitigation**: Use environment variables in examples; include "last tested" dates; provide both specific examples and conceptual guidance; version control tracks changes

### Cost Estimation Ranges vs. Precise Numbers
**Decision**: Provide cost ranges with assumptions rather than precise estimates
- **Pro**: Accounts for usage variability; sets expectations without over-committing; documents assumptions clearly; easier to estimate upfront
- **Con**: May be too vague for budgeting; requires follow-up monitoring; can be significantly wrong
- **Mitigation**: Document assumptions explicitly; provide ranges (min/likely/max); specify how to monitor actuals; plan for quarterly reviews; update after first month of real data

### Pipeline Automation vs. Documentation Only
**Decision**: Document pipeline requirements; implement if simple, otherwise provide implementation guidance
- **Pro**: Documentation always exists even if automation changes; allows flexibility in tooling choices; doesn't block on automation complexity
- **Con**: Documentation without automation may not be followed; manual procedures are error-prone; slower deployments
- **Mitigation**: Provide both automated and manual paths; prioritize automation for critical paths (production deployments); validate manual procedures periodically

### Comprehensive Troubleshooting vs. "Learn Through Incidents"
**Decision**: Proactively document anticipated issues based on architecture
- **Pro**: Reduces MTTR for common issues; captures architectural knowledge; helps during first incidents; assists on-call engineers
- **Con**: Can't predict all issues; documentation may miss actual problems; becomes outdated; effort upfront
- **Mitigation**: Start with architecture-based issues; update after each incident; encourage "troubleshooting guide PR" after resolution; accept incompleteness

### Environment-Specific Procedures vs. Generic Guidance
**Decision**: Document procedures for each environment (dev, staging, prod) when differences exist
- **Pro**: Reduces errors from environment confusion; clearer for operators; captures environment-specific configurations; safer production operations
- **Con**: More documentation to maintain; duplication across environments; can diverge over time
- **Mitigation**: Use templates with environment variables; clearly mark differences; automate environment setup where possible; regular cross-environment validation

### Rollback Testing vs. Documentation Only
**Decision**: Document rollback procedures with validation criteria; encourage testing but don't require it
- **Pro**: Rollback documentation exists even without testing; testing may not be feasible pre-production; allows validation in lower environments
- **Con**: Untested rollback may fail during crisis; false confidence in documentation; may miss edge cases
- **Mitigation**: Document "last tested" dates; provide validation criteria; encourage periodic rollback drills; test in lower environments; capture lessons from actual rollbacks

### Secret Management Centralization vs. Flexibility
**Decision**: Document specific tools and procedures, prefer centralized secret management
- **Pro**: Consistent approach across projects; leverages organizational tooling; easier auditing; supports secret rotation; reduces security risks
- **Con**: May not fit all projects; organizational tool may not exist; flexibility constrained; learning curve
- **Mitigation**: Recommend organizational standards; document alternatives if needed; provide migration paths; balance security with pragmatism

## Security & privacy notes

### Secret Management Security
- Deployment Agent must never expose secrets in documentation
- Use placeholder examples (e.g., `DATABASE_PASSWORD=<from secrets manager>`)
- Document secret access control and least-privilege principles
- Specify secret rotation frequencies appropriate to risk level
- Include emergency rotation procedures for compromised secrets
- Document audit logging for secret access
- Validate that secrets are not committed to version control (provide scanning tools)

### Secure Deployment Practices
- Document TLS/HTTPS requirements for external communication
- Specify encryption requirements for data at rest
- Define network segmentation and firewall rules
- Document authentication and authorization for deployment tools
- Require approval workflows for production deployments
- Specify audit logging for all deployments and operational changes
- Document secure communication channels for incident response

### Access Control Documentation
- Define who can deploy to each environment (RBAC, IAM roles)
- Document principle of least privilege for service accounts
- Specify MFA requirements for production access
- Document off-boarding procedures for revoked access
- Define emergency access procedures with approval and audit
- Specify service account credential rotation procedures

### Operational Security
- Document secure logging practices (no secrets in logs)
- Specify log retention and access controls
- Define incident response notification procedures
- Document security monitoring and alerting
- Specify vulnerability management for operational tools
- Include security-relevant metrics in monitoring

### Cost Security
- Document spending limits as security controls (prevent resource abuse)
- Specify alerts for unusual spending patterns (may indicate compromise)
- Define approval workflows for cost increases
- Document tagging strategies for cost accountability and audit
- Specify monitoring for cryptocurrency mining or other abuse

### Alignment with Security Agent
- Deployment Agent documents operational security practices
- Security Agent reviews and enhances security posture
- Handoff: Deployment Agent provides operational security baseline → Security Agent validates and strengthens
- Deployment Agent may need to implement security improvements identified by Security Agent
- Security scanning in CI/CD pipeline catches vulnerabilities before deployment

### Monitoring and Incident Response Security
- Document secure access to monitoring dashboards
- Specify PII handling in logs and metrics
- Define alert notification security (avoid exposing sensitive data)
- Document incident response communication channels
- Specify forensic data collection procedures for security incidents
- Include security team in escalation paths

### Compliance and Audit
- Document compliance requirements relevant to operations (HIPAA, PCI-DSS, SOC2)
- Specify audit log retention policies
- Define change management procedures for auditable changes
- Document evidence collection for compliance reporting
- Include compliance-relevant metrics in monitoring
