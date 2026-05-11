# Acceptance tests: Architect Agent

## Artifact Completeness

- [ ] **Given** a project spec, **When** Architect Agent completes work, **Then** architecture.md exists with all required sections
- [ ] **Given** architecture.md, **When** validating structure, **Then** it contains: Overview, Components & interfaces, Tradeoffs, Security & privacy notes
- [ ] **Given** a project, **When** Architect completes work, **Then** plan.md exists with 3-8 incremental milestones
- [ ] **Given** a project, **When** Architect completes work, **Then** tasks.md exists with clear "done when" criteria
- [ ] **Given** a project, **When** Architect completes work, **Then** test-plan.md exists with testing strategy
- [ ] **Given** a deployable project, **When** checking artifacts, **Then** runbook.md exists
- [ ] **Given** a project using paid resources, **When** checking artifacts, **Then** cost-plan.md exists
- [ ] **Given** architectural decisions, **When** documenting, **Then** decisions.md includes alternatives and rationale

## Architecture Quality

- [ ] **Given** architecture.md content, **When** reviewing components, **Then** key interfaces are clearly defined
- [ ] **Given** architecture.md content, **When** checking specificity, **Then** design is detailed enough to guide implementation
- [ ] **Given** architecture.md content, **When** checking flexibility, **Then** design doesn't over-specify internal implementation details
- [ ] **Given** architecture tradeoffs section, **When** reviewing, **Then** alternatives are documented with pros/cons
- [ ] **Given** architecture.md, **When** checking for tech stack, **Then** remains stack-agnostic unless spec mandates specific technology

## Plan Quality

- [ ] **Given** plan.md milestones, **When** reviewing, **Then** each milestone ends with "CI passes" or equivalent verification
- [ ] **Given** plan.md milestones, **When** checking scope, **Then** each delivers working, testable functionality (not just setup)
- [ ] **Given** plan.md milestones, **When** estimating effort, **Then** each is achievable in 1-3 days typically
- [ ] **Given** plan.md, **When** checking sequence, **Then** dependencies between milestones are clear
- [ ] **Given** plan.md, **When** validating incrementality, **Then** each milestone adds value over previous

## Task Quality

- [ ] **Given** tasks.md entries, **When** reviewing, **Then** each task has explicit "done when" criteria
- [ ] **Given** tasks.md entries, **When** checking actionability, **Then** each task is specific enough to start immediately
- [ ] **Given** tasks.md entries, **When** checking size, **Then** tasks are small enough to complete in hours or 1-2 days
- [ ] **Given** tasks.md, **When** checking links, **Then** tasks reference relevant artifacts (spec, architecture, test-plan)

## Test Plan Quality

- [ ] **Given** test-plan.md, **When** reviewing, **Then** testing levels are specified (unit, integration, e2e as appropriate)
- [ ] **Given** test-plan.md, **When** checking tooling, **Then** testing approach and tools are documented
- [ ] **Given** test-plan.md, **When** reviewing coverage, **Then** risk areas and coverage priorities are identified
- [ ] **Given** test-plan.md, **When** validating, **Then** plan aligns with acceptance criteria from spec.md

## Runbook Quality (Deployable Projects)

- [ ] **Given** runbook.md for deployable project, **When** reviewing, **Then** deployment procedures are documented
- [ ] **Given** runbook.md, **When** checking operations, **Then** start/stop/monitor procedures are clear
- [ ] **Given** runbook.md, **When** checking troubleshooting, **Then** common issues and solutions are documented
- [ ] **Given** runbook.md, **When** checking rollback, **Then** rollback procedure is defined
- [ ] **Given** runbook.md, **When** checking secrets, **Then** secret management approach is documented

## Cost Plan Quality (Paid Resources)

- [ ] **Given** cost-plan.md, **When** reviewing estimates, **Then** expected costs are documented with ranges
- [ ] **Given** cost-plan.md, **When** checking tracking, **Then** cost monitoring approach is defined
- [ ] **Given** cost-plan.md, **When** checking guardrails, **Then** spending limits and alerts are specified
- [ ] **Given** cost-plan.md, **When** reviewing assumptions, **Then** scale and usage assumptions are documented

## Status and Workflow

- [ ] **Given** project with status.json, **When** Architect Agent starts work, **Then** agent checks status is "active" or file doesn't exist
- [ ] **Given** status.json shows "blocked", **When** Architect Agent starts work, **Then** agent stops and reports blocked_reason
- [ ] **Given** status.json shows "on-hold", **When** Architect Agent starts work, **Then** agent stops without proceeding
- [ ] **Given** Architect completes initial work, **When** checking handoff, **Then** spec.md exists and was read

## Integration with Other Agents

- [ ] **Given** complete architecture artifacts, **When** SWE Agent reads them, **Then** sufficient information exists to begin implementation
- [ ] **Given** test-plan.md, **When** Testing Agent reads it, **Then** clear guidance exists for test infrastructure
- [ ] **Given** architecture.md security section, **When** Security Agent reviews, **Then** security considerations are documented
- [ ] **Given** architecture.md tradeoffs, **When** human reviews, **Then** decisions are defensible and well-reasoned

## Edge Cases

- [ ] **Given** a small project, **When** creating milestones, **Then** at least 2 milestones exist (not single "implement everything")
- [ ] **Given** unclear spec, **When** designing architecture, **Then** architect documents assumptions in decisions.md
- [ ] **Given** multiple viable architectures, **When** making choice, **Then** alternatives are compared in tradeoffs section
- [ ] **Given** architecture update after implementation starts, **When** modifying, **Then** changes are tracked and communicated

## Validation

- [ ] **Given** all architecture artifacts, **When** running validators, **Then** section headings match artifact contract exactly
- [ ] **Given** architecture.md, **When** checking case sensitivity, **Then** "Components & interfaces" uses ampersand (not "and")
- [ ] **Given** architecture.md, **When** checking sections, **Then** "Security & privacy notes" exists (not "Security and Privacy")
