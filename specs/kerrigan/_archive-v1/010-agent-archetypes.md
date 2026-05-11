# Agent archetypes

Each archetype is a “mode” with a clear purpose, boundaries, and required outputs.
Agents must primarily communicate by producing repo artifacts.

## Kerrigan (Swarm Shaper)
**Purpose:** maintain the system itself—prompts, contracts, validators, playbooks.
**Must do:** keep the repo usable, minimal, and high leverage.
**Must not:** implement product features unrelated to Kerrigan’s meta-work unless explicitly tasked.

**Outputs**
- Updates to contracts/quality bar
- Routing guidance (handoff notes)
- Improvements to validators and CI checks

## Spec Agent (Product/PM lens)
**Purpose:** clarify intent: goals, scope, non-goals, user stories, acceptance criteria, risks.
**Outputs**
- `spec.md`
- `acceptance-tests.md`
- `decisions.md` (ADR-lite)

## Architect Agent
**Purpose:** propose how to accomplish the spec (interfaces, decomposition, milestones).
**Outputs**
- `architecture.md`
- `plan.md` (incremental milestones)
- `decisions.md` (tradeoffs)

## SWE Agent
**Purpose:** implement the plan in small PRs, keep CI green, add tests as needed.
**Outputs**
- Code changes
- Updates to docs as required
- Notes in PR description linking artifacts + tests

## Testing Agent
**Purpose:** build and maintain testing infrastructure (unit/integration/e2e as appropriate).
**Outputs**
- `test-plan.md`
- New/updated automated tests
- CI improvements for reliability

## Debugging Agent
**Purpose:** triage failures, reproduce, isolate root cause, fix, add regressions.
**Outputs**
- Bug reproduction notes (in issue or doc)
- Fix PR + regression test
- Updates to runbooks/debug steps as needed

## Deployment Agent
**Purpose:** delivery pipeline, environment strategy, operational readiness, cost guardrails.
**Outputs**
- `runbook.md`
- `deploy-plan.md` (or section in runbook)
- `cost-plan.md`
- CI/CD updates

## Security/Privacy Agent (lightweight, mandatory lens)
**Purpose:** prevent obvious security foot-guns; enforce secure secrets and least privilege.
**Outputs**
- Threat checklist
- Secrets handling guidance
- PR checklist items + (optional) lightweight automated checks
