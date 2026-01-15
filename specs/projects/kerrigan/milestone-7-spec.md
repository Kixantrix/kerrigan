# Spec: Milestone 7 - Advanced Features and Scaling

## Goal

Take Kerrigan from a single-repository agent swarm system to an enterprise-ready platform that supports multi-repository orchestration, advanced workflow optimization, and comprehensive visibility/analytics.

Enable teams to:
- Manage coordinated work across multiple repositories
- Reduce manual workflow overhead through better tooling
- Gain real-time visibility into agent work and project status
- Track costs and optimize agent efficiency
- Support parallel agent work with dependency management

## Scope

### In scope

1. **Multi-repository support**
   - Define projects that span multiple repositories
   - Coordinate agent handoffs across repositories
   - Shared status tracking and artifact references
   - Cross-repo dependency management

2. **Workflow optimization**
   - CLI tool for common operations (project init, agent invoke, status check)
   - Prompt loading via URL or API (reduce copy-paste)
   - Automated git operations (branch creation, commit, push where safe)
   - Batch operations for multiple artifacts

3. **Status dashboard (web UI)**
   - View all active projects and their status
   - Monitor agent work in progress
   - Track blockers and dependencies
   - Display CI/validation results
   - Cost tracking and budget alerts

4. **Advanced agent coordination**
   - Parallel agent work on independent tasks
   - Explicit dependency declarations between tasks
   - Work queue management for agent load balancing
   - Handoff checklist automation

5. **Cost tracking and analytics**
   - Log API usage per project and agent role
   - Cost estimation before agent work begins
   - Budget alerts and guardrails
   - Usage analytics and optimization recommendations

6. **Prompt optimization**
   - TL;DR summaries for long prompts
   - Modular prompt composition (base + role-specific)
   - Version management for prompts
   - Context window size awareness

## Non-goals

- **Fully automated deployment**: Human approval for production deploys remains required
- **AI model hosting**: Use existing AI APIs (OpenAI, Anthropic, etc.)
- **Real-time collaboration**: Async workflow via Git/PRs is intentional
- **IDE integration**: Focus on CLI/API, let IDEs build on top
- **Breaking changes to existing workflows**: Milestone 7 should be additive

## Users & scenarios

### Multi-repo team lead

**Scenario**: Managing a microservices architecture with 5 repositories

- Defines a project that spans API, frontend, database, and infrastructure repos
- Agent workflow coordinates changes across all repos
- Single source of truth for project status
- Cross-repo dependency tracking ensures correct sequencing

### Efficiency-focused developer

**Scenario**: Wants to minimize manual steps in agent workflow

- Uses CLI tool to initialize projects and invoke agents
- Loads agent prompts via URL instead of copy-paste
- Automated git operations reduce manual branching/committing
- Focuses time on strategic decisions, not mechanics

### Engineering manager

**Scenario**: Needs visibility into agent work and costs

- Views dashboard showing all active projects
- Monitors which agents are working and on what
- Receives alerts when costs exceed budget
- Uses analytics to optimize workflow efficiency

### Agent with parallel tasks

**Scenario**: Multiple independent features can be worked simultaneously

