# Kerrigan Template Branches

This repository offers multiple template branches to support different use cases and experience levels. Choose the template that best fits your needs.

## Available Templates

### 🎯 `template/minimal` - Quick Start Template

**Best for**: First-time users who want to get started quickly with minimal configuration.

**Includes**:
- Core framework specs (constitution, agent archetypes, contracts)
- Agent prompts (`.github/agents/`)
- CI/CD workflows (`.github/workflows/`)
- Essential tools (validators, scripts)
- Basic documentation (setup, FAQ, architecture)
- Playbooks for common workflows

**Excludes**:
- All example projects
- Investigation artifacts and milestone documents
- Agent feedback history
- Meta-project specs about Kerrigan itself

**Usage**:
```bash
# Create a new repository from this template
gh repo create my-project --template Kixantrix/kerrigan --clone
cd my-project
git checkout template/minimal
git checkout -b main
git push origin main
```

### 📚 `template/with-examples` - Learning Template

**Best for**: Users who want to learn Kerrigan patterns through practical examples.

**Includes everything from minimal, plus**:
- `hello-swarm` - Minimal multi-agent example
- `hello-api` - Practical REST API example
- Example project documentation

**Usage**:
```bash
gh repo create my-project --template Kixantrix/kerrigan --clone
cd my-project
git checkout template/with-examples
git checkout -b main
git push origin main
```

### 🏢 `template/enterprise` - Full-Featured Template

**Best for**: Teams that want comprehensive tooling and all available examples.

**Includes everything from with-examples, plus**:
- All example projects (9 examples)
- Complete automation tooling
- Extended documentation
- All playbooks and guides

**Excludes**:
- Investigation artifacts (MILESTONE-*.md, *-VALIDATION.md, *-SUMMARY.md)
- Agent feedback history (feedback/agent-feedback/*.yaml except TEMPLATE.yaml)
- Meta-project specs (specs/projects/kerrigan/, specs/kerrigan/agents/)
- Milestone retrospectives

**Usage**:
```bash
gh repo create my-project --template Kixantrix/kerrigan --clone
cd my-project
git checkout template/enterprise
git checkout -b main
git push origin main
```

### 🔬 `main` - Full Reference Implementation

**Best for**: Contributing to Kerrigan or studying its complete development history.

**Includes**: Everything, including development artifacts, feedback files, and meta-project specs.

## Quick Comparison

| Feature | minimal | with-examples | enterprise | main |
|---------|---------|---------------|------------|------|
| Core framework | ✅ | ✅ | ✅ | ✅ |
| Agent prompts | ✅ | ✅ | ✅ | ✅ |
| CI/CD workflows | ✅ | ✅ | ✅ | ✅ |
| Essential docs | ✅ | ✅ | ✅ | ✅ |
| Basic examples | ❌ | ✅ (2) | ✅ (9+) | ✅ (9+) |
| All examples | ❌ | ❌ | ✅ | ✅ |
| Investigation artifacts | ❌ | ❌ | ❌ | ✅ |
| Development history | ❌ | ❌ | ❌ | ✅ |

## Choosing Your Template

**Start with `template/minimal` if**:
- You're new to Kerrigan
- You want a clean slate for your project
- You prefer to learn as you go

**Use `template/with-examples` if**:
- You want to see working examples
- You learn best by studying real implementations
- You want practical reference patterns

**Use `template/enterprise` if**:
- You're setting up for a team
- You want all available tooling
- You need comprehensive examples

**Use `main` if**:
- You're contributing to Kerrigan itself
- You want to study the complete development process
- You need all historical context

## Maintenance

Template branches are maintained by syncing from `main` and selectively removing files:

- **template/minimal**: Core files only
- **template/with-examples**: Core + curated examples
- **template/enterprise**: Core + all examples and tooling

Updates to core files in `main` are periodically synced to template branches.

## Support

- **Documentation**: See [docs/setup.md](docs/setup.md) for detailed setup instructions
- **Issues**: Report problems or suggest improvements in the [issue tracker](https://github.com/Kixantrix/kerrigan/issues)
- **Questions**: Check the [FAQ](docs/FAQ.md) or open a discussion

## Migration

If you started with one template and want to add features from another:

```bash
# Add files from another template branch
git checkout template/with-examples -- examples/hello-swarm examples/hello-api
git commit -m "Add example projects from template/with-examples"
```

Or cherry-pick specific files you need from `main`.
