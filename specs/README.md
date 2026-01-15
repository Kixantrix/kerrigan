# Specs

This folder contains the governing documents and specifications for all work done in this repository.

## Quick Reference

| Location | Purpose | Examples |
|----------|---------|----------|
| `specs/constitution.md` | Non-negotiable principles for all work | Quality standards, increment size, artifact-driven |
| `specs/kerrigan/` | Meta-specs about the agent system itself | Agent archetypes, artifact contracts, quality bar |
| `specs/projects/<name>/` | Per-project specifications and artifacts | spec.md, architecture.md, plan.md, tasks.md |
| `.github/agents/` | Agent prompt files for execution | role.swe.md, role.spec.md, role.architect.md |
| `docs/` | User-facing documentation and guides | setup.md, FAQ.md, architecture.md |
| `playbooks/` | Step-by-step operational guides | kickoff.md, handoffs.md, autonomy-modes.md |

## Folder Structure Explained

### Constitution (specs/constitution.md)
**Purpose**: Defines the highest-level principles that govern ALL work in this repository.

**Key principles**:
- Quality from day one
- Small, reviewable increments
- Artifact-driven collaboration
- Tests are part of the feature
- Stack-agnostic, contract-driven
- Operational responsibility
- Human-in-the-loop
- Clarity for agents

**Authority**: This is the ultimate authority. All other specs, meta-specs, and project work must align with these principles.

### Meta-Specs (specs/kerrigan/)
**Purpose**: Specifications about the Kerrigan *system* itself—how the agent swarm operates, what contracts exist between agents, and how quality is enforced.

**What belongs here**:
- Agent role definitions and responsibilities (e.g., `010-agent-archetypes.md`)
- Artifact contracts between roles (e.g., `020-artifact-contracts.md`)
- Quality bar definitions and enforcement (e.g., `030-quality-bar.md`)
- Toolchain and operational standards (e.g., `040-toolchain-and-ops.md`)
- Cost guardrails and automation contracts

**Important**: These are specs *about* the system, not specs *for* a project. They define how agents should work together, not what they should build.

**Naming convention**: Files are numbered (000, 010, 020, etc.) to indicate reading order and priority.

### Project Specs (specs/projects/<project-name>/)
**Purpose**: Specifications and artifacts for individual projects being built using the Kerrigan system.

**What belongs here**:
- `spec.md` - What the project should do (goals, scope, acceptance criteria)
- `architecture.md` - How the project is designed (components, decisions, trade-offs)
- `plan.md` - Implementation roadmap (milestones, dependencies)
- `tasks.md` - Detailed task breakdown (actionable work items)
- `test-plan.md` - Testing strategy (coverage, scenarios, automation)
- `runbook.md` - Operational guide (deployment, monitoring, troubleshooting)
- `cost-plan.md` - Resource and cost estimates
- `acceptance-tests.md` - Acceptance criteria in testable form
- `status.json` - Current project status (active, blocked, on-hold)

