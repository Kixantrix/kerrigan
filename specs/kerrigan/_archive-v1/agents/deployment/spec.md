# Spec: Deployment Agent

## Goal

Make deployable projects operationally ready for production by creating comprehensive operational documentation, establishing CI/CD pipelines, implementing cost tracking and guardrails, and ensuring secure secret management practices.

## Scope

- Creating `runbook.md` with deployment, operations, monitoring, troubleshooting, and rollback procedures
- Producing `cost-plan.md` with cost estimates, tracking mechanisms, and guardrails
- Building or enhancing CI/CD pipelines for automated build, test, and deployment
- Documenting secret management strategy and implementation
- Setting up monitoring dashboards and alert configurations
- Defining rollback procedures and emergency response protocols
- Establishing deployment verification and smoke tests
- Documenting operational procedures for different environments (dev, staging, prod)
- Creating cost budgets, alerts, and optimization recommendations
- Linking operational documentation to relevant artifacts (architecture, plan)

## Non-goals

- Creating specifications or acceptance criteria (Spec Agent's responsibility)
- Designing system architecture or data flows (Architect Agent's responsibility)
- Implementing application code or features (SWE Agent's responsibility)
- Writing comprehensive test suites (Testing Agent and SWE Agent's responsibility)
- Deep security hardening or threat modeling (Security Agent's responsibility)
- Actual deployment execution (unless part of pipeline automation)
- Infrastructure-as-code implementation (may document requirements, but not implement)

## Users & scenarios

### Primary Users
- **Operations Teams**: Use runbook.md for daily operations, incident response, and maintenance
- **On-Call Engineers**: Reference troubleshooting procedures during incidents
- **DevOps Engineers**: Implement CI/CD pipelines based on documentation
- **SRE Teams**: Monitor costs and system health using documented procedures
- **Finance/Budget Owners**: Track infrastructure costs and review optimization opportunities
- **Security Agent**: Reviews secret management and operational security practices
- **Future Maintainers**: Understand operational requirements and procedures

### Key Scenarios
1. **New Deployable Project**: Reads architecture.md → Creates runbook.md and cost-plan.md → Sets up CI/CD pipeline → Documents verification steps
2. **Deployment Procedure**: Developer needs to deploy → Follows runbook.md deployment section → Verifies deployment → Monitors for issues
3. **Production Incident**: Service degradation → On-call engineer uses troubleshooting section → Resolves issue or escalates → Documents learnings
4. **Cost Overrun**: Monthly bill exceeds budget → Reviews cost-plan.md → Identifies cost drivers → Implements optimization recommendations
5. **Rollback Scenario**: Bad deployment causes errors → Follows rollback procedure → Restores previous version → Verifies service health
6. **Environment Setup**: New staging environment needed → Follows deployment procedures → Configures monitoring → Sets cost guardrails
7. **Secret Rotation**: Quarterly secret rotation → Follows secret management documentation → Updates secrets → Performs rolling restart

## Constraints

- Must create runbook.md for all deployable projects
- Must create cost-plan.md for projects using paid resources
- Must check project status.json before starting work
- Must document secret management practices (never expose secrets)
- Must include rollback procedures for all deployment paths
- Must define verification steps for each deployment
- Should align with constitution principles (operational responsibility, cost awareness)
- Should follow existing operational patterns in the organization
- Must ensure CI/CD pipelines include security scanning
- Must document monitoring and alerting thresholds
- Should keep operational documentation actionable (commands, not just concepts)

## Acceptance criteria

- runbook.md exists with all required sections: Deployment, Operations, Monitoring, Troubleshooting, Rollback
- cost-plan.md exists for projects using paid resources with: Estimated Costs, Cost Tracking, Guardrails, Optimization Opportunities
- CI/CD pipeline automation implemented or documented with: Build, Test, Security Scan, Deploy, Smoke Test steps
- Secret management strategy documented with specific tools and rotation procedures
- Deployment procedures include prerequisites, expected duration, and verification steps
- Rollback procedures are tested or include clear validation criteria
- Monitoring section defines key metrics, thresholds, and dashboard links
- Troubleshooting section covers common issues with symptoms, causes, and solutions
- Cost estimates include infrastructure, third-party services, data transfer, and maintenance
- Guardrails include spending limits, auto-scaling constraints, and budget alerts
- All procedures reference specific commands or tools (actionable, not abstract)
- Operational documentation links to relevant artifacts (architecture.md, plan.md)

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Runbook becomes outdated after implementation | High | Link runbook to architecture; update during implementation changes; version control documentation |
| Cost estimates significantly inaccurate | High | Provide ranges with assumptions; document how to monitor actual costs; plan for quarterly reviews |
| Rollback procedure untested, fails during crisis | High | Require verification steps; document "tested on [date]"; encourage periodic rollback drills |
| Secret management procedure not followed | High | Document clearly with examples; automate scanning for hardcoded secrets; provide secret rotation reminders |
| Monitoring blind spots, incidents not detected | Medium | Collaborate with SRE teams on metrics; document key SLIs; review incident patterns quarterly |
| Over-complex deployment procedures | Medium | Keep procedures simple; automate where possible; provide both automated and manual paths |
| Cost guardrails too restrictive or too loose | Medium | Set conservative initial limits; document adjustment process; review monthly for first quarter |
| Documentation too abstract, not actionable | High | Include specific commands, tool names, and examples; validate with operators unfamiliar with system |

## Success metrics

- 100% of deployable projects have runbook.md before production deployment
- 100% of projects using paid resources have cost-plan.md with guardrails
- Deployment success rate >95% when following runbook procedures
- Rollback success rate >99% when procedure is followed
- Mean time to recovery (MTTR) reduced by >30% with comprehensive troubleshooting documentation
- Cost variance from estimates <20% in first 3 months, <10% after optimizations
- Zero secrets committed to version control after secret management documentation
- On-call engineers rate troubleshooting documentation as "helpful" or "very helpful" (>80%)
- Cost optimization opportunities identified and documented for >50% of projects
- CI/CD pipeline includes security scanning for 100% of deployable projects
