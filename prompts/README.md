# Kerrigan Prompt Library

This directory contains reusable, versioned agent prompts that can be loaded via URL instead of copied inline into GitHub issues.

## Available Prompts

### Core Workflow Prompts

| Prompt | Version | Purpose | Context Required | Variables |
|--------|---------|---------|------------------|-----------|
| [kickoff-spec.md](./kickoff-spec.md) | 1.0.0 | Initial project specification | constitution.md | PROJECT_NAME, REPO_NAME |
| [architecture-design.md](./architecture-design.md) | 1.0.0 | Technical architecture design | spec.md, constitution.md | PROJECT_NAME, REPO_NAME |
| [implementation-swe.md](./implementation-swe.md) | 1.0.0 | Feature implementation | spec.md, architecture.md, plan.md, tasks.md | PROJECT_NAME, REPO_NAME, TASK_ID |
| [security-review.md](./security-review.md) | 1.0.0 | Security assessment | spec.md, architecture.md, code | PROJECT_NAME, REPO_NAME |
| [deployment-ops.md](./deployment-ops.md) | 1.0.0 | Deployment execution | spec.md, architecture.md, runbook.md | PROJECT_NAME, REPO_NAME, ENVIRONMENT |
| [triage-analysis.md](./triage-analysis.md) | 1.0.0 | Issue triage and classification | issue description | PROJECT_NAME, REPO_NAME, ISSUE_NUMBER |

## Quick Start

### Using prompts in GitHub issues

Instead of copying full prompts inline, reference them by URL:

```markdown
@role.spec

Prompt: gh://Kixantrix/kerrigan/prompts/kickoff-spec.md

Project: my-awesome-app

Context:
- Building internal developer tooling
- Target audience: 50+ engineers
```

### Using prompts with CLI (future)

```bash
# Fetch and use prompt
kerrigan invoke spec --prompt-url gh://Kixantrix/kerrigan/prompts/kickoff-spec.md

# With custom variables
kerrigan invoke swe \
  --prompt-url gh://Kixantrix/kerrigan/prompts/implementation-swe.md \
  --var PROJECT_NAME=my-app \
  --var TASK_ID=implement-api-endpoint
```

## Prompt File Format

Each prompt follows this structure:

```markdown
---
prompt-version: 1.0.0
required-context:
  - constitution.md
  - spec.md
variables:
  - PROJECT_NAME
  - REPO_NAME
tags:
  - specification
  - planning
author: kerrigan-maintainers
min-context-window: 8000
---

# Prompt Title

[Prompt content with {VARIABLES} for substitution]
```

### Frontmatter Fields

- **prompt-version** (string): Semantic version (e.g., "1.0.0")
- **required-context** (array): Files needed before using this prompt
- **variables** (array): Variables expected for substitution
- **tags** (array): Categories for prompt discovery
- **author** (string): Contact for questions
- **min-context-window** (integer): Minimum context window size in tokens
- **deprecated** (boolean): Whether prompt is deprecated
- **replacement-url** (string): URL of replacement if deprecated

## URL Schemes

### GitHub Shorthand (Recommended)

```
gh://Kixantrix/kerrigan/prompts/kickoff-spec.md
gh://org/repo/prompts/custom-prompt.md@v1.0.0
```

Expands to raw GitHub URLs automatically.

### Direct HTTPS

```
https://raw.githubusercontent.com/Kixantrix/kerrigan/main/prompts/kickoff-spec.md
```

Use for non-GitHub hosted prompts or CDN-hosted libraries.

### Local File (Development)

```
file:///home/user/kerrigan/prompts/kickoff-spec.md
```

Use for testing new prompts before committing.

## Variable Substitution

Prompts support variables in `{VARIABLE_NAME}` format:

### Built-in Variables

Always available:
- `{PROJECT_NAME}` - Current project name
- `{REPO_NAME}` - Repository name
- `{TIMESTAMP}` - Current UTC timestamp (ISO 8601)
- `{AGENT_ROLE}` - Current agent role (spec, swe, etc.)

Conditionally available:
- `{ISSUE_NUMBER}` - GitHub issue number
- `{PR_NUMBER}` - GitHub PR number
- `{BRANCH_NAME}` - Current git branch

### Custom Variables

Define in `.kerriganrc`:

```yaml
variables:
  TEAM_NAME: "Platform Engineering"
  ENVIRONMENT: "production"
```

Or pass via CLI:

```bash
kerrigan invoke spec --var TEAM_NAME="Backend Team"
```

## Caching

Prompts are cached locally to reduce network requests:

**Cache location**: `.kerrigan/prompt-cache/`

**Cache invalidation**: Automatic via ETag/Last-Modified headers

**Manual refresh**:
```bash
# Clear all cached prompts
rm -rf .kerrigan/prompt-cache/

# Or refresh on fetch
kerrigan invoke spec --prompt-url <url> --refresh-cache
```

**Offline mode**: Uses cached version if network unavailable

## Versioning Strategy

### Semantic Versioning

- **Major** (1.0.0 → 2.0.0): Breaking changes (incompatible variables, major restructure)
- **Minor** (1.0.0 → 1.1.0): New features (new sections, optional variables)
- **Patch** (1.0.0 → 1.0.1): Bug fixes (typos, clarifications)

### Version Pinning

Pin to specific version in production:

```markdown
Prompt: gh://Kixantrix/kerrigan/prompts/kickoff-spec.md@v1.0.0
```

Use latest for development:

```markdown
Prompt: gh://Kixantrix/kerrigan/prompts/kickoff-spec.md
```

### Git Tags

Tag prompts for version tracking:

