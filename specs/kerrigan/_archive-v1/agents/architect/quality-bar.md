# Quality Bar: Architect Agent

## Definition of Done

An architecture is "done" when:
- [ ] All required artifacts exist for project type (minimum: architecture.md, plan.md, tasks.md, test-plan.md)
- [ ] Deployable projects include runbook.md
- [ ] Projects using paid resources include cost-plan.md
- [ ] All artifacts have required sections with exact heading names
- [ ] Plan contains 3-8 incremental milestones, each ending with "CI passes" or equivalent
- [ ] Tasks have explicit "done when" criteria
- [ ] Architecture is detailed enough to guide implementation but not over-specified
- [ ] Tradeoffs document alternatives and rationale
- [ ] Security considerations are documented
- [ ] status.json was checked before starting work
- [ ] Artifacts are internally consistent (tasks align with plan, test-plan aligns with architecture)

## Structural Standards

### Required Artifacts by Project Type

**All Projects (minimum 4 artifacts)**:
- architecture.md
- plan.md
- tasks.md
- test-plan.md

**Deployable Projects (add 1)**:
- runbook.md

**Projects Using Paid Resources (add 1)**:
- cost-plan.md

### architecture.md Required Sections (case-sensitive)
- `## Overview` – High-level approach and rationale (1-3 paragraphs)
- `## Components & interfaces` – Key components and how they interact
- `## Tradeoffs` – Design decisions with pros/cons (minimum 2 tradeoffs)
- `## Security & privacy notes` – Security considerations and mitigations

### plan.md Structure
- **3-8 milestones** typically (more for very large projects, fewer for small)
- Each milestone:
  - Has clear objective (what working functionality is delivered)
  - Contains 3-10 tasks typically
  - Ends with "Done when: CI passes" or equivalent verification
  - Builds incrementally on previous milestone

### tasks.md Structure
- Each task has:
  - Clear description (what needs to be done)
  - Explicit "done when" criteria
  - Links to relevant artifacts
  - Estimated effort (hours or days)
- Tasks are granular (completable in 1-2 days each typically)

### test-plan.md Sections
Should include:
- Testing levels (unit, integration, e2e, performance as appropriate)
- Tooling and framework selection
- Coverage goals and priorities
- Risk areas requiring focused testing
- CI/CD integration strategy

### runbook.md Sections (if deployable)
Must cover:
- Deployment procedures (how to deploy to each environment)
- Operational procedures (start, stop, monitor, scale)
- Monitoring and alerting
- Troubleshooting common issues
- Rollback procedures
- Secret management

### cost-plan.md Sections (if using paid resources)
Must include:
- Estimated costs with ranges and assumptions
- Cost tracking approach and tools
- Guardrails (budgets, alerts, limits)
- Optimization opportunities

## Content Quality Standards

### Architecture Clarity
✅ **Good** (clear and actionable):
- "API Layer: Express.js HTTP handlers at /api/v1/*, accepts JSON, returns JSON or error codes"
- "Authentication Middleware: Validates JWT tokens, attaches user context to request, returns 401 if invalid"
- "Data Layer: PostgreSQL via Knex.js, exposes async CRUD methods, handles connection pooling"

❌ **Bad** (vague or over-specified):
- "API Layer: Handles requests" (too vague)
- "Authentication: Uses JWT with RS256 algorithm, 2048-bit keys, token payload includes uid/email/roles, refresh token in httpOnly cookie with sameSite=strict" (over-specified implementation details)

### Tradeoff Documentation
✅ **Good** (alternatives with rationale):
```markdown
## Tradeoffs

### PostgreSQL vs MongoDB
**Decision**: PostgreSQL
- Pro: Relational model fits data, ACID guarantees, mature tooling
- Con: Less flexible schema, harder horizontal scaling
- Rationale: Data is relational, consistency matters more than flexibility

### Monolith vs Microservices
**Decision**: Start with monolith, modular structure for future splitting
- Pro: Simpler deployment, easier debugging, faster iteration
- Con: All components scale together, harder to split teams
- Rationale: Team is small, early stage, unclear where scaling will be needed
```

❌ **Bad** (no alternatives or rationale):
```markdown
## Tradeoffs
We're using PostgreSQL and a monolith because it's simpler.
```

### Milestone Incrementality
✅ **Good** (incremental value):
```markdown
## Milestone 1: Core API scaffold (1-2 days)
- Project setup with linting and CI
- Database schema and migrations
- Health check endpoint with tests
**Done when**: CI passes, health check returns 200

## Milestone 2: User authentication (2-3 days)
- User registration endpoint
- Login with JWT issuance
- Token validation middleware
- Integration tests for auth flow
**Done when**: Users can register, login, access protected routes; CI passes
```

❌ **Bad** (not incremental):
```markdown
## Milestone 1: Project setup (1 day)
- Create repo, add dependencies
**Done when**: Boilerplate exists

## Milestone 2: Implement everything (5 days)
- All features from spec
**Done when**: Everything works
```

### Task Actionability
✅ **Good** (clear and specific):
- "Implement user registration endpoint - Done when: POST /api/register accepts email/password, creates user in DB, returns 201 with user ID, includes tests"
- "Add JWT validation middleware - Done when: Middleware validates token, attaches user to request context, returns 401 on invalid token, includes unit tests"

❌ **Bad** (vague or too large):
- "Build authentication - Done when: Auth works"
- "Implement entire API - Done when: All endpoints from spec exist"

## Common Mistakes to Avoid

