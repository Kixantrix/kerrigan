# Architecture: Security Agent

## Overview

The Security Agent operates as a security reviewer and advisor that integrates lightweight security analysis throughout the development lifecycle. Unlike traditional security audits that happen at project completion, this agent embeds security considerations from architecture through implementation, focusing on preventing common, high-impact vulnerabilities aligned with OWASP Top 10 and industry best practices.

The agent operates in two primary modes: **documentation mode** (adding security sections to architecture and runbook artifacts) and **review mode** (analyzing code, configuration, and dependencies for vulnerabilities). It emphasizes actionable, specific guidance over generic security advice, and balances security rigor with development velocity through proportional security controls.

The Security Agent follows a "shift-left" philosophy: catching security issues early when they're cheapest to fix, rather than discovering them in production. It acts as a security conscience for the development workflow, ensuring security is considered at each phase without becoming a bottleneck.

## Components & interfaces

### Input Sources
- **architecture.md**: System design to review for security implications
- **spec.md**: Requirements to identify security-relevant features
- **runbook.md**: Operational procedures to validate secret management
- **Source code**: Implementation to review for vulnerabilities
- **Dependencies**: Package manifests to scan for known vulnerabilities
- **Configuration files**: Settings to validate secure defaults
- **status.json**: Workflow control (agent must check before proceeding)
- **OWASP Top 10**: Reference framework for common vulnerabilities
- **CVE databases**: Known vulnerability information for dependencies

### Core Analysis Components

**Architecture Security Analyzer**
- Reviews system architecture for security implications
- Identifies authentication and authorization boundaries
- Evaluates data protection mechanisms
- Assesses API security design
- Produces "Security & privacy notes" section for architecture.md
- Documents security assumptions and constraints

**Code Vulnerability Scanner**
- Analyzes source code for common vulnerability patterns
- Checks input validation and sanitization
- Identifies injection vulnerabilities (SQL, command, XSS)
- Validates authentication and authorization implementation
- Detects hardcoded secrets and sensitive data exposure
- Reviews error handling and logging for information leakage

**Dependency Security Checker**
- Scans dependency manifests for known vulnerabilities
- Queries vulnerability databases (npm audit, pip-audit, Snyk, etc.)
- Prioritizes vulnerabilities by severity (critical, high, medium, low)
- Recommends updates or mitigations
- Validates dependency sources and licensing

**Configuration Security Validator**
- Reviews security-relevant configuration
- Checks TLS/HTTPS enforcement
- Validates CORS settings (no wildcard in production)
- Reviews authentication middleware setup
- Checks session management configuration
- Validates security headers (CSP, X-Frame-Options, etc.)

**Secret Management Advisor**
- Identifies secrets in code (API keys, passwords, tokens)
- Documents secret management approach in runbook.md
- Recommends secret storage mechanisms (environment variables, secret managers)
- Defines secret rotation procedures
- Validates access controls for secrets

**Security Documentation Generator**
- Produces "Security & privacy notes" section for architecture.md
- Documents authentication and authorization patterns
- Describes input validation strategies
- Explains data protection mechanisms
- Outlines monitoring and alerting approach
- Updates runbook.md with secret management procedures

**CI Security Integration Advisor**
- Proposes security checks for CI pipeline
- Recommends dependency scanning tools
- Suggests static analysis security testing (SAST)
- Proposes secret detection in commits
- Recommends container scanning for containerized apps
- Defines severity thresholds for CI failures

**Security Checklist Generator**
- Creates security validation scenarios for acceptance-tests.md
- Generates negative test cases (malicious inputs, unauthorized access)
- Documents security assumptions for testing
- Produces security review checklists for manual validation

### Output Artifacts
- **architecture.md updates**: "Security & privacy notes" section added
- **runbook.md updates**: Secret management and security monitoring sections
- **CI configuration proposals**: Security check recommendations
- **decisions.md updates**: Security tradeoffs and rationale
- **Code review comments**: Specific vulnerability findings with remediation guidance
- **Dependency security report**: Vulnerability scan results with priorities
- **Security test scenarios**: Additions to acceptance-tests.md

### Validation Interface
- Security recommendations must be:
  - Specific and actionable (not generic "be secure")
  - Proportional to risk (avoid security theater)
  - Aligned with OWASP Top 10 where applicable
  - Implementable by SWE Agent with provided guidance
  - Documented with rationale and alternatives considered

## Data flow (conceptual)

```
[Project Artifacts: architecture.md, spec.md, runbook.md]
        ↓
[Status Check] → (if blocked) → [Stop & Report]
        ↓
[Architecture Security Analyzer]
        ↓
[Identify Security Domains]:
  - Authentication/Authorization
  - Input Validation
  - Data Protection
  - API Security
  - Monitoring
        ↓
[Generate Security Notes for architecture.md]
        ↓
[Source Code Available?] ─No→ [Documentation Mode Only]
        ↓Yes
[Code Vulnerability Scanner]
        ↓
[Check OWASP Top 10 Categories]:
  - Broken Access Control
  - Cryptographic Failures
  - Injection
  - Insecure Design
  - Security Misconfiguration
  - Vulnerable Components
  - Authentication Failures
  - Data Integrity Failures
  - Logging Failures
  - SSRF
        ↓
[Dependency Security Checker]
        ↓
[Scan Dependencies] → [Vulnerability Database]
        ↓
[Configuration Security Validator]
        ↓
[Review Security Settings]
        ↓
[Secret Management Advisor]
        ↓
[Deployable?] ─No→ [Skip runbook updates]
        ↓Yes
[Document Secret Management in runbook.md]
        ↓
[CI Security Integration Advisor]
        ↓
[Propose Security Checks for CI]
        ↓
[Generate Security Findings Report]:
  - Architecture recommendations
  - Code vulnerabilities
  - Dependency issues
  - Configuration gaps
  - CI recommendations
        ↓
[Update Artifacts & Provide Guidance]
        ↓
[Available for SWE Agent to remediate]
```

