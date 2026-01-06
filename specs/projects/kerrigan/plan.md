# Plan: Kerrigan

Milestones must end with green CI.

## Milestone 0: Foundation (current state)
**Status**: ✅ Complete

- [x] Repository structure established
- [x] Constitution and meta-specs written
- [x] Artifact contracts defined
- [x] Quality bar and validator tooling created
- [x] CI workflow configured
- [x] Agent role prompts drafted
- [x] Example project (hello-swarm) created
- [x] Playbooks written
- [x] MIT license added

**Deliverable**: Initial commit to main branch

## Milestone 1: Kerrigan governs itself
**Status**: ✅ Complete

**Goal**: Make Kerrigan the first project managed by the system

- [x] Create `specs/projects/kerrigan/` with all required artifacts
- [x] Fill in all kerrigan artifact files (spec, acceptance-tests, architecture, plan, tasks, test-plan, runbook, cost-plan)
- [x] Run validators on kerrigan project
- [x] Verify all validators work on kerrigan's own structure
- [x] Commit and verify CI passes

**Deliverable**: Kerrigan project passes all its own validators

**Dependencies**: None (uses existing foundation)

**Rollback**: Delete `specs/projects/kerrigan/` folder

**Note**: Testing autonomy modes and documenting gaps will be addressed in Milestone 2 during agent workflow validation.

## Milestone 2: Agent workflow validation
**Goal**: Prove agents can execute the full workflow end-to-end

- [ ] Create test issue with `agent:go` label
- [ ] Spec agent produces spec.md and acceptance-tests.md
- [ ] Architect agent produces architecture.md and plan.md
- [ ] Kerrigan meta-agent validates constitution alignment
- [ ] SWE agent implements a small feature (e.g., enhance validator)
- [ ] Testing agent adds test coverage
- [ ] All PRs keep CI green

**Deliverable**: At least one feature implemented entirely by agents

**Dependencies**: Milestone 1 (kerrigan self-governance)

**Rollback**: Revert agent-created PRs; mark playbooks with lessons learned

## Milestone 3: Status tracking and pause/resume
**Goal**: Enable robust control of agent workflow state

- [ ] Add `status.json` schema and validator
- [ ] Update playbooks to include status checks
- [ ] Test blocking/unblocking via status field
- [ ] Add status visibility to CI output
- [ ] Document status tracking in handoff playbook

**Deliverable**: Agents can pause and resume based on status.json

**Dependencies**: Milestone 2 (validated workflow)

**Rollback**: Status tracking is optional; can be removed without breaking core flow

## Milestone 4: Autonomy gate enforcement
**Goal**: Implement label-based autonomy controls in CI

- [ ] Enhance `agent-gates.yml` workflow to check labels
- [ ] Add GitHub API integration for label reading (or manual alternative)
- [ ] Test on-demand mode (require `agent:go`)
- [ ] Test sprint mode (allow `agent:sprint`)
- [ ] Test override label (`autonomy:override`)
- [ ] Document limitations and manual fallbacks

**Deliverable**: CI enforces autonomy modes based on labels

**Dependencies**: Milestone 3 (status tracking)

**Rollback**: Remove autonomy gate workflow; rely on human PR review only

## Milestone 5: Handoff protocol refinement
**Goal**: Optimize role-to-role transitions based on real usage

- [ ] Run full spec → deploy cycle on a new example project
- [ ] Identify handoff friction points
- [ ] Update playbooks/handoffs.md with learnings
- [ ] Refine agent prompts for clearer output expectations
- [ ] Add handoff checklist to artifact contracts

**Deliverable**: Smooth multi-agent workflow with minimal human intervention

**Dependencies**: Milestones 2-4 (full workflow with controls)

**Rollback**: Revert to Milestone 2 playbooks

## Milestone 6: Documentation and onboarding polish
**Goal**: Make Kerrigan usable by external teams

- [ ] Add architecture diagrams to README
- [ ] Create video or step-by-step walkthrough
- [ ] Add FAQ for common setup issues
- [ ] Test onboarding with fresh user (no context)
- [ ] Polish agent prompt clarity based on feedback

**Deliverable**: External team can adopt Kerrigan in < 2 hours

**Dependencies**: Milestone 5 (refined workflow)

**Rollback**: None (documentation improvements)

## Future (post-v1)
- Status dashboard (web UI for visibility)
- Cost tracking across projects
- Advanced quality metrics (test coverage, cyclomatic complexity)
- Integration with external spec tools (e.g., Spec Kit)
- Multi-repo support (orchestrating across services)
