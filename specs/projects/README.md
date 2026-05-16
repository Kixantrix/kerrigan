# Kerrigan Projects

Status legend for all projects in this directory.

## Status Definitions

| Status | Meaning |
|--------|---------|
| **Active** | Currently maintained; referenced in live documentation and actively developed |
| **Reference** | Complete and stable; kept as educational examples or reusable scaffolds |
| **Archived** | Spec work complete or investigation concluded; no ongoing implementation |

---

## Active Projects

Projects currently maintained and referenced in documentation.

| Project | Purpose | Status | Last Updated |
|---------|---------|--------|--------------|
| [kerrigan](kerrigan/) | Meta-project for Kerrigan itself — building the agent swarm system | Active | 2026-01-15 |
| [docs-reorganization](docs-reorganization/) | Reorganize the `docs/` directory into a hierarchical structure | Active | 2026-05-12 |

---

## Reference Projects

Complete examples maintained for educational purposes. Safe to copy and adapt.

| Project | Purpose | Status | Implementation | Last Updated |
|---------|---------|--------|----------------|--------------|
| [hello-api](hello-api/) | REST API scaffold — validates the spec-to-deployment workflow | Reference | [examples/hello-api/](../../examples/hello-api/) | 2026-01-10 |
| [hello-cli](hello-cli/) | CLI tool scaffold — validates the CLI development workflow | Reference | [examples/hello-cli/](../../examples/hello-cli/) | 2026-01-10 |
| [hello-swarm](hello-swarm/) | Minimal artifact structure — shows the smallest valid project | Reference | Stack-agnostic (no code) | — |
| [task-tracker-real](task-tracker-real/) | Real workflow example with authentic pause/resume cycles | Reference | [examples/task-tracker-real/](../../examples/task-tracker-real/) | 2026-01-16 |
| [task-dashboard-example](task-dashboard-example/) | Design system example with working HTML/CSS/JS playground | Reference | [examples/task-dashboard-design/](../../examples/task-dashboard-design/) | 2026-05-12 |

---

## Archived Projects

Specs or investigations that have concluded. Kept for historical context; no active implementation expected.

| Project | Reason | Archived Date |
|---------|--------|---------------|
| [agent-frontmatter-upgrade](agent-frontmatter-upgrade/) | YAML frontmatter was added to all agent files as part of the v2 rollout | 2026-05-12 |
| [copilot-sdk-integration](copilot-sdk-integration/) | Investigation complete; findings captured in [research-findings.md](copilot-sdk-integration/research-findings.md) | 2026-05-12 |
| [design-system-playground](design-system-playground/) | Playground spec and static implementation complete; no active use case driving further work | 2026-05-12 |
| [pause-resume-demo](pause-resume-demo/) | M3 pause/resume workflow validation complete; all status transitions confirmed | 2026-01-15 |
| [validator-enhancement](validator-enhancement/) | Specs complete and implementation-ready, but the enhancement was not prioritised; lessons captured in STATUS.md | 2026-01-10 |

---

## Special Folders

| Folder | Purpose |
|--------|---------|
| [_archive/](_archive/) | Container for fully archived project specs. Projects moved here have low future reference value but are kept for historical context and audit trail. |
| [_template/](_template/) | Canonical template for new projects. Copy this folder when starting a new project. |

---

## Quick Discovery Commands

```bash
# List all projects
ls -d specs/projects/*/

# Check a project's status.json
cat specs/projects/<project>/status.json

# Find all projects with implementations in examples/
ls examples/

# Search for a project's acceptance criteria
grep -r "Acceptance" specs/projects/<project>/
```

## See Also

- [docs/project-directory.md](../../docs/project-directory.md) — extended narrative overview of each project
- [_archive/README.md](_archive/README.md) — guidance on archiving and restoring projects
- [_template/](_template/) — start here when creating a new project
- [playbooks/project-lifecycle.md](../../playbooks/project-lifecycle.md) — full lifecycle management guide
