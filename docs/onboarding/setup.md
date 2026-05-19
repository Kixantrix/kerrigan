# Setup Walkthrough

This guide walks you through setting up Kerrigan from scratch and running your first agent-driven project.

## Prerequisites

Before you begin, ensure you have:

- **GitHub Account**: With repository access where you'll use Kerrigan
- **Git**: Installed and configured on your machine
- **AI Agent Access**: GitHub Copilot or similar AI coding assistant
- **Python 3.8+**: For running validators (optional but recommended)
- **PowerShell 5.1+**: For local automation scripts (PowerShell 7+ recommended)

## Step 1: Choose Your Template and Create Repository

Kerrigan offers different templates for different needs. Choose the one that fits your experience level and project requirements:

### 📋 Template Options

Choose a template branch that fits your needs:

- **template/minimal** - Core framework only (best for beginners)
- **template/with-examples** - Core + 2 curated examples (best for learning)
- **template/enterprise** - Full tooling + all examples (best for teams)
- **🔬 main** - Complete reference including development history

### Option A: Use as Template (Recommended for New Projects)

1. Navigate to https://github.com/Kixantrix/kerrigan
2. Click **"Use this template"** → **"Create a new repository"**
3. Name your repository (e.g., `my-project-swarm`)
4. Choose visibility (public or private)
5. Click **"Create repository"**
6. **Choose your template branch**:
   ```bash
   git clone https://github.com/yourusername/my-project-swarm.git
   cd my-project-swarm
   
   # For minimal template (recommended for first-time users)
   git checkout template/minimal
   git checkout -b main
   git push origin main
   
   # Or for with-examples
   git checkout template/with-examples
   git checkout -b main
   git push origin main
   
   # Or for enterprise
   git checkout template/enterprise
   git checkout -b main
   git push origin main
   ```

### Option B: Clone Existing Repository
```bash
git clone https://github.com/yourusername/your-kerrigan-repo.git
cd your-kerrigan-repo
```

## Step 2: Set Up GitHub Labels

Kerrigan uses labels to control agent autonomy and assign work to agents. Create these labels in your repository:

### Required Labels

| Label | Description | Color |
|-------|-------------|-------|
| `agent:go` | Agent has autonomy — proceed | `#0e8a16` (green) |
| `agent:wait` | Blocked on human — stop | `#fbca04` (yellow) |
| `agent:local` | Requires human's machine | `#d4c5f9` (purple) |
| `autonomy:override` | Human override for a blocked gate | `#d73a4a` (red) |
| `allow:large-file` | Bypass large file checks (use sparingly) | `#f9d0c4` (orange) |

### Creating Labels via GitHub UI

1. Navigate to your repository
2. Click **"Issues"** → **"Labels"**
3. Click **"New label"**
4. Enter name, description, and color
5. Repeat for all required labels

### Creating Labels via GitHub CLI (Faster)

**Prerequisite**: Install GitHub CLI from https://cli.github.com/

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Ubuntu/Debian: sudo apt install gh  
# Windows: winget install GitHub.cli
# Or download from: https://cli.github.com/

# Authenticate
gh auth login

# Create required labels (v2: 4 labels)
gh label create "agent:go" --color "0e8a16" --description "Agent has autonomy - proceed" --force
gh label create "agent:wait" --color "fbca04" --description "Blocked on human - stop" --force
gh label create "agent:local" --color "5319e7" --description "Requires human machine" --force
gh label create "autonomy:override" --color "d73a4a" --description "Human override for blocked gate" --force

