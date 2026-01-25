# Security Policy

## Reporting Security Vulnerabilities

We take the security of Kerrigan seriously. If you discover a security vulnerability, please follow these steps:

### 🔒 Private Disclosure

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues privately using one of these methods:

1. **GitHub Security Advisories** (Preferred)
   - Navigate to the [Security tab](https://github.com/Kixantrix/kerrigan/security/advisories)
   - Click "Report a vulnerability"
   - Provide detailed information about the vulnerability

2. **Email**
   - Send details to the repository maintainers via GitHub
   - Include "SECURITY" in the subject line
   - Provide as much detail as possible about the vulnerability

### 📋 What to Include

When reporting a vulnerability, please include:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and attack scenarios
- **Reproduction**: Step-by-step instructions to reproduce the issue
- **Environment**: Affected versions, configurations, or environments
- **Proof of Concept**: Code or commands demonstrating the vulnerability (if applicable)
- **Suggested Fix**: Any ideas for addressing the issue (optional)

### ⏱️ Response Timeline

- **Acknowledgment**: Within 48 hours of report
- **Initial Assessment**: Within 7 days
- **Status Updates**: Regular updates on progress
- **Resolution**: Security patches released as quickly as possible

### 🛡️ Scope

This security policy applies to:

- **Core Framework**: All code in `.github/agents/`, `tools/`, and workflow configurations
- **Documentation**: Security-relevant documentation and setup guides
- **Dependencies**: Known vulnerabilities in project dependencies
- **Examples**: Security issues in example projects that could be replicated

### ⚠️ Out of Scope

The following are typically considered out of scope:

- Vulnerabilities in third-party dependencies (report to the respective projects)
- Social engineering attacks
- Physical attacks
- Issues in forked or customized versions not maintained by this project
- Issues requiring unlikely user interaction or configuration

### 🔐 Security Best Practices

When using Kerrigan:

1. **Secrets Management**
   - Never commit secrets, API keys, or credentials to the repository
   - Use GitHub Secrets for sensitive workflow configuration
   - Enable secret scanning and push protection (see below)

2. **Workflow Security**
   - Review workflow permissions regularly
   - Use principle of least privilege for `GITHUB_TOKEN`
   - Pin action versions to specific commits or tags
   - Be cautious with `pull_request_target` triggers

3. **Dependencies**
   - Keep dependencies up to date
   - Enable Dependabot security updates
   - Review security advisories for dependencies
   - Use lock files for reproducible builds

4. **Agent Prompts**
   - Review agent-generated code before merging
   - Validate inputs and sanitize outputs
   - Apply security linters and scanners
   - Follow secure coding practices

### 🔧 Recommended Repository Settings

For repositories using Kerrigan, we recommend enabling these GitHub security features:

1. **Secret Scanning**: Settings → Code security and analysis → Secret scanning
2. **Push Protection**: Settings → Code security and analysis → Push protection
3. **Dependabot Alerts**: Settings → Code security and analysis → Dependabot alerts
4. **Dependabot Security Updates**: Settings → Code security and analysis → Dependabot security updates
5. **Branch Protection**: Settings → Branches → Add protection rule for `main`
   - Require pull request reviews
   - Require status checks to pass (CI, Agent Gates)
   - Restrict who can push to matching branches

### 📚 Additional Resources

- [GitHub Security Best Practices](https://docs.github.com/en/code-security/getting-started/securing-your-repository)
- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

### 🤝 Acknowledgments

We appreciate the security research community's efforts in responsibly disclosing vulnerabilities. Contributors who report valid security issues will be acknowledged in our security advisories (with their permission).

---

**Thank you for helping keep Kerrigan and its users safe!**
