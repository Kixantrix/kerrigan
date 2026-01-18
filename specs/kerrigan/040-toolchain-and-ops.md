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

## Kerrigan CLI Tool Architecture

### Overview

The Kerrigan CLI tool provides command-line capabilities for:
- Project initialization and management
- Agent invocation and handoff coordination
- Multi-repository operations
- Status checking and validation
- Future integration with dashboard and analytics

**Design Principles**:
- **Consistency**: Python-based to align with existing toolchain (validators, scripts)
- **Simplicity**: Clear command structure with intuitive names
- **Extensibility**: Plugin system for custom commands and workflows
- **Cross-platform**: Support Windows PowerShell, macOS, and Linux environments
- **Git-native**: All operations respect Git as source of truth

### Language and Framework Choice

**Language**: Python 3.8+
- Consistent with existing validator tooling
- Rich ecosystem for CLI frameworks
- Easy distribution via PyPI
- Good Windows support

**CLI Framework**: Click
- Proven framework with strong ecosystem
- Excellent help generation and error handling
- Subcommand support for command grouping
- Context passing for configuration
- Existing use in examples/hello-cli demonstrates pattern

**Alternative Considered**: Typer
- Modern, type-hinted CLI framework
- More Pythonic API
- Decision: Stick with Click for consistency with existing examples

### Command Structure

#### Core Commands

```bash
# Version and help
kerrigan --version                          # Show CLI version
kerrigan --help                             # Show help for all commands

# Project management
kerrigan init <project-name>                # Initialize new project structure
kerrigan init <project-name> --template=multi-repo  # Use specific template
kerrigan status                             # Show project status across repos
kerrigan status --json                      # Output status in JSON format
kerrigan validate                           # Run all validators on current project
kerrigan validate --fix                     # Auto-fix common issues

# Agent invocation
kerrigan agent <role> <task>                # Invoke agent with task description
kerrigan agent spec --mode kickoff          # Run spec agent in kickoff mode
kerrigan agent spec --prompt-file=custom.md # Use custom prompt file
kerrigan agent list                         # List available agent roles

# Handoff management
kerrigan handoff <from-role> <to-role>      # Execute handoff between agents
kerrigan handoff check                      # Verify handoff readiness
kerrigan handoff list                       # Show handoff history

# Multi-repo operations
kerrigan repos list                         # List all repos in project
kerrigan repos sync                         # Sync status across repos
kerrigan repos check                        # Verify all repos accessible
kerrigan repos add <repo-url>               # Add repository to project

# Configuration
kerrigan config get <key>                   # Get configuration value
kerrigan config set <key> <value>           # Set configuration value
kerrigan config list                        # List all configuration
kerrigan config init                        # Initialize config file interactively
```

#### Command Naming Conventions

1. **Noun-verb pattern**: `kerrigan <noun> <verb>` (e.g., `kerrigan repos list`, `kerrigan handoff check`)
2. **Group commands**: Related commands under subcommand groups (e.g., `repos list`, `repos sync`)
3. **Consistent flags**:
   - `--help, -h`: Show help
   - `--verbose, -v`: Verbose output
   - `--quiet, -q`: Minimal output
   - `--dry-run`: Show what would happen without executing
   - `--json`: Output in JSON format
   - `--config`: Specify config file path

### Configuration Schema

#### Configuration File Location

**Search order**:
1. `--config` flag value (if provided)
2. `.kerrigan/config.yaml` in current directory
3. `.kerrigan/config.yaml` in Git repository root
4. `~/.kerrigan/config.yaml` (user global)
5. Default values

#### Configuration File Format

**File**: `.kerrigan/config.yaml`

