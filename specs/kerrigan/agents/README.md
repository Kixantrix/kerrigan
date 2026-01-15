# Agent Role Specifications

This directory contains comprehensive specifications for each of the 7 core agent roles in the Kerrigan multi-agent system.

## Purpose

These specifications formalize what is currently defined as agent prompts in `.github/agents/role.*.md`. They provide:
- **Formal specifications** for each agent's responsibilities
- **Artifact contracts** - what each agent produces
- **Quality standards** - how to measure agent output quality
- **Operational guidelines** - how each agent operates internally

## Structure

Each agent has 4 specification documents:

```
specs/kerrigan/agents/<agent-name>/
├── spec.md              # What the agent is responsible for
├── acceptance-tests.md  # How to verify the agent works correctly
├── architecture.md      # How the agent operates internally
└── quality-bar.md       # Quality standards for agent output
```

## Agents

### 1. Spec Agent (`spec/`)
**Purpose**: Transform project ideas into clear, measurable specifications with explicit acceptance criteria.

**Key Artifacts**: `spec.md`, `acceptance-tests.md`, `decisions.md`

**Quality Focus**: Measurability, clarity, completeness

### 2. Architect Agent (`architect/`)
**Purpose**: Design system architectures and implementation roadmaps that translate specifications into actionable plans.

**Key Artifacts**: `architecture.md`, `plan.md`, `tasks.md`, `test-plan.md`, `runbook.md`, `cost-plan.md`

**Quality Focus**: Incrementality, feasibility, completeness

### 3. SWE Agent (`swe/`)
**Purpose**: Implement software incrementally with TDD, maintaining high code quality and green CI.

**Key Artifacts**: Code, tests, linting config, documentation

**Quality Focus**: Test coverage, code quality, maintainability

### 4. Testing Agent (`testing/`)
**Purpose**: Strengthen test infrastructure, increase coverage, eliminate flaky tests, improve test quality.

**Key Artifacts**: Enhanced tests, test infrastructure, `test-plan.md` updates

**Quality Focus**: Coverage (>80%), reliability (<1% flaky), speed, clarity

### 5. Debugging Agent (`debugging/`)
**Purpose**: Investigate failures, identify root causes, create fixes with regression tests, prevent recurrence.

**Key Artifacts**: Reproduction steps, fix with regression test, runbook updates

**Quality Focus**: Root cause identification, minimal fixes, prevention

### 6. Deployment Agent (`deployment/`)
**Purpose**: Make deployable projects operationally ready for production.

**Key Artifacts**: `runbook.md`, `cost-plan.md`, CI/CD pipelines

**Quality Focus**: Operational readiness, cost awareness, reliability

### 7. Security Agent (`security/`)
**Purpose**: Identify and prevent common security issues early in development.

**Key Artifacts**: Security notes in `architecture.md` and `runbook.md`, CI security checks

**Quality Focus**: OWASP Top 10 coverage, secure defaults, proportional security

## Relationship to Agent Prompts

The specifications in this directory complement the agent prompts in `.github/agents/`:

- **Agent Prompts** (`.github/agents/role.*.md`): Operational instructions for executing agent work
- **Agent Specs** (this directory): Formal specifications for agent capabilities and quality standards

The prompts reference these specs for detailed quality standards and acceptance criteria.

## Artifact Contract

Each agent specification follows this structure:

### spec.md
- **Goal**: 1-2 sentence purpose
- **Scope**: What's included
- **Non-goals**: What's explicitly excluded
- **Users & scenarios**: Who uses the agent and how
- **Constraints**: Limitations and requirements
- **Acceptance criteria**: How to measure success
- **Risks & mitigations**: What could go wrong
- **Success metrics**: Quantifiable measures

### acceptance-tests.md
Given/When/Then scenarios covering:
- Artifact completeness
- Quality standards
- Process compliance
- Edge cases
- Integration with other agents

### architecture.md
- **Overview**: High-level approach
- **Components & interfaces**: How the agent operates
- **Data flow (conceptual)**: Information flow through agent
- **Tradeoffs**: Design decisions and alternatives
- **Security & privacy notes**: Security considerations

### quality-bar.md
- **Definition of done**: When agent work is complete
- **Structural standards**: Required sections, limits
- **Content quality standards**: Good vs. bad examples
- **Common mistakes**: Errors to avoid
- **Validation checklist**: Pre-submission checks
- **Review standards**: How to review agent output

## Using These Specifications

### For Agent Development
When implementing or improving an agent:
1. Read `spec.md` to understand purpose and scope
2. Review `architecture.md` to understand how it should operate
3. Use `quality-bar.md` to ensure output meets standards
4. Validate against `acceptance-tests.md`

### For Quality Assurance
When validating agent output:
1. Check `acceptance-tests.md` for verification scenarios
2. Apply `quality-bar.md` standards
3. Ensure alignment with `spec.md` acceptance criteria

### For Evolution
When improving the agent system:
1. Propose changes via issues
2. Update relevant specifications
3. Align agent prompts with updated specs
4. Validate changes don't break acceptance tests

## Alignment with Constitution

All agent specifications align with the Kerrigan constitution (`specs/constitution.md`):
1. **Quality from day one** - Every agent enforces quality standards
2. **Small, reviewable increments** - Agents work incrementally
3. **Artifact-driven collaboration** - Agents communicate via artifacts
4. **Tests are part of the feature** - Testing integrated throughout
5. **Stack-agnostic, contract-driven** - Specifications remain technology-neutral
6. **Operational responsibility** - Deployment and cost awareness included
7. **Human-in-the-loop** - Agents support human decision-making
8. **Clarity for agents** - Specifications provide clear guidance

## Contributing

To improve agent specifications:
1. Open an issue describing the improvement
2. Provide examples of current vs. improved approach
3. Update relevant specification files
4. Ensure changes align with constitution principles
5. Update agent prompts if needed

## See Also

- **Constitution**: `specs/constitution.md` - Governing principles
- **Artifact Contracts**: `specs/kerrigan/020-artifact-contracts.md` - Required artifacts
- **Quality Bar**: `specs/kerrigan/030-quality-bar.md` - System-wide quality standards
- **Agent Prompts**: `.github/agents/` - Operational agent instructions
