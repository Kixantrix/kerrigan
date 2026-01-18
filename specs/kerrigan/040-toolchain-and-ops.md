# Toolchain and ops (stack-agnostic)

## GitHub workflow
- PRs are the unit of change.
- CI enforces artifact completeness and baseline quality heuristics.
- Autonomy gates optionally control when agents may open PRs.

## Secrets
- Use GitHub Secrets or environment-specific secret stores.
- Never commit .env files or credentials.

## Azure (optional)
This repo does not mandate Azure services. If a project deploys to Azure:
- Document environment strategy in `runbook.md`
- Include cost guardrails in `cost-plan.md`
- Use tagging and budgets/alerts where appropriate

## Prompt URL loading system

### Overview

The prompt URL loading system enables agents to reference prompts via URL instead of requiring inline copy-paste from GitHub issues. This enables:
- **Version control**: Track prompt changes over time
- **Reusability**: Share prompts across projects and teams
- **Centralization**: Maintain prompt libraries
- **Consistency**: Ensure all agents use the same prompt version

### Usage in GitHub issues

Instead of copying full agent prompts inline, reference them by URL:

```markdown
@role.spec

Prompt: https://raw.githubusercontent.com/org/kerrigan/main/prompts/kickoff-spec.md

Project: myapp
Context:
- Requirements gathered from stakeholder meeting
- Target audience: internal tooling users
```

The agent (or CLI tool) fetches the prompt from the URL, performs variable substitution, and uses the result as the working prompt.

### Prompt file format

Prompts are markdown files with optional YAML frontmatter for metadata:

```markdown
---
prompt-version: 1.0.0
required-context:
  - spec.md
  - constitution.md
variables:
  - PROJECT_NAME
  - REPO_NAME
tags:
  - kickoff
  - specification
author: team@example.com
---

# Kickoff Specification

You are the spec agent conducting project kickoff for {PROJECT_NAME}.

## Your role

Review the requirements and create a comprehensive specification following the artifact contracts defined in specs/kerrigan/020-artifact-contracts.md.

## Context files required

Before starting, ensure you have access to:
- constitution.md (project principles)
- Any requirements documents referenced in the issue

## Output

Create specs/projects/{PROJECT_NAME}/spec.md with:
- Goal
- Scope / Non-goals
- Users & scenarios
- Constraints
- Acceptance criteria
- Risks & mitigations
- Success metrics

Repository: {REPO_NAME}
Generated at: {TIMESTAMP}
```

#### Frontmatter schema

**Required fields**: None (frontmatter is optional)

**Optional fields**:
- `prompt-version` (string): Semantic version of the prompt (e.g., "1.0.0", "2.1.3")
- `required-context` (array): Files or artifacts the agent must have before using this prompt
- `variables` (array): List of variables this prompt expects to be substituted
- `tags` (array): Categories or keywords for prompt discovery
- `author` (string): Contact for prompt questions
- `min-context-window` (integer): Minimum context window size in tokens (e.g., 8000)
- `deprecated` (boolean): Mark prompt as deprecated
- `replacement-url` (string): URL of replacement prompt if deprecated

### URL schemes

The system supports multiple URL schemes for flexibility:

#### https:// - Direct HTTP(S) URLs

Standard web URLs, typically pointing to raw content:

```
https://raw.githubusercontent.com/Kixantrix/kerrigan/main/prompts/kickoff-spec.md
https://example.com/prompts/security-review.md
```

**Best for**: Production use, public prompt libraries, CDN-hosted prompts

#### file:// - Local file system

Local file paths for development and testing:

```
file:///home/user/kerrigan/prompts/kickoff-spec.md
file:///tmp/experimental-prompt.md
```

**Best for**: Local development, testing new prompts, offline work

#### gh:// - GitHub shorthand

Shorthand for GitHub repository paths:

```
gh://Kixantrix/kerrigan/prompts/kickoff-spec.md
gh://org/private-repo/prompts/security-review.md@v2.0.0
```

Expands to: `https://raw.githubusercontent.com/{org}/{repo}/{branch-or-tag}/{path}`

Default branch: `main`

**Best for**: Cleaner issue syntax, version pinning with tags

**Tag/branch syntax**: `gh://org/repo/path@branch-or-tag`

Examples:
- `gh://Kixantrix/kerrigan/prompts/spec.md@v1.0.0` (specific tag)
- `gh://Kixantrix/kerrigan/prompts/spec.md@develop` (branch)

### Caching mechanism

To reduce network requests and enable offline work, prompts are cached locally.

#### Cache location

`.kerrigan/prompt-cache/` (relative to project root or user home)