# Optional labels
gh label create "allow:large-file" --color "f9d0c4" --description "Bypass large file checks" --force
```

**Note**: Label colors are suggestions and can be customized to your preference.

## Step 3: Choose Your Autonomy Mode

Kerrigan v2 uses **2 agent profiles** (local conductor + cloud executor) with label-based gating:

- Add `agent:go` to an issue → cloud agent picks it up
- Add `agent:wait` to pause → agent stops
- Add `agent:local` when the task needs your machine (device I/O, secrets)
- Add `autonomy:override` to bypass a blocked gate

**Configuration**: Edit `playbooks/autonomy-modes.md` if you want to customize behavior.

## Step 4: Configure Agent Assignment (Optional)

Agent assignment automation is pre-configured but disabled by default. To enable automatic assignment of issues/PRs based on role labels:

### 1. Edit Assignment Configuration

Open `.github/automation/reviewers.json` and add GitHub usernames or teams:

```json
{
  "default_assignee": "your-github-username",
  "auto_assign_on_label": true,
  "comment_on_assignment": true
}
```

### 2. How It Works

When you add the `agent:go` label to an issue:
- Agents with access to the repo can pick up the work
- Work follows the spec-kit lifecycle: specify → plan → tasks → implement
- See [AGENTS.md](../../AGENTS.md) for full details

**Note**: This is optional. You can manually assign issues without labels.

## Step 5: Understand the Repository Structure

Familiarize yourself with the key directories:

```
your-repo/
├── .github/
│   ├── agents/           # Agent role prompts
│   └── workflows/        # CI configuration
├── specs/
│   ├── constitution.md   # Core principles
│   ├── kerrigan/         # Meta-specs (how Kerrigan works)
│   └── projects/         # Your projects go here
│       ├── _template/    # Template for new projects
│       └── <project>/    # Individual project folders
├── playbooks/            # Process documentation
├── tools/
│   └── validators/       # Artifact validation scripts
├── examples/             # Example projects
└── docs/                 # Additional documentation
```

## Step 6: Read Core Documentation

Before creating your first project, review these key documents:

1. **`README.md`**: Quick start and philosophy
2. **`specs/constitution.md`**: Non-negotiable principles
3. **`playbooks/kickoff.md`**: How to start a project
4. **`playbooks/autonomy-modes.md`**: How agent control works
5. **`.github/agents/README.md`**: Overview of agent roles

**Time investment**: ~15-20 minutes for initial reading

## Step 7: Create Your First Project

Let's create a simple project to test the workflow.

### 6.1: Create Project Folder

```bash
cd specs/projects/
cp -r _template/ my-first-project/
cd my-first-project/
```

### 6.2: Create a GitHub Issue

1. Go to your repository on GitHub
2. Click **"Issues"** → **"New issue"**
3. Title: `Create my-first-project: Hello World API`
4. Body:
   ```markdown
   ## Goal
   Create a simple REST API that responds with "Hello, World!" at GET /hello

   ## Scope
   - Single endpoint: GET /hello
   - Returns JSON: {"message": "Hello, World!"}
   - Include basic tests
   - Add README with usage instructions

   ## Success Criteria
   - API runs locally
   - Tests pass
   - Documentation is clear
   ```
5. Add label: `agent:go` (to enable agent work)
6. Click **"Submit new issue"**

### 6.3: Invoke the Spec Agent

Copy the `.github/agents/role.spec.md` prompt into your AI assistant along with:

```
Project name: my-first-project
Issue: [paste your issue URL]

