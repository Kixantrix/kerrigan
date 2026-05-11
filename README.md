# Kerrigan

[![CI](https://github.com/Kixantrix/kerrigan/actions/workflows/ci.yml/badge.svg)](https://github.com/Kixantrix/kerrigan/actions/workflows/ci.yml)

A stack-agnostic coding-swarm harness built on [GitHub Spec Kit](https://github.com/github/spec-kit). Two agent profiles (`local` conductor + `cloud` executor), spec-driven lifecycle, and automated verification.

> Agents read [AGENTS.md](AGENTS.md). Humans start here.

---

## Quick Start

### Templates

- **[template/minimal](../../tree/template/minimal)** — Core framework only
- **[template/with-examples](../../tree/template/with-examples)** — Core + 2 curated examples
- **[template/enterprise](../../tree/template/enterprise)** — Full tooling + all examples
- **main** — Complete reference (including development history)

### Setup

1. **[Use this template](https://github.com/Kixantrix/kerrigan/generate)** and choose your branch
2. **Create 4 labels**: `agent:go`, `agent:wait`, `agent:local`, `autonomy:override` ([details](docs/setup.md))
3. **Create an issue** with your goal and add the `agent:go` label
4. **Point your agent** at the repo — it reads [AGENTS.md](AGENTS.md) and starts working

**CI enforces**: artifact structure, quality bar (800 LOC max), autonomy gates.

📖 **[Full setup guide](docs/setup.md)** · **[FAQ](docs/FAQ.md)**

---

## Architecture

```
Human goal → local agent → spec-kit lifecycle → cloud dispatch → PR → review → merge
              (plans)      (specify → plan       (one task,       (CI + Copilot
                            → tasks)              one PR)          review → human
                                                                   reviews direction)
```

**Key principles** ([constitution](specs/constitution.md)):
- **Artifact-driven** — all work in repo files, validated by CI
- **Two profiles** — `local` plans and dispatches, `cloud` implements and self-verifies
- **Human-in-loop for direction** — agents handle technical quality; humans verify intent
- **Stack-agnostic** — works with any language, framework, or toolchain

---

## Documentation

### Getting Started
- **[Setup Guide](docs/setup.md)** — First-time setup walkthrough
- **[FAQ](docs/FAQ.md)** — Common questions
- **[CLI Reference](docs/cli-reference.md)** — `kerrigan check`, `kerrigan init`, etc.
- **[Architecture](docs/architecture.md)** — System design and workflow

### Agent Profiles
- **[AGENTS.md](AGENTS.md)** — Canonical entry point for all agents
- **[Agent Profiles](.github/agents/README.md)** — `local`, `cloud`, `kerrigan` + adapters
- **[Skills Library](.github/skills/README.md)** — Briefing packets, delegation rubric, etc.
- **[Skills Framework](skills/README.md)** — Project-specific skill templates

### Process
- **[Kickoff](playbooks/kickoff.md)** — Start a new project
- **[Project Lifecycle](playbooks/project-lifecycle.md)** — Active → completed → archived
- **[Autonomy Modes](playbooks/autonomy-modes.md)** — Label-based agent control
- **[PR Review](playbooks/pr-review.md)** — Review guidelines
- **[Replication Guide](playbooks/replication-guide.md)** — Set up Kerrigan in new repos

### Specifications
- **[Constitution](specs/constitution.md)** — 8 non-negotiable principles
- **[V2 Design](specs/kerrigan-v2/000-vision.md)** — Why 2 profiles, not 10 roles
- **[Delegation Rubric](specs/kerrigan-v2/050-delegation-rubric.md)** — Cloud vs local routing

---

## Autonomy Control

Four labels control agent work:

| Label | Purpose |
|-------|---------|
| `agent:go` | Agent has autonomy — proceed |
| `agent:wait` | Blocked on human — stop |
| `agent:local` | Requires human's machine (device I/O, secrets) |
| `autonomy:override` | Human override for a blocked gate |

See [playbooks/autonomy-modes.md](playbooks/autonomy-modes.md) for configuration.

---

## Quick Reference

| Task | How |
|------|-----|
| Start new project | `kerrigan init <name>` or copy `specs/projects/_template/` |
| Check project status | `kerrigan status <name>` |
| Enable agent work | Add `agent:go` label to issue |
| Validate locally | `kerrigan check` or `python tools/validators/check_artifacts.py` |
| Bootstrap environment | `bash tools/bootstrap.sh` |
| Install CLI | `cd tools/cli/kerrigan && pip install -e .` ([reference](docs/cli-reference.md)) |

---

## Repository Structure

```
kerrigan/
├── .github/
│   ├── agents/              # local, cloud, kerrigan profiles + adapters
│   ├── skills/              # Built-in skills (briefing, delegation, etc.)
│   └── workflows/           # CI: validators, autonomy gates, smoke tests
├── docs/                    # Setup, architecture, FAQ, guides
├── playbooks/               # Process guides (kickoff, lifecycle, review)
├── skills/                  # Project-specific skill templates
├── specs/
│   ├── constitution.md      # Core principles
│   ├── kerrigan-v2/         # V2 design specs (active)
│   └── projects/            # Your projects go here (_template/ included)
├── tools/
│   ├── validators/          # Artifact validation scripts
│   └── cli/                 # kerrigan CLI
├── examples/                # Complete example projects
├── feedback/                # Agent feedback backchannel
└── services/                # Optional: SDK agent service
```

---

## Contributing

- Fork and adapt for your workflow
- Add custom validators or skills
- Share feedback via the [satellite feedback system](feedback/satellite/README.md)

---

## License

MIT (see [LICENSE](LICENSE)).
