# Tasks: Milestone 7 - Advanced Features and Scaling

Each task should be executable and have "done" criteria.

## Milestone 7a: Foundation (Multi-repo + CLI)

**Target**: Q1 2026 (weeks 1-8)

### Phase 1.1: Multi-repository spec design

- [ ] Task: Design multi-repo project spec schema
  - Done when: Schema documented in artifact contracts with examples
  - Links: specs/kerrigan/020-artifact-contracts.md
  - Details: Add `repositories` array, cross-repo artifact references, dependency syntax

- [ ] Task: Create multi-repo example project
  - Done when: 2-repo example (API + frontend) with specs, handoffs documented
  - Links: examples/multi-repo-app/
  - Details: Simple TODO app with REST API and React frontend

- [ ] Task: Update agent prompts for multi-repo awareness
  - Done when: All role prompts check for multi-repo context, follow cross-repo handoffs
  - Links: .github/agents/role.*.md
  - Details: Add sections on handling multiple repos, artifact references

- [ ] Task: Add multi-repo validation to check_artifacts.py
  - Done when: Validator ensures cross-repo references are valid
  - Links: tools/validators/check_artifacts.py
  - Details: Check repository field, validate artifact paths across repos

- [ ] Task: Document multi-repo workflow in playbooks
  - Done when: playbooks/multi-repo.md explains setup, coordination, gotchas
  - Links: playbooks/multi-repo.md
  - Details: When to use multi-repo vs monorepo, dependency management, permissions

### Phase 1.2: CLI tool foundation

- [ ] Task: Design CLI tool architecture
  - Done when: Architecture documented with commands, config, plugin system
  - Links: specs/projects/kerrigan-cli/architecture.md
  - Details: Choose language (Python/Go/Node), command structure, config format

- [ ] Task: Implement `kerrigan init` command
  - Done when: Creates new project from template, validates structure
  - Links: tools/cli/kerrigan-cli
  - Details: Takes project name, template, creates folder structure

- [ ] Task: Implement `kerrigan status` command
  - Done when: Shows project status, active agents, blockers
  - Links: tools/cli/kerrigan-cli
  - Details: Reads status.json, GitHub API for PRs/issues

- [ ] Task: Implement `kerrigan invoke` command
  - Done when: Fetches agent prompt, optionally opens in editor/AI tool
  - Links: tools/cli/kerrigan-cli
  - Details: Takes role name, formats context, copies to clipboard or opens URL

- [ ] Task: Add CLI configuration file
  - Done when: .kerriganrc supports GitHub token, AI tool integration, defaults
  - Links: tools/cli/kerrigan-cli
  - Details: YAML config, environment variable overrides

- [ ] Task: Package CLI tool for distribution
  - Done when: Available via pip/npm/brew, version checking works
  - Links: tools/cli/kerrigan-cli
  - Details: Setup.py, package.json, or Homebrew formula

- [ ] Task: Write CLI tool documentation
  - Done when: docs/cli-reference.md covers all commands with examples
  - Links: docs/cli-reference.md
  - Details: Installation, configuration, command reference, troubleshooting

### Phase 1.3: Prompt URL loading

- [ ] Task: Create prompt API endpoint
  - Done when: GET /prompts/{role} returns latest prompt for role
  - Links: tools/prompt-server/ or GitHub Pages
  - Details: Simple static file server or GitHub raw URLs

- [ ] Task: Add version management to prompts
  - Done when: Prompts have version headers, changelog tracked
  - Links: .github/agents/
  - Details: Add `# Version: 1.2.3` header, CHANGELOG.md for prompts

- [ ] Task: Update CLI to fetch prompts via URL
  - Done when: `kerrigan invoke spec --remote` fetches from prompt server
  - Links: tools/cli/kerrigan-cli
  - Details: HTTP GET, cache locally, version checking

- [ ] Task: Document prompt URL usage
  - Done when: docs/prompt-loading.md explains URLs, versions, caching
  - Links: docs/prompt-loading.md
  - Details: How to integrate with AI tools, version pinning

### Phase 1.4: Dependency syntax

