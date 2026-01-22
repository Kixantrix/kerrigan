#!/bin/bash
# Script to create template branches for Kerrigan
# This script creates three template branches with different levels of content:
# - template/minimal: Core framework only
# - template/with-examples: Core + 2 curated examples
# - template/enterprise: Core + all examples minus investigation artifacts

set -e

# Determine repository directory dynamically
REPO_DIR="$(git rev-parse --show-toplevel)"
cd "$REPO_DIR"

echo "Creating Kerrigan template branches..."
echo "Working directory: $REPO_DIR"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Get the current branch to return to later
ORIGINAL_BRANCH=$(git branch --show-current)
echo "Current branch: $ORIGINAL_BRANCH"
echo ""

# Files/dirs to remove for ALL templates (investigation artifacts)
INVESTIGATION_ARTIFACTS=(
  "DESIGN-SYSTEM-IMPLEMENTATION-SUMMARY.md"
  "MILESTONE-2-VALIDATION.md"
  "MILESTONE-3-COMPLETION.md"
  "MILESTONE-4-COMPLETION.md"
  "docs/milestone-6-retrospective.md"
  "docs/AGENT-SPEC-VALIDATION-SUMMARY.md"
  "docs/fresh-user-test.md"
  "docs/test-issue-agent-workflow.md"
)

# Agent feedback files to remove (keep TEMPLATE.yaml)
AGENT_FEEDBACK_FILES=(
  "feedback/agent-feedback/2026-01-17-67-draft-pr-ci-triggering.yaml"
  "feedback/agent-feedback/2026-01-17-71-powershell-unicode-compatibility.yaml"
  "feedback/agent-feedback/2026-01-17-71-triage-role-success.yaml"
  "feedback/agent-feedback/2026-01-17-74-quality-bar-label-override.yaml"
  "feedback/agent-feedback/2026-01-17-88-phased-issue-creation-strategy.yaml"
  "feedback/agent-feedback/2026-01-17-88-proactive-label-creation.yaml"
  "feedback/agent-feedback/2026-01-17-copilot-reviewer-feedback-workflow.yaml"
  "feedback/agent-feedback/2026-01-17-feedback-archival-mechanism.yaml"
  "feedback/agent-feedback/2026-01-17-self-improvement-report-visibility.yaml"
  "feedback/agent-feedback/2026-01-17-triage-script-coverage-gaps.yaml"
  "feedback/agent-feedback/2026-01-18-96-git-rebase-interactive-mode.yaml"
)

# Meta-project specs to remove
META_PROJECT_SPECS=(
  "specs/projects/kerrigan"
  "specs/kerrigan/agents"
)

# All examples except hello-swarm and hello-api
EXAMPLE_PROJECTS_TO_REMOVE=(
  "examples/hello-cli"
  "examples/hello-multiapp-api"
  "examples/hello-multiapp-frontend"
  "examples/hello-multiapp-infra"
  "examples/task-dashboard-design"
  "examples/task-tracker"
  "examples/task-tracker-real"
  "examples/MULTI-REPO-WALKTHROUGH.md"
)

# All example project specs except hello-swarm and hello-api
SPEC_PROJECTS_TO_REMOVE=(
  "specs/projects/design-system-playground"
  "specs/projects/hello-cli"
  "specs/projects/pause-resume-demo"
  "specs/projects/task-dashboard-example"
  "specs/projects/task-tracker-real"
  "specs/projects/validator-enhancement"
)

# Function to remove files safely
remove_files() {
    local files=("$@")
    for file in "${files[@]}"; do
        if [ -e "$file" ]; then
            git rm -rf "$file" 2>/dev/null || true
            echo "  ✓ Removed: $file"
        fi
    done
}

# ============================================
# Create template/minimal branch
# ============================================
echo "============================================"
echo "Creating template/minimal branch..."
echo "============================================"

# Check if branch exists and delete it
if git show-ref --verify --quiet refs/heads/template/minimal; then
    echo "Branch template/minimal already exists. Deleting..."
    git branch -D template/minimal
fi

git checkout -b template/minimal

echo "Removing investigation artifacts..."
remove_files "${INVESTIGATION_ARTIFACTS[@]}"

echo "Removing agent feedback files..."
remove_files "${AGENT_FEEDBACK_FILES[@]}"

echo "Removing meta-project specs..."
remove_files "${META_PROJECT_SPECS[@]}"

