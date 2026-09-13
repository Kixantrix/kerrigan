# Kerrigan Replication Guide

## Purpose
This guide provides step-by-step instructions for setting up the Kerrigan agent swarm system in a new repository. Kerrigan is designed to be replicated into different team repositories and organizational settings, enabling effective agent-driven development workflows. This guide ensures someone unfamiliar with Kerrigan can establish the system using only this documentation.

For the current operating contract, follow [session operations](session-operations.md): direct app sessions are primary; issues are an optional adapter. Treat configuration examples as inputs to inspect, not permission to mutate another repository. Copy the current checked-in profiles, validators, and `verify.yml` through the authorized bootstrap rather than recreating retired v1 gates. Confirm worker-start and ownership acknowledgment; setup or issue/session metadata is not execution evidence.

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
4. Set up annotations only if using the optional issue adapter (see [GitHub Labels Setup](#github-labels-setup))
5. Configure CI workflows
6. Validate setup with bootstrap script

### Use Case 2: Adding to Existing Repository
**Situation**: An existing project wants to adopt Kerrigan's workflow without starting from scratch.

**Integration Steps**:
1. Clone the existing repository: `git clone <repo-url>`
2. Add Kerrigan structure alongside existing code
3. Configure validators to accommodate existing code structure
4. Preserve required workflows; configure optional issue-adapter annotations if used
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

The following historical layout sketch is retained for orientation, not as a current file manifest or instruction to recreate every listed workflow. Use [AGENTS.md](../AGENTS.md#where-things-live), the checked-in tree, and the [bootstrap guide](v2-bootstrap.md) for current paths. In particular, old `auto-triage-on-assign.yml`, role labels, and autonomy-control workflows are not prerequisites.

```
kerrigan/
├── .github/
│   ├── agents/              # v2 agent profiles
│   │   ├── README.md        # Overview of the two-profile model
│   │   ├── kerrigan.md      # Conductor + swarm-shaper (interactive)
│   │   ├── cloud.md         # Executor (cloud or worktree)
│   │   └── adapters/        # Thin adapters to built-in sub-agents (Explore, Plan, code-review)
│   ├── skills/              # Reusable agent knowledge (agent-skills spec)
│   ├── workflows/           # CI/CD automation
│   │   ├── verify.yml       # Main validation workflow (required check)
│   │   ├── budget-telemetry.yml
│   │   └── sync-template-branches.yml
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
   - verify.yml - Existing validators, tests and smoke checks, including dependent PR targets and merge-group support
   - Preserve other actually configured repository gates; do not recreate retired `agent-gates.yml` from historical instructions

6. **Playbooks** (playbooks/*.md)
   - kickoff.md - Project startup guide
   - session-operations.md - Dispatch, owner acknowledgment, delivery states and accountable handoffs
   - docs/operations/autonomy-modes.md - Authority and optional issue annotations

7. **Documentation** (docs/*.md)
   - setup.md - Setup walkthrough
   - architecture.md - System design
   - FAQ.md - Common questions

### Step 4: GitHub Labels Setup

Direct app sessions need no issue or label. For the optional issue adapter, use the four annotations in [GitHub labels](../docs/operations/github-labels.md). Retired v1 `agent:sprint` and `role:*` labels are migration history, not current role selection or permission controls.

```bash
# Optional issue-adapter annotations, when authorized
gh label create "agent:go" --color "0e8a16" --description "Issue ready for explicit assignment"
gh label create "agent:wait" --color "fbca04" --description "Issue intentionally waiting; not a runtime stop"
gh label create "agent:local" --color "5319e7" --description "Requires local capability"
gh label create "autonomy:override" --color "d73a4a" --description "Human-approved exception where supported"
```

Labels record intent; they do not start/stop app workers or grant permissions. Preserve any actual repository-specific merge gate and require human approval for a supported override.

### Step 5: Configure CI

1. **Enable GitHub Actions**:
   - Go to repository Settings → Actions → General
   - Select "Allow all actions and reusable workflows"
   - Save changes

2. **Branch Protection** (optional but recommended):
   - Settings → Branches → Add rule
   - Branch name pattern: `main`
   - Enable "Require status checks to pass before merging"
   - Select the checks declared by the repository's actual protection contract, not a name copied from a historical example
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

Choose one authorized, low-risk pilot outcome:

1. **Chat with `kerrigan`** in an app session; prepare the scope, AC/tests, owner, base, resources, and stop condition.
2. **Dispatch separately from planning**: `/speckit.tasks` generates tasks, not dispatch. Use an explicit app executor; for the optional issue adapter, `/kerrigan.dispatch` creates issues but does not itself assign Copilot. The coordinator separately performs and verifies authorized assignment.
3. **Confirm worker-start and ownership acknowledgment** before claiming success. The executor then implements the accepted pilot and opens one PR.
4. **Verify**:
   - `verify` workflow passes
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
**Historical minimal example, not the current installation contract.** Preserve this illustration for older repositories; do not use it to replace the checked-in `verify.yml`, dependencies, required jobs, or merge-group support. The current verify workflow runs validators, smoke and tests for main and dependent PR targets.

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

### Priority 2: Agent Profiles

Agent profiles define how agents behave. v2 keeps this to **two profiles** plus thin adapters:

- **`.github/agents/kerrigan.md`**: Conductor + swarm-shaper. Interactive; plans, dispatches, and maintains the harness. Never implements feature code directly.
- **`.github/agents/cloud.md`**: Executor. Runs one task slice end-to-end in a cloud container (GitHub Copilot) or a Claude Code worktree session. Writes code + tests, self-verifies, opens one PR.
- **`.github/agents/adapters/`**: Thin adapters to built-in sub-agents (`Explore`, `Plan` mode, Copilot code-review, Copilot coding agent).

Claude Code can mirror these from `.claude/agents/`; GitHub Copilot reads them directly.

**Setup**: See [Self-Assembly Guide](../docs/self-assembly.md) for template structure.

### Priority 3: Documentation

Documentation helps humans and agents understand the system:

- **docs/onboarding/setup.md**: First-time setup walkthrough
- **docs/architecture/architecture.md**: System design and workflow
- **docs/agent-assignment.md**: How to assign work
- **docs/onboarding/FAQ.md**: Common questions
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

# Verify current CI configuration
cat .github/workflows/verify.yml
```

### Manual Validation

1. **Define an authorized pilot outcome**:
   - Brief a direct app worker, or optionally create an issue annotated `agent:go` for explicit assignment.

2. **Dispatch via `kerrigan`**:
   - Chat with the `kerrigan` profile in VS Code / Claude Code / Copilot CLI.
   - Task generation, issue creation, assignment and worker-start acknowledgment are separate evidence steps. The issue adapter requires separately verified `@copilot` assignment.
   - Do not infer successful cloud startup/control from metadata alone. The acknowledged executor performs only the pilot slice and opens one PR.

3. **Verify agent output**:
   - Check that all required files are created
   - Verify `verify` workflow passes on the PR
   - Review artifacts meet quality standards

4. **Close out within authority**:
   - Preserve PRs, commits, unresolved work and handoff evidence; confirm resource release and automation stop.
   - Close an optional test issue or delete a pilot artifact only when explicitly authorized, not merely because the session is idle.

### Success Criteria

Kerrigan is fully recovered when:
- [ ] All critical files present and valid
- [ ] Optional issue-adapter annotations configured if used
- [ ] CI workflows active and passing
- [ ] Validators run successfully
- [ ] Test suite passes
- [ ] Worker started, acknowledged ownership and completed the accepted pilot with evidence
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
2. Check actual workflow syntax and PR-target filters: `.github/workflows/verify.yml`
3. Review Actions tab for errors
4. Ensure Python version and dependencies match the checked-in workflow

### Issue: Labels missing or misconfigured

**Symptoms**: The optional issue adapter's annotations or a configured repository-specific gate do not match expectations; app-session dispatch does not require labels.

**Solution**:
```bash
# List current labels
gh label list

# Recreate missing labels (see Step 4)
gh label create "agent:go" --color "0e8a16" --description "Issue ready for explicit assignment"
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
- **Setup Guide**: [docs/onboarding/setup.md](../docs/onboarding/setup.md)
- **Architecture**: [docs/architecture/architecture.md](../docs/architecture/architecture.md)
- **Self-Assembly Guide**: [docs/self-assembly.md](../docs/self-assembly.md)
- **FAQ**: [docs/onboarding/FAQ.md](../docs/onboarding/FAQ.md)

### Reference Implementations
- **Examples**: [examples/](../examples/) directory
- **Harness specs**: [specs/kerrigan-v2/](../specs/kerrigan-v2/)

### Community
- **GitHub Issues**: Report problems or ask questions
- **Discussions**: Share experiences and improvements

## Conclusion

This guide provides everything needed to replicate Kerrigan into new repositories and team settings. The key principle is that Kerrigan is **artifact-driven and git-native**, meaning it can be fully set up using the documentation and structure provided in this repository.

By following this guide, teams unfamiliar with Kerrigan can establish the agent swarm system in their own projects, adapting it to their specific needs while maintaining the core principles that make Kerrigan effective.

---

**Historical baseline**: 2026-01-15. The original guide recorded clean-environment validation; this documentation update does not re-attest current cloud startup/control or satellite execution.
**Maintained by**: Kerrigan Core Team