- [ ] Task: Design task dependency syntax
  - Done when: Syntax defined in artifact contracts with examples
  - Links: specs/kerrigan/020-artifact-contracts.md
  - Details: YAML frontmatter or separate dependencies.yaml file

- [ ] Task: Implement dependency validator
  - Done when: CI fails if task references non-existent dependency
  - Links: tools/validators/check_dependencies.py
  - Details: Parse dependency graph, check for cycles, validate task IDs exist

- [ ] Task: Add dependency visualization to CLI
  - Done when: `kerrigan deps` shows task graph
  - Links: tools/cli/kerrigan-cli
  - Details: Text-based tree or graph, highlight blockers

- [ ] Task: Document dependency best practices
  - Done when: playbooks/dependencies.md explains when/how to declare dependencies
  - Links: playbooks/dependencies.md
  - Details: Granularity guidance, anti-patterns, examples

### Phase 1.5: Testing and validation

- [ ] Task: Test multi-repo workflow end-to-end
  - Done when: 2-repo example project completes spec → deploy cycle
  - Links: examples/multi-repo-app/
  - Details: Manual walkthrough, document timing and friction points

- [ ] Task: Test CLI tool on all platforms
  - Done when: CLI works on Linux, macOS, Windows with automated tests
  - Links: tools/cli/kerrigan-cli
  - Details: CI matrix testing, installation tests, command tests

- [ ] Task: Benchmark workflow time savings
  - Done when: Measured reduction in manual steps, documented in retrospective
  - Links: docs/milestone-7a-metrics.md
  - Details: Compare old workflow (manual) vs new (CLI-assisted)

- [ ] Task: Gather agent feedback on Phase 1 features
  - Done when: 3+ agent feedback files collected, reviewed, addressed
  - Links: feedback/agent-feedback/
  - Details: Use TEMPLATE.yaml, focus on multi-repo and CLI usability

## Milestone 7b: Visibility (Dashboard + Monitoring)

**Target**: Q2 2026 (weeks 9-16)

### Phase 2.1: Dashboard architecture

- [ ] Task: Design dashboard architecture
  - Done when: Architecture documented with tech stack, data flow, hosting strategy
  - Links: specs/projects/kerrigan-dashboard/architecture.md
  - Details: Evaluate frameworks (React/Vue/Svelte), backend (serverless), deployment
  - Decision criteria: Community size, TypeScript support, performance, team familiarity

- [ ] Task: Define dashboard API endpoints
  - Done when: API spec documents endpoints for projects, status, costs, analytics
  - Links: specs/projects/kerrigan-dashboard/api-spec.md
  - Details: RESTful or GraphQL, authentication, rate limiting

- [ ] Task: Set up dashboard hosting infrastructure
  - Done when: Deployed to production with CI/CD pipeline
  - Links: .github/workflows/deploy-dashboard.yml
  - Details: Choose platform (Vercel, Netlify, AWS), domain setup, SSL

### Phase 2.2: Core dashboard features

- [ ] Task: Implement project list view
  - Done when: Dashboard shows all projects with status, last update, CI status
  - Links: dashboard/src/components/ProjectList.tsx
  - Details: Fetch from GitHub API, display in table/card layout

- [ ] Task: Implement project detail view
  - Done when: Click project shows artifacts, PRs, agent activity, timeline
  - Links: dashboard/src/components/ProjectDetail.tsx
  - Details: Fetch project artifacts, parse status.json, show linked issues/PRs

- [ ] Task: Implement real-time status updates
  - Done when: Dashboard updates when PRs opened, CI runs, status.json changes
  - Links: dashboard/src/hooks/useRealtime.ts
  - Details: GitHub webhooks or polling, WebSocket for live updates

- [ ] Task: Implement agent activity view
  - Done when: Shows which agents are working, on what tasks, time in phase
  - Links: dashboard/src/components/AgentActivity.tsx
  - Details: Parse PR metadata, assignees, labels, time since last update

- [ ] Task: Add CI/validation status display
  - Done when: Shows validator results, quality bar checks, pass/fail details
  - Links: dashboard/src/components/CIStatus.tsx
  - Details: Fetch GitHub Actions API, display check runs, link to logs