Structure:
```
.kerrigan/
  prompt-cache/
    {url-hash}/
      prompt.md           # Cached prompt content
      metadata.json       # Cache metadata (ETag, Last-Modified, fetch time)
```

#### Cache key generation

Hash the full URL (including scheme, domain, path, query) using SHA-256:

```python
import hashlib
cache_key = hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
```

#### Cache invalidation

**On fetch**:
1. Check if cache entry exists
2. If exists, check `ETag` or `Last-Modified` from previous fetch
3. Make HTTP request with `If-None-Match` (ETag) or `If-Modified-Since` headers
4. If `304 Not Modified`, use cached version
5. If `200 OK`, update cache with new content and metadata

**Manual invalidation**:
- Delete `.kerrigan/prompt-cache/` directory
- Use CLI flag: `--no-cache` or `--refresh-cache`

**Offline mode**:
If network unavailable or URL unreachable:
1. Use cached version if available
2. Warn user that cached version is being used
3. Fail only if cache doesn't exist

#### Cache expiry

**No automatic expiry** by default (prompts are versioned, not time-sensitive)

Optional: Configure max-age in `.kerriganrc`:
```yaml
prompt_cache:
  max_age_days: 7
  offline_mode: false
```

### Variable substitution

Prompts may contain variables in `{VARIABLE_NAME}` format that are substituted at load time.

#### Built-in variables

**Always available**:
- `{PROJECT_NAME}`: Current project name (from spec.md or directory name)
- `{REPO_NAME}`: Current repository name (from git remote)
- `{TIMESTAMP}`: Current UTC timestamp (ISO 8601 format)
- `{AGENT_ROLE}`: Current agent role (e.g., "spec", "swe", "architect")

**Conditionally available**:
- `{ISSUE_NUMBER}`: GitHub issue number (if invoked from issue context)
- `{PR_NUMBER}`: GitHub PR number (if invoked from PR context)
- `{BRANCH_NAME}`: Current git branch name

#### Custom variables

Projects can define custom variables in `.kerriganrc`:

```yaml
variables:
  TEAM_NAME: "Platform Engineering"
  ENVIRONMENT: "production"
  CONTACT_EMAIL: "team@example.com"
```

Or pass via CLI:
```bash
kerrigan invoke spec --var PROJECT_NAME=myapp --var TEAM=infra
```

#### Substitution behavior

**Undefined variables**:
- **Strict mode** (default): Fail if variable is undefined
- **Lenient mode**: Leave `{UNDEFINED_VAR}` as-is with warning

**Escaping**: Use double braces to escape: `{{NOT_A_VARIABLE}}` → `{NOT_A_VARIABLE}`

**Nested substitution**: Not supported (single-pass only)

### Security model

#### Trusted domains (allowlist)

Only URLs from trusted domains are allowed by default:

**Default allowlist**:
- `raw.githubusercontent.com`
- `gist.githubusercontent.com`
- `github.com` (redirects to raw.githubusercontent.com)

**Custom allowlist** in `.kerriganrc`:
```yaml
prompt_security:
  trusted_domains:
    - raw.githubusercontent.com
    - prompts.example.com
    - cdn.company.com
  allow_file_urls: true  # Enable file:// (disable in production)
  allow_all_domains: false  # Disable allowlist (dangerous)
```

#### Validation before execution

Before using a fetched prompt:

1. **Schema validation**: Verify YAML frontmatter parses correctly
2. **Size check**: Reject prompts exceeding reasonable size (e.g., 1 MB)
3. **Content inspection**: Warn if prompt contains suspicious patterns (optional)
4. **User confirmation**: Show prompt preview and require explicit approval (in interactive mode)

#### Untrusted source warnings

If URL is not in allowlist:
```
⚠️  WARNING: Untrusted prompt source
URL: https://unknown-domain.com/prompt.md
Domain: unknown-domain.com

This domain is not in your trusted list. Prompts from untrusted sources
may contain malicious instructions.

Preview (first 500 chars):
---
[prompt preview]
---

Do you want to proceed? [y/N]:
```

#### Future: Signing and verification

**Not implemented in initial version**, but designed for future extension:

- Prompts may include PGP signatures in frontmatter
- System verifies signature against trusted public keys
- Unsigned prompts trigger warning
- Invalid signatures fail validation

```yaml
---
prompt-version: 1.0.0
signature: |
  -----BEGIN PGP SIGNATURE-----
  [signature data]
  -----END PGP SIGNATURE-----
---
```

### Error handling

#### Network failures

**Fetch fails**:
- Check cache for previous version
- If cache exists: use cached version with warning
- If no cache: fail with clear error message

**Timeout**:
- Default timeout: 10 seconds
- Configurable via `.kerriganrc`: `prompt_fetch_timeout: 30`

#### Invalid prompt files

