# CLI Reference

The Kerrigan CLI provides a command-line interface for project management and multi-repository operations.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from source

```bash
cd tools/cli/kerrigan
pip install -e .
```

### Install with clipboard support

For clipboard support in the `agent` command:

```bash
pip install -e ".[clipboard]"
```

## Configuration

Kerrigan CLI can be configured using a configuration file in one of these locations:

1. `.kerriganrc` in the current directory
2. `~/.kerriganrc` in your home directory
3. `~/.config/kerrigan/config.yaml`

### Configuration file format

```yaml
# GitHub token for API access (optional)
github_token: ghp_xxxxxxxxxxxxx

# Default template for project initialization
default_template: _template
```

You can also set configuration values via environment variables:

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
```

## Commands

### General Usage

```bash
kerrigan [OPTIONS] COMMAND [ARGS]...
```

**Options:**
- `--version`: Show version and exit
- `--help`: Show help message and exit

### kerrigan init

Initialize a new project from a template.

**Usage:**

```bash
kerrigan init PROJECT_NAME [OPTIONS]
```

**Arguments:**
- `PROJECT_NAME`: Name of the project to create

**Options:**
- `--template TEXT`: Template to use (default: _template)
- `--force`: Overwrite existing project if it exists

**Examples:**

```bash
# Create a new project from the default template
kerrigan init my-project

# Create a project from a specific template
kerrigan init my-api --template hello-api

# Overwrite an existing project
kerrigan init my-project --force
```

**What it does:**
- Creates a new project directory under `specs/projects/<project-name>/`
- Copies all files from the specified template
- Updates timestamps in status.json if present
- Provides next steps for project setup

### kerrigan status

Show the status of one or all projects.

**Usage:**

```bash
kerrigan status [PROJECT_NAME] [OPTIONS]
```

**Arguments:**
- `PROJECT_NAME`: Name of the project (optional if using --all)

**Options:**
- `--all`: Show status for all projects

**Examples:**

```bash
# Show status for a specific project
kerrigan status my-project

# Show status for all projects
kerrigan status --all
```

**What it displays:**
- Project status (active/blocked/completed/on-hold)
- Current phase (spec/architecture/implementation/testing/deployment)
- Last updated timestamp (formatted as "X time ago")
- Blocked reason (if status is blocked or on-hold)
- Additional notes

### kerrigan validate

Run artifact validators on project(s).

**Usage:**

```bash
kerrigan validate [PROJECT_NAME] [OPTIONS]
```

**Arguments:**
- `PROJECT_NAME`: Name of the project to validate (optional)

**Options:**
- `--all`: Validate all projects

**Examples:**

```bash
# Validate a specific project
kerrigan validate my-project

# Validate all projects
kerrigan validate --all
```

**What it checks:**
- Required artifact files exist (spec.md, architecture.md, etc.)
- Required sections are present in key documents
- status.json format is valid (if present)
- Project structure follows Kerrigan conventions

### kerrigan repos

Multi-repository operations for projects spanning multiple repositories.

#### kerrigan repos list

List repositories configured in a multi-repo project.

**Usage:**

```bash
kerrigan repos list PROJECT_NAME
```

**Arguments:**
- `PROJECT_NAME`: Name of the multi-repo project

**Examples:**

```bash
kerrigan repos list my-multi-repo-project
```

**What it displays:**
- List of repositories from repositories.json
- Repository owner and name
- Local path (if configured)

**Configuration:**

Create a `repositories.json` file in your project directory:

```json
{
  "repositories": [
    {
      "owner": "myorg",
      "name": "backend",
      "path": "../backend"
    },
    {
      "owner": "myorg",
      "name": "frontend",
      "path": "../frontend"
    }
  ]
}
```

#### kerrigan repos sync

Sync status across repositories in a multi-repo project.

**Usage:**

```bash
kerrigan repos sync PROJECT_NAME [OPTIONS]
```

**Arguments:**
- `PROJECT_NAME`: Name of the multi-repo project

**Options:**
- `--dry-run`: Show what would be synced without making changes

**Examples:**

```bash
# Sync status to all repositories
kerrigan repos sync my-multi-repo-project

# Preview sync without making changes
kerrigan repos sync my-multi-repo-project --dry-run
```

**What it does:**
- Reads status.json from the primary project
- Copies status to all configured repositories with local paths
- Updates status.json in each repository location
- Reports sync results

### kerrigan agent

Invoke agents with role-specific prompts.

**Usage:**

```bash
kerrigan agent [ROLE] [OPTIONS]
```

**Arguments:**
- `ROLE`: Agent role (spec, swe, architect, testing, etc.)

**Options:**
- `--list`: List all available agent roles
- `--show`: Display the agent prompt
- `--copy`: Copy prompt to clipboard (requires pyperclip)

**Examples:**

```bash
# List available agent roles
kerrigan agent --list

# Display the spec agent prompt
kerrigan agent spec --show

# Copy the SWE agent prompt to clipboard
kerrigan agent swe --copy
```

**Available Roles:**
- `spec`: Specification agent
- `architect`: Architecture design agent
- `swe`: Software engineering agent
- `testing`: Testing agent
- `deployment`: Deployment agent
- `security`: Security review agent
- `debugging`: Debugging agent
- `triage`: Issue triage agent

## Troubleshooting

### Command not found

If you get a "command not found" error after installation:

1. Check that the installation completed successfully
2. Ensure `~/.local/bin` is in your PATH
3. Try using the full path: `~/.local/bin/kerrigan`

### Cannot find repository root

Kerrigan commands must be run from within a Kerrigan repository. Ensure:

1. You are in a Kerrigan repository directory
2. The `specs/projects/` directory exists
3. The `.github/agents/` directory exists (for agent commands)

### Permission errors

If you encounter permission errors during installation:

```bash
pip install --user -e .
```

### Clipboard not working

To enable clipboard support:

```bash
pip install pyperclip
```

Note: On Linux, you may need additional system packages:

```bash
# Ubuntu/Debian
sudo apt-get install xclip

# Fedora/RHEL
sudo dnf install xclip
```

## See Also

- [Setup Guide](setup.md): Initial repository setup
- [Project Lifecycle](../playbooks/project-lifecycle.md): Managing projects
- [Artifact Contracts](../specs/kerrigan/020-artifact-contracts.md): Required files and structure