echo "Removing ALL examples..."
if [ -d "examples" ]; then
    git rm -rf examples 2>/dev/null || true
    echo "  ✓ Removed: examples/"
fi

echo "Removing example project specs..."
remove_files "${SPEC_PROJECTS_TO_REMOVE[@]}"
for project in "hello-swarm" "hello-api"; do
    if [ -d "specs/projects/$project" ]; then
        git rm -rf "specs/projects/$project" 2>/dev/null || true
        echo "  ✓ Removed: specs/projects/$project"
    fi
done

# Create a minimal examples README
mkdir -p examples
cat > examples/README.md << 'EXEOF'
# Examples

This is the minimal template. For working examples, see:
- [template/with-examples](../../tree/template/with-examples) - Includes hello-swarm and hello-api
- [template/enterprise](../../tree/template/enterprise) - Includes all examples
- [main](../../tree/main) - Complete reference with all examples and development history

To add examples to your project:
```bash
# Cherry-pick specific examples from another template
git checkout template/with-examples -- examples/hello-swarm examples/hello-api
git commit -m "Add example projects"
```
EXEOF
git add examples/README.md

# Update README for minimal template
cat > README.md << 'READMEEOF'
# Kerrigan (Minimal Template)

This is the **minimal template** of Kerrigan - a repo template for defining and evolving a **swarm of agents** that completes software projects the way *you* want them completed—without you having to be "the glue".

This template includes:
- ✅ Core framework specs (constitution, agent archetypes, contracts)
- ✅ Agent prompts (`.github/agents/`)
- ✅ CI/CD workflows (`.github/workflows/`)
- ✅ Essential tools (validators, scripts)
- ✅ Basic documentation (setup, FAQ, architecture)
- ✅ Playbooks for common workflows

This template **excludes**:
- ❌ Example projects (for examples, see [template/with-examples](../../tree/template/with-examples))
- ❌ Investigation artifacts and milestone documents
- ❌ Development history

**Need more?** See [TEMPLATE-BRANCHES.md](TEMPLATE-BRANCHES.md) for other templates.

---

## 🚀 Quick Start

1. **Create GitHub labels**: `agent:go`, `agent:sprint`, `autonomy:override`, `allow:large-file`, plus role labels
2. **Create an issue** with your project idea and add the `agent:go` label
3. **Add role label** to assign work (e.g., `role:swe`)
4. **Copy agent prompts** from `.github/agents/` to your AI assistant
5. **Let agents build**: Spec → Architecture → Implementation → Testing

📖 **Full setup guide**: [docs/setup.md](docs/setup.md)

---

## 📐 How It Works

```
Issue → [Control Plane] → Spec Agent → Architect → SWE → Testing → Deploy
         ↑ Labels              ↓ Artifacts
         ↑ status.json         ↓ Validated by CI
```

**Key principles**:
- **Artifact-driven**: All work captured in repo files
- **Quality from day one**: Tests and structure from the start
- **Human-in-loop**: Humans decide strategy, agents execute
- **Stack-agnostic**: Works with any language or framework

See [docs/architecture.md](docs/architecture.md) for complete details.

---

## 📚 Documentation

- [Setup Guide](docs/setup.md) - Step-by-step walkthrough
- [Agent Assignment](docs/agent-assignment.md) - How to assign work via labels
- [FAQ](docs/FAQ.md) - Common questions
- [Architecture](docs/architecture.md) - System design
- [Constitution](specs/constitution.md) - Core principles
- [Artifact Contracts](specs/kerrigan/020-artifact-contracts.md) - Required files

---

## 📋 Templates

- **🎯 template/minimal** (this branch) - Quick start
- **📚 [template/with-examples](../../tree/template/with-examples)** - With curated examples
- **🏢 [template/enterprise](../../tree/template/enterprise)** - Full-featured
- **🔬 [main](../../tree/main)** - Complete reference

See [TEMPLATE-BRANCHES.md](TEMPLATE-BRANCHES.md) for details.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.
READMEEOF
git add README.md

git commit -m "Create template/minimal branch with core framework only" || echo "Nothing to commit"

echo "✓ template/minimal created"
echo ""

# ============================================
# Create template/with-examples branch
# ============================================
echo "============================================"
echo "Creating template/with-examples branch..."
echo "============================================"

git checkout "$ORIGINAL_BRANCH"

