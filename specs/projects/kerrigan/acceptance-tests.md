# Acceptance tests: Kerrigan

## Artifact validation
- [x] Given a project folder exists under `specs/projects/<name>/`
      When CI runs
      Then it verifies all required files exist (spec, architecture, plan, tasks, test-plan, acceptance-tests)

- [ ] Given a spec.md is missing required sections
      When CI runs
      Then it fails with actionable error message

- [ ] Given a project has deployable components
      When CI runs
      Then it requires runbook.md and cost-plan.md

## Quality bar enforcement
- [x] Given a source file exceeds 800 LOC
      When CI runs
      Then it fails the quality bar check

- [x] Given a source file is between 400-800 LOC
      When CI runs
      Then it warns but allows the PR

- [ ] Given a PR has label `allow:large-file`
      When CI runs
      Then it bypasses size limits for that file

## Autonomy controls
- [ ] Given an agent opens a PR without `agent:go` label on the issue
      When autonomy mode is "on-demand"
      Then CI fails with autonomy gate message

- [ ] Given a PR has `autonomy:override` label
      When CI runs
      Then it bypasses autonomy gates

- [ ] Given an issue has `agent:sprint` label
      When autonomy mode is "sprint"
      Then agents can open PRs referencing that issue

## Agent workflow
- [ ] Given a human creates a spec issue
      When spec agent is invoked
      Then it produces spec.md and acceptance-tests.md

- [ ] Given spec.md exists
      When architect agent is invoked
      Then it produces architecture.md and plan.md

- [ ] Given architecture.md exists
      When Kerrigan meta-agent reviews
      Then it validates alignment with constitution

- [ ] Given plan.md exists with milestones
      When SWE agent is invoked
      Then it implements first milestone and keeps CI green

## Status tracking
- [ ] Given a project has status.json
      When an agent completes a phase
      Then it updates status with completion timestamp

- [ ] Given status.json shows "blocked"
      When an agent checks the project
      Then it pauses work until unblocked

## Documentation
- [ ] Given a new user reads README.md
      When they want to start a project
      Then they find playbooks/kickoff.md within 100 lines

- [ ] Given an agent reads a role prompt
      When it needs to know what to produce
      Then artifact contracts are clearly referenced
