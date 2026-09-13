# Kerrigan

[![CI](https://github.com/Kixantrix/kerrigan/actions/workflows/ci.yml/badge.svg)](https://github.com/Kixantrix/kerrigan/actions/workflows/ci.yml)

A stack-agnostic coding-swarm harness built on [GitHub Spec Kit](https://github.com/github/spec-kit). Two agent profiles (`kerrigan` conductor + `cloud` executor), spec-driven lifecycle, and automated verification.

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
2. **Open a GitHub Copilot app session** in the repo and give `kerrigan` your outcome
3. **Let the conductor brief and dispatch explicit executor sessions** on capability-appropriate local/cloud hosts — see [session operations](playbooks/session-operations.md)
4. **Use issues optionally** for context or issue-agent dispatch; labels and `@copilot` assignment belong to that adapter ([setup](docs/onboarding/setup.md)). Existing repository gates still apply.

**Startup defaults:** explicit profile selection or delegated worker assignment wins on either host. Otherwise, local human-facing conversations follow `kerrigan`, and known cloud execution follows `cloud`. These instructions govern behavior, not the app's picker or permissions. Give the conductor an outcome; it owns routine sequencing and child decisions through authorized delivery. See [startup role policy](AGENTS.md#startup-role-policy) and [outcome ownership](AGENTS.md#outcome-ownership).

**CI enforces**: the checked-in validators, tests, and smoke checks, including artifact structure and quality rules. There is no implemented autonomy-label gate in this repository; honor any additional gates actually configured in a consuming repository.

📖 **[Full setup guide](docs/onboarding/setup.md)** · **[FAQ](docs/onboarding/FAQ.md)**

---

## Architecture

```
Human goal → kerrigan → spec-kit lifecycle → worker session → PR → review → merge
              (plans)      (specify → plan       (one task,       (CI + Copilot
                            → tasks)              one PR)          review → human
                                                                   reviews direction)
```

**Key principles** ([constitution](specs/constitution.md)):
- **Artifact-driven** — all work in repo files, validated by CI
- **Two profiles** — `kerrigan` plans and dispatches, `cloud` implements and self-verifies
- **Human-in-loop for direction** — agents handle technical quality; humans verify intent
- **Stack-agnostic** — works with any language, framework, or toolchain

---

## Documentation

### Getting Started
- **[Setup Guide](docs/onboarding/setup.md)** — First-time setup walkthrough
- **[FAQ](docs/onboarding/FAQ.md)** — Common questions
- **[CLI Reference](docs/operations/cli-reference.md)** — `kerrigan check`, `kerrigan init`, etc.
- **[Architecture](docs/architecture/architecture.md)** — System design and workflow

### Agent Profiles
- **[AGENTS.md](AGENTS.md)** — Canonical entry point for all agents
- **[Agent Profiles](.github/agents/README.md)** — `kerrigan`, `cloud` + adapters
- **[Skills Library](.github/skills/README.md)** — Briefing packets, delegation rubric, etc.
- **[Skills Framework](skills/README.md)** — Project-specific skill templates

### Process
- **[Session Operations](playbooks/session-operations.md)** — Primary app dispatch, ownership, resources, triage, and automation boundaries
- **[Kickoff](playbooks/kickoff.md)** — Start a new project
- **[Project Lifecycle](playbooks/project-lifecycle.md)** — Active → completed → archived
- **[2D & 3D Asset Design](playbooks/asset-design.md)** — Cards, CAD/CNC, voxel game assets
- **[Autonomy Modes](docs/operations/autonomy-modes.md)** — Session authority and optional issue-adapter annotations
- **[PR Review](playbooks/pr-review.md)** — Review guidelines
- **[Replication Guide](playbooks/replication-guide.md)** — Set up Kerrigan in new repos

### Specifications
- **[Constitution](specs/constitution.md)** — 8 non-negotiable principles
- **[V2 Design](specs/kerrigan-v2/000-vision.md)** — Why 2 profiles, not 10 roles
- **[Delegation Rubric](specs/kerrigan-v2/050-delegation-rubric.md)** — Cloud vs local routing

---

## Autonomy Control

Four labels annotate the optional issue path; they do not control app sessions or grant permissions:

| Label | Purpose |
|-------|---------|
| `agent:go` | Issue ready for dispatch |
| `agent:wait` | Issue intentionally undispatched |
| `agent:local` | Requires human's machine (device I/O, secrets) |
| `autonomy:override` | Human override for a blocked gate |

See [docs/operations/autonomy-modes.md](docs/operations/autonomy-modes.md) for configuration.

---

## Quick Reference

| Task | How |
|------|-----|
| Start new project | `kerrigan init <name>` or copy `specs/projects/_template/` |
| Check project status | `kerrigan status <name>` |
| Dispatch agent work | Brief an explicit executor session; issue adapter optional |
| Validate locally | `kerrigan check` or `python tools/validators/check_artifacts.py` |
| Bootstrap environment | `bash tools/bootstrap.sh` |
| Install CLI | `cd tools/cli/kerrigan && pip install -e .` ([reference](docs/operations/cli-reference.md)) |

---

## Repository Structure

```
kerrigan/
├── .github/
│   ├── agents/              # kerrigan, cloud profiles + adapters
│   ├── skills/              # Built-in skills (briefing, delegation, etc.)
│   └── workflows/           # CI: validators, tests, smoke checks
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
