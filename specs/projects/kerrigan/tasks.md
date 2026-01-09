# Tasks: Kerrigan

Each task should be executable and have "done" criteria.

## Milestone 1: Kerrigan governs itself

- [x] Task: Create kerrigan project folder
  - Done when: `specs/projects/kerrigan/` exists with all template files
  - Links: architecture.md (artifact layer)

- [x] Task: Fill in kerrigan spec.md
  - Done when: spec.md has goal, scope, acceptance criteria, risks
  - Links: spec.md template, constitution.md

- [x] Task: Fill in kerrigan acceptance-tests.md
  - Done when: tests cover validator enforcement, autonomy gates, agent workflow
  - Links: acceptance-tests.md template

- [x] Task: Fill in kerrigan architecture.md
  - Done when: documents components, data flow, tradeoffs
  - Links: architecture.md template, meta-specs

- [x] Task: Fill in kerrigan plan.md
  - Done when: has 6+ milestones from foundation to external adoption
  - Links: plan.md template

- [x] Task: Fill in kerrigan tasks.md
  - Done when: has executable tasks with done criteria for each milestone
  - Links: tasks.md template

- [x] Task: Fill in kerrigan test-plan.md
  - Done when: defines testing strategy for validators and workflows
  - Links: test-plan.md template

- [x] Task: Fill in kerrigan runbook.md
  - Done when: documents how to operate Kerrigan swarm
  - Links: runbook.md template, playbooks/

- [x] Task: Fill in kerrigan cost-plan.md
  - Done when: estimates agent API costs and defines guardrails
  - Links: cost-plan.md template, cost-guardrails.md

- [x] Task: Run validators on kerrigan project
  - Done when: `python tools/validators/check_artifacts.py` passes
  - Links: check_artifacts.py

- [x] Task: Commit and verify CI
  - Done when: CI goes green on PR with kerrigan artifacts
  - Links: .github/workflows/ci.yml

## Milestone 2: Agent workflow validation

- [ ] Task: Create GitHub labels
  - Done when: `agent:go`, `agent:sprint`, `autonomy:override`, `allow:large-file`, role labels exist
  - Links: playbooks/autonomy-modes.md

- [ ] Task: Create test issue for agent workflow
  - Done when: issue exists with clear scope and `agent:go` label
  - Links: playbooks/kickoff.md

- [ ] Task: Test spec agent prompt
  - Done when: agent produces valid spec.md and acceptance-tests.md
  - Links: .github/agents/role.spec.md

- [ ] Task: Test architect agent prompt
  - Done when: agent produces valid architecture.md and plan.md
  - Links: .github/agents/role.architect.md

- [ ] Task: Test Kerrigan meta-agent prompt
  - Done when: agent validates constitution compliance and provides feedback
  - Links: .github/agents/kerrigan.swarm-shaper.md

- [ ] Task: Test SWE agent on small feature
  - Done when: agent implements feature with tests and CI stays green
  - Links: .github/agents/role.swe.md

- [ ] Task: Document workflow gaps
  - Done when: learnings added to playbooks/handoffs.md
  - Links: playbooks/handoffs.md

## Milestone 3: Status tracking

- [ ] Task: Design status.json schema
  - Done when: schema documented in artifact contracts
  - Links: specs/kerrigan/020-artifact-contracts.md

- [ ] Task: Add status.json validator
  - Done when: check_artifacts.py validates status.json structure
  - Links: tools/validators/check_artifacts.py

- [ ] Task: Update agent prompts to check status
  - Done when: all role prompts include status.json check step
  - Links: .github/agents/role.*.md

- [ ] Task: Test pause/resume workflow
  - Done when: agent respects "blocked" status and resumes on "active"
  - Links: playbooks/handoffs.md

## Milestone 4: Autonomy gates

- [ ] Task: Research GitHub label reading in Actions
  - Done when: know how to access PR/issue labels in CI
  - Links: .github/workflows/agent-gates.yml

- [ ] Task: Implement autonomy gate workflow
  - Done when: workflow checks for required labels based on mode
  - Links: playbooks/autonomy-modes.md

- [ ] Task: Test on-demand mode
  - Done when: PR without `agent:go` fails CI
  - Links: autonomy-modes.md

- [ ] Task: Test override mechanism
  - Done when: PR with `autonomy:override` bypasses gate
  - Links: autonomy-modes.md

- [ ] Task: Document limitations
  - Done when: README notes any manual workarounds needed
  - Links: README.md

## Milestone 5: Handoff refinement

- [ ] Task: Run full workflow on new example project
  - Done when: new project goes from spec to deploy using only agents
  - Links: playbooks/kickoff.md

- [ ] Task: Identify handoff friction
  - Done when: list of issues documented in playbooks/handoffs.md
  - Links: playbooks/handoffs.md

- [ ] Task: Update agent prompts based on learnings
  - Done when: prompts are clearer about handoff triggers and outputs
  - Links: .github/agents/

- [ ] Task: Add handoff checklist to contracts
  - Done when: artifact contracts include inter-role dependencies
  - Links: specs/kerrigan/020-artifact-contracts.md

## Milestone 6: Documentation polish

- [x] Task: Add architecture diagram to README
  - Done when: visual showing agent flow and control plane
  - Links: README.md, docs/architecture.md

- [x] Task: Create setup walkthrough
  - Done when: step-by-step guide or video exists
  - Links: docs/setup.md

- [x] Task: Write FAQ
  - Done when: covers common setup and workflow questions
  - Links: docs/FAQ.md

- [x] Task: External user test
  - Done when: someone unfamiliar adopts Kerrigan successfully
  - Links: docs/fresh-user-test.md

- [x] Task: Polish agent prompts
  - Done when: prompts are concise and unambiguous
  - Links: .github/agents/

- [x] Task: Verify documentation links
  - Done when: all internal links validated
  - Links: link validation script

- [x] Task: Create retrospective
  - Done when: lessons learned documented
  - Links: docs/milestone-6-retrospective.md