if git show-ref --verify --quiet refs/heads/template/with-examples; then
    echo "Branch template/with-examples already exists. Deleting..."
    git branch -D template/with-examples
fi

git checkout -b template/with-examples

echo "Removing investigation artifacts..."
remove_files "${INVESTIGATION_ARTIFACTS[@]}"

echo "Removing agent feedback files..."
remove_files "${AGENT_FEEDBACK_FILES[@]}"

echo "Removing meta-project specs..."
remove_files "${META_PROJECT_SPECS[@]}"

echo "Removing non-essential examples (keeping hello-swarm and hello-api)..."
remove_files "${EXAMPLE_PROJECTS_TO_REMOVE[@]}"

echo "Removing non-essential spec projects..."
remove_files "${SPEC_PROJECTS_TO_REMOVE[@]}"

# Update examples README
cat > examples/README.md << 'EXEOF'
# Examples

This template includes two curated examples:

## 🐝 hello-swarm
A minimal multi-agent example showing the basic Kerrigan workflow.

## 🌐 hello-api
A practical REST API example demonstrating real-world usage.

## Need More Examples?

- **[template/enterprise](../../tree/template/enterprise)** - All examples
- **[main](../../tree/main)** - Complete reference with development history

To add more examples:
```bash
git checkout template/enterprise -- examples/hello-cli
git commit -m "Add hello-cli example"
```
EXEOF
git add examples/README.md

# Update README for with-examples template
cat > README.md << 'READMEEOF'
# Kerrigan (With Examples Template)

This is the **with-examples template** of Kerrigan - a repo template for defining and evolving a **swarm of agents** that completes software projects the way *you* want them completed—without you having to be "the glue".

This template includes:
- ✅ Core framework specs (constitution, agent archetypes, contracts)
- ✅ Agent prompts (`.github/agents/`)
- ✅ CI/CD workflows (`.github/workflows/`)
- ✅ Essential tools (validators, scripts)
- ✅ Documentation (setup, FAQ, architecture)
- ✅ Playbooks for common workflows
- ✅ **2 curated examples** (hello-swarm, hello-api)

This template **excludes**:
- ❌ Additional examples (for all examples, see [template/enterprise](../../tree/template/enterprise))
- ❌ Investigation artifacts and milestone documents
- ❌ Development history

**Need more?** See [TEMPLATE-BRANCHES.md](TEMPLATE-BRANCHES.md) for other templates.

---

## 🚀 Quick Start

1. **Study the examples**: Check out `examples/hello-swarm` and `examples/hello-api`
2. **Create GitHub labels**: `agent:go`, `agent:sprint`, `autonomy:override`, `allow:large-file`, plus role labels
3. **Create an issue** with your project idea and add the `agent:go` label
4. **Add role label** to assign work (e.g., `role:swe`)
5. **Copy agent prompts** from `.github/agents/` to your AI assistant
6. **Let agents build**: Spec → Architecture → Implementation → Testing

📖 **Full setup guide**: [docs/setup.md](docs/setup.md)

---

## 📐 How It Works

```
Issue → [Control Plane] → Spec Agent → Architect → SWE → Testing → Deploy
         ↑ Labels              ↓ Artifacts
         ↑ status.json         ↓ Validated by CI
```

See [docs/architecture.md](docs/architecture.md) for complete details.

---

## 📚 Documentation

- [Setup Guide](docs/setup.md) - Step-by-step walkthrough
- [Agent Assignment](docs/agent-assignment.md) - How to assign work via labels
- [FAQ](docs/FAQ.md) - Common questions
- [Architecture](docs/architecture.md) - System design

---

## 📋 Templates

- **🎯 [template/minimal](../../tree/template/minimal)** - Quick start
- **📚 template/with-examples** (this branch) - With curated examples
- **🏢 [template/enterprise](../../tree/template/enterprise)** - Full-featured
- **🔬 [main](../../tree/main)** - Complete reference

See [TEMPLATE-BRANCHES.md](TEMPLATE-BRANCHES.md) for details.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.
READMEEOF
git add README.md

git commit -m "Create template/with-examples branch with core + curated examples" || echo "Nothing to commit"

echo "✓ template/with-examples created"
echo ""

# ============================================
# Create template/enterprise branch
# ============================================
echo "============================================"
echo "Creating template/enterprise branch..."
echo "============================================"

git checkout "$ORIGINAL_BRANCH"

