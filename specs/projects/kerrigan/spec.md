# Spec: Kerrigan

## Goal
Build a functional agent swarm system that can autonomously execute software projects from spec to deployment while maintaining quality, transparency, and human control.

## Scope
- Complete agent role definitions and prompts
- CI enforcement of artifact contracts and quality bar
- Autonomy mode controls (on-demand, sprint, hybrid)
- Handoff protocols between agent roles
- Status tracking and visibility
- Validator tooling for artifacts and code quality
- Documentation and playbooks for swarm operation

## Non-goals
- Building a specific application or service
- Creating a GUI for swarm management
- Real-time agent orchestration platform
- Mandating specific tech stacks or frameworks

## Users & scenarios
- **Human project lead**: defines scope, approves architecture, steers direction
- **Spec agent**: creates detailed specifications with acceptance criteria
- **Architect agent**: designs system architecture and implementation plan
- **SWE agent**: implements features incrementally with tests
- **Testing agent**: strengthens test coverage and harnesses
- **Debugging agent**: fixes failures and adds regression tests
- **Deployment agent**: creates runbooks and wires CD pipelines
- **Security agent**: reviews for vulnerabilities and compliance
- **Kerrigan (meta-agent)**: ensures constitution compliance and artifact quality

## Constraints
- Must be stack-agnostic
- All work must be artifact-driven and in-repo
- CI must enforce quality bar automatically
- Agents cannot bypass human approval gates
- Must support pause/resume via labels
- Must keep PRs small and reviewable

## Acceptance criteria
- [ ] CI validates all artifact contracts
- [ ] CI enforces quality bar heuristics
- [ ] Autonomy gates work via GitHub labels
- [ ] Agent prompts cover all roles with clear handoffs
- [ ] Example project (hello-swarm) passes all validators
- [ ] Playbooks guide humans through swarm operation
- [ ] Status tracking supports pause/resume workflow
- [ ] Constitution defines enforceable quality principles

## Risks & mitigations
- **Risk**: Runaway agents create too many PRs
  - **Mitigation**: autonomy gates require human labels to proceed
- **Risk**: Artifacts drift from actual implementation
  - **Mitigation**: CI validation on every PR
- **Risk**: Agents violate constitution principles
  - **Mitigation**: Kerrigan meta-agent reviews all artifacts
- **Risk**: Large, unreviewable PRs
  - **Mitigation**: Quality bar enforces file size limits

## Success metrics
- New project can be started using only playbooks
- Agents produce CI-green PRs without human debugging
- Human review time focuses on direction, not code quality
- Time from spec to working feature decreases over iterations
