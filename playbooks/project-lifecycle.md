# Project Lifecycle Management

## Overview

This playbook defines how to manage projects in `specs/projects/` through their lifecycle, from active development to completion and archival. It ensures the projects folder stays focused while preserving valuable validation work and examples.

## Project Types

### Production Projects
Projects that deliver ongoing value and require maintenance.

**Examples**: `kerrigan` (the meta-project itself)

**Location**: `specs/projects/<project-name>/`

**Status**: Active, no special markers needed

### Validation Projects
Projects created to validate workflows, test agent capabilities, or explore new approaches.

**Examples**: `hello-api`, `hello-cli`, `validator-enhancement`

**Location**: `specs/projects/<project-name>/`

**Status**: Can be active, completed, or archived

### Reference Examples
Minimal projects that demonstrate patterns or serve as templates.

**Examples**: `hello-swarm`, `_template`

**Location**: `specs/projects/<project-name>/`

**Status**: Active as reference material

## Project States

### Active
Project is under development or requires ongoing maintenance.

**Markers**:
- No special STATUS.md file needed
- Tasks in tasks.md may be incomplete
- Referenced in main documentation

### Completed
Project fulfilled its purpose. Specs and implementation exist for reference.

**Markers**:
- Create `STATUS.md` in project folder with completion details
- All acceptance criteria met
- Implementation exists (if applicable)
- No planned future work

**Discovery**: Search for `STATUS.md` files or "Status: Completed" marker

### Archived
Project specs moved to `specs/projects/_archive/` to reduce clutter.

**When to archive**:
- Project completed AND no longer referenced in documentation
- Implementation moved to examples/ (if applicable)
- Lessons learned captured elsewhere
- Low future reference value

**How to archive**:
```bash
# Move project to archive folder
mv specs/projects/<project-name> specs/projects/_archive/<project-name>

# Update any documentation references
grep -r "projects/<project-name>" docs/ playbooks/
```

**Discovery**: Browse `specs/projects/_archive/` or use git history

## Workflow for New Projects

### 1. Starting a Project
```bash
# Copy template
cp -r specs/projects/_template/ specs/projects/<project-name>/

# Create spec and acceptance tests
# See playbooks/kickoff.md for full workflow
```

### 2. During Development
- Keep tasks.md updated
- Maintain artifact quality (CI enforces)
- Follow constitution principles

### 3. Completing a Project

When a validation or experimental project reaches completion:

**Step 1**: Verify completion
- [ ] All acceptance criteria met (check spec.md)
- [ ] Implementation exists (if applicable)
- [ ] CI passes
- [ ] Documentation updated

**Step 2**: Create STATUS.md
```bash
cd specs/projects/<project-name>/
cat > STATUS.md << 'EOF'
# Project Status: Completed

**Completion Date**: YYYY-MM-DD

## Purpose
[Why this project existed - e.g., "Validate spec agent workflow" or "Test CLI best practices"]

## Outcomes
[What was delivered - e.g., "Working CLI tool with 95% test coverage"]

## Lessons Learned
[Key insights for future projects]

## Implementation
[Where code lives - e.g., "examples/hello-cli/" or "Implemented in tools/validators/"]

## Future Reference
[When to reference this project - e.g., "See this project when building CLIs" or "No future reference needed"]
EOF
```

**Step 3**: Update documentation
- Remove project from active examples if no longer relevant
- Add to completed projects list (if maintaining one)
- Update any workflow references

### 4. Archiving (Optional)

Archive completed projects when they add noise without value:

**Good candidates for archiving**:
- One-off experiments with low reuse potential
- Validation projects superseded by better examples
- Projects with lessons learned captured elsewhere

**Keep in main projects/ (don't archive)**:
- Examples referenced in documentation
- Common patterns (CLI, API, service templates)
- Projects with unique lessons or approaches

## Discovery Mechanisms

### Find Active Projects
```bash
# List all projects (active projects won't have STATUS.md with "Completed")
ls -d specs/projects/*/
```

### Find Completed Projects
```bash
# Search for completed projects
grep -r "Status: Completed" specs/projects/
```

### Find Archived Projects
```bash
# List archived projects
ls -d specs/projects/_archive/*/
```

### Browse Examples
```bash
# See implemented examples
ls -d examples/*/
```

## Decision Guidelines

### Should I archive this completed project?

**Archive if**:
- ✅ Low future reference value
- ✅ Not mentioned in documentation
- ✅ Implementation captured in examples/
- ✅ Lessons learned documented elsewhere

**Keep if**:
- ❌ Referenced in docs or playbooks
- ❌ Unique validation approach
- ❌ Useful pattern for future projects
- ❌ Active as reference material

### Should this be a validation project or production project?

**Validation project** if:
- Testing a workflow or agent capability
- Exploring a new approach
- Time-boxed experimentation
- Will be completed and not maintained

**Production project** if:
- Delivers ongoing value
- Requires maintenance
- Part of core system (like `kerrigan` itself)
- Long-term reference

## Alignment with Constitution

This lifecycle approach aligns with constitution principles:

- **Low overhead** (Principle 8): Simple status markers, no complex tooling
- **Artifact-driven** (Principle 3): Status captured in repo files
- **Quality from day one** (Principle 1): No change to quality bar
- **Clarity for agents** (Principle 8): Clear markers and discoverable structure

## Examples

### Example: hello-api (Completed Validation Project)

**Purpose**: Validated spec-to-implementation workflow for REST API

**Status**: Completed, kept in specs/projects/hello-api/ with STATUS.md

**Why not archived**: Good reference for future API projects, referenced in examples/

### Example: validator-enhancement (Completed Validation Project)

**Purpose**: Added color output to artifact validator

**Status**: Completed, implementation merged into tools/validators/

**Could be archived**: Specs served their purpose, implementation is the source of truth

### Example: hello-swarm (Active Reference)

**Purpose**: Minimal example showing artifact contracts

**Status**: Active as reference material

**Why not completed**: Serves ongoing reference value

## Summary

This lightweight approach:
- ✅ Keeps projects/ focused on active and reference material
- ✅ Preserves validation work with clear markers
- ✅ Makes discovery easy (STATUS.md, _archive folder, git history)
- ✅ Low overhead (simple files, no complex tooling)
- ✅ Aligns with constitution principles

**Next steps**: Apply this strategy to current validation projects (see next section).