**Malformed YAML frontmatter**:
- Log error with line/column number
- Fail with actionable message: "Fix YAML syntax in frontmatter"

**Missing required context**:
- If `required-context` lists files not available
- Warn user: "Prompt expects spec.md but file not found"
- Allow override with `--ignore-missing-context`

**Variable substitution failures**:
- If required variable undefined (strict mode)
- Fail with message: "Variable {VAR_NAME} undefined. Pass via --var or define in .kerriganrc"

#### Version mismatches

**Deprecated prompts**:
- Show warning with `replacement-url`
- Continue with deprecated prompt (don't fail)
- Log deprecation to help users migrate

**Min context window not met**:
- If AI model's context window < `min-context-window`
- Warn: "Prompt designed for 8000+ token window, current model supports 4000"
- Continue (don't fail)

### Integration with CLI

The prompt URL system integrates with the Kerrigan CLI tool (future implementation):

#### Invoke with URL

```bash
# Fetch and use remote prompt
kerrigan invoke spec --prompt-url gh://Kixantrix/kerrigan/prompts/kickoff-spec.md

# With variable overrides
kerrigan invoke swe \
  --prompt-url https://example.com/prompts/implementation.md \
  --var PROJECT_NAME=myapp \
  --var TEAM=backend

# Force cache refresh
kerrigan invoke architect --prompt-url gh://org/repo/prompts/arch.md --refresh-cache
```

#### Prompt management commands

```bash
# List cached prompts
kerrigan prompt cache list

# Clear cache
kerrigan prompt cache clear

# Show prompt preview
kerrigan prompt show gh://Kixantrix/kerrigan/prompts/spec.md

# Validate prompt file
kerrigan prompt validate ./prompts/custom-spec.md
```

### Example workflow

**1. Create reusable prompt**:

Create `prompts/kickoff-spec.md` in your repository:

```markdown
---
prompt-version: 1.0.0
required-context:
  - constitution.md
variables:
  - PROJECT_NAME
---

# Specification Kickoff for {PROJECT_NAME}

You are creating the initial specification...
[full prompt content]
```

**2. Reference in GitHub issue**:

```markdown
## New project: User authentication service

@role.spec

Prompt: gh://Kixantrix/kerrigan/prompts/kickoff-spec.md

Project: auth-service

Requirements:
- OAuth2 and SAML support
- Integration with existing user database
[additional context]
```

**3. Agent workflow**:

1. Agent sees issue assignment
2. Extracts prompt URL: `gh://Kixantrix/kerrigan/prompts/kickoff-spec.md`
3. CLI fetches prompt (checking cache first)
4. Substitutes variables: `{PROJECT_NAME}` → `auth-service`
5. Loads resulting prompt into AI context
6. Agent proceeds with specification work

**4. Version management**:

When prompt needs changes:
1. Update `prompts/kickoff-spec.md`
2. Increment `prompt-version` to `1.1.0`
3. Commit with semantic versioning
4. Tag release: `git tag prompts/kickoff-spec/v1.1.0`
5. Old issues still work (URLs cached or use version tags)

### Best practices

#### Prompt versioning

- Use semantic versioning in `prompt-version` field
- Breaking changes (incompatible variable changes): bump major version
- New features (new optional sections): bump minor version
- Bug fixes (typos, clarifications): bump patch version
- Tag prompts in git: `prompts/{name}/v{version}`

#### Variable design

- Keep variables minimal and self-documenting
- Use `SCREAMING_SNAKE_CASE` for visibility
- Document expected variables in frontmatter
- Provide sensible defaults where possible

#### Security

- Never load prompts from untrusted domains in production
- Review prompt content before adding to allowlist
- Use `gh://` URLs for organizational prompts (version control)
- Disable `allow_file_urls` in production environments
- Require human approval for new domains

#### Caching

- Commit `.kerrigan/prompt-cache/` to `.gitignore`
- CI/CD may need to refresh cache or disable caching
- Document cache location if non-standard

#### Context requirements

- Always specify `required-context` for prompts needing specific files
- Fail fast if context missing (easier to debug)
- Keep prompts self-contained when possible (reduce dependencies)

### Migration from inline prompts

**Phase 1: Extract to files**
1. Copy inline prompts to `prompts/` directory
2. Add frontmatter with version
3. Identify repeated variables

**Phase 2: Add URLs**
1. Commit prompts to repository
2. Update issues to reference URLs
3. Test fetch and substitution

**Phase 3: Centralize**
1. Move common prompts to shared prompt repository
2. Update URLs to shared location
3. Maintain version compatibility

**Backward compatibility**:
- Inline prompts continue to work (no breaking changes)
- URL loading is opt-in enhancement
- Both methods can coexist during migration
