# Architecture: Architect Agent

## Overview

The Architect Agent serves as the bridge between high-level product specifications and concrete implementation plans. It reads specifications produced by the Spec Agent and transforms them into comprehensive architectural designs, milestone-based roadmaps, and actionable task lists that enable downstream agents to execute independently.

The agent operates in a document-generation mode with structured decision-making processes. It evaluates tradeoffs, selects appropriate architectural patterns, decomposes work into milestones, and produces multiple interconnected artifacts that serve different audiences (SWE Agent, Testing Agent, Deployment Agent, Security Agent, and human reviewers).

## Components & interfaces

### Input Sources
- **spec.md**: Primary input defining goals, scope, acceptance criteria
- **acceptance-tests.md**: Scenarios that inform testing strategy
- **status.json**: Workflow control (agent must check before proceeding)
- **constitution.md**: Principles guiding architectural decisions (quality from day one, small increments)
- **artifact contracts**: Required sections and structure for all outputs
- **Existing codebase** (if project update): Current architecture to maintain consistency

### Core Processing Components

**Architecture Designer**
- Analyzes spec requirements and constraints
- Proposes high-level system structure (layers, components, boundaries)
- Defines key interfaces and data flows
- Selects architectural patterns (layered, event-driven, microservices, etc.)
- Evaluates technology stack options (if spec allows flexibility)

**Tradeoff Analyzer**
- Identifies multiple viable approaches
- Evaluates pros/cons for each alternative
- Documents rationale for selected approach
- Considers: simplicity, team skills, scalability, cost, maintainability
- Produces tradeoffs section for architecture.md and entries in decisions.md

**Milestone Planner**
- Decomposes project into 3-8 incremental deliverables
- Ensures each milestone ends with working, tested functionality
- Sequences milestones based on dependencies and risk
- Validates milestones align with "CI passes" principle
- Estimates effort (1-3 days per milestone typically)

**Task Decomposer**
- Breaks milestones into granular, actionable tasks
- Defines clear "done when" criteria for each task
- Links tasks to relevant artifacts (spec, architecture, tests)
- Identifies dependencies between tasks
- Produces tasks.md with executable work items

**Test Strategy Designer**
- Determines appropriate testing levels (unit, integration, e2e, performance)
- Identifies risk areas requiring focused testing
- Selects testing tools and frameworks
- Defines coverage goals and success criteria
- Produces test-plan.md for Testing Agent

**Operational Planner** (for deployable projects)
- Designs deployment approach (CI/CD, manual, containerized, serverless)
- Documents operational procedures (deploy, monitor, troubleshoot, rollback)
- Defines health checks and monitoring strategy
- Plans secret management approach
- Produces runbook.md for Deployment Agent

**Cost Estimator** (for projects with paid resources)
- Identifies cost drivers (compute, storage, bandwidth, third-party APIs)
- Estimates monthly costs with ranges based on scale assumptions
- Defines cost guardrails (budgets, alerts, auto-scaling limits)
- Plans cost tracking and optimization approach
- Produces cost-plan.md for Deployment Agent

### Output Artifacts
- **architecture.md**: System design with components, interfaces, tradeoffs, security notes
- **plan.md**: 3-8 milestones, each ending with "CI passes"
- **tasks.md**: Granular work items with "done when" criteria
- **test-plan.md**: Testing strategy, levels, tooling, coverage goals
- **runbook.md**: Operational procedures (if deployable)
- **cost-plan.md**: Cost estimates and guardrails (if using paid resources)
- **decisions.md**: Architectural decision records (updates from Spec Agent)

### Validation Interface
- Artifacts must pass validators checking:
  - Required sections present with exact headings
  - Structural completeness (all 6+ artifacts for appropriate projects)
  - Internal consistency (tasks align with milestones, test-plan aligns with architecture)

## Data flow (conceptual)