```yaml
# Kerrigan CLI Configuration
version: "1.0"

# GitHub integration
github:
  token: "${GITHUB_TOKEN}"  # Environment variable reference
  api_url: "https://api.github.com"
  timeout: 30

# Project settings
project:
  default_template: "standard"
  auto_validate: true
  
# Agent settings
agents:
  default_mode: "assisted"  # assisted | sprint | autonomous
  prompt_cache_ttl: 3600    # seconds
  prompt_source: "local"     # local | remote | auto
  
# Multi-repo settings
repos:
  default_branch: "main"
  sync_interval: 300        # seconds
  max_repos: 10
  
# CLI behavior
cli:
  color_output: true
  interactive: true
  editor: "${EDITOR}"       # Defaults to system EDITOR
  pager: "${PAGER}"         # Defaults to 'less'
  
# Plugins (for future extensibility)
plugins:
  enabled: []
  search_paths:
    - ".kerrigan/plugins"
    - "~/.kerrigan/plugins"

# Dashboard integration (Milestone 7b)
dashboard:
  enabled: false
  url: ""
  api_key: "${KERRIGAN_API_KEY}"

# Cost tracking (Milestone 7c)
cost_tracking:
  enabled: false
  budget_limit: 0
  alert_threshold: 0.8
```

#### Environment Variable Overrides

Configuration values support environment variable substitution using `${VAR_NAME}` syntax.

**Priority order** (highest to lowest):
1. Command-line flags
2. Environment variables
3. Project-level config (`.kerrigan/config.yaml` in repo)
4. User-level config (`~/.kerrigan/config.yaml`)
5. Default values

**Key environment variables**:
- `GITHUB_TOKEN`: GitHub personal access token
- `KERRIGAN_CONFIG`: Path to config file
- `KERRIGAN_PROJECT_ROOT`: Override project root detection
- `KERRIGAN_DEBUG`: Enable debug logging
- `EDITOR`: Preferred text editor for interactive commands
- `PAGER`: Preferred pager for long output

#### Secure Credential Storage

**Never store credentials directly in config files**. Use one of:

1. **Environment variables**: `export GITHUB_TOKEN=ghp_xxx`
2. **GitHub CLI integration**: Reuse `gh auth token` if available
3. **System keyring** (future): `keyring` library for secure storage
4. **CI/CD secrets**: GitHub Actions secrets, Azure Key Vault, etc.

### Error Handling

#### Error Message Patterns

**Structure**: `Error: <What went wrong> - <Suggested fix>`

**Examples**:
```
Error: Project not found - Run 'kerrigan init <name>' to create a new project
Error: GitHub token not configured - Set GITHUB_TOKEN environment variable or run 'kerrigan config set github.token'
Error: Invalid repository URL - Expected format: https://github.com/owner/repo or owner/repo
Error: Validator failed: Missing required file spec.md - Create file or use 'kerrigan validate --fix' to auto-generate template
```

#### Exit Codes (POSIX Conventions)

| Code | Meaning | Usage |
|------|---------|-------|
| 0 | Success | Command completed successfully |
| 1 | General error | Validation failed, file not found, etc. |
| 2 | Misuse | Invalid arguments, unknown command |
| 3 | Configuration error | Missing or invalid configuration |
| 4 | Network error | GitHub API failure, timeout |
| 5 | Permission error | Insufficient permissions, auth failure |
| 6 | Validation error | Artifact validation failed |
| 130 | User interrupt | Ctrl+C pressed |

#### Error Handling Strategies

1. **Fail fast with clear messages**: Don't continue if prerequisites are missing
2. **Suggest fixes**: Every error should include actionable next steps
3. **Validate early**: Check configuration and permissions before expensive operations
4. **Graceful degradation**: Fall back to simpler behavior when optional features unavailable
5. **Network resilience**: Retry transient failures with exponential backoff
6. **Debug mode**: `--debug` flag shows full stack traces and API calls

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Kerrigan CLI Tool                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Project   │  │    Agent     │  │  Multi-repo  │       │
│  │  Commands   │  │  Commands    │  │   Commands   │       │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
│         └─────────────────┴──────────────────┘               │
│                           │                                  │
│                  ┌────────▼────────┐                         │
│                  │  Core CLI Engine │                        │
│                  │   (Click-based)  │                        │
│                  └────────┬─────────┘                        │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐         │
│  │   Config    │  │  Validators │  │   GitHub    │         │
│  │   Manager   │  │   Runner    │  │  API Client │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
┌───────▼───────┐  ┌────────▼─────────┐  ┌──────▼──────┐
│  Git Repos    │  │  GitHub API      │  │  Config     │
│  (local)      │  │  (remote)        │  │  Files      │
└───────────────┘  └──────────────────┘  └─────────────┘
```

### Plugin System Design

#### Plugin Architecture

**Goal**: Allow custom commands and workflows without modifying core CLI.

**Plugin Discovery**:
1. Search paths defined in config: `plugins.search_paths`
2. Convention: Python modules with specific entry points
3. Auto-discovery via naming convention: `kerrigan_plugin_*.py`

**Plugin Interface**:

```python
# Example plugin: kerrigan_plugin_custom.py
import click
from kerrigan.plugins import KerriganPlugin

