# Spec: hello-swarm

## Goal
Demonstrate the Kerrigan artifact flow with the smallest possible example.

## Scope
- A project folder with required artifacts
- Validators passing in CI

## Non-goals
- Deploying any real service
- Choosing a tech stack

## Users & scenarios
- Agents reading the repo for the first time

## Constraints
- Keep entrypoints short and link-driven.

## Acceptance criteria
- CI passes
- Required artifacts exist and contain required headings

## Risks & mitigations
- Risk: docs drift → mitigate with validators

## Success metrics
- A new agent can find the next step in under 2 minutes.
