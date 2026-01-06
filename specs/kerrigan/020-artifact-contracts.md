# Artifact contracts

Artifacts are the API between agents. Handoffs are not complete until required artifacts exist.

## Per-project required files (minimum)

For each project under `specs/projects/<project-name>/`:

1) `spec.md`
   - Goal
   - Scope / Non-goals
   - Users & scenarios
   - Constraints
   - Acceptance criteria (measurable)
   - Risks & mitigations
   - Success metrics

2) `acceptance-tests.md`
   - Human-readable checks (Given/When/Then or checklist)
   - Edge cases / failure modes

3) `architecture.md`
   - Proposed approach
   - Key components + interfaces
   - Data flows (conceptual)
   - Tradeoffs
   - Security & privacy notes (lightweight)

4) `plan.md`
   - Milestones (each ends with green CI)
   - Dependencies
   - Rollback strategy (if relevant)

5) `tasks.md`
   - Executable work items with clear “done” criteria
   - Links to relevant artifacts

6) `test-plan.md`
   - Test levels (unit/integration/e2e)
   - Tooling strategy
   - Coverage focus and risk areas

7) `runbook.md` (if deployable)
   - How to deploy
   - How to operate
   - How to debug
   - Oncall/incident basics (even if “none”)

8) `cost-plan.md` (if deployable / uses paid resources)
   - Expected cost drivers
   - Guardrails (budgets/alerts/tags)
   - Scale assumptions

## Kerrigan-wide artifacts
- `specs/constitution.md` governs all work.
- `specs/kerrigan/030-quality-bar.md` defines definition-of-done and heuristics.

## Naming and linking
- Each PR must link the project folder it advances (e.g., `specs/projects/foo/`).
- Each artifact should link to adjacent artifacts (spec ↔ plan ↔ tasks).