### Phase 2.3: Dashboard UX and polish

- [ ] Task: Design dashboard UI/UX
  - Done when: Figma mockups or wireframes for all views, responsive design
  - Links: specs/projects/kerrigan-dashboard/designs/
  - Details: Color scheme, navigation, mobile layout

- [ ] Task: Implement dashboard navigation
  - Done when: Sidebar/header navigation, breadcrumbs, search
  - Links: dashboard/src/components/Navigation.tsx
  - Details: React Router or similar, keyboard shortcuts

- [ ] Task: Add dashboard filtering and search
  - Done when: Filter projects by status, search by name, filter agents by role
  - Links: dashboard/src/components/Filters.tsx
  - Details: Client-side filtering, URL state for sharing links

- [ ] Task: Implement dashboard settings
  - Done when: User can configure refresh rate, theme, notifications
  - Links: dashboard/src/components/Settings.tsx
  - Details: Local storage for preferences, dark mode toggle

- [ ] Task: Add dashboard help and onboarding
  - Done when: First-time user sees guided tour, help tooltips on all features
  - Links: dashboard/src/components/Onboarding.tsx
  - Details: Step-by-step walkthrough, contextual help

### Phase 2.4: Basic cost tracking

- [ ] Task: Design cost tracking schema
  - Done when: Schema defined for logging API usage, costs per project/role/call
  - Links: specs/kerrigan/090-cost-tracking.md
  - Details: JSON structure, aggregation strategy, privacy considerations

- [ ] Task: Implement cost logging library
  - Done when: Library can wrap AI API calls, log usage/cost to file or service
  - Links: tools/cost-tracker/
  - Details: Python decorator, JS wrapper, or CLI post-processor

- [ ] Task: Add cost display to dashboard
  - Done when: Dashboard shows total cost, cost by project, cost trends
  - Links: dashboard/src/components/CostTracking.tsx
  - Details: Charts for trends, breakdown by agent role, budget progress

- [ ] Task: Implement budget alerts
  - Done when: Dashboard and/or CLI alerts when project approaches budget limit
  - Links: dashboard/src/services/alerts.ts
  - Details: Check budget in status.json, warn at 80%, block at 100%

- [ ] Task: Document cost tracking setup
  - Done when: docs/cost-tracking.md explains setup, usage, privacy, accuracy
  - Links: docs/cost-tracking.md
  - Details: How to instrument AI calls, limitations, manual vs automatic

### Phase 2.5: Testing and validation

- [ ] Task: Test dashboard with real project data
  - Done when: Dashboard displays 3+ active projects accurately
  - Links: dashboard/
  - Details: Use Kerrigan's own projects, validate data accuracy

- [ ] Task: Test dashboard on multiple browsers/devices
  - Done when: Works on Chrome, Firefox, Safari, mobile browsers
  - Links: dashboard/
  - Details: Cross-browser testing, responsive design validation

- [ ] Task: Load test dashboard API
  - Done when: Dashboard handles 100+ concurrent users, 10+ projects
  - Links: tests/load-tests/
  - Details: Use k6 or similar, identify bottlenecks

- [ ] Task: Document dashboard usage
  - Done when: docs/dashboard-guide.md explains features, tips, troubleshooting
  - Links: docs/dashboard-guide.md
  - Details: Screenshots, video walkthrough, common workflows

- [ ] Task: Gather user feedback on dashboard
  - Done when: 3+ teams use dashboard, provide feedback, satisfaction 80%+
  - Links: feedback/dashboard-feedback/
  - Details: Survey, interviews, usage analytics

## Milestone 7c: Optimization (Coordination + Analytics)

**Target**: Q3 2026 (weeks 17-24)

### Phase 3.1: Advanced coordination

- [ ] Task: Implement parallel task assignment
  - Done when: Multiple agents can claim independent tasks simultaneously
  - Links: tools/task-queue/
  - Details: FIFO queue with claimed tasks, conflict detection

