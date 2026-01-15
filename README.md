# Kerrigan

Kerrigan is a repo template for defining and evolving a **swarm of agents** that completes software projects the way *you* want them completed—without you having to be “the glue”.

This repo is intentionally **stack-agnostic**. It focuses on:
- a repeatable spec-driven workflow,
- artifact contracts between roles,
- a strict quality bar from day one,
- and optional autonomy controls for agent-driven PRs.

> Practical intent: agents should be able to pick up this repo, find what they need within ~100 lines, and reliably produce high-quality, reviewable PRs.

---

## 🚀 5-Minute Quickstart

**New to Kerrigan?** Get started fast:

1. **Clone or use as template**: [Use this template](https://github.com/Kixantrix/kerrigan/generate) to create your own repository
2. **Create GitHub labels**: `agent:go`, `agent:sprint`, `autonomy:override`, `allow:large-file`, plus role labels like `role:swe`, `role:spec` ([detailed instructions](docs/setup.md#step-2-set-up-github-labels))
3. **Create an issue** with your project idea and add the `agent:go` label
4. **Add role label** to assign work (e.g., `role:swe` for implementation tasks) — see [Agent Assignment Guide](docs/agent-assignment.md)
5. **Copy agent prompts** from `.github/agents/` to your AI assistant (GitHub Copilot, Claude, etc.)
6. **Let agents build**: Spec → Architecture → Implementation → Testing → Deploy

**CI automatically enforces**:
- Required artifacts and structure
- Quality bar (max 800 LOC per file)
- Autonomy gates (label-based control)

📖 **Full setup guide**: [docs/setup.md](docs/setup.md)

**Automation** (optional): Configure auto-assignment of reviewers, auto-generation of issues, and more. See [.github/automation/README.md](.github/automation/README.md) and [playbooks/automation.md](playbooks/automation.md) for setup.

---

## 📐 Architecture

Kerrigan orchestrates specialized agents through an artifact-driven workflow:

```
Issue → [Control Plane] → Spec Agent → Architect → SWE → Testing → Deploy → PR → Review → Merge
         ↑ Labels              ↓ Artifacts
         ↑ status.json         ↓ Validated by CI
```

**Visual diagram**: See [docs/architecture.md](docs/architecture.md) for complete workflow and component details.

**Key principles**:
- **Artifact-driven**: All work captured in repo files (specs, code, tests, runbooks)
- **Quality from day one**: No prototype mode—tests and structure from the start
- **Human-in-loop**: Humans decide strategy, agents execute details
- **Stack-agnostic**: Works with any language, framework, or toolchain

---

## 📚 Documentation

### Getting Started
- **[Setup Guide](docs/setup.md)**: Step-by-step walkthrough for first-time setup
- **[Agent Assignment](docs/agent-assignment.md)**: How to assign work to agents via labels
- **[Project Directory](docs/project-directory.md)**: Overview of all projects and their status
- **[FAQ](docs/FAQ.md)**: Answers to common questions
- **[Architecture](docs/architecture.md)**: System design and workflow visualization
- **[Self-Assembly Guide](docs/self-assembly.md)**: Technical reference for replicating Kerrigan

### Process & Workflow
- **[Kickoff Playbook](playbooks/kickoff.md)**: How to start a new project
- **[Project Lifecycle](playbooks/project-lifecycle.md)**: Managing projects from active to completed/archived
- **[Autonomy Modes](playbooks/autonomy-modes.md)**: Control when agents can work
- **[Handoffs](playbooks/handoffs.md)**: How agents pass work between phases
- **[PR Review](playbooks/pr-review.md)**: Human review guidelines
- **[Replication Guide](playbooks/replication-guide.md)**: Set up Kerrigan in new repositories

### Specifications
- **[Constitution](specs/constitution.md)**: Non-negotiable principles
- **[Artifact Contracts](specs/kerrigan/020-artifact-contracts.md)**: Required files and structure
- **[Quality Bar](specs/kerrigan/030-quality-bar.md)**: Quality standards and enforcement

### Agent Roles
- **[Agent README](.github/agents/README.md)**: Overview of all agent types
- **Individual prompts**: See `.github/agents/role.*.md` for each specialized agent

---

## 🎯 Autonomy Control

Kerrigan gives you fine-grained control over when agents can work:

**Autonomy gates**: PRs require `agent:go` or `agent:sprint` label on linked issues, or `autonomy:override` label on the PR itself. This ensures human control over when agents can work.

**Status tracking**: Use `status.json` to pause/resume work:
```json
{"status": "blocked", "blocked_reason": "Awaiting security review"}
```

See [playbooks/autonomy-modes.md](playbooks/autonomy-modes.md) for detailed configuration options.

---

## 📋 Quick Reference

| Task | Command/Location |
|------|------------------|
| Start new project | `cp -r specs/projects/_template/ specs/projects/<name>/` |
| Enable agent work | Add `agent:go` label to GitHub issue |
| Pause project | Create `status.json` with `"status": "blocked"` |
| Invoke agent | Copy prompt from `.github/agents/role.*.md` |
| Validate locally | `python tools/validators/check_artifacts.py` |
| Bootstrap environment | `bash tools/bootstrap.sh` |
| Check CI | View GitHub Actions tab |

---

## 🗂️ Repository Structure

```
kerrigan/
├── .github/
│   ├── agents/              # Agent role prompts (Spec, Architect, SWE, etc.)
│   └── workflows/           # CI configuration (validators, autonomy gates)
├── docs/                    # Comprehensive documentation
│   ├── architecture.md      # System design and workflow diagram
│   ├── setup.md            # Step-by-step setup guide
│   └── FAQ.md              # Frequently asked questions
├── playbooks/               # Process guides (kickoff, handoffs, autonomy modes)
├── specs/
│   ├── constitution.md      # Core principles
│   ├── kerrigan/           # Meta-specs (how Kerrigan works)
│   └── projects/           # Your projects go here
│       ├── _template/      # Template for new projects
│       └── <project>/      # Individual project artifacts
├── tools/
│   └── validators/         # Artifact validation scripts
└── examples/               # Complete example projects
```

---

## 🤝 Contributing

Kerrigan is designed to be customized! Feel free to:
- Fork and adapt for your workflow
- Add custom validators or agent roles
- Improve documentation
- Share examples and learnings

See examples in `examples/` and specifications in `specs/kerrigan/` for how the system works.

---

## 📜 License

MIT (see `LICENSE`).

---

## 🙋 Need Help?

- **First time?** Start with the [Setup Guide](docs/setup.md)
- **Questions?** Check the [FAQ](docs/FAQ.md)
- **Issues?** Open a GitHub issue
- **Want to understand the system?** Read the [Architecture](docs/architecture.md)
