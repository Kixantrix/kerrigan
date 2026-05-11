# Quality Bar: Spec Agent

## Definition of Done

A spec is "done" when:
- [ ] All required artifacts exist (spec.md, acceptance-tests.md, and decisions.md if applicable)
- [ ] All required sections are present in spec.md with exact heading names
- [ ] Acceptance criteria are measurable and testable (no subjective terms)
- [ ] Both functional and non-functional requirements are documented
- [ ] Edge cases and failure modes are identified in acceptance-tests.md
- [ ] Content focuses on "what" (outcomes) not "how" (implementation)
- [ ] Document is concise and uses links appropriately
- [ ] status.json was checked before starting work
- [ ] Artifacts pass automated validators

## Structural Standards

### Required Sections (case-sensitive)
spec.md MUST include:
- `## Goal` – 1-2 sentences, clear and measurable
- `## Scope` – Bullet list of what's included
- `## Non-goals` – Bullet list of what's explicitly excluded
- `## Acceptance criteria` – Measurable success criteria (lowercase 'c')

spec.md SHOULD include (for completeness):
- `## Users & scenarios` – Who uses this and in what contexts
- `## Constraints` – Technical, business, or resource constraints
- `## Risks & mitigations` – What could go wrong and how to prevent it
- `## Success metrics` – How to measure project success

### Section Length Guidelines
- **Goal**: 1-2 sentences (< 100 words)
- **Scope**: 3-10 bullet points typically
- **Non-goals**: 2-8 bullet points typically
- **Acceptance criteria**: 5-15 criteria for most projects
- **Overall spec.md**: Prefer < 500 lines; MUST be < 1000 lines

### acceptance-tests.md Structure
- Use Given/When/Then format OR checklist format (be consistent)
- Group tests by category (functionality, edge cases, errors, performance, security)
- Include at least 2 edge cases or failure scenarios
- Typically 10-30 test scenarios for a complete feature

## Content Quality Standards

### Measurability
✅ **Good** (measurable):
- "API response time < 200ms at 95th percentile under normal load"
- "Support authentication via Google and GitHub OAuth2"
- "System handles 1000 concurrent users without degradation"
- "All data encrypted at rest using AES-256"

❌ **Bad** (vague/subjective):
- "API is fast"
- "Authentication works well"
- "System is scalable"
- "Data is secure"

### Focus on Outcomes
✅ **Good** (user-centric):
- "Users can filter search results by date range"
- "Failed login attempts show clear error messages"
- "Administrators can export usage reports as CSV"

❌ **Bad** (implementation-focused):
- "Use Redis for caching search results"
- "Implement JWT-based authentication"
- "Store usage data in PostgreSQL with daily rollup jobs"

### Non-functional Requirements
Every spec SHOULD address:
- **Performance**: Response times, throughput, capacity
- **Security**: Authentication, authorization, data protection
- **Reliability**: Uptime, error rates, recovery
- **Usability**: User experience considerations
- **Maintainability**: Code quality, documentation needs
- **Cost**: Budget constraints, resource limits

If a non-functional area is not applicable, state it explicitly in Non-goals.

## Common Mistakes to Avoid

### Structural Errors
- ❌ Using "Acceptance Criteria" (capital C) instead of "Acceptance criteria"
- ❌ Using "In scope:" as label instead of `## Scope` heading with bullets
- ❌ Missing required sections (Goal, Scope, Non-goals, Acceptance criteria)
- ❌ Mixing heading levels (use ## for main sections consistently)

### Content Errors
- ❌ Including technology choices in spec (e.g., "Use React and Node.js")
- ❌ Specifying architecture (e.g., "Three-tier architecture with API gateway")
- ❌ Subjective criteria (e.g., "Interface is intuitive and user-friendly")
- ❌ Copying requirements verbatim without organizing or clarifying

### Process Errors
- ❌ Starting work when status.json shows "blocked" or "on-hold"
- ❌ Skipping decisions.md when important tradeoffs were considered
- ❌ Creating spec without verifying it will pass artifact validators
- ❌ Over-specifying edge cases that constrain implementation options

## Validation Checklist

Before considering spec complete, verify:

### Artifact Presence
- [ ] `specs/projects/<project>/spec.md` exists
- [ ] `specs/projects/<project>/acceptance-tests.md` exists
- [ ] `specs/projects/<project>/decisions.md` exists (if decisions were made)

### Content Completeness
- [ ] Goal is clear and addresses the "why"
- [ ] Scope has 3+ items that define boundaries
- [ ] Non-goals has 2+ items to prevent scope creep
- [ ] Acceptance criteria includes both functional and non-functional requirements
- [ ] Edge cases and error conditions are documented
- [ ] Security requirements are explicit (if applicable)
- [ ] Performance requirements have thresholds (if applicable)

### Quality Checks
- [ ] No subjective terms in acceptance criteria
- [ ] No implementation details or tech stack mentions
- [ ] Document is concise (prefers bullets and links over prose)
- [ ] All sections use consistent formatting
- [ ] Links to external resources are valid
- [ ] Grammar and spelling are correct

### Handoff Readiness
- [ ] Architect Agent can design a system from this spec alone
- [ ] Non-technical stakeholder can understand goals and criteria
- [ ] Testing Agent can derive test plan from acceptance criteria
- [ ] No ambiguity about what success looks like

## Review Standards

### Self-Review
Before submitting spec, agent should:
1. Re-read acceptance criteria and verify each is measurable
2. Check that scope items align with goal
3. Verify non-goals prevent common scope creep risks
4. Confirm no implementation leakage
5. Run through artifact validators if available

### Peer Review (Human or Agent)
Reviewers should validate:
- Spec completeness and clarity
- Alignment with constitution principles
- Measurability of acceptance criteria
- Appropriate level of detail (not too vague, not over-specified)
- Consistency with existing project artifacts (if update)

### Acceptance Criteria for the Spec Itself
A good spec passes this meta-test:
- [ ] Can answer: "What problem does this solve?"
- [ ] Can answer: "Who benefits and how?"
- [ ] Can answer: "How do we know when it's done?"
- [ ] Can answer: "What's explicitly out of scope?"
- [ ] Cannot answer: "How is it implemented?" (that's intentional - architect's job)

## Examples

### Minimal but Complete Spec
Even small projects need structure:
```markdown
## Goal
Enable CLI users to generate UUIDs quickly.

## Scope
- Generate UUID v4
- Output to stdout

## Non-goals
- Other UUID versions
- File output
- Batch generation

## Acceptance criteria
- Command runs in < 100ms
- Outputs valid UUID v4 format
- Returns exit code 0 on success
```

### Well-Specified Non-functional Requirements
```markdown
## Acceptance criteria
- API responds in < 200ms (p95) under normal load
- Handles 1000 req/sec without errors
- Uptime > 99.9% per month
- All data encrypted at rest (AES-256)
- Authentication via OAuth2 (Google, GitHub)
- Rate limit: 100 req/min per user
```

## Continuous Improvement

The Spec Agent role should evolve based on:
- Feedback from downstream agents (Architect, SWE) on spec clarity
- Patterns in clarification requests during implementation
- Artifact validator failures that reveal common mistakes
- Constitution updates that affect spec requirements

Changes to this quality bar should be proposed via:
1. Issue documenting the problem
2. Example of current vs. improved approach
3. Update to this quality-bar.md
4. Update to role.spec.md agent prompt
