# Kickoff playbook (start a new project)

## 0) Choose autonomy mode
Read `playbooks/autonomy-modes.md` and decide how agents may open PRs.

## 1) Create project folder
Create: `specs/projects/<project-name>/`

Minimum files (copy from `specs/projects/_template/`):
- spec.md
- acceptance-tests.md
- decisions.md (optional initially)
- architecture.md
- plan.md
- tasks.md
- test-plan.md
- runbook.md (if deployable)
- cost-plan.md (if deployable)

## 2) Run the swarm in stages
1) Spec Agent → produce/iterate `spec.md` + acceptance criteria
2) Architect Agent → produce `architecture.md` + `plan.md`
3) Kerrigan Agent → check alignment with constitution + contracts, request fixes
4) SWE Agent → implement milestone 1 (keep CI green)
5) Testing Agent → strengthen harness and coverage
6) Debugging Agent → respond to failures and add regressions
7) Deployment Agent → produce runbook + cost plan and wire CD (if needed)

## 3) Human approvals (recommended)
- Approve scope/non-goals in `spec.md`
- Approve architecture tradeoffs in `architecture.md`
- Approve autonomy mode changes and overrides
