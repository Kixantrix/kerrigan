# Acceptance tests: Security Agent

## Security Documentation Completeness

- [ ] **Given** architecture.md exists, **When** Security Agent reviews it, **Then** "Security & privacy notes" section is added with all subsections
- [ ] **Given** Security notes section, **When** validating content, **Then** it covers authentication, authorization, input validation, data protection, and monitoring
- [ ] **Given** a deployable project, **When** checking runbook.md, **Then** secret management procedures are documented
- [ ] **Given** runbook.md with secrets section, **When** reviewing, **Then** secret rotation, access controls, and storage mechanisms are specified
- [ ] **Given** security decisions made, **When** documenting, **Then** decisions.md includes security tradeoffs and rationale
- [ ] **Given** acceptance-tests.md, **When** Security Agent contributes, **Then** security validation scenarios are added

## Input Validation & Sanitization

- [ ] **Given** code accepting user input, **When** reviewing, **Then** validation logic is present before processing
- [ ] **Given** file upload functionality, **When** checking, **Then** file type and size restrictions are enforced
- [ ] **Given** user input used in file paths, **When** reviewing, **Then** path traversal prevention (no `../`) is implemented
- [ ] **Given** user input used in shell commands, **When** checking, **Then** command injection prevention is present or flagged
- [ ] **Given** SQL queries, **When** reviewing code, **Then** parameterized queries or ORM are used (no string concatenation)
- [ ] **Given** HTML output, **When** checking, **Then** XSS prevention via escaping or templating is present

## Authentication & Authorization

- [ ] **Given** authentication implementation, **When** reviewing, **Then** password hashing with strong algorithm (bcrypt, argon2) is used
- [ ] **Given** authentication system, **When** checking, **Then** session management includes timeout and secure cookie settings
- [ ] **Given** protected resources, **When** reviewing routes/endpoints, **Then** authentication checks are present before access
- [ ] **Given** sensitive operations, **When** reviewing, **Then** authorization checks verify user permissions
- [ ] **Given** authentication failures, **When** checking logs, **Then** failures are logged without exposing sensitive info
- [ ] **Given** multi-user system, **When** reviewing, **Then** RBAC or equivalent authorization model is implemented

## Data Protection

- [ ] **Given** sensitive data at rest, **When** checking storage, **Then** encryption mechanism is documented in architecture.md
- [ ] **Given** data in transit, **When** reviewing configuration, **Then** TLS/HTTPS is enforced
- [ ] **Given** source code, **When** scanning, **Then** no hardcoded secrets (API keys, passwords, tokens) are present
- [ ] **Given** error messages and logs, **When** reviewing, **Then** sensitive data is not exposed
- [ ] **Given** PII handling, **When** checking documentation, **Then** data retention and deletion policies are defined
- [ ] **Given** secrets needed by application, **When** reviewing, **Then** environment variables or secret manager is used

## Dependencies & Supply Chain

- [ ] **Given** project dependencies, **When** scanning, **Then** known vulnerabilities are identified with severity ratings
- [ ] **Given** high/critical vulnerabilities, **When** reviewing, **Then** updates or mitigations are recommended
- [ ] **Given** new dependencies added, **When** checking, **Then** Security Agent validates necessity and trustworthiness
- [ ] **Given** dependency versions, **When** reviewing, **Then** versions are pinned (not using loose ranges in production)
- [ ] **Given** package managers in use, **When** checking project, **Then** lock files are present and committed

## API Security

- [ ] **Given** public API endpoints, **When** reviewing, **Then** rate limiting is implemented or recommended
- [ ] **Given** CORS configuration, **When** checking, **Then** CORS is not set to wildcard (`*`) in production
- [ ] **Given** API keys in use, **When** reviewing runbook, **Then** key rotation procedures are documented
- [ ] **Given** API error responses, **When** checking, **Then** errors don't leak sensitive system information
- [ ] **Given** RESTful API, **When** reviewing, **Then** appropriate HTTP methods and status codes are used
- [ ] **Given** API authentication, **When** checking, **Then** token expiration and refresh mechanisms are present

## Logging & Monitoring

- [ ] **Given** authentication failures occur, **When** checking logs, **Then** failures are logged with timestamp and context
- [ ] **Given** authorization denials occur, **When** checking logs, **Then** denials are logged for security monitoring
- [ ] **Given** security logs, **When** reviewing, **Then** logs don't contain sensitive data (passwords, tokens, PII)
- [ ] **Given** production environment, **When** checking runbook, **Then** security monitoring and alerting are documented
- [ ] **Given** suspicious patterns defined, **When** reviewing, **Then** anomaly detection or alerting is configured
- [ ] **Given** security incidents, **When** checking procedures, **Then** incident response process is documented in runbook.md

