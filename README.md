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

📖 **Full setup guide**: [docs/onboarding/setup.md](docs/onboarding/setup.md)

---

## 📐 Architecture

```
Issue → [Control Plane] → Spec Agent → Architect → SWE → Testing → Deploy
         ↑ Labels              ↓ Artifacts
         ↑ status.json         ↓ Validated by CI
```

See [docs/architecture/architecture.md](docs/architecture/architecture.md) for complete workflow details.

---

## 📚 Documentation

Comprehensive documentation for all aspects:

### Getting Started
- [Setup Guide](docs/onboarding/setup.md)
- [CLI Reference](docs/operations/cli-reference.md)
- [Agent Assignment](docs/agent-assignment.md)
- [FAQ](docs/onboarding/FAQ.md)

### Process & Workflow
- [Kickoff Playbook](playbooks/kickoff.md)
- [Project Lifecycle](playbooks/project-lifecycle.md)
- [Autonomy Modes](playbooks/autonomy-modes.md)

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
