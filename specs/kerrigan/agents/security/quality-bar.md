# Quality Bar: Security Agent

## Definition of Done

A security review is "done" when:
- [ ] architecture.md includes "Security & privacy notes" section with all relevant subsections
- [ ] Security notes cover: authentication, authorization, input validation, data protection, monitoring
- [ ] runbook.md (for deployable projects) documents secret management and access controls
- [ ] OWASP Top 10 categories reviewed where applicable to project type
- [ ] Source code reviewed for common vulnerability patterns
- [ ] Dependencies scanned for known vulnerabilities with severity ratings
- [ ] High/critical vulnerabilities flagged with specific remediation guidance
- [ ] Configuration validated for secure defaults (TLS, CORS, session management)
- [ ] No hardcoded secrets detected in source code
- [ ] CI security checks proposed when appropriate (dependency scan, linting, secret detection)
- [ ] Security recommendations are specific and actionable (not generic)
- [ ] Security tradeoffs documented in decisions.md where applicable
- [ ] Security validation scenarios added to acceptance-tests.md
- [ ] status.json was checked before starting work

## Structural Standards

### Required Security Documentation

**architecture.md - Security & privacy notes section**:
- `### Authentication` – How users/systems authenticate (JWT, OAuth, API keys)
- `### Authorization` – How access control is enforced (RBAC, ABAC, ownership)
- `### Input Validation` – How input is validated and sanitized
- `### Data Protection` – Encryption at rest/transit, secret management, data retention
- `### Monitoring` – Security logging, alerting, anomaly detection

**runbook.md - Security sections** (deployable projects):
- `## Secret Management` – How secrets are stored, accessed, rotated
- `## Access Controls` – Who has access to what resources and how
- `## Security Monitoring` – What security events are logged and alerted
- `## Incident Response` – Basic security incident procedures

**decisions.md - Security decisions**:
- Document security tradeoffs (performance vs. security, usability vs. security)
- Include rationale for security choices (algorithm selection, control mechanisms)
- Note when security review identified risks that were accepted

**acceptance-tests.md - Security test scenarios**:
- Negative test cases (malicious input, unauthorized access)
- Security validation checks (authentication required, authorization enforced)
- Edge cases relevant to security (empty input, special characters, large payloads)

## Content Quality Standards

### Good vs. Bad Security Documentation

#### Authentication Documentation
✅ **Good** (specific and actionable):
```markdown
### Authentication
- JWT tokens with 1-hour expiration, refresh tokens with 7-day expiration
- Tokens signed with HS256, secret stored in environment variable JWT_SECRET
- Passwords hashed with bcrypt (cost factor 12)
- Failed login attempts rate-limited to 5 per minute per IP
- Session tokens stored in httpOnly cookies with secure and sameSite=strict flags
```

❌ **Bad** (vague):
```markdown
### Authentication
- Uses JWT for authentication
- Passwords are hashed
- Rate limiting is implemented
```

#### Authorization Documentation
✅ **Good** (specific and actionable):
```markdown
### Authorization
- Role-based access control with roles: admin, user, guest
- Roles stored in JWT payload and validated on each request
- Middleware checks role before allowing access to protected routes
- Database queries filter results by user ownership (user_id field)
- Admin-only endpoints: POST /api/users, DELETE /api/users/:id
```

❌ **Bad** (vague):
```markdown
### Authorization
- Users have different permissions based on roles
- Authorization is checked before sensitive operations
```

#### Input Validation Documentation
✅ **Good** (specific and actionable):
```markdown
### Input Validation
- All API endpoints validate input against JSON schemas using Joi
- File uploads restricted to: max 5MB, types: .jpg, .png, .pdf
- Filename sanitization: strip path separators and null bytes
- SQL injection prevented via parameterized queries (Knex.js)
- XSS prevention: Output escaped using DOMPurify for user-generated content
- Command injection: No shell commands executed with user input
```

❌ **Bad** (vague):
```markdown
### Input Validation
- All inputs are validated
- File uploads are restricted
- SQL injection and XSS are prevented
```

#### Data Protection Documentation
✅ **Good** (specific and actionable):
```markdown
### Data Protection
- All communication over HTTPS (TLS 1.3, certificate from Let's Encrypt)
- Database credentials stored in AWS Secrets Manager, rotated every 90 days
- PII fields (email, phone) encrypted at rest with AES-256-GCM
- Encryption keys stored in environment variables, rotated annually
- Personal data retention: 90 days after account deletion
- Audit logs retained for 1 year for compliance
```

❌ **Bad** (vague):
```markdown
### Data Protection
- Data encrypted in transit and at rest
- Secrets not hardcoded
- PII handled securely
```