- [ ] Task: Add dependency-aware task scheduling
  - Done when: Tasks with unmet dependencies blocked, ready tasks highlighted
  - Links: tools/task-queue/
  - Details: Evaluate dependency graph, mark tasks as ready/blocked/in_progress

- [ ] Task: Implement work queue visualization
  - Done when: Dashboard and CLI show task queue, agent assignments, dependencies
  - Links: dashboard/src/components/TaskQueue.tsx
  - Details: Kanban-style board or table, color-coded by status

- [ ] Task: Add agent load balancing
  - Done when: System suggests task distribution to balance load across agents
  - Links: tools/task-queue/
  - Details: Simple heuristics (round-robin, least-busy, cost-optimized)

- [ ] Task: Document advanced coordination patterns
  - Done when: playbooks/parallel-work.md explains when/how to use parallel agents
  - Links: playbooks/parallel-work.md
  - Details: Best practices, anti-patterns, examples

### Phase 3.2: Cost analytics and optimization

- [ ] Task: Build cost analytics dashboard
  - Done when: Dashboard shows cost per project, role, time period with charts
  - Links: dashboard/src/components/CostAnalytics.tsx
  - Details: Line charts for trends, pie charts for breakdown, export CSV

- [ ] Task: Implement cost estimation
  - Done when: CLI/dashboard estimates cost before starting project based on plan
  - Links: tools/cost-estimator/
  - Details: Use historical data, prompt token counts, task complexity

- [ ] Task: Generate cost optimization recommendations
  - Done when: System analyzes usage, suggests prompt improvements, workflow changes
  - Links: tools/cost-optimizer/
  - Details: Identify expensive agents, suggest batching, prompt compression

- [ ] Task: Add cost comparison reporting
  - Done when: Compare actual vs estimated costs, identify variances
  - Links: dashboard/src/components/CostComparison.tsx
  - Details: Budget vs actual, explain variances, track accuracy over time

- [ ] Task: Document cost optimization strategies
  - Done when: docs/cost-optimization.md explains techniques, tools, case studies
  - Links: docs/cost-optimization.md
  - Details: Prompt engineering, caching, batching, model selection

### Phase 3.3: Prompt optimization

- [ ] Task: Add TL;DR summaries to long prompts
  - Done when: All prompts >100 lines have 5-10 line summary at top
  - Links: .github/agents/role.*.md
  - Details: Extract key points, must-know info, link to full prompt

- [ ] Task: Implement modular prompt composition
  - Done when: Prompts composed from base + role-specific + project-specific modules
  - Links: .github/agents/modules/
  - Details: Split common sections (constitution, handoffs) from role-unique content

- [ ] Task: Add context window size warnings
  - Done when: Prompts document token count, warn if approaching limits
  - Links: .github/agents/README.md
  - Details: Calculate token counts, document by model (GPT-4, Claude, etc.)

- [ ] Task: Create prompt versioning system
  - Done when: Prompts have semantic versions, changelog, deprecation policy
  - Links: .github/agents/CHANGELOG.md
  - Details: Breaking vs non-breaking changes, migration guides

- [ ] Task: Document prompt optimization techniques
  - Done when: docs/prompt-engineering.md explains best practices for Kerrigan
  - Links: docs/prompt-engineering.md
  - Details: Clarity, brevity, examples, testing, versioning

### Phase 3.4: Performance tuning

- [ ] Task: Profile CLI tool performance
  - Done when: Identify and fix slow commands, <1s response for common operations
  - Links: tools/cli/kerrigan-cli
  - Details: Use profiling tools, cache aggressively, parallel requests

- [ ] Task: Optimize dashboard load times
  - Done when: Dashboard loads in <2s, interactive in <4s
  - Links: dashboard/
  - Details: Code splitting, lazy loading, CDN for assets

- [ ] Task: Optimize validator performance
  - Done when: Validators run in <5s for typical project
  - Links: tools/validators/
  - Details: Cache file reads, parallel validation, skip unchanged files

- [ ] Task: Add caching for GitHub API calls
  - Done when: Reduce API calls by 50%, respect rate limits
  - Links: tools/github-cache/
  - Details: Redis or file-based cache, TTL strategy, cache invalidation

