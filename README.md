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

📖 **Full setup guide**: [docs/onboarding/setup.md](docs/onboarding/setup.md)

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

See [docs/architecture/architecture.md](docs/architecture/architecture.md) for complete details.

---

## 📚 Documentation

- [Setup Guide](docs/onboarding/setup.md) - Step-by-step walkthrough
- [Agent Assignment](docs/agent-assignment.md) - How to assign work via labels
- [FAQ](docs/onboarding/FAQ.md) - Common questions
- [Architecture](docs/architecture/architecture.md) - System design
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
