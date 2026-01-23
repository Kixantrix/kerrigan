# Hello Swarm

A minimal end-to-end example demonstrating the Kerrigan artifact flow with the smallest possible footprint.

## Overview

Hello Swarm is **intentionally simple** and serves as a teaching tool for understanding:
- **Required artifacts** for any Kerrigan project
- **Minimal structure** needed to pass CI validators
- **Artifact-driven workflow** without stack-specific implementation

This example does **not mandate a tech stack**—it focuses purely on the artifact contracts that make Kerrigan's agent coordination possible.

## Quick Start

1. **Navigate to the example**:
   ```bash
   cd examples/hello-swarm
   ```

2. **Explore the artifacts**:
   ```bash
   ls -la
   # You'll see: spec.md, tasks.md, README.md
   ```

3. **Review the spec**:
   ```bash
   cat spec.md
   # Shows goal, scope, acceptance criteria
   ```

4. **Check tasks**:
   ```bash
   cat tasks.md
   # Demonstrates AUTO-ISSUE task tracking
   ```

## What You'll Learn

### 1. **Minimal Artifact Set**
This example shows the absolute minimum required for a Kerrigan project:
- `spec.md` - Defines the project goal, scope, and acceptance criteria
- `tasks.md` - Tracks work items (with optional AUTO-ISSUE markers)
- `README.md` - Entry point for humans and agents

### 2. **Artifact Flow**
Understanding how artifacts connect:
```
Issue → spec.md → tasks.md → Implementation → CI Validation
```

Key principles demonstrated:
- **Spec-first**: All work starts with a specification
- **Validator-enforced**: CI checks that required artifacts exist
- **Link-driven**: Keep files short and reference other docs

### 3. **AUTO-ISSUE Pattern**
The `tasks.md` file demonstrates automated issue generation:
- Use `<!-- AUTO-ISSUE: role:swe priority:high -->` markers
- Automation creates GitHub issues from task definitions
- Agents can be automatically assigned via role labels

### 4. **Stack-Agnostic Design**
This example intentionally avoids implementation details:
- No specific programming language
- No framework choices
- No deployment scripts

This demonstrates that Kerrigan's artifact contracts work for **any technology stack**.

## Artifact Details

### spec.md
Contains the standard specification structure:
- **Goal**: What the project achieves
- **Scope**: What's included
- **Non-goals**: What's explicitly excluded
- **Users & scenarios**: Who benefits and how
- **Constraints**: Technical or process limitations
- **Acceptance criteria**: Definition of done
- **Risks & mitigations**: Known issues and solutions
- **Success metrics**: How to measure success

### tasks.md
Demonstrates task tracking with:
- Task descriptions and acceptance criteria
- Dependencies between tasks
- AUTO-ISSUE markers for automation
- Effort estimates
- Mix of automated and manual tasks

## Documentation

For more complete examples, see:
- [hello-cli](../hello-cli/) - Full CLI implementation with tests
- [hello-api](../hello-api/) - REST API with Docker support
- [task-tracker](../task-tracker/) - Complex project with full artifact set

## Related Specs

This example lives in `examples/` but follows the same structure as projects in `specs/projects/`. For production projects:
1. Copy the `specs/projects/_template/` directory
2. Fill in the artifacts following this example's pattern
3. Add implementation-specific details (architecture, test plans, etc.)

See [specs/kerrigan/020-artifact-contracts.md](../../specs/kerrigan/020-artifact-contracts.md) for the full list of required artifacts.
