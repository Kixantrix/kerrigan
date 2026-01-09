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

**Key accomplishments**:
- Created `specs/projects/kerrigan/` with all required artifacts
- Filled in all 8 artifact files with comprehensive content
- Verified validators pass for kerrigan's own structure
- Committed changes and confirmed CI passes

**Deliverable**: Kerrigan project passes all its own validators ✅

**Dependencies**: None (uses existing foundation)

**Rollback**: Delete `specs/projects/kerrigan/` folder

**Tasks**: See Milestone 1 section in `specs/projects/kerrigan/tasks.md` for complete task list (11 tasks, all complete)

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
**Status**: ✅ Complete

**Goal**: Optimize role-to-role transitions based on real usage

- [x] Run full spec → deploy cycle on a new example project (hello-api)
- [x] Identify handoff friction points (6 documented friction points)
- [x] Update playbooks/handoffs.md with learnings
- [x] Refine agent prompts for clearer output expectations
- [x] Add handoff checklist to artifact contracts

**Deliverable**: Smooth multi-agent workflow with minimal human intervention ✅

**Key Accomplishments**:
- Created hello-api example project with full workflow execution
- Documented 6 friction points across all agent phases
- Updated handoffs.md with workflow refinements and checklist
- Achieved 97% test coverage on implementation
- Validated artifact contracts through real usage
- Identified validator heading requirements as key pain point

**Lessons Learned**:
1. Validator expectations need explicit documentation
2. Manual testing essential even with high automated coverage
3. Architecture phase is heaviest (6+ artifacts)
4. Linting config should be created with code, not after
5. Testing guidance needed in SWE agent prompt
6. Deploy validation may need environment-specific workarounds

**Dependencies**: Milestones 2-4 (full workflow with controls)

**Rollback**: Revert to Milestone 2 playbooks

## Milestone 6: Documentation and onboarding polish
**Status**: ✅ Complete

**Goal**: Make Kerrigan usable by external teams

**Key accomplishments**:
- Created comprehensive documentation suite (architecture, setup, FAQ)
- Added Mermaid architecture diagram showing workflow and control plane
- Polished all agent prompts with examples and guidelines (5x expansion)
- Completed fresh user test and validated onboarding experience
- Enhanced README with 5-minute quickstart section
- Verified all internal links (100% passing)
- Validated CI passes with all updates

**Deliverable**: External team can adopt Kerrigan in < 2 hours ✅

**Key Metrics**:
- Documentation created: 43K+ characters across 4 new files
- Agent prompts expanded: 300 → 1,500 lines (5x average)
- Link validity: 100%
- Time to productivity: <2 hours
- CI status: All passing ✅

**Dependencies**: Milestone 5 (refined workflow)

**Rollback**: None (documentation improvements)

## Future (post-v1)
- Status dashboard (web UI for visibility)
- Cost tracking across projects
- Advanced quality metrics (test coverage, cyclomatic complexity)
- Integration with external spec tools (e.g., Spec Kit)
- Multi-repo support (orchestrating across services)