- [ ] Task: Document performance expectations
  - Done when: docs/performance.md defines SLOs, benchmarks, optimization tips
  - Links: docs/performance.md
  - Details: Response time targets, throughput, resource usage

### Phase 3.5: Production hardening

- [ ] Task: Add comprehensive error handling
  - Done when: All tools handle errors gracefully, provide actionable messages
  - Links: tools/
  - Details: Retry logic, fallbacks, user-friendly error messages

- [ ] Task: Implement logging and observability
  - Done when: Structured logging, error tracking, performance monitoring
  - Links: tools/logging/
  - Details: Log levels, correlation IDs, integration with Sentry/DataDog

- [ ] Task: Add security scanning to dashboard
  - Done when: Dashboard scanned for vulnerabilities, HTTPS enforced, auth secured
  - Links: .github/workflows/security-scan.yml
  - Details: OWASP checks, dependency scanning, CSP headers

- [ ] Task: Create disaster recovery plan
  - Done when: Documented procedures for dashboard downtime, data loss, API outages
  - Links: docs/disaster-recovery.md
  - Details: Backup strategy, failover, communication plan

- [ ] Task: Write Milestone 7 retrospective
  - Done when: docs/milestone-7-retrospective.md documents learnings, metrics, next steps
  - Links: docs/milestone-7-retrospective.md
  - Details: What worked, challenges, recommendations for Milestone 8

### Phase 3.6: Testing and validation

- [ ] Task: Run Milestone 7 on 5+ real projects
  - Done when: 5 projects use multi-repo, CLI, dashboard successfully
  - Links: examples/
  - Details: Diverse project types, gather feedback, measure metrics

- [ ] Task: Validate all success metrics achieved
  - Done when: Adoption, efficiency, reliability, cost, quality metrics met
  - Links: specs/projects/kerrigan/milestone-7-spec.md
  - Details: Compare actual vs target, document variances

- [ ] Task: Gather comprehensive agent feedback
  - Done when: 10+ feedback files from agents using M7 features, 80%+ positive
  - Links: feedback/agent-feedback/
  - Details: Structured feedback via TEMPLATE.yaml, categorize and prioritize

- [ ] Task: Update all documentation for Milestone 7
  - Done when: README, architecture, playbooks, FAQ updated with M7 features
  - Links: docs/
  - Details: Add M7 sections, update architecture diagram, new FAQ entries

- [ ] Task: Tag Milestone 7 release
  - Done when: Git tag v2.0.0 created, release notes published
  - Links: GitHub releases
  - Details: Changelog, migration guide, breaking changes

## Cross-cutting concerns

### Documentation maintenance

- [ ] Task: Keep agent prompts in sync with features
  - Ongoing: Review prompts quarterly, update based on feedback
  - Links: .github/agents/

- [ ] Task: Update FAQ with Milestone 7 questions
  - Ongoing: Add Q&A as patterns emerge
  - Links: docs/FAQ.md

- [ ] Task: Maintain example projects
  - Ongoing: Keep examples working, update with new features
  - Links: examples/

### Community and adoption

- [ ] Task: Write Milestone 7 announcement
  - Done when: Blog post/README update announces M7 features
  - Links: README.md, docs/announcements/

- [ ] Task: Create video walkthrough of Milestone 7
  - Done when: 10-minute video demonstrates multi-repo, CLI, dashboard
  - Links: docs/videos/

- [ ] Task: Host community demo session
  - Done when: Live demo to interested teams, Q&A, gather feedback
  - Links: docs/community-sessions.md

### Quality assurance

- [ ] Task: Extend CI for Milestone 7 features
  - Done when: CI validates multi-repo projects, CLI commands, dashboard builds
  - Links: .github/workflows/ci.yml

- [ ] Task: Add integration tests for end-to-end workflows
  - Done when: Automated tests cover multi-repo, CLI, dashboard interaction
  - Links: tests/integration/

- [ ] Task: Monitor and fix bugs
  - Ongoing: Triage issues, prioritize fixes, release patches
  - Links: GitHub issues