## CI Security Checks

- [ ] **Given** a new project, **When** Security Agent reviews, **Then** dependency scanning is proposed for CI pipeline
- [ ] **Given** CI configuration, **When** checking, **Then** security linting (bandit, eslint-plugin-security) is included where appropriate
- [ ] **Given** repository, **When** reviewing CI, **Then** secret detection tool is recommended or configured
- [ ] **Given** containerized project, **When** checking CI, **Then** container scanning is proposed
- [ ] **Given** CI security checks, **When** reviewing, **Then** severity thresholds are set (block on high/critical)

## Common Vulnerabilities (OWASP Top 10)

- [ ] **Given** web application, **When** reviewing for broken access control, **Then** authorization checks are present on all protected resources
- [ ] **Given** cryptographic operations, **When** checking, **Then** strong algorithms are used (no MD5, SHA1 for passwords)
- [ ] **Given** user input processing, **When** reviewing for injection, **Then** parameterized queries and input validation are present
- [ ] **Given** system design, **When** checking for insecure design, **Then** security controls are documented in architecture
- [ ] **Given** configuration files, **When** reviewing, **Then** default credentials are changed and verbose errors disabled
- [ ] **Given** deserialization, **When** checking code, **Then** untrusted data deserialization is prevented or validated
- [ ] **Given** authentication implementation, **When** reviewing, **Then** weak password policies and broken session management are flagged
- [ ] **Given** SSRF potential, **When** reviewing server-side requests, **Then** URL validation and allowlisting are present

## Status and Workflow

- [ ] **Given** project with status.json, **When** Security Agent starts work, **Then** agent checks status is "active" or file doesn't exist
- [ ] **Given** status.json shows "blocked", **When** Security Agent starts work, **Then** agent stops and reports blocked_reason
- [ ] **Given** status.json shows "on-hold", **When** Security Agent starts work, **Then** agent stops without proceeding
- [ ] **Given** architecture.md complete, **When** Security Agent reviews, **Then** security section is added before implementation begins

## Integration with Other Agents

- [ ] **Given** Architect Agent creates architecture.md, **When** Security Agent reviews, **Then** security notes are added for Architect to incorporate
- [ ] **Given** SWE Agent implements features, **When** Security Agent reviews code, **Then** specific vulnerabilities are flagged with fix suggestions
- [ ] **Given** Testing Agent creates tests, **When** Security Agent reviews, **Then** security test cases are suggested (negative tests, malicious inputs)
- [ ] **Given** Deployment Agent prepares deployment, **When** Security Agent reviews, **Then** secure deployment practices are validated

## Edge Cases

- [ ] **Given** legacy code without security controls, **When** reviewing, **Then** Security Agent prioritizes high-risk areas for remediation
- [ ] **Given** conflicting security requirements, **When** documenting, **Then** tradeoffs are clearly explained in decisions.md
- [ ] **Given** prototype or demo project, **When** reviewing, **Then** Security Agent documents security shortcuts and risks
- [ ] **Given** third-party authentication (OAuth), **When** reviewing, **Then** proper token handling and validation are verified
- [ ] **Given** security false positive, **When** identified, **Then** Security Agent documents reasoning for dismissal
- [ ] **Given** intentional security tradeoff, **When** documenting, **Then** justification and mitigation plans are recorded

## Security Review Quality

- [ ] **Given** security recommendations, **When** reviewing, **Then** recommendations are specific with code examples or links
- [ ] **Given** vulnerability identified, **When** documenting, **Then** severity, impact, and remediation steps are provided
- [ ] **Given** security best practices, **When** applying, **Then** recommendations are proportional to project risk level
- [ ] **Given** security documentation, **When** reviewing, **Then** documentation is actionable and not generic advice
- [ ] **Given** security checklist, **When** validating, **Then** all relevant OWASP Top 10 categories are addressed

## Validation

- [ ] **Given** architecture.md with security notes, **When** running validators, **Then** "Security & privacy notes" section heading is exact (case-sensitive, with "&")
- [ ] **Given** security recommendations, **When** human reviews, **Then** recommendations are clear, actionable, and justified
- [ ] **Given** security controls documented, **When** SWE implements, **Then** documentation is sufficient to implement correctly
