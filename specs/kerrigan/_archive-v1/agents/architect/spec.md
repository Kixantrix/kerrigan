# Spec: Architect Agent

## Goal

Design system architectures and implementation roadmaps that translate specifications into actionable, milestone-based plans while balancing technical tradeoffs, quality standards, and project constraints.

## Scope

- Creating `architecture.md` with system design, components, interfaces, and tradeoffs
- Producing `plan.md` with incremental milestones that each end with "CI passes"
- Writing `tasks.md` with executable work items and clear "done when" criteria
- Developing `test-plan.md` outlining testing strategy and coverage goals
- Creating `runbook.md` for deployable projects with operational procedures
- Writing `cost-plan.md` for projects using paid resources with estimates and guardrails
- Documenting architectural decisions and tradeoffs in `decisions.md`

## Non-goals

- Writing actual implementation code (SWE Agent's responsibility)
- Executing tests or building test infrastructure (Testing Agent's responsibility)
- Detailed debugging or troubleshooting procedures beyond initial architecture
- Making product decisions about scope or requirements (Spec Agent's responsibility)
- Final security hardening or detailed threat modeling (Security Agent reviews architecture)

## Users & scenarios

### Primary Users
- **SWE Agent**: Follows architecture and plan to implement system incrementally
- **Testing Agent**: Uses test-plan.md to build appropriate test infrastructure
- **Deployment Agent**: References runbook.md to prepare operational readiness
- **Security Agent**: Reviews architecture.md for security considerations
- **Human Technical Lead**: Reviews architectural decisions for soundness

### Key Scenarios
1. **New Project Architecture**: Reads complete spec → Designs system → Produces all 6 artifacts
2. **Architecture Refinement**: SWE discovers implementation issue → Architect updates architecture.md and plan.md
3. **Milestone Planning**: Breaks large project into 3-5 milestones, each deliverable with green CI
4. **Technology Selection**: Evaluates stack options → Documents tradeoffs in decisions.md
5. **Capacity Planning**: Deployable project → Estimates costs, documents in cost-plan.md

## Constraints

- Must follow exact artifact contract (section headings case-sensitive)
- Must keep stack-agnostic unless spec mandates specific technology
- Must create incremental milestones (each deliverable, not just setup)
- Must include "done when" criteria for all tasks
- Must check project status.json before starting work
- Should align with constitution principles (quality from day one, small increments)
- Artifacts must be sufficient for downstream agents to execute independently

## Acceptance criteria

- All 6+ artifacts exist for appropriate projects (architecture, plan, tasks, test-plan, runbook if deployable, cost-plan if using paid resources)
- architecture.md includes: Overview, Components & interfaces, Tradeoffs, Security & privacy notes
- plan.md contains 3-8 milestones, each ending with "CI passes" or equivalent verification
- tasks.md has clear "done when" criteria for each task
- test-plan.md specifies testing levels (unit/integration/e2e) and tooling
- runbook.md (if applicable) covers deployment, operations, monitoring, troubleshooting, rollback
- cost-plan.md (if applicable) includes estimates, tracking approach, and guardrails
- Milestones are incremental (each delivers working functionality)
- Tasks are actionable and can be completed in 1-3 days each
- Tradeoffs document alternatives considered and rationale for choices
- Architecture is detailed enough for implementation but not over-specified

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Architecture too abstract, SWE can't implement | High | Provide concrete component interfaces, data flow examples; reference similar patterns |
| Architecture over-specifies, constrains implementation unnecessarily | Medium | Focus on contracts and boundaries, not internal implementation; allow SWE flexibility |
| Milestones too large, can't deliver incrementally | High | Enforce "each milestone ends with CI green"; validate milestone size (1-3 days ideal) |
| Tasks lack clarity, SWE unsure when complete | Medium | Require explicit "done when" criteria; provide examples of good vs. bad tasks |
| Missing artifacts (forgets runbook or cost-plan) | Medium | Checklist in agent prompt; validate artifact count matches project type |
| Technology choices don't align with team skills | Medium | Default to stack-agnostic; only specify tech if mandated by spec or strong rationale |
| Cost estimates wildly inaccurate | Low | Provide ranges; document assumptions; plan for monitoring and adjustment |

## Success metrics

- 100% of projects have complete architecture artifacts before implementation begins
- Milestones are appropriately sized (target: 80% completed within estimated timeframe)
- SWE Agent clarification requests during implementation (target: < 3 per milestone)
- Architecture artifacts pass validators on first attempt (target: >80%)
- Downstream agents report architecture is sufficient and clear (qualitative feedback)
- Post-implementation architecture drift is minimal (< 20% of components significantly changed)
