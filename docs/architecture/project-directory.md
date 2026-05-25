# Project Directory

This document provides an overview of all projects in `specs/projects/` and their current status.

## Active Production Projects

The Kerrigan harness itself is no longer tracked as a managed project here. Its specs live in [`specs/kerrigan-v2/`](../../specs/kerrigan-v2/) and its current state is summarised in [`AGENTS.md`](../../AGENTS.md).

## Active Reference Projects

### hello-api
**Purpose**: REST API development workflow example
**Implementation**: [`examples/hello-api/`](../../examples/hello-api/)
**Specs**: [`specs/projects/hello-api/`](../../specs/projects/hello-api/)

### _template
**Purpose**: Template for new projects
**Usage**: Copy to start new projects
**Location**: [`specs/projects/_template/`](../../specs/projects/_template/)

## Active Work

### docs-reorganization
**Status**: In progress (3 / 22 tasks)
**Specs**: [`specs/projects/docs-reorganization/`](../../specs/projects/docs-reorganization/)

### tests-cleanup
**Status**: Mostly resolved organically by v1 retirement PRs; 3 stragglers + branch-protection update remaining
**Specs**: [`specs/projects/tests-cleanup/`](../../specs/projects/tests-cleanup/)

## Archived Projects

Located in [`specs/projects/_archive/`](../../specs/projects/_archive/). Kept as reference material; not actively worked.

| Project | Reason archived |
|---|---|
| `hello-cli` | Completed validation project; reference CLI example |
| `hello-swarm` | Completed minimum-viable-project reference |
| `design-system-playground` | Completed design-iteration workflow validation |
| `task-tracker-real` | Stale (4+ months inactive, 7/53 tasks) |
| `task-dashboard-example` | Stub (no tasks) |
| `validator-enhancement` | Stale (4+ months inactive, never started) |
| `agent-frontmatter-upgrade`, `copilot-sdk-integration`, `pause-resume-demo` | Archived in PR #277 (v1-era completed work) |

See [Project Lifecycle Playbook](../../playbooks/project-lifecycle.md) for archival criteria and process.

## Quick Discovery Commands

```bash
# List active projects
ls -d specs/projects/*/ | grep -v _archive | grep -v _template

# List archived projects
ls -d specs/projects/_archive/*/

# Find in-progress work
grep -l "\[ \]" specs/projects/*/tasks.md
```

## How to Use This Directory

1. **Starting a new project**: Copy `_template/` and see [Kickoff Playbook](../../playbooks/kickoff.md)
2. **Finding examples**: Look in `examples/` for runnable artifacts; their archived specs live in `specs/projects/_archive/`
3. **Managing lifecycle**: See [Project Lifecycle Playbook](../../playbooks/project-lifecycle.md)