if git show-ref --verify --quiet refs/heads/template/enterprise; then
    echo "Branch template/enterprise already exists. Deleting..."
    git branch -D template/enterprise
fi

git checkout -b template/enterprise

echo "Removing investigation artifacts..."
remove_files "${INVESTIGATION_ARTIFACTS[@]}"

echo "Removing agent feedback files..."
remove_files "${AGENT_FEEDBACK_FILES[@]}"

echo "Removing meta-project specs..."
remove_files "${META_PROJECT_SPECS[@]}"

# Update README for enterprise template
cat > README.md << 'READMEEOF'
# Kerrigan (Enterprise Template)

This is the **enterprise template** of Kerrigan - a repo template for defining and evolving a **swarm of agents** that completes software projects the way *you* want them completed—without you having to be "the glue".

This template includes:
- ✅ Core framework specs (constitution, agent archetypes, contracts)
- ✅ Agent prompts (`.github/agents/`)
- ✅ CI/CD workflows (`.github/workflows/`)
- ✅ Complete tooling (validators, scripts, automation)
- ✅ Comprehensive documentation
- ✅ All playbooks
- ✅ **All 9+ example projects**

This template **excludes** only:
- ❌ Investigation artifacts and milestone documents
- ❌ Agent feedback history (development iterations)
- ❌ Meta-project specs about Kerrigan itself

**Need less?** See [TEMPLATE-BRANCHES.md](TEMPLATE-BRANCHES.md) for simpler templates.

---

## 🚀 Quick Start

1. **Explore examples**: 9+ complete examples in `examples/`
2. **Create GitHub labels**: `agent:go`, `agent:sprint`, `autonomy:override`, `allow:large-file`, plus role labels
3. **Create an issue** with your project idea and add the `agent:go` label
4. **Add role label** to assign work (e.g., `role:swe`)
5. **Copy agent prompts** from `.github/agents/` to your AI assistant
6. **Let agents build**: Spec → Architecture → Implementation → Testing

📖 **Full setup guide**: [docs/setup.md](docs/setup.md)

---

## 📐 Architecture

```
Issue → [Control Plane] → Spec Agent → Architect → SWE → Testing → Deploy
         ↑ Labels              ↓ Artifacts
         ↑ status.json         ↓ Validated by CI
```

See [docs/architecture.md](docs/architecture.md) for complete workflow details.

---

## 📚 Documentation

Comprehensive documentation for all aspects:

### Getting Started
- [Setup Guide](docs/setup.md)
- [CLI Reference](docs/cli-reference.md)
- [Agent Assignment](docs/agent-assignment.md)
- [FAQ](docs/FAQ.md)

### Process & Workflow
- [Kickoff Playbook](playbooks/kickoff.md)
- [Project Lifecycle](playbooks/project-lifecycle.md)
- [Autonomy Modes](playbooks/autonomy-modes.md)
- [Handoffs](playbooks/handoffs.md)

### Specifications
- [Constitution](specs/constitution.md)
- [Artifact Contracts](specs/kerrigan/020-artifact-contracts.md)
- [Quality Bar](specs/kerrigan/030-quality-bar.md)

---

## 📋 Templates

- **🎯 [template/minimal](../../tree/template/minimal)** - Quick start
- **📚 [template/with-examples](../../tree/template/with-examples)** - With curated examples
- **🏢 template/enterprise** (this branch) - Full-featured
- **🔬 [main](../../tree/main)** - Complete reference

See [TEMPLATE-BRANCHES.md](TEMPLATE-BRANCHES.md) for details.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.
READMEEOF
git add README.md

git commit -m "Create template/enterprise branch with full tooling minus investigation artifacts" || echo "Nothing to commit"

echo "✓ template/enterprise created"
echo ""

# ============================================
# Summary
# ============================================
echo "============================================"
echo "Template branches created successfully!"
echo "============================================"
echo ""
echo "Created branches:"
if git branch -a | grep -q template; then
    git branch -a | grep template
else
    echo "No template branches found"
fi
echo ""
echo "To push these branches to GitHub:"
echo "  git push -u origin template/minimal"
echo "  git push -u origin template/with-examples"
echo "  git push -u origin template/enterprise"
echo ""

# Return to original branch
git checkout "$ORIGINAL_BRANCH"
echo "Returned to branch: $ORIGINAL_BRANCH"
