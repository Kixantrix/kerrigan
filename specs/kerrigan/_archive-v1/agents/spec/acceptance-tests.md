# Acceptance tests: Spec Agent

## Artifact Completeness

- [ ] **Given** a new project request, **When** Spec Agent completes work, **Then** spec.md exists with all required sections
- [ ] **Given** spec.md is created, **When** validating structure, **Then** it contains: Goal, Scope, Non-goals, Acceptance criteria
- [ ] **Given** spec.md is created, **When** validating, **Then** acceptance-tests.md exists with Given/When/Then scenarios
- [ ] **Given** tradeoff decisions are made, **When** documenting, **Then** decisions.md includes rationale and alternatives

## Quality Standards

- [ ] **Given** acceptance criteria in spec.md, **When** reviewing, **Then** all criteria are measurable (no subjective terms)
- [ ] **Given** a spec with performance requirements, **When** validating, **Then** specific thresholds are defined (e.g., "< 200ms" not "fast")
- [ ] **Given** spec.md content, **When** checking length, **Then** document is concise (prefer bullet points and links)
- [ ] **Given** acceptance-tests.md, **When** reviewing, **Then** edge cases and failure scenarios are included

## Section Headings

- [ ] **Given** spec.md artifact, **When** checking headings, **Then** "Acceptance criteria" uses lowercase 'c'
- [ ] **Given** spec.md artifact, **When** checking headings, **Then** all required section headings match artifact contract exactly

## Content Boundaries

- [ ] **Given** spec.md content, **When** reviewing for implementation details, **Then** no technology stack or framework is specified (unless mandated by constraint)
- [ ] **Given** spec.md content, **When** checking for architecture, **Then** no component design or interface definitions are present
- [ ] **Given** spec.md, **When** checking scope, **Then** it focuses on "what" (user outcomes) not "how" (technical approach)

## Non-functional Requirements

- [ ] **Given** a complete spec, **When** reviewing acceptance criteria, **Then** security requirements are documented (if applicable)
- [ ] **Given** a complete spec, **When** reviewing acceptance criteria, **Then** performance requirements are documented (if applicable)
- [ ] **Given** a complete spec, **When** reviewing, **Then** operational constraints are identified (cost, scalability, availability)

## Stakeholder Communication

- [ ] **Given** spec.md, **When** reviewed by non-technical stakeholder, **Then** goals and acceptance criteria are understandable
- [ ] **Given** spec.md, **When** reviewed by Architect Agent, **Then** sufficient information exists to design system
- [ ] **Given** ambiguous requirement, **When** Spec Agent clarifies, **Then** updates spec.md with clear, measurable criteria

## Status and Workflow

- [ ] **Given** project with status.json, **When** Spec Agent starts work, **Then** agent checks status is "active" or file doesn't exist
- [ ] **Given** status.json shows "blocked", **When** Spec Agent starts work, **Then** agent stops and reports blocked_reason
- [ ] **Given** status.json shows "on-hold", **When** Spec Agent starts work, **Then** agent stops without proceeding

## Edge Cases

- [ ] **Given** spec for extremely small project, **When** creating artifacts, **Then** all required sections present even if brief
- [ ] **Given** spec update request, **When** modifying existing spec, **Then** agent updates last_updated date and maintains consistency
- [ ] **Given** conflicting requirements, **When** documenting, **Then** conflict is noted in risks or decisions.md with mitigation
- [ ] **Given** empty or minimal project brief, **When** starting spec, **Then** agent asks clarifying questions before producing vague spec
