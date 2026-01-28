# Spec: Copilot SDK/CLI Integration Investigation

**Status**: ✅ Investigation Complete  
**Findings**: [research-findings.md](./research-findings.md)

## Summary of Findings

The GitHub Copilot SDK is a **programmatic interface to the Copilot CLI** that communicates via JSON-RPC. Key discovery:

- **SDK requires CLI**: The SDK spawns or connects to Copilot CLI in server mode
- **User authentication required**: Uses OAuth/CLI auth, not GitHub App tokens  
- **Subscription-based**: Consumes user's Copilot premium request quota
- **Not CI-native**: Requires CLI installed and authenticated on the runner

**Bottom line**: Fully autonomous CI-triggered agents are **not directly supported** without infrastructure changes (self-hosted runner with cached auth).

See [research-findings.md](./research-findings.md) for full analysis, recommended paths forward, and implementation options.

---

## Goal

Investigate the newly announced GitHub Copilot SDK and CLI to determine:
1. How they could enable further automation of the Kerrigan agent system, potentially addressing the current limitation where "GitHub Copilot cannot be directly triggered or invoked from GitHub Actions."
2. What additional benefits and capabilities the SDK provides beyond basic automation (custom agents, context injection, specialized workflows, etc.)

## Background

The Kerrigan system currently has a fundamental automation gap documented in [automation-limits.md](../../../docs/automation-limits.md):

> **Key Finding**: GitHub Actions can automate issue management and workflow orchestration, but **GitHub Copilot cannot be directly triggered or invoked from GitHub Actions**. This requires a human with a GitHub account and Copilot access to work locally or through the web interface.

GitHub has announced new Copilot SDK and CLI tooling that may change this landscape. This investigation will determine:
1. What new capabilities are available
2. How they could integrate with Kerrigan's workflows
3. What the implementation path would look like

## Scope

### In scope
- Research GitHub Copilot SDK capabilities and API surface
- Research GitHub Copilot CLI capabilities and invocation patterns
- Evaluate authentication models (GitHub App, OAuth, service accounts)
- Identify which current manual steps could become automated
- Draft potential architecture for SDK/CLI integration
- Assess security implications and human-in-the-loop requirements
- Document cost implications (API calls, token usage, rate limits)

#### Additional SDK Benefits to Investigate
- **Custom Copilot Extensions**: Can we build Kerrigan-specific Copilot extensions?
- **Context Injection**: Can we feed project specs, architecture docs, and conventions to Copilot?
- **Custom Agents**: Can we define specialized agent behaviors (spec writer, architect, SWE)?
- **MCP Integration**: Does the SDK support Model Context Protocol for tool use?
- **Code Review Automation**: Can we build custom review workflows with project-specific rules?
- **Documentation Generation**: Automated docs from code with project context?
- **Test Generation**: Custom test generation aligned with our test-plan.md patterns?
- **Knowledge Base**: Can we index Kerrigan's specs/playbooks for agent reference?
- **Multi-model Support**: Does the SDK allow model selection or fine-tuning?
- **Telemetry & Analytics**: What insights can we gather about agent effectiveness?

### Out of scope (for this investigation)
- Actual implementation of SDK/CLI integration
- Production deployment of any new automation
- Changes to existing Kerrigan workflows

## Non-goals

- Replace human review for critical decisions (constitution principle)
- Eliminate all manual steps (some are intentional safety gates)
- Build custom Copilot extensions (unless SDK supports this simply)

## Research questions

### 1. SDK Capabilities
- [ ] What is the GitHub Copilot SDK API surface?
- [ ] Can it be invoked programmatically (not just from IDE)?
- [ ] What authentication methods are supported?
- [ ] Can it run in CI/CD environments (GitHub Actions)?
- [ ] What are the rate limits and cost model?

### 2. CLI Capabilities  
- [ ] What commands does the Copilot CLI provide?
- [ ] Can it be invoked in non-interactive (scripted) mode?
- [ ] Does it support code generation workflows?
- [ ] Can it process issue descriptions and generate PRs?
- [ ] What authentication is required?

