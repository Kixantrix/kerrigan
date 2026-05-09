# Kerrigan Meta-Spec

## Goal
Define a reusable, stack-agnostic repo template that enables a swarm of agents to execute projects in a consistent, high-quality way—driven by specs, enforced by CI, and guided by explicit handoffs.

## Scope
- Agent archetypes and responsibilities
- Artifact contracts between roles
- Quality bar & enforceable heuristics
- Autonomy modes (on-demand vs sprint vs hybrid)
- Tooling: validators + GitHub Actions

## Non-goals
- Building a single product/service
- Mandating one tech stack, framework, or cloud service

## Success criteria
- A new project can be started using only the playbooks + prompts in this repo.
- CI enforces artifact completeness and a baseline quality bar.
- Agents can open PRs that are small, test-backed, and aligned to constitution principles.