### Good vs. Bad Code Review Comments

#### Specific Vulnerability Finding
✅ **Good** (specific with remediation):
```markdown
**SQL Injection Vulnerability** (HIGH)
Location: src/api/users.js:42
Issue: User input directly concatenated into SQL query
```javascript
const query = `SELECT * FROM users WHERE email = '${req.body.email}'`;
```
Remediation: Use parameterized queries
```javascript
const query = db('users').where('email', req.body.email);
```
Reference: OWASP SQL Injection Prevention Cheat Sheet
```

❌ **Bad** (vague):
```markdown
Security issue found in users.js. SQL injection possible. Use parameterized queries.
```

#### Configuration Issue
✅ **Good** (specific with fix):
```markdown
**CORS Misconfiguration** (MEDIUM)
Location: src/server.js:15
Issue: CORS allows all origins in production
```javascript
app.use(cors({ origin: '*' }));
```
Remediation: Specify allowed origins
```javascript
app.use(cors({ 
  origin: process.env.ALLOWED_ORIGINS?.split(',') || 'http://localhost:3000' 
}));
```
Impact: Any website can make authenticated requests to this API
```

❌ **Bad** (vague):
```markdown
CORS is not configured correctly. Fix the origin setting.
```

#### Hardcoded Secret Detection
✅ **Good** (specific with guidance):
```markdown
**Hardcoded Secret** (CRITICAL)
Location: src/config/database.js:8
Issue: Database password hardcoded in source
```javascript
const password = 'MySuperSecretPassword123';
```
Remediation:
1. Remove hardcoded password from code
2. Store in environment variable
```javascript
const password = process.env.DB_PASSWORD;
```
3. Update .env.example with placeholder
4. Document in runbook.md how to set DB_PASSWORD
5. Rotate database password immediately (assume compromised)
```

❌ **Bad** (vague):
```markdown
Password hardcoded. Use environment variables instead.
```

### Good vs. Bad Security Recommendations

#### CI Security Check Proposal
✅ **Good** (specific with implementation):
```markdown
## Recommended CI Security Checks

### Dependency Scanning
Add to .github/workflows/security.yml:
```yaml
- name: Scan dependencies
  run: npm audit --audit-level=high
```
Fails build on high or critical vulnerabilities

### Secret Detection
Add pre-commit hook or CI check:
```yaml
- name: Detect secrets
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
```
Prevents commits with secrets from reaching repository
```

❌ **Bad** (vague):
```markdown
## Security Recommendations
- Add dependency scanning to CI
- Scan for secrets before committing
```

### Good vs. Bad Dependency Vulnerability Reports

✅ **Good** (prioritized with context):
```markdown
## Dependency Vulnerabilities Found

### Critical (1)
- **lodash@4.17.15** - Prototype Pollution (CVE-2020-8203)
  - Severity: Critical (CVSS 9.1)
  - Affected: All versions < 4.17.21
  - Remediation: Update to lodash@4.17.21 or higher
  - Impact: Remote code execution possible via malicious input
  - Action: Update immediately before deployment

### High (2)
- **axios@0.19.0** - SSRF (CVE-2021-3749)
  - Severity: High (CVSS 7.5)
  - Affected: < 0.21.2
  - Remediation: Update to axios@0.21.2+
  - Impact: Server-side request forgery via redirect handling
  - Action: Update in next sprint

- **jsonwebtoken@8.5.0** - Signature Verification Bypass (CVE-2022-23529)
  - Severity: High (CVSS 7.6)
  - Affected: < 9.0.0
  - Remediation: Update to jsonwebtoken@9.0.0+
  - Impact: Attacker can forge valid tokens
  - Action: Update immediately (authentication bypass)

### Medium (5)
- See full report for details, plan for remediation in next security review
```

❌ **Bad** (no prioritization or guidance):
```markdown
## Vulnerabilities
- lodash has vulnerability
- axios has vulnerability
- jsonwebtoken has vulnerability
- 5 medium severity issues

Please update dependencies.
```

## Common Mistakes to Avoid

### Documentation Mistakes
- ❌ Using "Security and Privacy" instead of "Security & privacy notes" (artifact contract violation)
- ❌ Generic security advice ("be secure", "validate input") without specifics
- ❌ Missing security section in architecture.md for projects with authentication
- ❌ Forgetting to document secret management in runbook.md for deployable projects
- ❌ Not documenting security tradeoffs when security conflicts with other goals

