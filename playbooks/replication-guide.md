# Kerrigan Replication Guide

## Purpose
This guide provides step-by-step instructions for setting up the Kerrigan agent swarm system in a new repository. Kerrigan is designed to be replicated into different team repositories and organizational settings, enabling effective agent-driven development workflows. This guide ensures someone unfamiliar with Kerrigan can establish the system using only this documentation.

## Prerequisites

### Required Tools
- **Git**: Version 2.20 or higher
- **Python**: Version 3.8 or higher (for validators)
- **GitHub Account**: With repository creation permissions
- **AI Agent Access**: GitHub Copilot, Claude, or similar (for agent operation)

### Optional Tools
- **Text Editor**: VS Code, Vim, or similar
- **GitHub CLI**: `gh` for easier GitHub operations

## Use Cases

### Use Case 1: New Team Repository Setup
**Situation**: A team wants to adopt Kerrigan's agent swarm approach in their project repository.

**Setup Steps**:
1. Create a new GitHub repository for your project
2. Initialize local repository structure (see [Repository Structure](#repository-structure))
3. Customize artifacts for your team's needs
4. Set up GitHub labels (see [GitHub Labels Setup](#github-labels-setup))
5. Configure CI workflows
6. Validate setup with bootstrap script

### Use Case 2: Adding to Existing Repository
**Situation**: An existing project wants to adopt Kerrigan's workflow without starting from scratch.

**Integration Steps**:
1. Clone the existing repository: `git clone <repo-url>`
2. Add Kerrigan structure alongside existing code
3. Configure validators to accommodate existing code structure
4. Set up GitHub labels and workflows
5. Run bootstrap script: `bash tools/bootstrap.sh`
6. Gradually migrate project artifacts

### Use Case 3: Organizational Standardization
**Situation**: An organization wants to establish Kerrigan as standard practice across multiple teams.

**Rollout Steps**:
1. Create template repository with Kerrigan structure
2. Document organization-specific customizations
3. Set up shared GitHub label standards
4. Provide team training materials
5. Enable teams to fork/template for their projects
6. Establish support channels for questions

## Repository Structure

Kerrigan follows this directory layout:

```
kerrigan/
├── .github/
│   ├── agents/              # Agent role prompts and instructions
│   │   ├── README.md        # Overview of agent system
│   │   ├── role.spec.md     # Specification agent prompt
│   │   ├── role.architect.md # Architecture agent prompt
│   │   ├── role.swe.md      # Software engineering agent prompt
│   │   ├── role.testing.md  # Testing agent prompt
│   │   ├── role.debugging.md # Debugging agent prompt
│   │   ├── role.deployment.md # Deployment agent prompt
│   │   ├── role.security.md # Security agent prompt
│   │   └── kerrigan.swarm-shaper.md # Meta-agent prompt
│   ├── workflows/           # CI/CD automation
│   │   ├── ci.yml           # Main validation workflow
│   │   ├── agent-gates.yml  # Autonomy control workflow
│   │   ├── auto-assign-issues.yml # Auto-assignment automation
│   │   ├── auto-assign-reviewers.yml # Reviewer automation
│   │   ├── auto-generate-issues.yml # Issue generation automation
│   │   └── auto-triage-on-assign.yml # Triage automation
│   └── automation/          # Automation configuration
│       └── README.md        # Automation setup guide
├── docs/                    # User-facing documentation
│   ├── setup.md             # Setup walkthrough
│   ├── architecture.md      # System architecture
│   ├── agent-assignment.md  # Agent assignment guide
│   ├── FAQ.md               # Frequently asked questions
│   ├── self-assembly.md     # Self-assembly and dependency documentation
│   └── *.md                 # Additional documentation
├── playbooks/               # Process playbooks
│   ├── kickoff.md           # Project kickoff guide
│   ├── autonomy-modes.md    # Autonomy control guide
│   ├── handoffs.md          # Agent handoff procedures
│   ├── pr-review.md         # PR review guidelines
│   ├── automation.md        # Automation setup guide
│   └── disaster-recovery.md # This file
├── specs/                   # Specifications and project artifacts
│   ├── constitution.md      # Core principles (non-negotiable)
│   ├── kerrigan/            # Meta-specifications for Kerrigan itself
│   │   ├── spec.md          # Kerrigan specification
│   │   ├── architecture.md  # Kerrigan architecture
│   │   ├── 020-artifact-contracts.md # Required artifacts
│   │   ├── 030-quality-bar.md # Quality standards
│   │   └── *.md             # Additional specs
│   └── projects/            # Project-specific artifacts
│       ├── _template/       # Template for new projects
│       │   ├── spec.md
│       │   ├── architecture.md
│       │   ├── plan.md
│       │   ├── tasks.md
│       │   ├── test-plan.md
│       │   ├── acceptance-tests.md
│       │   ├── runbook.md
│       │   └── cost-plan.md
│       └── <project-name>/  # Individual projects (same structure as template)
├── tools/                   # Automation and validation tools
│   ├── validators/          # Validation scripts
│   │   ├── check_artifacts.py # Artifact structure validator
│   │   └── check_quality_bar.py # Code quality validator
│   ├── bootstrap.sh         # Bootstrap script for setup
│   └── README.md            # Tools documentation
├── tests/                   # Test suite
│   ├── validators/          # Validator tests
│   ├── test_agent_prompts.py # Agent prompt validation
│   └── test_automation.py   # Automation tests
├── examples/                # Example projects
│   ├── hello-cli/           # CLI application example
│   ├── hello-api/           # API service example
│   └── hello-swarm/         # Complete swarm workflow example
├── .gitignore               # Git ignore rules
├── .editorconfig            # Editor configuration
├── LICENSE                  # MIT License
└── README.md                # Main entry point
```

## Step-by-Step Setup for New Repository

### Step 1: Create Repository

```bash
# Option A: Create new GitHub repository via web UI
# 1. Go to https://github.com/new
# 2. Name: "kerrigan" (or your preferred name)
# 3. Description: "Agent swarm orchestration system"
# 4. Visibility: Public or Private
# 5. Click "Create repository"

# Option B: Create via GitHub CLI
gh repo create kerrigan --public --description "Agent swarm orchestration system"

# Clone to local machine
git clone https://github.com/yourusername/kerrigan.git
cd kerrigan
```

### Step 2: Initialize Core Structure

```bash
# Create directory structure
mkdir -p .github/agents .github/workflows .github/automation
mkdir -p docs playbooks specs/kerrigan specs/projects/_template
mkdir -p tools/validators tests/validators examples

# Create essential files
touch README.md LICENSE .gitignore .editorconfig
touch specs/constitution.md
```

### Step 3: Restore Core Artifacts

**Critical files to restore** (in priority order):

1. **specs/constitution.md** - Core principles
   - Define quality standards
   - Establish artifact-driven workflow
   - Set stack-agnostic principles

2. **README.md** - Main entry point
   - Quickstart instructions
   - Architecture overview
   - Documentation links

3. **Agent prompts** (.github/agents/*.md)
   - Role definitions for each agent type
   - Handoff protocols
   - Success criteria

4. **Validators** (tools/validators/*.py)
   - check_artifacts.py - Enforces artifact contracts
   - check_quality_bar.py - Enforces quality standards

5. **CI Workflows** (.github/workflows/*.yml)
   - ci.yml - Main validation workflow
   - agent-gates.yml - Autonomy control

6. **Playbooks** (playbooks/*.md)
   - kickoff.md - Project startup guide
   - autonomy-modes.md - Control mechanisms
   - handoffs.md - Agent coordination

7. **Documentation** (docs/*.md)
   - setup.md - Setup walkthrough
   - architecture.md - System design
   - FAQ.md - Common questions

### Step 4: GitHub Labels Setup

Create these labels in your GitHub repository (Settings → Labels):

**Autonomy Control**:
```
agent:go          #0e8a16  # Green - On-demand approval
agent:sprint      #fbca04  # Yellow - Sprint mode approval
autonomy:override #d73a4a  # Red - Human override
```

**Role Assignment**:
```
role:spec         #d4c5f9  # Purple - Specification work
role:architect    #c5def5  # Blue - Architecture design
role:swe          #bfdadc  # Teal - Software engineering
role:testing      #c2e0c6  # Light green - Testing work
role:debugging    #fef2c0  # Light yellow - Debugging work
role:deployment   #f9d0c4  # Orange - Deployment work
role:security     #e99695  # Light red - Security review
```

**Special Controls**:
```
allow:large-file  #f9d0c4  # Orange - Bypass file size checks
```

**Using GitHub CLI**:
```bash
# Autonomy control
gh label create "agent:go" --color "0e8a16" --description "On-demand approval for agent work"
gh label create "agent:sprint" --color "fbca04" --description "Sprint-mode approval"
gh label create "autonomy:override" --color "d73a4a" --description "Human override"

# Role assignment
gh label create "role:spec" --color "d4c5f9" --description "Specification work"
gh label create "role:architect" --color "c5def5" --description "Architecture design"
gh label create "role:swe" --color "bfdadc" --description "Software engineering"
gh label create "role:testing" --color "c2e0c6" --description "Testing work"
gh label create "role:debugging" --color "fef2c0" --description "Debugging work"
gh label create "role:deployment" --color "f9d0c4" --description "Deployment work"
gh label create "role:security" --color "e99695" --description "Security review"

# Special controls
gh label create "allow:large-file" --color "f9d0c4" --description "Bypass large file checks"
```

### Step 5: Configure CI

1. **Enable GitHub Actions**:
   - Go to repository Settings → Actions → General
   - Select "Allow all actions and reusable workflows"
   - Save changes

2. **Branch Protection** (optional but recommended):
   - Settings → Branches → Add rule
   - Branch name pattern: `main`
   - Enable "Require status checks to pass before merging"
   - Select "validate" check
   - Enable "Require branches to be up to date before merging"

3. **Validate CI**:
   ```bash
   # Push initial structure
   git add .
   git commit -m "Initial Kerrigan structure"
   git push origin main
   
   # Check Actions tab for workflow runs
   ```

### Step 6: Bootstrap Environment

```bash
# Run bootstrap script (if available)
bash tools/bootstrap.sh

# Or manually validate
python --version  # Should be 3.8+
python tools/validators/check_artifacts.py
python tools/validators/check_quality_bar.py
```

### Step 7: Validate Setup

Create a test issue to validate the system:

1. **Create issue** with label `agent:go` and `role:spec`
2. **Copy agent prompt** from `.github/agents/role.spec.md`
3. **Have agent create** a test project in `specs/projects/test-project/`
4. **Verify**:
   - CI passes on agent's PR
   - All required artifacts present
   - Quality bar checks pass

## File-by-File Setup Guide

### Priority 1: Critical Files

These files are absolutely required for Kerrigan to function:

#### specs/constitution.md
**Purpose**: Defines non-negotiable principles

**Minimal content**:
```markdown
# Constitution (Kerrigan Principles)

## 1) Quality from day one
- No "prototype exception" mode
- Start with structure, tests, and CI immediately

## 2) Small, reviewable increments
- PRs should be narrow and well-scoped
- Keep CI green

## 3) Artifact-driven collaboration
- Work must be expressed in repo artifacts
- If it isn't written down, it doesn't exist

## 4) Tests are part of the feature
- Every feature has tests
- Every bug fix includes a regression test

## 5) Stack-agnostic, contract-driven
- Compatible with any stack
- Contracts define artifacts and quality criteria

## 6) Operational responsibility
- Deployable work requires runbook and cost awareness
- Use secure secret handling

## 7) Human-in-the-loop
- Humans approve decisions and direction
- Agents own implementation excellence

## 8) Clarity for agents
- Keep entrypoints discoverable within ~100 lines
```

#### tools/validators/check_artifacts.py
**Purpose**: Validates required artifacts exist

**Setup**: This Python script enforces artifact contracts. See [Self-Assembly Guide](../docs/self-assembly.md) for full source code.

**Key validation logic**:
- Checks for required files in `specs/projects/*/`
- Validates required sections in spec.md and architecture.md
- Optionally validates status.json format

#### .github/workflows/ci.yml
**Purpose**: Runs validators on every PR

**Minimal content**:
```yaml
name: CI
on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [ main ]

permissions:
  contents: read
  pull-requests: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Run validators
        run: |
          python tools/validators/check_artifacts.py
          python tools/validators/check_quality_bar.py
      
      - name: Run tests
        run: |
          python -m unittest discover -s tests -p "test_*.py" -v
```

### Priority 2: Agent Prompts

Agent prompts define how agents behave. These are markdown files in `.github/agents/`:

- **role.spec.md**: Creates specifications from requirements
- **role.architect.md**: Designs system architecture
- **role.swe.md**: Implements features with tests
- **role.testing.md**: Strengthens test coverage
- **role.debugging.md**: Fixes failures
- **role.deployment.md**: Creates deployment runbooks
- **role.security.md**: Reviews for vulnerabilities
- **kerrigan.swarm-shaper.md**: Ensures constitution compliance

**Setup**: See [Self-Assembly Guide](../docs/self-assembly.md) for template structure.

### Priority 3: Documentation

Documentation helps humans and agents understand the system:

- **docs/setup.md**: First-time setup walkthrough
- **docs/architecture.md**: System design and workflow
- **docs/agent-assignment.md**: How to assign work
- **docs/FAQ.md**: Common questions
- **playbooks/*.md**: Process guides

**Setup**: Can be created from examples in the Kerrigan repository.

## Validation

After recovery, validate that Kerrigan is functioning:

### Automated Validation

```bash
# Run validators
python tools/validators/check_artifacts.py
python tools/validators/check_quality_bar.py

# Run test suite
python -m unittest discover -s tests -p "test_*.py" -v

# Check git status
git status

# Verify CI configuration
cat .github/workflows/ci.yml
```

### Manual Validation

1. **Create test issue**:
   - Title: "Test: Validate Kerrigan recovery"
   - Add labels: `agent:go`, `role:spec`

2. **Invoke spec agent**:
   - Copy prompt from `.github/agents/role.spec.md`
   - Paste into AI assistant with issue link
   - Agent should create test project in `specs/projects/test-recovery/`

3. **Verify agent output**:
   - Check that all required files are created
   - Verify CI passes on agent's PR
   - Review artifacts meet quality standards

4. **Clean up**:
   - Close test issue
   - Optionally delete test project

### Success Criteria

Kerrigan is fully recovered when:
- [ ] All critical files present and valid
- [ ] GitHub labels configured correctly
- [ ] CI workflows active and passing
- [ ] Validators run successfully
- [ ] Test suite passes
- [ ] Agent can complete test issue successfully
- [ ] Documentation is accessible and accurate

## Version Control Best Practices

When replicating Kerrigan to your repository:

1. **Use template or fork approach** - Start from the Kerrigan template repository
2. **Tag important milestones**: `git tag -a v1.0 -m "Initial Kerrigan setup"`
3. **Maintain detailed commit messages** - Document customizations you make
4. **Review PRs before merging** to catch issues early
5. **Keep main branch stable** - always passing CI
6. **Document team-specific adaptations** in your repository's README

## Setup Time Estimates

Time required to set up Kerrigan in a new repository:

| Scenario | Estimated Setup Time | Required Knowledge Level |
|----------|---------------------|-------------------------|
| New repository from template | 1-2 hours | Intermediate |
| New repository from scratch | 4-8 hours | Advanced |
| Adding to existing repository | 2-4 hours | Advanced |
| Fork and customize | 30-60 minutes | Beginner |
| Validate existing setup | 15-30 minutes | Beginner |

## Common Issues & Troubleshooting

### Issue: Validators fail after setup

**Symptoms**: `check_artifacts.py` reports missing sections

**Solution**:
```bash
# Check which project is failing
python tools/validators/check_artifacts.py

# Review the specific project structure
ls -la specs/projects/<project-name>/

# Compare against template
diff -r specs/projects/_template/ specs/projects/<project-name>/
```

### Issue: CI workflow not running

**Symptoms**: No checks appear on PRs

**Solution**:
1. Verify Actions enabled: Settings → Actions → General
2. Check workflow file syntax: `.github/workflows/ci.yml`
3. Review Actions tab for errors
4. Ensure Python version matches CI: `python-version: "3.11"`

### Issue: Labels missing or misconfigured

**Symptoms**: Autonomy gates fail, agents can't be assigned

**Solution**:
```bash
# List current labels
gh label list

# Recreate missing labels (see Step 4)
gh label create "agent:go" --color "0e8a16" --description "On-demand approval"
```

### Issue: Agent prompts not working

**Symptoms**: Agents produce incorrect or incomplete output

**Solution**:
1. Verify agent prompt file exists and is complete
2. Check that constitution.md is accessible
3. Ensure artifact contracts are defined
4. Review agent's context window size (may need to summarize)

## Support & Resources

### Documentation
- **Setup Guide**: [docs/setup.md](../docs/setup.md)
- **Architecture**: [docs/architecture.md](../docs/architecture.md)
- **Self-Assembly Guide**: [docs/self-assembly.md](../docs/self-assembly.md)
- **FAQ**: [docs/FAQ.md](../docs/FAQ.md)

### Reference Implementations
- **Examples**: [examples/](../examples/) directory
- **Kerrigan Project**: [specs/projects/kerrigan/](../specs/projects/kerrigan/)

### Community
- **GitHub Issues**: Report problems or ask questions
- **Discussions**: Share experiences and improvements

## Conclusion

This guide provides everything needed to replicate Kerrigan into new repositories and team settings. The key principle is that Kerrigan is **artifact-driven and git-native**, meaning it can be fully set up using the documentation and structure provided in this repository.

By following this guide, teams unfamiliar with Kerrigan can establish the agent swarm system in their own projects, adapting it to their specific needs while maintaining the core principles that make Kerrigan effective.

---

**Last Updated**: 2026-01-15
**Tested**: Yes - validated in clean environment
**Maintained by**: Kerrigan Core Team
