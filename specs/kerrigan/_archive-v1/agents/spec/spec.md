# Spec: Spec Agent

## Goal

Define a specialized agent role that transforms project ideas into clear, measurable specifications with explicit acceptance criteria, ensuring alignment between stakeholders and implementation teams.

## Scope

- Creating and updating `spec.md` documents with clear goal, scope, non-goals, and acceptance criteria
- Producing `acceptance-tests.md` with Given/When/Then test scenarios
- Documenting key decisions in `decisions.md` (ADR-lite format)
- Clarifying user stories, constraints, and success metrics
- Identifying risks and mitigation strategies
- Ensuring specifications are measurable and testable

## Non-goals

- Implementation details or technical architecture (Architect Agent's responsibility)
- Writing actual code or tests (SWE Agent's responsibility)
- Creating detailed implementation plans or milestones (Architect Agent's responsibility)
- Operational procedures or deployment strategies (Deployment Agent's responsibility)

## Users & scenarios

### Primary Users
- **Architect Agent**: Reads spec to design system architecture and create implementation roadmap
- **SWE Agent**: References spec to ensure implementation aligns with requirements
- **Testing Agent**: Uses acceptance criteria to guide test coverage priorities
- **Human Stakeholders**: Review spec to approve project direction before implementation begins

### Key Scenarios
1. **New Project**: Stakeholder has project idea → Spec Agent creates initial spec.md and acceptance-tests.md
2. **Requirement Clarification**: SWE finds ambiguity → Spec Agent updates spec with clarification
3. **Scope Change**: Stakeholder requests feature addition → Spec Agent evaluates fit and updates scope or non-goals
4. **Handoff to Architecture**: Complete spec → Architect Agent begins design phase

## Constraints

- Must follow exact artifact contract (section headings case-sensitive)
- Must produce measurable, non-subjective acceptance criteria
- Must align with constitution principles (quality from day one, artifact-driven)
- Should keep spec concise (prefer links over long prose)
- Must check project status.json before starting work (respect "blocked" or "on-hold" status)

## Acceptance criteria

- All specs include required sections: Goal, Scope, Non-goals, Acceptance criteria
- Acceptance criteria are measurable (no vague terms like "good" or "fast")
- Both functional and non-functional requirements are documented
- Edge cases and failure modes are identified in acceptance-tests.md
- Section headings match artifact contract exactly (case-sensitive)
- Specs are concise and focused on "what" not "how"
- Links to related artifacts and external resources where appropriate
- Risk assessment includes mitigation strategies

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Spec too vague, leads to implementation disagreement | High | Enforce measurable criteria; provide clear examples in acceptance-tests.md |
| Spec includes implementation details, constrains architecture | Medium | Clear guidance on "what not how"; examples of good vs. bad specs |
| Spec becomes too long, agents can't parse effectively | Medium | Encourage conciseness; use links; enforce structure |
| Missing non-functional requirements (performance, security) | High | Explicit checklist in agent prompt; examples showing non-functional criteria |
| Spec diverges from constitution principles | High | Reference constitution in agent prompt; validation checks |

## Success metrics

- 100% of projects have spec.md before architecture phase begins
- Acceptance criteria reviewable by non-technical stakeholders
- Reduced clarification requests during implementation (target: <2 per milestone)
- Specs pass artifact validators on first attempt (target: >80%)
- Architecture and implementation teams report spec is sufficient (qualitative feedback)