### Review Mistakes
- ❌ Flagging every minor issue without severity prioritization
- ❌ Providing vulnerability findings without remediation guidance
- ❌ Over-focusing on theoretical vulnerabilities that don't apply to the project
- ❌ Recommending complex security controls disproportionate to risk
- ❌ Missing obvious issues (hardcoded secrets, SQL injection) while focusing on edge cases

### Process Mistakes
- ❌ Starting work when status.json shows "blocked" or "on-hold"
- ❌ Blocking development for low-severity issues
- ❌ Not checking if codebase is deployable before requiring runbook updates
- ❌ Recommending security controls already implemented
- ❌ Not documenting false positives when dismissing security scan findings

### Code Analysis Mistakes
- ❌ Flagging test code for security issues (tests often use intentionally insecure patterns)
- ❌ Missing context (flagging parameterized query as SQL injection)
- ❌ Not considering defense-in-depth (multiple layers of security)
- ❌ Ignoring error handling (errors can leak sensitive information)
- ❌ Not checking for logging of sensitive data (passwords, tokens in logs)

## Validation Checklist

Before considering security review complete:

### Documentation
- [ ] architecture.md has "Security & privacy notes" section (exact heading, case-sensitive)
- [ ] Security notes cover all relevant areas: auth, authz, input validation, data protection, monitoring
- [ ] runbook.md documents secret management (if deployable)
- [ ] runbook.md documents security monitoring and alerting (if deployable)
- [ ] decisions.md updated with security tradeoffs (if applicable)
- [ ] acceptance-tests.md includes security validation scenarios

### OWASP Top 10 Coverage (Web Applications)
- [ ] Broken Access Control - authorization checks reviewed
- [ ] Cryptographic Failures - encryption and hashing reviewed
- [ ] Injection - input validation and sanitization reviewed
- [ ] Insecure Design - security controls documented in architecture
- [ ] Security Misconfiguration - defaults and configuration reviewed
- [ ] Vulnerable Components - dependencies scanned
- [ ] Authentication Failures - auth implementation reviewed
- [ ] Data Integrity Failures - serialization and signatures reviewed
- [ ] Logging Failures - security logging and monitoring reviewed
- [ ] SSRF - server-side request handling reviewed (if applicable)

### Code Review
- [ ] Input validation present for all user inputs
- [ ] SQL queries use parameterized queries or ORM (no string concatenation)
- [ ] HTML output escaped or uses safe templating (XSS prevention)
- [ ] No hardcoded secrets detected
- [ ] Authentication required for protected resources
- [ ] Authorization checks before sensitive operations
- [ ] Error messages don't leak sensitive information
- [ ] Logs don't contain passwords, tokens, or PII

### Dependencies
- [ ] Dependencies scanned for known vulnerabilities
- [ ] High/critical vulnerabilities identified and flagged
- [ ] Remediation guidance provided for each critical vulnerability
- [ ] Dependency versions pinned (lock files present)

### Configuration
- [ ] TLS/HTTPS enforced for production
- [ ] CORS not set to wildcard in production
- [ ] Session management secure (timeout, secure cookies)
- [ ] Security headers recommended (CSP, X-Frame-Options, etc.)
- [ ] Rate limiting implemented or recommended for public APIs

### CI Integration
- [ ] Dependency scanning proposed for CI pipeline
- [ ] Security linting recommended where appropriate
- [ ] Secret detection recommended
- [ ] Severity thresholds defined (fail build on high/critical)