class CustomPlugin(KerriganPlugin):
    """Custom organization-specific commands."""
    
    name = "custom"
    version = "1.0.0"
    
    @click.command()
    @click.argument('action')
    def custom_command(action):
        """Custom organization command."""
        click.echo(f"Running custom action: {action}")
    
    def register(self, cli):
        """Register plugin commands with main CLI."""
        cli.add_command(self.custom_command)

# Entry point
def init_plugin():
    return CustomPlugin()
```

#### Hook System

**Pre/post command hooks** for custom workflow integration:

```python
# Hook example
@kerrigan.hook('pre_init')
def validate_org_policy(ctx, project_name):
    """Validate project name against org policy."""
    if not project_name.startswith('org-'):
        raise ValueError("Project names must start with 'org-'")

@kerrigan.hook('post_init')
def notify_team(ctx, project_name):
    """Notify team of new project creation."""
    send_slack_notification(f"New project created: {project_name}")
```

**Available hooks** (defined but not implemented in 7a):
- `pre_init`, `post_init`: Project initialization
- `pre_agent_invoke`, `post_agent_invoke`: Agent invocation
- `pre_validate`, `post_validate`: Validation runs
- `pre_handoff`, `post_handoff`: Agent handoffs

#### Plugin Distribution

**Milestone 7a**: Local plugins only (file-based discovery)
**Milestone 7b**: Package-based plugins via PyPI or private package indices
**Milestone 7c**: Plugin marketplace and version management

### Implementation Notes

#### Project Structure

```
tools/cli/kerrigan-cli/
├── kerrigan/
│   ├── __init__.py
│   ├── __main__.py           # Entry point: python -m kerrigan
│   ├── cli.py                # Main CLI group
│   ├── version.py            # Version info
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── project.py        # init, status, validate
│   │   ├── agent.py          # agent invocation
│   │   ├── handoff.py        # handoff management
│   │   ├── repos.py          # multi-repo commands
│   │   └── config.py         # config management
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # Config loading/management
│   │   ├── github.py         # GitHub API client
│   │   ├── validators.py    # Validator runner
│   │   └── project.py        # Project detection/management
│   ├── plugins/
│   │   ├── __init__.py
│   │   └── base.py           # Plugin base class
│   └── utils/
│       ├── __init__.py
│       ├── colors.py         # Terminal colors
│       ├── errors.py         # Error classes
│       └── output.py         # Output formatting
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_commands.py
│   └── test_plugins.py
├── setup.py                   # Package configuration
├── requirements.txt           # Dependencies
├── README.md                  # CLI documentation
└── CHANGELOG.md              # Version history
```

#### Dependencies

**Core dependencies**:
- `click>=8.0`: CLI framework
- `pyyaml>=6.0`: Config file parsing
- `requests>=2.32.0`: HTTP client for GitHub API (security patches)
- `rich>=13.0`: Rich terminal output (optional, for enhanced UX)
- `pygments>=2.15`: Syntax highlighting (optional)

**Development dependencies**:
- `pytest>=7.0`: Testing framework
- `pytest-cov>=4.0`: Coverage reporting
- `black>=23.0`: Code formatting
- `flake8>=6.0`: Linting
- `mypy>=1.0`: Type checking

#### Distribution Strategy

**Milestone 7a**: Development installation
```bash
# From repository root
cd tools/cli/kerrigan-cli
pip install -e .
```

**Milestone 7b**: PyPI distribution
```bash
pip install kerrigan-cli
```

**Milestone 7c**: Platform-specific packages
- Homebrew (macOS): `brew install kerrigan-cli`
- Chocolatey (Windows): `choco install kerrigan-cli`
- APT/YUM (Linux): Distribution packages

### Usage Examples

#### Example 1: Initialize New Project

```bash
# Create new project with default template
$ kerrigan init my-api-service
✓ Created project structure at specs/projects/my-api-service/
✓ Generated spec.md from template
✓ Generated architecture.md from template
✓ Generated plan.md from template
✓ Generated tasks.md from template
✓ Generated test-plan.md from template
✓ Generated acceptance-tests.md from template
✓ Initialized status.json