Please create the spec.md and acceptance-tests.md files for this project.
```

The Spec Agent will create:
- `specs/projects/my-first-project/spec.md`
- `specs/projects/my-first-project/acceptance-tests.md`

### 6.4: Review and Commit Spec

Review the generated files and commit them:

```bash
git add specs/projects/my-first-project/
git commit -m "Add spec for my-first-project"
git push origin main
```

### 6.5: Invoke the Architect Agent

Copy the `.github/agents/role.architect.md` prompt with the project context. The Architect Agent will create:
- `architecture.md`
- `plan.md`
- `tasks.md`
- `test-plan.md`

### 6.6: Continue Through Agents

Follow the workflow defined in `playbooks/kickoff.md`:
1. Spec Agent (done)
2. Architect Agent (done)
3. Kerrigan Meta-Agent (validates constitution compliance)
4. SWE Agent (implements the feature)
5. Testing Agent (strengthens test coverage)
6. Deploy Agent (creates operational docs)

Each agent handoff is artifact-driven — one agent produces files that the next agent consumes.

## Step 8: Validate with CI

After each major change, push to GitHub and let CI run:

```bash
git add .
git commit -m "Implement my-first-project milestone 1"
git push origin main
```

CI will automatically:
- ✅ Validate artifact structure
- ✅ Check for required sections
- ✅ Enforce quality bar (max file size)
- ✅ Verify autonomy gates

If CI fails, check:
1. **Artifact Validator**: Do all required files exist? Do they have exact heading names?
2. **Autonomy Gates**: Is the issue labeled correctly?
3. **Quality Bar**: Are any files >800 lines? Use `allow:large-file` label if justified.

## Step 9: Work with Pull Requests

When an agent wants to merge work:

1. **Create PR** referencing the issue:
   ```
   Fixes #123
   
   Implementation of my-first-project milestone 1.
   ```

2. **CI Runs**: Autonomy gates check for labels
   - PR must reference an issue with `agent:go`
   - Or PR itself must have `autonomy:override` label

3. **Human Review**: Review the PR and either:
   - ✅ Approve and merge
   - 🔄 Request changes (agent iterates)
   - ❌ Close (start over)

## Step 10: Pause and Resume Work (Optional)

You can control agent workflow state with `status.json`:

### Pause Work
```bash
cat > specs/projects/my-first-project/status.json << EOF
{
  "status": "blocked",
  "current_phase": "implementation",
  "blocked_reason": "Awaiting security review",
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
git add specs/projects/my-first-project/status.json
git commit -m "Pause my-first-project for security review"
git push origin main
```

Agents will check `status.json` before starting work and respect the "blocked" status.

### Resume Work
```bash
cat > specs/projects/my-first-project/status.json << EOF
{
  "status": "active",
  "current_phase": "implementation",
  "notes": "Security review complete",
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
git add specs/projects/my-first-project/status.json
git commit -m "Resume my-first-project after security review"
git push origin main
```

## Common Issues and Solutions

### Issue 1: CI Fails with "Autonomy gate blocked"
**Solution**: Add `agent:go` label to the linked issue, or `autonomy:override` to the PR.

### Issue 2: Validator fails with "Missing required section"
**Solution**: Check that section headings match exactly (case-sensitive):
- ✅ `## Goal` not `## GOAL`
- ✅ `## Acceptance criteria` not `## Acceptance Criteria`

See `.github/agents/role.spec.md` and `role.architect.md` for exact heading names.

### Issue 3: Large file warning
**Solution**: 
- Refactor large files into smaller modules (<400 LOC ideal)
- If truly necessary, add `allow:large-file` label to PR

### Issue 4: Agent doesn't know what to do next
**Solution**: Check the briefing packet attached to the issue (see [`.github/skills/briefing-packet/SKILL.md`](../../.github/skills/briefing-packet/SKILL.md)) and the closest [`AGENTS.md`](../../AGENTS.md) for context.

## Next Steps

Now that you've completed your first project:

1. **Read `examples/`**: See complete example projects
2. **Customize agents**: Edit `.github/agents/*.md` for your workflow
3. **Set up multiple projects**: Create additional folders under `specs/projects/`
4. **Refine autonomy mode**: Adjust based on your team's comfort level
5. **Add custom validators**: Extend `tools/validators/` for your needs

## Getting Help

- **FAQ**: See `docs/onboarding/FAQ.md` for common questions
- **Architecture**: Read `docs/architecture/architecture.md` for system design
- **Issues**: Check existing issues in the repository
- **Community**: [Add your community links here]

## Quick Reference Card

| Need | Command/Action |
|------|----------------|
| Start new project | `cp -r specs/projects/_template/ specs/projects/<name>/` |
| Enable agent work | Add `agent:go` label to issue |
| Pause project | Create `status.json` with `"status": "blocked"` |
| Validate locally | `python tools/validators/check_artifacts.py` |
| Check CI status | View GitHub Actions tab |
| Override gates | Add `autonomy:override` label to PR |

Happy building with Kerrigan! 🚀
