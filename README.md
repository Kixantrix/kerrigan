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