**Special case**: `specs/projects/kerrigan/` contains specs for Kerrigan *as a project* (building the agent swarm system), not about how the system works (that's in `specs/kerrigan/`).

### Agent Prompts (.github/agents/)
**Purpose**: Executable prompts that humans copy into AI assistants to perform specific roles.

**What belongs here**:
- `role.spec.md` - Prompt for the Spec Agent
- `role.architect.md` - Prompt for the Architect Agent
- `role.swe.md` - Prompt for the SWE Agent
- `role.testing.md` - Prompt for the Testing Agent
- `role.debugging.md` - Prompt for the Debugging Agent
- `role.deployment.md` - Prompt for the Deploy Agent
- `role.security.md` - Prompt for the Security Agent
- `kerrigan.swarm-shaper.md` - Prompt for the meta-agent that maintains the system

**Relationship to meta-specs**: Agent prompts *implement* the agent archetypes defined in `specs/kerrigan/010-agent-archetypes.md`. The meta-spec defines *what* each role is responsible for; the prompt defines *how* to execute that role.

### Documentation (docs/)
**Purpose**: Human-readable guides, tutorials, and explanations for using the Kerrigan system.

**What belongs here**:
- `setup.md` - Getting started guide
- `FAQ.md` - Frequently asked questions
- `architecture.md` - Visual overview of the system
- `agent-assignment.md` - How to assign work to agents
- Retrospectives and process documentation

**When to use docs/ vs specs/**: 
- Use `docs/` for explanatory content aimed at humans learning the system
- Use `specs/` for normative content that defines how the system must work

### Playbooks (playbooks/)
**Purpose**: Step-by-step operational guides for executing common workflows with the Kerrigan system.

**What belongs here**:
- `kickoff.md` - How to start a new project
- `handoffs.md` - Agent-to-agent handoff procedures
- `autonomy-modes.md` - Configuring agent autonomy levels
- `pr-review.md` - Guidelines for reviewing agent PRs
- `automation.md` - Setting up automated workflows

**When to use playbooks/ vs docs/**:
- Use `playbooks/` for prescriptive, step-by-step workflows ("do this, then that")
- Use `docs/` for explanatory guides and reference material ("here's how this works")

## The Flow: Constitution → Meta-Specs → Agent Prompts → Project Specs

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Constitution (specs/constitution.md)                        │
│    "All work must follow these principles"                     │
└───────────────────────┬─────────────────────────────────────────┘
                        │ governs
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Meta-Specs (specs/kerrigan/)                                │
│    "Agents have these roles and responsibilities"              │
│    "Artifacts must follow these contracts"                     │
│    "Quality bar is enforced with these metrics"                │
└───────────────────────┬─────────────────────────────────────────┘
                        │ define what
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Agent Prompts (.github/agents/)                             │
│    "Here's how to execute the Spec Agent role"                 │
│    "Here's how to execute the SWE Agent role"                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │ produce
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Project Specs (specs/projects/<name>/)                      │
│    "This project should build X with these features"           │
│    "Architecture uses these components and patterns"           │
│    "Implementation plan has these milestones"                  │
└─────────────────────────────────────────────────────────────────┘
```

## Kerrigan the System vs Kerrigan the Project

This is a common source of confusion. Here's the distinction:

### Kerrigan the System
- **What it is**: The agent swarm framework itself—roles, contracts, prompts, validators
- **Where it's defined**: `specs/kerrigan/` (meta-specs) and `.github/agents/` (prompts)
- **Purpose**: Defines *how* agents collaborate to build *any* project
- **Examples**: Agent archetypes, artifact contracts, quality bar standards

### Kerrigan the Project
- **What it is**: The specific work of building and improving the Kerrigan system
- **Where it's defined**: `specs/projects/kerrigan/` (project specs)
- **Purpose**: Tracks the goals, architecture, and implementation of the Kerrigan system itself
- **Examples**: "Add validator for artifact completeness", "Create handoff playbook"

**Analogy**: Think of it like a programming language:
- **Kerrigan the System** = The language specification (how the language works)
- **Kerrigan the Project** = The implementation of the language (building the compiler/interpreter)

## Decision Tree: Where Does This File Belong?

Use this decision tree to determine where a file should go:

```
Is it about fundamental principles that apply to all work?
├─ YES → specs/constitution.md
└─ NO → Continue

Is it about how the agent system works (roles, contracts, quality)?
├─ YES → specs/kerrigan/<numbered-file>.md
└─ NO → Continue

Is it an executable prompt for a specific agent role?
├─ YES → .github/agents/role.<name>.md
└─ NO → Continue

Is it a specification or artifact for a specific project?
├─ YES → specs/projects/<project-name>/<artifact-name>.md
└─ NO → Continue

Is it a step-by-step operational workflow or procedure?
├─ YES → playbooks/<workflow-name>.md
└─ NO → Continue

Is it explanatory documentation for humans using the system?
├─ YES → docs/<topic>.md
└─ NO → Ask: Does this fit the Kerrigan model? Consider if you need a new category.
```

## Naming Conventions

### Meta-Specs (specs/kerrigan/)
- **Format**: `<number>-<topic>.md`
- **Numbering**: Use increments of 10 (000, 010, 020) to allow insertion
- **Example**: `010-agent-archetypes.md`, `020-artifact-contracts.md`
- **Rationale**: Numbers indicate reading order and priority

### Project Specs (specs/projects/<project-name>/)
- **Folder name**: Lowercase, hyphenated (e.g., `hello-swarm`, `validator-enhancement`)
- **Standard artifacts**: Use exact names from artifact contracts
  - `spec.md` (not `specification.md` or `spec.txt`)
  - `architecture.md` (not `design.md` or `arch.md`)
  - `plan.md` (not `roadmap.md` or `plan.txt`)
  - `tasks.md` (not `todo.md` or `task-list.md`)
  - `test-plan.md` (not `testing.md` or `tests.md`)
  - `runbook.md` (not `operations.md` or `ops.md`)
  - `cost-plan.md` (not `costs.md` or `budget.md`)
  - `acceptance-tests.md` (not `acceptance.md` or `tests.md`)
  - `status.json` (not `status.yaml` or `state.json`)
- **Rationale**: Exact names allow validators to check for presence and structure

### Agent Prompts (.github/agents/)
- **Format**: `role.<name>.md` or `<name>.<role>.md`
- **Examples**: 
  - `role.swe.md` - SWE Agent prompt
  - `role.architect.md` - Architect Agent prompt
  - `kerrigan.swarm-shaper.md` - Special meta-agent prompt
- **Rationale**: `role.` prefix makes it clear these are agent prompts, not documentation

### Documentation (docs/)
- **Format**: `<topic>.md`
- **Examples**: `setup.md`, `FAQ.md`, `agent-assignment.md`
- **Rationale**: Descriptive names that clearly indicate content

### Playbooks (playbooks/)
- **Format**: `<workflow>.md`
- **Examples**: `kickoff.md`, `handoffs.md`, `autonomy-modes.md`
- **Rationale**: Action-oriented names describing the workflow or procedure

## Examples: What Belongs Where?

### Example 1: Adding a new quality rule
**Question**: "I want to add a rule that all functions must have docstrings."

**Decision**:
- Is it a fundamental principle? **No** (too specific)
- Is it about the agent system? **Yes** (quality bar rule)
- **Location**: `specs/kerrigan/030-quality-bar.md`
- **Action**: Add a section or bullet point to the existing quality bar spec

### Example 2: Creating a new agent role
**Question**: "I want to add a 'UI/UX Agent' that designs user interfaces."

**Decision**:
- Add role definition to `specs/kerrigan/010-agent-archetypes.md`
- Create prompt file `.github/agents/role.ui-ux.md`
- Update artifact contracts in `specs/kerrigan/020-artifact-contracts.md` if new artifacts are needed

### Example 3: Starting a new project
**Question**: "I want to build a REST API for user management."

**Decision**:
- Create folder: `specs/projects/user-api/`
- Copy template: `cp -r specs/projects/_template/* specs/projects/user-api/`
- Fill in artifacts: `spec.md`, `architecture.md`, etc.

### Example 4: Writing a how-to guide
**Question**: "I want to explain how to debug agent failures."

**Decision**:
- Is it a spec or guide? **Guide** (explanatory)
- Is it a prompt or documentation? **Documentation** (for humans)
- **Location**: `docs/debugging-agents.md`

### Example 5: Improving an existing agent prompt
**Question**: "The SWE Agent isn't generating good test names."

**Decision**:
- Is it about the role definition? **No** (role is fine)
- Is it about the prompt? **Yes** (execution details)
- **Location**: `.github/agents/role.swe.md`
- **Action**: Update the examples and guidelines in the prompt

### Example 6: Creating a workflow guide
**Question**: "I want to document the process for deploying a project."

**Decision**:
- Is it a specification? **No** (it's a procedure)
- Is it a step-by-step workflow? **Yes**
- **Location**: `playbooks/deployment.md` or update `playbooks/handoffs.md`
- **Action**: Create a new playbook or extend an existing one with deployment steps

## Validation

Agents should treat `specs/constitution.md` as the highest authority. All meta-specs, agent prompts, and project specs must align with constitutional principles.

CI validators check:
- Project specs have required artifacts (spec.md, architecture.md, etc.)
- Files follow quality bar limits (e.g., max 800 lines)
- Naming conventions are followed
- Required sections are present in each artifact

See `tools/validators/` for implementation details.
