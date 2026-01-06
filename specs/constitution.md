# Constitution (Kerrigan Principles)

This document defines the non-negotiable principles for all work produced under Kerrigan.

## 1) Quality from day one
- No “prototype exception” mode. Start with structure, tests, and CI, immediately.
- Prefer maintainable modular code over giant single-file implementations.

## 2) Small, reviewable increments
- PRs should be narrow, well-scoped, and keep CI green.
- If a change is large, split it into milestones with intermediate value.

## 3) Artifact-driven collaboration
- Work must be expressed in repo artifacts:
  - specs, plans, task lists, ADRs, test plans, runbooks.
- If it isn’t written down in the agreed artifact contract, it doesn’t exist.

## 4) Tests are part of the feature
- Every feature has tests; every bug fix includes a regression test.
- Favor automation and repeatability over manual checking.

## 5) Stack-agnostic, contract-driven
- Kerrigan is compatible with any stack.
- Contracts define required artifacts and quality criteria; teams choose the tech.

## 6) Operational responsibility (incl. cost)
- Deployable work requires a runbook and cost awareness.
- Use secure secret handling and least-privilege access.

## 7) Human-in-the-loop, not human-as-glue
- Humans approve key decisions and direction.
- Agents own implementation, testing, debugging, and deployment excellence.

## 8) Clarity for agents
- Keep key entrypoints discoverable within ~100 lines:
  - README, playbooks, and top-level spec docs should point directly to next steps.
