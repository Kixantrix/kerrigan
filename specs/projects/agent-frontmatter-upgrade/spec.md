# Agent Frontmatter Upgrade & Assignment Strategy Investigation

## Problem Statement

Our agent `.md` files in `.github/agents/` do not include the YAML frontmatter required for GitHub to recognize them as custom agents. This means:

1. **Agents don't appear in GitHub's agent dropdown** - Users cannot directly select agents in agent sessions on GitHub.com
2. **Issue-based workflow is friction-heavy** - Currently requires creating an issue, applying labels, and setting up automation
3. **No direct agent invocation** - Cannot start a quick agent session to propose modifications on the fly

## Goal

1. **Update all agent files** to use proper YAML frontmatter so they appear directly in GitHub agent sessions
2. **Investigate optimal agent assignment workflow** - Compare issue-based vs. direct agent session approaches

---

## Part 1: Agent Frontmatter Update

### Required Structure

Each agent file should use this structure:

```yaml
---
name: <Display Name>
description: <Purpose and capabilities - REQUIRED>
tools: <Optional list of tool aliases - defaults to all if omitted>
---

<Agent prompt content in Markdown>
```

### Files to Update

| File | Current State | Proposed `name` | Proposed `description` |
|------|---------------|-----------------|------------------------|
| `kerrigan.swarm-shaper.md` | No frontmatter | `kerrigan-swarm-shaper` | Maintains and improves the Kerrigan system: prompts, validators, playbooks, and contracts |
| `role.architect.md` | No frontmatter | `architect` | Designs system architecture, creates implementation roadmaps, and defines technical decisions |
| `role.debugging.md` | No frontmatter | `debugging` | Investigates failures, fixes bugs, and adds regression tests |
| `role.deployment.md` | No frontmatter | `deployment` | Makes projects production-ready: runbooks, cost plans, and deployment pipelines |
| `role.design.md` | No frontmatter | `design` | Creates and refines design systems, tokens, and component libraries |
| `role.security.md` | No frontmatter | `security` | Identifies and prevents security issues, reviews for vulnerabilities |
| `role.spec.md` | No frontmatter | `spec` | Defines project goals, acceptance criteria, and success metrics |
| `role.swe.md` | No frontmatter | `swe` | Implements features with tests, keeps PRs small and CI green |
| `role.testing.md` | No frontmatter | `testing` | Strengthens test coverage and reliability |
| `role.triage.md` | No frontmatter | `triage` | Manages PR review pipeline, CI status, approvals, and merges |

### Configuration Properties Reference

From [GitHub's custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration):

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Display name (optional, defaults to filename) |
| `description` | string | **Required** - Purpose and capabilities |
| `tools` | list | Tool aliases the agent can use (optional, defaults to all) |
| `target` | string | `vscode`, `github-copilot`, or both (optional) |
| `infer` | boolean | Whether Copilot can auto-select this agent (default: true) |

### Acceptance Criteria - Part 1

- [ ] All 10 agent files in `.github/agents/` have valid YAML frontmatter
- [ ] Each agent has a unique, descriptive `name` 
- [ ] Each agent has a clear `description` (required by GitHub)
- [ ] Agents appear in GitHub's agent dropdown after merge to default branch
- [ ] Existing prompt content preserved below frontmatter
- [ ] README.md updated to document new agent invocation methods

---

## Part 2: Agent Assignment Strategy Investigation

### Current State

Our current workflow for agent assignment:

1. **Label-based assignment** (`role:swe`, `role:spec`, etc.)
2. Requires creating a GitHub issue first
3. Automation in `.github/automation/reviewers.json` maps labels → users
4. Users manually copy prompts to AI assistants
5. Alternative: Assign `@copilot` directly to issues

### New Capabilities (via GitHub Custom Agents)

With proper frontmatter, agents can be invoked:

| Method | Description | Setup Required | Use Case |
|--------|-------------|----------------|----------|
| **Agent Sessions** | Direct invocation from GitHub's Agents tab/panel | Just frontmatter | Quick tasks, on-the-fly modifications |
| **Issue Assignment** | Assign Copilot + select custom agent | Issue + assignment | Tracked work, audit trail |
| **VS Code/JetBrains** | Select from agent dropdown in IDE | Frontmatter in workspace | Local development sessions |
| **GitHub CLI** | `gh agent-task create` with `/agent` command | CLI installed | Automation, scripting |
| **Dashboard** | Start task from GitHub dashboard | Nothing | Quick access |
| **Chat** | Use `/task` in Copilot Chat | Nothing | Conversational |

### Questions to Answer

1. **When should we use issue-based assignment vs. direct agent sessions?**
   - Issues: Audit trail, project tracking, milestone association
   - Sessions: Quick fixes, explorations, prototyping

2. **Should our label-based system (`role:swe`) complement or be replaced by direct agent selection?**
   - Labels still useful for filtering, automation, and human assignment
   - Direct selection removes friction for simple tasks

3. **How do we maintain project context across approaches?**
   - Issues link to `specs/projects/<name>/` artifacts
   - Sessions may need explicit context via custom instructions or repository-level `.github/copilot-instructions.md`

4. **Should some agents be VS Code-only or GitHub.com-only?**
   - Use `target: vscode` or `target: github-copilot` property
   - Design agent might benefit from VS Code focus (live preview)

### Proposed Hybrid Strategy

| Scenario | Recommended Approach | Reason |
|----------|---------------------|--------|
| **New project kickoff** | Issue + Spec agent | Audit trail, milestone tracking |
| **Quick bug fix** | Agent session + Debugging agent | Low friction, fast turnaround |
| **Feature implementation** | Issue + SWE agent | Track progress, link to spec |
| **Code review/triage** | Agent session + Triage agent | Real-time, iterative |
| **Exploratory refactor** | Agent session | No upfront planning needed |
| **Design iteration** | VS Code + Design agent | Local preview capabilities |
| **Security audit** | Issue + Security agent | Documented findings |

### Acceptance Criteria - Part 2

- [ ] Document recommended workflow for each agent role
- [ ] Update `docs/agent-assignment.md` with new invocation methods
- [ ] Create decision tree: "How should I invoke an agent?"
- [ ] Identify which agents benefit from `target` restrictions
- [ ] Test agent session workflow end-to-end
- [ ] Document how to pass project context to agent sessions

---

## Implementation Plan

### Milestone 1: Frontmatter Update (1-2 hours)
1. Add YAML frontmatter to all 10 agent files
2. Validate format matches GitHub specification
3. Update `.github/agents/README.md` 
4. Test locally that files parse correctly

### Milestone 2: Deployment & Testing (30 min)
1. Merge to default branch
2. Verify agents appear in GitHub dropdown
3. Test invoking each agent via session

### Milestone 3: Documentation Update (1 hour)
1. Update `docs/agent-assignment.md` with new methods
2. Add decision tree for invocation choice
3. Update playbooks affected by new workflow

### Milestone 4: Strategy Recommendation (async)
1. Team discussion on hybrid approach
2. Finalize recommendations per agent role
3. Update constitution or playbooks if needed

---

## References

- [GitHub Custom Agents Configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [Creating Custom Agents](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents)
- [About Custom Agents](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-custom-agents)
- [Asking Copilot to Create a PR](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-a-pr)
- [Current Agent Assignment Pattern](../../../docs/agent-assignment.md)

---

## Notes

- Agent profiles in `.github/agents/` are repository-level (project-specific)
- Organization-level agents go in `.github-private` repo if needed
- Maximum prompt size: 30,000 characters
- Filename convention: `<name>.md` or `<name>.agent.md` (we use `.md`)