```bash
git tag prompts/kickoff-spec/v1.0.0
git push --tags
```

## Creating Custom Prompts

### 1. Create Prompt File

```markdown
---
prompt-version: 1.0.0
required-context:
  - your-required-file.md
variables:
  - YOUR_VARIABLE
tags:
  - your-category
author: you@example.com
---

# Your Prompt Title

Your prompt content with {YOUR_VARIABLE} substitution...
```

### 2. Test Locally

```bash
# Validate syntax
kerrigan prompt validate ./prompts/your-prompt.md

# Test substitution
kerrigan invoke your-role --prompt-url file:///path/to/your-prompt.md
```

### 3. Commit and Version

```bash
git add prompts/your-prompt.md
git commit -m "Add custom prompt for X"
git tag prompts/your-prompt/v1.0.0
git push origin main --tags
```

### 4. Use in Issues

```markdown
Prompt: gh://your-org/your-repo/prompts/your-prompt.md
```

## Security

### Trusted Domains

Only prompts from these domains are allowed by default:
- `raw.githubusercontent.com`
- `gist.githubusercontent.com`
- `github.com`

Add custom domains in `.kerriganrc`:

```yaml
prompt_security:
  trusted_domains:
    - prompts.yourcompany.com
    - cdn.example.com
```

### Validation

All prompts are validated before use:
- ✅ YAML frontmatter syntax check
- ✅ Size limit check (1 MB max)
- ✅ Domain allowlist check
- ✅ User confirmation for untrusted sources (interactive mode)

### Best Practices

- ✅ Review prompt content before adding to allowlist
- ✅ Use `gh://` URLs for version control
- ✅ Pin versions in production
- ✅ Disable `allow_file_urls` in production
- ❌ Never load prompts from untrusted domains
- ❌ Never include secrets in prompt files

## Migration from Inline Prompts

### Step 1: Extract Existing Prompts

Copy prompts from `.github/agents/` to this directory:

```bash
cp .github/agents/role.spec.md prompts/kickoff-spec.md
# Edit to add frontmatter and variables
```

### Step 2: Add Frontmatter

Add YAML frontmatter with version, variables, etc.

### Step 3: Update Issues

Replace inline prompts with URLs:

```markdown
# Before
@role.spec
[... full prompt text ...]

# After  
@role.spec
Prompt: gh://Kixantrix/kerrigan/prompts/kickoff-spec.md
```

### Step 4: Test

Verify prompts work with URL loading before removing inline versions.

## Examples

### Example 1: Start New Project

```markdown
## New Project: User Authentication Service

@role.spec

Prompt: gh://Kixantrix/kerrigan/prompts/kickoff-spec.md

Project: auth-service

Requirements:
- OAuth2 and SAML support
- Integration with existing user database
- Admin dashboard for user management
```

### Example 2: Implementation Task

```markdown
## Implement Login API

@role.swe

Prompt: gh://Kixantrix/kerrigan/prompts/implementation-swe.md

Project: auth-service
Task: implement-login-api

Acceptance Criteria:
- POST /api/login accepts username/password
- Returns JWT token on success
- Rate limiting applied (10 req/min per IP)
```

### Example 3: Security Review

```markdown
## Security Review: Authentication Service

@role.security

Prompt: gh://Kixantrix/kerrigan/prompts/security-review.md

Project: auth-service

Focus Areas:
- Password storage (bcrypt usage)
- JWT token security
- Rate limiting effectiveness
- Session management
```

## Troubleshooting

### Prompt Won't Load

**Error**: "Failed to fetch prompt from URL"

**Check**:
- Is URL accessible? (Try in browser)
- Is domain in allowlist?
- Is network connection working?
- Try with `--no-cache` flag

### Variable Not Substituted

**Error**: "Variable {VAR_NAME} undefined"

**Fix**:
- Pass variable via `--var VAR_NAME=value`
- Define in `.kerriganrc` under `variables:`
- Check spelling matches frontmatter

### Cache Out of Date

**Issue**: Using old version of prompt

**Fix**:
```bash
# Clear cache
rm -rf .kerrigan/prompt-cache/

# Or refresh on next fetch
kerrigan invoke --refresh-cache
```

## Contributing

### Adding New Prompts

1. Create prompt file in `prompts/` directory
2. Follow naming convention: `{purpose}-{role}.md`
3. Include complete frontmatter
4. Document all variables
5. Add to table in this README
6. Test thoroughly before committing
7. Version with semantic versioning

### Updating Existing Prompts

1. Make changes to prompt file
2. Increment version in frontmatter:
   - Patch: typos, clarifications
   - Minor: new sections, optional features
   - Major: breaking changes
3. Update CHANGELOG (if exists)
4. Tag with new version: `git tag prompts/{name}/v{version}`
5. Update README table with new version

### Quality Standards

All prompts must:
- [ ] Have valid YAML frontmatter
- [ ] Include `prompt-version` field
- [ ] List all required context
- [ ] Document all variables
- [ ] Use clear, actionable language
- [ ] Include examples where helpful
- [ ] Follow Markdown best practices
- [ ] Be tested before merging

## Further Reading

- [Prompt URL Loading System Specification](../specs/kerrigan/040-toolchain-and-ops.md#prompt-url-loading-system)
- [Agent Archetypes](../specs/kerrigan/010-agent-archetypes.md)
- [Artifact Contracts](../specs/kerrigan/020-artifact-contracts.md)
- [Quality Bar](../specs/kerrigan/030-quality-bar.md)

## Questions?

- **Issues**: Open an issue in this repository
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Follow responsible disclosure for security issues

---

**Prompt Library Version**: 1.0.0
**Last Updated**: 2026-01-18