### Structural Errors
- ❌ Using "Components and Interfaces" instead of "Components & interfaces"
- ❌ Using "Security and Privacy" instead of "Security & privacy notes"
- ❌ Missing required artifacts (especially runbook for deployable or cost-plan for paid resources)
- ❌ Creating single massive milestone instead of 3+ incremental ones

### Content Errors
- ❌ Architecture too abstract (SWE Agent can't implement from it)
- ❌ Architecture over-specified (dictates internal implementation choices unnecessarily)
- ❌ Milestones that are just setup (Milestone 1: "Add dependencies")
- ❌ Tasks without "done when" criteria
- ❌ No tradeoffs documented (every design has tradeoffs)
- ❌ Technology choices without rationale

### Process Errors
- ❌ Starting work when status.json shows "blocked" or "on-hold"
- ❌ Not reading spec.md before designing architecture
- ❌ Forgetting to create test-plan.md
- ❌ Creating artifacts that don't pass validators

## Validation Checklist

Before considering architecture complete, verify:

### Artifact Presence
- [ ] architecture.md exists with all required sections
- [ ] plan.md exists with 3-8 milestones
- [ ] tasks.md exists with clear "done when" criteria
- [ ] test-plan.md exists
- [ ] runbook.md exists (if deployable project)
- [ ] cost-plan.md exists (if using paid resources)
- [ ] decisions.md updated (if architectural decisions made)

### Architecture Quality
- [ ] Overview explains approach and rationale
- [ ] Components and interfaces are clearly defined
- [ ] At least 2 tradeoffs documented with alternatives
- [ ] Security considerations documented
- [ ] Detailed enough for implementation but not over-specified
- [ ] Stack-agnostic unless spec mandates technology

### Plan Quality
- [ ] 3-8 milestones (appropriate for project size)
- [ ] Each milestone delivers working functionality
- [ ] Each milestone ends with "CI passes" or equivalent
- [ ] Milestones are sequenced logically
- [ ] Dependencies between milestones are clear

### Task Quality
- [ ] All tasks have "done when" criteria
- [ ] Tasks are granular (1-2 days each typically)
- [ ] Tasks link to relevant artifacts
- [ ] Tasks are actionable (can start immediately)

### Test Plan Quality
- [ ] Testing levels appropriate for project
- [ ] Tooling and frameworks specified
- [ ] Coverage goals defined
- [ ] Risk areas identified
- [ ] Aligns with acceptance criteria from spec

### Runbook Quality (if applicable)
- [ ] Deployment procedures documented
- [ ] Operational procedures clear
- [ ] Monitoring approach defined
- [ ] Troubleshooting guidance provided
- [ ] Rollback procedures documented
- [ ] Secret management approach specified

### Cost Plan Quality (if applicable)
- [ ] Cost estimates with ranges
- [ ] Assumptions documented
- [ ] Tracking approach defined
- [ ] Guardrails specified (budgets, alerts)

### Consistency
- [ ] Tasks align with milestones
- [ ] Test plan aligns with architecture
- [ ] Runbook aligns with architecture
- [ ] No contradictions between artifacts

## Review Standards

### Self-Review
Before submitting architecture, agent should:
1. Verify all required artifacts exist for project type
2. Check that SWE Agent could implement from these artifacts alone
3. Confirm milestones are incremental and appropriately sized
4. Validate tradeoffs document real alternatives
5. Ensure security considerations are addressed
6. Run through artifact validators if available

### Peer Review (Human or Agent)
Reviewers should validate:
- Architecture completeness and clarity
- Appropriateness of technology choices (if specified)
- Incrementality of milestones
- Feasibility of implementation plan
- Alignment with spec requirements
- Alignment with constitution principles

### Handoff Readiness
Architecture is ready for handoff when:
- [ ] SWE Agent can begin implementation immediately
- [ ] Testing Agent can build test infrastructure from test-plan.md
- [ ] Deployment Agent can prepare operational procedures from runbook.md
- [ ] Security Agent can review for security adequacy
- [ ] Human technical lead can approve architectural decisions

## Examples

### Good Tradeoff Documentation
```markdown
## Tradeoffs

### REST vs GraphQL API
**Decision**: REST
- Pro: Simpler for team, better tooling, easier caching
- Con: Multiple round trips for related data, no schema introspection
- Rationale: Team unfamiliar with GraphQL, clients can batch requests

### SQL vs NoSQL
**Decision**: PostgreSQL
- Pro: ACID guarantees, relational model, strong consistency
- Con: Rigid schema, vertical scaling limits
- Rationale: Data is highly relational (users, posts, comments), consistency critical
```

### Good Milestone Structure
```markdown
## Milestone 1: Foundation (2 days)
- Project structure, linting, CI config
- Database schema and migrations
- Health check endpoint
**Done when**: CI passes with green health check test

## Milestone 2: Core API (3 days)
- CRUD endpoints for primary resource
- Input validation
- Integration tests
**Done when**: Can create, read, update, delete resource via API; CI passes

## Milestone 3: Authentication (2 days)
- User registration and login
- JWT middleware
- Protected route examples
**Done when**: Auth flow works end-to-end; CI passes
```

## Continuous Improvement

The Architect Agent role should evolve based on:
- Feedback from SWE Agent on architecture clarity and completeness
- Patterns in architecture changes made during implementation (indicates initial design gaps)
- Milestone completion rates (indicates sizing accuracy)
- Downstream agent success (Testing, Deployment, Security)

Changes to this quality bar should be proposed via:
1. Issue documenting the problem or improvement opportunity
2. Example of current vs. improved approach
3. Update to this quality-bar.md
4. Update to role.architect.md agent prompt
