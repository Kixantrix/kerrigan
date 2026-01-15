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
**Status**: ✅ Complete

**Goal**: Prove agents can execute the full workflow end-to-end

- [x] Create test issue with `agent:go` label
- [x] Spec agent produces spec.md and acceptance-tests.md
- [x] Architect agent produces architecture.md and plan.md
- [x] Kerrigan meta-agent validates constitution alignment
- [x] SWE agent implements a small feature (e.g., enhance validator)
- [x] Testing agent adds test coverage
- [x] All PRs keep CI green

**Deliverable**: At least one feature implemented entirely by agents ✅

**Key accomplishments**:
- Created comprehensive test project: `specs/projects/validator-enhancement/`
- Validated all agent prompts produce valid, validator-passing artifacts
- Documented 13 workflow learnings in `playbooks/handoffs.md`
- Created GitHub labels documentation and test issue template
- Performed systematic constitution compliance review
- Maintained CI green throughout validation
- Generated comprehensive completion report

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

## Milestone 7: Advanced features and scaling
**Status**: 🔄 Planning (current)

**Goal**: Take Kerrigan from single-repository agent swarm to enterprise-ready platform with multi-repo orchestration, workflow optimization, and comprehensive visibility/analytics.

**Split into 3 phases**:
- **7a**: Multi-repo support + CLI tool foundation (8 weeks, ~Jan-Feb 2026)
- **7b**: Status dashboard + basic cost tracking (8 weeks, ~Mar-Apr 2026)
- **7c**: Advanced coordination + cost analytics + optimization (8 weeks, ~May-Jun 2026)

**Key features**:
- Multi-repository project coordination
- CLI tool for workflow automation (`kerrigan init`, `status`, `invoke`)
- Prompt loading via URL (reduce copy-paste)
- Web dashboard for project visibility and monitoring
- Task dependency management and parallel agent work
- Cost tracking, estimation, and optimization
- Prompt optimization (TL;DR summaries, modular composition)

**Deliverable**: Teams manage work across multiple repos with automated tooling and real-time visibility ✅

**Key Metrics**:
- Multi-repo support adopted by 3+ teams
- CLI tool used in 50%+ of projects
- Workflow time reduced 30% via automation
- Dashboard accessed 10+ times/week per team
- Cost tracking enables 50% reduction in budget overruns

**Dependencies**: Milestones 1-6 (complete), optionally 3-4 for enhanced status tracking

**Rollback**: All features additive; old projects work unchanged. Can disable individual features:
- Multi-repo: Projects continue in single-repo mode
- CLI: Manual workflow remains supported
- Dashboard: CLI provides same data, GitHub API as fallback
- Cost tracking: Optional; can be fully disabled

**Tasks**: See Milestone 7 sections in `specs/projects/kerrigan/milestone-7-tasks.md` for complete breakdown (60+ tasks across 3 phases)

**Risks and Mitigations**:
1. **Multi-repo complexity**: Start with 2-repo examples, limit to 5 repos max, require explicit dependencies
2. **Scope creep**: Split into 3 sub-milestones, time-box to 3 months each, defer nice-to-haves
3. **Breaking changes**: All features additive, version markers for opt-in, parallel testing against M1-6
4. **Dashboard as SPOF**: Read-only view of Git state, CLI provides same data, fallback to GitHub UI
5. **Cost tracking overhead**: Opt-in by default, async logging, focus on project-level budgets

**Success Criteria**:
- [ ] Multi-repo project spec schema defined and validated
- [ ] CLI tool (init, status, invoke) working cross-platform
- [ ] Prompts accessible via stable URLs with versioning
- [ ] Dashboard displays projects, status, CI results, costs
- [ ] Task dependencies enforced by CI
- [ ] Cost estimation and budget alerts functional
- [ ] Example multi-repo project completes spec → deploy cycle
- [ ] 30% reduction in manual workflow steps measured
- [ ] Agent feedback 80%+ positive on M7 features
- [ ] All Milestone 1-6 projects continue working unchanged

**Related Documents**:
- `specs/projects/kerrigan/milestone-7-spec.md` - Detailed specification
- `specs/projects/kerrigan/milestone-7-tasks.md` - Actionable task breakdown
- `docs/milestone-6-retrospective.md` - Learnings that informed M7 planning

## Future (post-v2)

**Note**: Milestone 7 (phases 7a, 7b, 7c) collectively represents the v2.0 release of Kerrigan. The items below are considerations for v3+ and beyond.

- Advanced quality metrics (test coverage, cyclomatic complexity)
- Integration with external spec tools (e.g., Spec Kit)
- Agent self-improvement (learning from feedback history)
- Template customization for different project types
- Security audit trails and compliance reporting
- Integration with external tools (Slack, monitoring, etc.)
