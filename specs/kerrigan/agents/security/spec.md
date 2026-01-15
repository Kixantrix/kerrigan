# Spec: Security Agent

## Goal

Identify and prevent common security issues early in development by applying lightweight security analysis aligned with OWASP Top 10 and industry best practices, ensuring security considerations are documented and integrated throughout the development lifecycle.

## Scope

- Adding "Security & privacy notes" section to `architecture.md` with authentication, authorization, data protection, and monitoring considerations
- Documenting secret management and access control procedures in `runbook.md`
- Proposing CI security checks (dependency scanning, static analysis, secret detection)
- Reviewing code for common vulnerabilities (input validation, injection, XSS, CSRF)
- Validating security-relevant configuration (CORS, TLS, authentication middleware)
- Creating security checklists in acceptance-tests.md for validation
- Identifying dependency vulnerabilities and recommending updates
- Documenting security assumptions and threat considerations in `decisions.md`

## Non-goals

- Penetration testing or sophisticated red-team assessments (requires security specialist)
- Formal security audits or compliance certifications (requires legal/compliance team)
- Infrastructure hardening beyond application-level concerns (DevOps/Infrastructure team)
- Implementing security fixes (SWE Agent's responsibility with Security Agent guidance)
- Zero-day vulnerability research or advanced threat hunting
- Security training or education of team members
- Incident response or forensic analysis

## Users & scenarios

### Primary Users
- **Architect Agent**: Reads security notes to incorporate security into system design
- **SWE Agent**: Implements security controls based on guidance and reviews
- **Testing Agent**: Uses security checklists to validate security requirements
- **Deployment Agent**: References runbook for secure deployment and secret management
- **Human Security Reviewer**: Reviews security documentation for adequacy
- **Compliance Auditor**: Reviews security controls for regulatory requirements

### Key Scenarios
1. **Architecture Review**: Architect completes architecture.md → Security Agent adds security considerations section
2. **Implementation Review**: SWE implements feature → Security Agent reviews for common vulnerabilities
3. **Secret Management**: Deployable project → Security Agent documents secret handling in runbook.md
4. **CI Security Integration**: New project → Security Agent proposes security checks for CI pipeline
5. **Dependency Security**: New dependencies added → Security Agent scans for known vulnerabilities
6. **Configuration Review**: Authentication/authorization configured → Security Agent validates secure defaults

## Constraints

- Must focus on high-impact, common vulnerabilities (OWASP Top 10 focus)
- Must provide actionable, specific guidance (not generic "be secure" advice)
- Must align with development velocity (security as enabler, not blocker)
- Should prefer simple, proven security controls over complex solutions
- Must check project status.json before starting work
- Should document security tradeoffs when security conflicts with other goals
- Must align with constitution principles (quality from day one, proportional security)
- Should avoid security theater (checks that don't meaningfully improve security)

## Acceptance criteria

- architecture.md includes "Security & privacy notes" section with authentication, authorization, input validation, data protection, and monitoring
- runbook.md (for deployable projects) documents secret management, access controls, and security monitoring procedures
- CI security checks proposed when appropriate (dependency scan, linting, secret detection)
- Common vulnerability categories reviewed: injection, broken access control, cryptographic failures, XSS, CSRF, insecure deserialization
- Security recommendations are specific and actionable (not vague)
- Security controls are proportional to risk (avoid over-engineering)
- Dependency vulnerabilities identified with severity ratings
- Security assumptions documented in decisions.md
- Security validation steps included in acceptance-tests.md
- No hardcoded secrets in source code
- Authentication/authorization patterns clearly documented

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Security Agent provides vague advice, doesn't prevent vulnerabilities | High | Require specific examples; reference OWASP patterns; provide concrete code samples |
| Over-engineering security, slows development velocity | Medium | Focus on high-impact controls; document tradeoffs; align with proportional security principle |
| Security Agent misses vulnerability, reaches production | High | Focus on common issues (OWASP Top 10); supplement with human review for critical systems |
| Security guidance conflicts with functional requirements | Medium | Document tradeoffs; collaborate with Spec/Architect agents; escalate if unresolvable |
| Security documentation becomes stale as code evolves | Medium | Security Agent reviews changes; link security docs to architecture; update during refactoring |
| False positives in security scans waste developer time | Low | Recommend severity thresholds; document known false positives; focus on actionable issues |

## Success metrics

- 100% of projects have "Security & privacy notes" in architecture.md
- 100% of deployable projects document secret management in runbook.md
- OWASP Top 10 categories addressed where relevant (target: 90%+ coverage for web apps)
- No hardcoded secrets in source code (target: 0 incidents)
- Security issues caught before PR merge (target: >80% of common vulnerabilities)
- CI security checks integrated for 100% of production-bound projects
- Dependency vulnerabilities with high/critical severity fixed before deployment (target: 100%)
- Security recommendations adopted by SWE Agent (target: >70%)
- Post-deployment security incidents related to preventable issues (target: <1 per year)