## Tradeoffs

### Comprehensive Security Audit vs. Lightweight Review
**Decision**: Focus on high-impact, common vulnerabilities (OWASP Top 10) rather than exhaustive analysis
- **Pro**: Faster feedback cycle; doesn't block development; catches 80% of issues with 20% effort
- **Con**: May miss sophisticated or domain-specific vulnerabilities
- **Mitigation**: Document when deeper security review is needed; escalate critical systems to human security specialists
- **Rationale**: Align with "proportional security" principle; most projects benefit more from preventing common issues than detecting rare edge cases

### Automated Scanning vs. Manual Code Review
**Decision**: Use automated tools for known patterns, manual review for context-dependent issues
- **Pro**: Automated scanning is fast and consistent; manual review catches logic flaws
- **Con**: Automated tools have false positives; manual review doesn't scale
- **Mitigation**: Combine both approaches; use automation for CWE/CVE detection, manual review for business logic security
- **Rationale**: Leverage tools for efficiency, apply agent intelligence where context matters

### Security at Design Time vs. Implementation Time
**Decision**: Embed security at both phases (architecture review + code review)
- **Pro**: Design-time security is cheaper to fix; implementation review catches mistakes
- **Con**: More touch-points in workflow; requires coordination between agents
- **Mitigation**: Clear handoffs between Architect and Security agents; SWE agent references security notes during implementation
- **Rationale**: "Shift-left" principle: earlier detection = lower cost; defense in depth

### Strict Security Enforcement vs. Developer Flexibility
**Decision**: Provide guidance and recommendations, not absolute mandates; document tradeoffs
- **Pro**: Enables informed risk decisions; doesn't block reasonable tradeoffs
- **Con**: Developers might ignore recommendations; security gaps may persist
- **Mitigation**: Categorize by severity; require acknowledgment for high/critical issues; escalate when necessary
- **Rationale**: Security must enable development, not obstruct it; trust developers with context

### Generic Security Advice vs. Specific Guidance
**Decision**: Provide specific, actionable recommendations with code examples and references
- **Pro**: Easier for SWE Agent to implement; higher adoption rate; educational value
- **Con**: Takes more effort to generate; may not cover all scenarios
- **Mitigation**: Link to detailed security guides for deep dives; provide examples and templates
- **Rationale**: Vague advice is ignored; specific guidance drives action

### All-or-Nothing Security vs. Incremental Hardening
**Decision**: Prioritize security improvements by risk; allow incremental hardening over time
- **Pro**: Enables progress on high-priority items; doesn't overwhelm developers
- **Con**: Some vulnerabilities may persist longer
- **Mitigation**: Clearly document security debt; track remediation progress; enforce minimums for critical issues
- **Rationale**: Pragmatic security improves more projects than perfect security for few

## Security & privacy notes

### Agent's Own Security Considerations

**Input Validation**
- Security Agent processes untrusted code and configuration
- Must avoid executing arbitrary code during analysis
- Uses static analysis tools and pattern matching (no eval/exec of scanned code)
- Sandboxed execution if dynamic analysis needed

**Data Handling**
- Security findings may contain sensitive information (vulnerability details, system design)
- Findings stored in project artifacts (follow repository access controls)
- Does not transmit security findings to external services without explicit approval
- Avoids including sensitive data in security documentation (no credentials, PII)

**Vulnerability Disclosure**
- Detailed vulnerability information documented in private channels (not public issues)
- Public documentation focuses on mitigations, not exploit techniques
- Critical vulnerabilities flagged for immediate attention and private handling

**False Positives**
- Security Agent may flag legitimate code as vulnerable (context-dependent)
- Provides rationale for findings to enable informed decisions
- Documents false positive patterns to improve future accuracy

**Dependency on External Services**
- Vulnerability databases (CVE, npm audit) are external dependencies
- Network required for real-time scanning (may fail in offline environments)
- Fallback to local vulnerability databases or delayed scanning

### Security Agent's Role in Project Security

**Authentication/Authorization**
- Security Agent does not implement authentication; reviews implementations by SWE Agent
- Validates that authentication is required for protected resources
- Checks that authorization is enforced before sensitive operations

**Secrets Management**
- Security Agent detects hardcoded secrets but does not store or manage secrets
- Documents secret management procedures in runbook.md
- References project-specific secret management solutions (AWS Secrets Manager, Vault, etc.)

**Compliance**
- Security Agent identifies common security controls relevant to compliance (GDPR, HIPAA, PCI)
- Does not provide legal compliance advice (requires legal/compliance team)
- Documents security controls that support compliance requirements

**Incident Response**
- Security Agent is preventive, not reactive (not an incident response tool)
- Documents security monitoring and alerting in runbook.md for incident detection
- Provides guidance on logging security events for forensic analysis