### Quality
- [ ] All recommendations are specific and actionable
- [ ] Vulnerability findings include severity, impact, and remediation
- [ ] Security controls are proportional to project risk
- [ ] No security theater (checks that don't meaningfully improve security)
- [ ] False positives documented when dismissed

## Review Standards

### Self-Review
Before completing security review, agent should:
1. Verify all OWASP Top 10 categories reviewed where relevant
2. Confirm all recommendations are specific with examples or code
3. Check that severity ratings are appropriate (critical/high/medium/low)
4. Validate that documentation is actionable by SWE Agent
5. Ensure security controls are proportional to risk
6. Review for false positives and document reasoning if dismissed

### Human Security Review (Critical Systems)
For high-risk systems, human security specialist should validate:
- Threat model is appropriate for system and data sensitivity
- Security controls are sufficient for compliance requirements
- Architecture security notes cover all relevant attack vectors
- Dependency vulnerabilities are addressed appropriately
- Security recommendations are technically sound and current

### Handoff Readiness
Security review is ready for handoff when:
- [ ] SWE Agent can implement security controls from guidance provided
- [ ] Testing Agent can create security test cases from scenarios provided
- [ ] Deployment Agent can configure secure deployment from runbook
- [ ] Human reviewer can validate security adequacy for risk level

## Examples

### Complete Security Documentation (Web API)

```markdown
## Security & privacy notes

### Authentication
- JWT tokens with 1-hour expiration, refresh tokens with 7-day expiration
- Tokens signed with HS256, secret in environment variable JWT_SECRET (min 256 bits)
- Passwords hashed with bcrypt (cost factor 12)
- Failed login attempts rate-limited to 5 per minute per IP address
- Account lockout after 10 failed attempts in 15 minutes
- Session tokens in httpOnly cookies with secure and sameSite=strict

### Authorization
- Role-based access control: admin, user, guest
- Roles stored in JWT payload, validated on each request via middleware
- Admin endpoints: POST/DELETE /api/users, GET /api/admin/*
- Users can only access/modify their own resources (user_id check in queries)
- API key authentication for service-to-service calls (stored in API_KEYS env var)

### Input Validation
- All endpoints validate input with Joi schemas before processing
- File uploads: max 5MB, types restricted to .jpg/.png/.pdf
- Filename sanitization: strip path separators, null bytes, control characters
- SQL injection prevented via Knex.js parameterized queries (no raw SQL)
- XSS prevention: DOMPurify sanitizes user-generated HTML content
- No shell command execution with user input (command injection prevention)
- Path traversal prevented: reject any input containing ../

### Data Protection
- All communication over HTTPS (TLS 1.3, certificates from Let's Encrypt)
- Database credentials in AWS Secrets Manager, rotated every 90 days
- PII fields (email, phone, address) encrypted at rest with AES-256-GCM
- Encryption keys stored in environment variable, rotated annually
- Personal data retention: deleted 90 days after account deletion
- Audit logs retained for 1 year for compliance (PCI-DSS)
- No sensitive data in error messages or logs

### Monitoring
- Failed authentication attempts logged with timestamp, IP, username
- Authorization denials logged with user ID, resource, action attempted
- Anomaly detection: alert on >10 failed logins per minute per IP
- Security events sent to CloudWatch with alerts to security team
- Logs don't contain passwords, tokens, PII (only hashed/redacted values)
- Rate limit breaches logged and temporarily block IP
```

### Security Vulnerability Finding Report

```markdown
## Security Review Findings - User Registration API

### Critical Issues (1)

**C1: SQL Injection in User Search**
- Location: `src/api/users.js:87`
- Severity: Critical (CVSS 9.8)
- Issue: User input concatenated directly into SQL query
```javascript
const searchQuery = `SELECT * FROM users WHERE username LIKE '%${req.query.search}%'`;
db.raw(searchQuery);
```
- Impact: Attacker can read/modify entire database
- Remediation:
```javascript
db('users').where('username', 'like', `%${req.query.search}%`);
```
- Status: Must fix before deployment

### High Issues (2)

**H1: Hardcoded Database Password**
- Location: `src/config/db.js:12`
- Severity: High (exposed secret)
- Remediation: Move to environment variable, rotate password
- Status: Fix immediately

**H2: Missing Authorization Check**
- Location: `src/api/users.js:45` - DELETE /api/users/:id
- Severity: High (any user can delete any account)
- Remediation: Add authorization middleware to verify admin role or ownership
- Status: Fix before deployment

### Medium Issues (3)

**M1: Weak Password Requirements**
- Location: `src/auth/validation.js:22`
- Current: Min 6 characters
- Recommended: Min 8 characters, require uppercase/lowercase/number
- Status: Fix in next sprint

**M2: Missing Rate Limiting**
- Location: POST /api/auth/login
- Issue: No rate limiting on login endpoint (brute force possible)
- Remediation: Add express-rate-limit middleware (5 attempts per minute)
- Status: Fix in next sprint

**M3: CORS Allows All Origins**
- Location: `src/server.js:18`
- Issue: `cors({ origin: '*' })` in production
- Remediation: Specify allowed origins from environment variable
- Status: Fix before production deployment

### Low/Info (2)
- Session timeout not configured (recommend 30 minutes)
- Missing security headers (recommend helmet.js)
```

## Continuous Improvement

The Security Agent role should evolve based on:
- Post-deployment security incidents (what was missed?)
- Emerging vulnerability patterns (new OWASP entries, CVEs)
- False positive/negative rates from automated scans
- Feedback from SWE Agent on actionability of recommendations
- Changes in security landscape and best practices
- Technology-specific security patterns (framework updates)

Changes to this quality bar should be proposed via:
1. Issue documenting security gap or improvement opportunity
2. Example of current vs. improved security guidance
3. Update to this quality-bar.md
4. Update to role.security.md agent prompt
5. Validation that change improves security without creating false noise
