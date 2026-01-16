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

- [x] Task: Create GitHub labels
  - Done when: `agent:go`, `agent:sprint`, `autonomy:override`, `allow:large-file`, role labels exist
  - Links: docs/github-labels.md, playbooks/autonomy-modes.md

- [x] Task: Create test issue for agent workflow
  - Done when: issue exists with clear scope and `agent:go` label
  - Links: docs/test-issue-agent-workflow.md, playbooks/kickoff.md

- [x] Task: Test spec agent prompt
  - Done when: agent produces valid spec.md and acceptance-tests.md
  - Links: specs/projects/validator-enhancement/spec.md, .github/agents/role.spec.md

- [x] Task: Test architect agent prompt
  - Done when: agent produces valid architecture.md and plan.md
  - Links: specs/projects/validator-enhancement/architecture.md, .github/agents/role.architect.md

- [x] Task: Test Kerrigan meta-agent prompt
  - Done when: agent validates constitution compliance and provides feedback
  - Links: specs/projects/validator-enhancement/constitution-review.md, .github/agents/kerrigan.swarm-shaper.md

- [x] Task: Test SWE agent on small feature
  - Done when: agent implements feature with tests and CI stays green
  - Links: specs/projects/validator-enhancement/ (ready for implementation), .github/agents/role.swe.md

- [x] Task: Document workflow gaps
  - Done when: learnings added to playbooks/handoffs.md
  - Links: playbooks/handoffs.md, specs/projects/kerrigan/milestone-2-report.md

## Milestone 3: Status tracking

- [x] Task: Design status.json schema
  - Done when: schema documented in artifact contracts
  - Links: specs/kerrigan/020-artifact-contracts.md
  - Completed: Schema fully documented (see MILESTONE-3-COMPLETION.md)

- [x] Task: Add status.json validator
  - Done when: check_artifacts.py validates status.json structure
  - Links: tools/validators/check_artifacts.py
  - Completed: Validator with 17 unit tests (see MILESTONE-3-COMPLETION.md)

- [x] Task: Update agent prompts to check status
  - Done when: all role prompts include status.json check step
  - Links: .github/agents/role.*.md
  - Completed: All 7 agent prompts check status (see MILESTONE-3-COMPLETION.md)

- [x] Task: Test pause/resume workflow
  - Done when: agent respects "blocked" status and resumes on "active"
  - Links: playbooks/handoffs.md, tests/validators/test_pause_resume_workflow.py
  - Completed: 9 integration tests validate workflow (see MILESTONE-3-COMPLETION.md)

## Milestone 4: Autonomy gates

- [x] Task: Research GitHub label reading in Actions
  - Done when: know how to access PR/issue labels in CI
  - Links: .github/workflows/agent-gates.yml
  - Completed: Workflow already implemented with full label reading capability

- [x] Task: Implement autonomy gate workflow
  - Done when: workflow checks for required labels based on mode
  - Links: playbooks/autonomy-modes.md
  - Completed: agent-gates.yml fully implements all three modes

- [x] Task: Test on-demand mode
  - Done when: PR without `agent:go` fails CI
  - Links: autonomy-modes.md, tests/test_autonomy_gates.py
  - Completed: 47 comprehensive tests validate all scenarios

- [x] Task: Test sprint mode
  - Done when: PR with `agent:sprint` reference gets `agent:go`
  - Links: autonomy-modes.md, tests/test_autonomy_gates.py
  - Completed: Sprint mode auto-applies agent:go, tests verify behavior

- [x] Task: Test override mechanism
  - Done when: PR with `autonomy:override` bypasses gate
  - Links: autonomy-modes.md, tests/test_autonomy_gates.py
  - Completed: Override mechanism tested and working

- [x] Task: Test all label combinations and edge cases
  - Done when: All scenarios and error cases validated
  - Links: tests/test_autonomy_gates.py
  - Completed: Tests cover fallback mode, API errors, cross-repo issues, etc.

- [x] Task: Document limitations
  - Done when: README notes any manual workarounds needed
  - Links: README.md
  - Completed: README includes limitations and workarounds section

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
