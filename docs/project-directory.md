# Project Directory

This document provides an overview of all projects in `specs/projects/` and their current status.

## Active Production Projects

### kerrigan
**Purpose**: Kerrigan meta-project - the agent swarm system itself  
**Status**: Active (ongoing development and maintenance)  
**Location**: `specs/projects/kerrigan/`

## Completed Validation Projects

These projects validated the Kerrigan workflow and agent capabilities. They remain in the projects folder for reference value.

### hello-api
**Purpose**: Validate REST API development workflow  
**Status**: ✅ Completed (2026-01-10)  
**Implementation**: `examples/hello-api/`  
**Reference value**: High - Example for API projects  
**Details**: See `specs/projects/hello-api/STATUS.md`

### hello-cli
**Purpose**: Validate CLI tool development workflow  
**Status**: ✅ Completed (2026-01-10)  
**Implementation**: `examples/hello-cli/`  
**Reference value**: High - Example for CLI projects  
**Details**: See `specs/projects/hello-cli/STATUS.md`

### validator-enhancement
**Purpose**: Test spec and architect agent prompts with focused enhancement  
**Status**: ✅ Completed (2026-01-10)  
**Implementation**: Specs only (not implemented)  
**Reference value**: Medium - Example of focused enhancement specs  
**Details**: See `specs/projects/validator-enhancement/STATUS.md`

## Active Reference Projects

### hello-swarm
**Purpose**: Minimal example of artifact structure  
**Status**: Active reference  
**Implementation**: Stack-agnostic (no code)  
**Reference value**: High - Shows minimum viable project  
**Details**: See `specs/projects/hello-swarm/STATUS.md`

### _template
**Purpose**: Template for new projects  
**Status**: Active template  
**Usage**: Copy to start new projects  
**Location**: `specs/projects/_template/`

## Archived Projects

Currently no archived projects. When projects are archived, they move to `specs/projects/_archive/`.

See [Project Lifecycle Playbook](../playbooks/project-lifecycle.md) for archival criteria and process.

## Quick Discovery Commands

```bash
# List all projects
ls -d specs/projects/*/

# Find completed projects
grep -r "Status: Completed" specs/projects/

# Find active references
grep -r "Status: Active Reference" specs/projects/

# List archived projects
ls -d specs/projects/_archive/*/

# View project status
cat specs/projects/<project-name>/STATUS.md
```

## How to Use This Directory

1. **Starting a new project**: Copy `_template/` and see [Kickoff Playbook](../playbooks/kickoff.md)
2. **Finding examples**: Check completed validation projects (hello-api, hello-cli)
3. **Understanding minimums**: See hello-swarm for minimum viable structure
4. **Managing lifecycle**: See [Project Lifecycle Playbook](../playbooks/project-lifecycle.md)

## Status File Convention

Projects use `STATUS.md` files to indicate completion:
- **No STATUS.md**: Active production project (e.g., kerrigan)
- **STATUS.md with "Completed"**: Completed validation/experimental project
- **STATUS.md with "Active Reference"**: Ongoing reference material (e.g., hello-swarm)

This convention enables easy discovery via grep or file browsing.