Next steps:
1. Edit specs/projects/my-api-service/spec.md to define goals
2. Run 'kerrigan validate' to check artifacts
3. Run 'kerrigan agent spec --mode kickoff' to start spec agent
```

#### Example 2: Check Project Status

```bash
$ kerrigan status
Project: my-api-service
Status: active
Phase: architecture
Last updated: 2026-01-15 14:32:00

Artifacts:
  ✓ spec.md (completed)
  ✓ architecture.md (in progress)
  ✗ plan.md (not started)
  ✗ tasks.md (not started)

Open PRs:
  #42 - spec: Define API service architecture (role.architect)

Blockers: None
```

#### Example 3: Invoke Agent

```bash
$ kerrigan agent architect "Design REST API architecture"
Fetching prompt for role: architect
Agent context:
  Role: architect
  Project: my-api-service
  Task: Design REST API architecture
  Current phase: architecture

Prompt copied to clipboard.
Open in GitHub Copilot? [y/N]: y
Opening in VS Code...
```

#### Example 4: Multi-repo Operations

```bash
# List repositories in multi-repo project
$ kerrigan repos list
my-api-service (2 repositories):
  1. api-backend (https://github.com/org/api-backend)
     Branch: main | Status: ✓ accessible
  2. api-frontend (https://github.com/org/api-frontend)
     Branch: main | Status: ✓ accessible

# Sync status across repos
$ kerrigan repos sync
Syncing status across 2 repositories...
✓ api-backend: status.json updated
✓ api-frontend: status.json updated
All repositories in sync.
```

#### Example 5: Validate Project

```bash
$ kerrigan validate
Running validators on specs/projects/my-api-service/...

✓ check_artifacts.py
  - All required files present
  - All required sections present

✗ check_quality_bar.py
  - spec.md: Missing success metrics section
  - architecture.md: File size exceeds 50KB limit

Validation failed with 2 errors.
Run 'kerrigan validate --fix' to auto-fix common issues.
```

### Windows PowerShell Support

#### PowerShell-Specific Considerations

1. **Path handling**: Use `pathlib` for cross-platform path operations
2. **Environment variables**: Support both `%VAR%` and `$env:VAR` syntax
3. **Color output**: Detect Windows Terminal vs legacy console
4. **Line endings**: Handle both CRLF and LF
5. **Command aliases**: Support both `/` and `-` flag prefixes where common

#### Installation on Windows

```powershell
# Using pip
pip install kerrigan-cli

# Or from source
cd tools\cli\kerrigan-cli
pip install -e .

# Verify installation
kerrigan --version
```

#### Windows-Specific Features

- Respect `%USERPROFILE%` for config location
- Support Windows Credential Manager for token storage (future)
- Handle Windows file locking during Git operations
- Proper handling of Windows line endings in config files

### Migration Path and Backward Compatibility

**Milestone 7a** (current):
- CLI is additive; existing manual workflows continue to work
- No breaking changes to artifact contracts or validator interfaces
- Projects can opt-in to CLI usage gradually

**Version compatibility**:
- CLI version format: `MAJOR.MINOR.PATCH` (semantic versioning)
- CLI checks compatibility with artifact contract versions
- Warning displayed if CLI version is significantly outdated

**Deprecation policy**:
- Features deprecated with 6-month notice
- Old commands aliased to new ones with deprecation warnings
- Breaking changes only in major version bumps

### Future Enhancements (Post-7a)

**Milestone 7b integrations**:
- Dashboard URL opening: `kerrigan dashboard open`
- Real-time status streaming: `kerrigan status --watch`
- Webhook management: `kerrigan webhooks setup`

**Milestone 7c integrations**:
- Cost estimation: `kerrigan cost estimate`
- Task queue management: `kerrigan queue list`
- Parallel agent orchestration: `kerrigan agents start --parallel`
- Prompt optimization tools: `kerrigan prompts analyze`

**Community requests**:
- Shell completion (bash, zsh, fish, PowerShell)
- Interactive TUI mode: `kerrigan tui`
- VS Code extension integration
- GitHub Actions integration: `kerrigan-action`