```
[spec.md, acceptance-tests.md]
        ↓
[Status Check] → (if blocked) → [Stop & Report]
        ↓
[Architecture Designer] → [Architecture.md Draft]
        ↓                            ↓
[Tradeoff Analyzer] ←───────────────┘
        ↓
[Finalized Architecture.md]
        ↓
[Milestone Planner] → [Plan.md with 3-8 milestones]
        ↓
[Task Decomposer] → [Tasks.md with "done when" criteria]
        ↓
[Test Strategy Designer] → [Test-plan.md]
        ↓
[Deployable?] ─No→ [Skip runbook/cost-plan]
        ↓Yes
[Operational Planner] → [Runbook.md]
        ↓
[Uses Paid Resources?] ─No→ [Skip cost-plan]
        ↓Yes
[Cost Estimator] → [Cost-plan.md]
        ↓
[All Artifacts Written to Repo]
        ↓
[Available for SWE Agent, Testing Agent, Deployment Agent]
```

## Tradeoffs

### Prescriptive Architecture vs. Implementation Flexibility
**Decision**: Define contracts and boundaries, allow SWE Agent flexibility within components
- **Pro**: Balances guidance with implementation freedom; avoids over-specification
- **Con**: Requires clear interface definitions; some ambiguity may remain
- **Mitigation**: Define public interfaces precisely, leave internal implementation to SWE; provide examples

### Large Comprehensive Plan vs. Iterative Planning
**Decision**: Create complete plan upfront with 3-8 milestones, allow updates as implementation progresses
- **Pro**: Provides roadmap for entire project; all agents can see big picture
- **Con**: Later milestones may need revision based on learnings from early implementation
- **Mitigation**: Expect plan updates; use decisions.md to track changes; keep milestone scope flexible

### Technology Agnostic vs. Specific Recommendations
**Decision**: Default to stack-agnostic, only specify technology if mandated by spec or strong rationale
- **Pro**: Maximizes team flexibility; keeps architecture broadly applicable
- **Con**: May require SWE Agent to make tech choices that architect could make better
- **Mitigation**: Document technology selection criteria; provide guidance without mandating unless necessary

### Detailed Tasks vs. High-Level Guidance
**Decision**: Produce granular tasks with "done when" criteria (1-2 days per task)
- **Pro**: Clear execution path for SWE Agent; easy to track progress
- **Con**: Can feel overly prescriptive; tasks may need adjustment during implementation
- **Mitigation**: Frame tasks as guidance not orders; expect SWE Agent to adapt as needed

### Single Large Artifact vs. Multiple Specialized Artifacts
**Decision**: Use 6+ separate artifacts (architecture, plan, tasks, test-plan, runbook, cost-plan)
- **Pro**: Each artifact serves specific audience; enables agent specialization; easier to update independently
- **Con**: More files to maintain; risk of inconsistency between artifacts
- **Mitigation**: Link artifacts explicitly; validate consistency; use clear naming conventions

## Security & privacy notes

### Architectural Security Considerations
- Architect Agent must include "Security & privacy notes" section in architecture.md
- Should identify:
  - Authentication and authorization approach
  - Data protection mechanisms (encryption, access controls)
  - Input validation and sanitization strategies
  - Secret management approach
  - Security boundaries between components

### Handoff to Security Agent
- Security Agent reviews architecture.md for security adequacy
- Architect documents security considerations, Security Agent validates and enhances
- Runbook.md must include secret management procedures if deployable

### Threat Modeling (Lightweight)
- Consider common threats for project type (OWASP Top 10 for web apps, etc.)
- Document mitigations at architectural level
- Flag areas requiring deeper security analysis

### Cost-Related Security
- Cost-plan.md should include security of cost controls (prevent cost-based DoS)
- Runbook should document access controls for cost-sensitive operations

### Information Leakage
- Architecture artifacts are committed to repo (follow repo access controls)
- Should not document specific vulnerabilities or attack vectors in detail
- Can reference security standards and best practices

### Compliance Requirements
- If spec includes compliance requirements (GDPR, HIPAA, PCI), architecture must address them
- Document compliance-relevant architectural decisions
- Flag if specialized security review is needed