- Task queue shows available work for multiple agents
- Dependencies prevent conflicts (e.g., don't implement before spec complete)
- Load balancing distributes work efficiently
- Parallel work reduces time-to-completion

### Cost-conscious team

**Scenario**: Operating with limited API budget

- Sets budget guardrails before starting projects
- Receives alerts when approaching limits
- Analyzes cost breakdown by agent role and project
- Optimizes prompts and workflows to reduce costs

## Constraints

### Technical constraints
- Must maintain backward compatibility with Milestone 1-6 workflows
- Multi-repo coordination limited by GitHub API rate limits
- Dashboard requires hosting infrastructure (deployment complexity)
- CLI tool must work cross-platform (Linux, macOS, Windows)

### Philosophical constraints
- **Human-in-loop**: Automation should reduce toil, not eliminate human judgment
- **Artifact-driven**: All coordination through repo files, no external state stores
- **Stack-agnostic**: Solutions must work across programming languages
- **Quality first**: Optimizations cannot compromise quality bar

### Operational constraints
- Dashboard hosting has ongoing costs (consider serverless options)
- Multi-repo requires permissions across all repositories
- CLI tool distribution and versioning adds maintenance overhead
- Cost tracking requires API instrumentation (may need wrapper services)

## Acceptance criteria

### Multi-repository support
- [ ] Project spec can reference multiple repositories
- [ ] Agent prompts understand multi-repo context
- [ ] Status tracking works across repositories
- [ ] Cross-repo dependency declaration syntax defined
- [ ] Example multi-repo project validates end-to-end

### Workflow optimization
- [ ] CLI tool can init projects, invoke agents, check status
- [ ] Prompts accessible via stable URLs
- [ ] Git operations automated where deterministic and safe
- [ ] Time to execute common tasks reduced by 30%+

### Status dashboard
- [ ] Web UI displays all active projects
- [ ] Real-time status updates from GitHub webhooks
- [ ] CI/validation results visible per project
- [ ] Cost tracking integrated into dashboard
- [ ] Responsive design works on mobile

### Advanced coordination
- [ ] Task dependency syntax defined and validated
- [ ] Multiple agents can work in parallel on independent tasks
- [ ] Work queue shows available tasks per agent role
- [ ] Dependency violations blocked by CI

### Cost tracking
- [ ] API usage logged per project and role
- [ ] Cost estimates provided before agent work
- [ ] Budget guardrails enforced
- [ ] Analytics dashboard shows cost trends
- [ ] Optimization recommendations generated

### Prompt optimization
- [ ] All long prompts have TL;DR summaries
- [ ] Prompt composition reduces duplication
- [ ] Version management tracks prompt changes
- [ ] Context window requirements documented

## Risks & mitigations

### Risk: Multi-repo complexity explosion

**Risk**: Coordinating across repos introduces exponential coordination overhead

**Mitigation**:
- Start with simple 2-repo examples
- Limit initial support to 5 repos max per project
- Require explicit dependency declarations (fail fast on conflicts)
- Document when multi-repo is appropriate vs. monorepo

### Risk: Dashboard becomes a single point of failure

**Risk**: Teams depend on dashboard for visibility; downtime blocks work

**Mitigation**:
- Dashboard is read-only view of Git state (source of truth remains in repos)
- CLI tool provides same information without dashboard
- Document fallback to direct GitHub interface
- Design for eventual consistency (stale data acceptable)

### Risk: CLI tool version fragmentation

**Risk**: Different team members use different CLI versions; inconsistent behavior

**Mitigation**:
- Semantic versioning with clear compatibility guarantees
- Version check in CLI warns about mismatches
- Pin CLI version in CI (deterministic builds)
- Distribution via standard package managers (brew, apt, etc.)

### Risk: Cost tracking overhead slows agents

**Risk**: Instrumenting API calls adds latency and complexity

**Mitigation**:
- Make cost tracking opt-in (default disabled)
- Use async logging (non-blocking)
- Aggregate cost reports daily (not real-time)
- Focus on project-level budgets, not per-call optimization

### Risk: Breaking existing workflows

**Risk**: Changes to prompts, contracts, or CI break Milestone 1-6 projects

**Mitigation**:
- All new features additive (old projects work unchanged)
- Version markers in project specs (explicit opt-in to M7 features)
- Parallel testing against Milestone 1-6 example projects
- Migration guide documents upgrade path

### Risk: Scope creep and never shipping

**Risk**: Milestone 7 tries to do too much; delays indefinitely

**Mitigation**:
- Split into Milestone 7a (multi-repo + CLI) and 7b (dashboard + analytics)
- Define MVP for each feature area (ship iteratively)
- Time-box to 3 months per sub-milestone
- Defer nice-to-haves to Milestone 8

## Success metrics

### Adoption metrics
- 3+ teams adopt multi-repo support within 3 months
- CLI tool used in 50%+ of projects by 6 months
- Dashboard accessed 10+ times per week per team

### Efficiency metrics
- Time for common operations reduced by 30% (measured via CLI telemetry)
- Manual copy-paste steps reduced from 10+ to 3 or fewer per workflow
- Agent handoff time reduced by 20% (measured via PR timestamps)

### Reliability metrics
- Multi-repo projects maintain 95%+ CI success rate
- Dashboard uptime 99%+ (excluding scheduled maintenance)
- CLI tool backward compatible across 3+ minor versions

### Cost metrics
- Average project cost measured and tracked
- Budget overruns reduced by 50% (proactive alerts)
- Cost per feature delivered decreases 20% via optimization

### Quality metrics
- No regressions in Milestone 1-6 projects (validated via CI)
- New features pass existing quality bar standards
- Agent feedback on M7 features 80%+ positive

## Phased rollout

### Phase 1: Foundation (Milestone 7a)

**Target**: 8 weeks starting Q1 2026 (approximately Jan-Feb 2026)

- Multi-repository project spec schema
- CLI tool MVP (init, status, invoke)
- Prompt URL loading
- Dependency syntax definition
- Example 2-repo project

**Deliverable**: Teams can manage work across 2 repos with CLI assistance

### Phase 2: Visibility (Milestone 7b)

**Target**: 8 weeks following 7a (approximately Mar-Apr 2026)

- Status dashboard web UI
- Real-time project status
- CI/validation integration
- Basic cost tracking
- Analytics reporting

**Deliverable**: Teams have comprehensive visibility into agent work

### Phase 3: Optimization (Milestone 7c)

**Target**: 8 weeks following 7b (approximately May-Jun 2026)

- Advanced coordination (parallel work, dependencies)
- Cost analytics and recommendations
- Prompt optimization and versioning
- Performance tuning
- Production hardening

**Deliverable**: System scales to 10+ concurrent projects per team

**Note**: Each phase can be independently adopted. Teams may complete 7a and 7b while deferring 7c based on their needs. The 3-phase structure manages scope and enables iterative delivery.

## Dependencies

### Technical dependencies
- GitHub API (rate limits, permissions)
- Hosting infrastructure for dashboard (serverless, CDN)
- CLI distribution channels (brew, npm, PyPI)
- Webhook endpoints for real-time updates

### Milestone dependencies
- **Required**: Milestones 1-6 complete (artifact contracts, quality bar, documentation)
- **Recommended**: Milestone 3 complete (status.json tracking)
- **Recommended**: Milestone 4 complete (autonomy gates)

### External dependencies
- AI API providers (OpenAI, Anthropic) for cost tracking
- Package managers for CLI distribution
- Cloud hosting for dashboard (AWS, GCP, Vercel, etc.)

## Rollback strategy

### If multi-repo support fails
- Projects continue working in single-repo mode
- Remove multi-repo extensions from artifact contracts
- Document limitations in architecture.md
- No impact on existing projects

### If CLI tool adoption is low
- CLI remains optional; manual workflow still supported
- Mark CLI as experimental in documentation
- Continue maintaining but don't expand features
- Gather feedback for v2 redesign

### If dashboard proves too costly/complex
- Dashboard remains optional; CLI provides same data
- Shut down dashboard hosting (no data loss)
- Document how to query GitHub API directly
- Consider simpler reporting (e.g., daily email digest)

### If cost tracking overhead is prohibitive
- Make cost tracking fully opt-in
- Remove instrumentation from critical path
- Provide manual cost estimation tools instead
- Document manual tracking processes

## Related documents

- `specs/projects/kerrigan/plan.md` - Overall roadmap (will be updated)
- `specs/projects/kerrigan/architecture.md` - System design
- `docs/milestone-6-retrospective.md` - Learnings informing this milestone
- `docs/automation-limits.md` - Constraints on automation
- `specs/kerrigan/020-artifact-contracts.md` - Existing contracts to extend