### 3. Integration Opportunities
- [ ] Could agents be triggered automatically on issue creation?
- [ ] Could PR creation be fully automated from specs?
- [ ] Could code review comments be generated automatically?
- [ ] Could test generation be automated?
- [ ] What would the workflow look like?

### 4. Security & Compliance
- [ ] What permissions would the integration require?
- [ ] How does it align with Kerrigan's human-in-the-loop principles?
- [ ] What audit trail exists for automated actions?
- [ ] Are there enterprise/organizational controls?

### 5. Custom Extensions & Agents
- [ ] Can we build custom Copilot extensions for Kerrigan roles?
- [ ] Can extensions access repository context (specs, architecture, conventions)?
- [ ] Can we define custom prompts/instructions per agent role?
- [ ] Is there a marketplace or distribution mechanism?
- [ ] What's the development/testing workflow for extensions?

### 6. Context & Knowledge
- [ ] Can we inject project-specific context (specs, playbooks, conventions)?
- [ ] Does the SDK support RAG or knowledge base integration?
- [ ] Can we provide examples of good artifacts for few-shot learning?
- [ ] How does context window management work?
- [ ] Can we feed historical decisions/patterns to improve consistency?

### 7. Advanced Capabilities
- [ ] Does the SDK support MCP (Model Context Protocol) for tool use?
- [ ] Can agents invoke external tools (validators, linters, test runners)?
- [ ] Is there multi-turn conversation support for complex tasks?
- [ ] Can we chain multiple agents in a workflow?
- [ ] What debugging/observability tools are available?

## Users & scenarios

### Scenario 1: Automated agent triggering
**As a** project maintainer  
**I want** agents to automatically start work when issues are labeled  
**So that** I don't need to manually invoke Copilot for each task

### Scenario 2: CI-driven code generation
**As a** Kerrigan administrator  
**I want** GitHub Actions to invoke Copilot for implementation tasks  
**So that** the full workflow from spec to PR is automated

### Scenario 3: Scheduled improvements
**As a** Kerrigan administrator  
**I want** self-improvement analysis to generate implementation PRs automatically  
**So that** approved improvements are implemented without manual intervention

## Constraints

- Must maintain human-in-the-loop for merge decisions (constitution)
- Must not require Personal Access Tokens in repository (security)
- Must work within GitHub Actions execution limits (6 hours, rate limits)
- Must have clear audit trail for all automated actions
- Cost must be predictable and within reasonable bounds

## Acceptance criteria

- [ ] SDK/CLI capabilities documented with examples
- [ ] Authentication requirements clearly documented
- [ ] Integration architecture proposal drafted (if feasible)
- [ ] Cost estimate for typical usage patterns
- [ ] Security assessment completed
- [ ] Go/no-go recommendation with rationale
- [ ] If go: Implementation plan with milestones

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SDK/CLI not suitable for CI use | High | Early validation before detailed planning |
| High API costs | Medium | Document costs, set budget limits |
| Security concerns with automated code generation | High | Maintain human approval gates |
| Rate limits prevent practical use | Medium | Design with batching/queuing |
| Feature not GA or may change | Medium | Wait for stable release if needed |

## Success metrics

- Clear recommendation documented within 1 week of starting
- If feasible: Architecture proposal ready for review
- Stakeholder alignment on next steps

## Resources to investigate

- GitHub Copilot SDK documentation (when available)
- GitHub Copilot CLI documentation
- GitHub Copilot for Business/Enterprise API docs
- GitHub App authentication patterns
- GitHub Actions secrets and permissions model

## Related documents

- [automation-limits.md](../../../docs/automation-limits.md) - Current limitations
- [autonomy-modes.md](../../../playbooks/autonomy-modes.md) - Autonomy controls
- [constitution.md](../../constitution.md) - Human-in-loop requirements
