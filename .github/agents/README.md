# Agent Role Prompts

This directory contains prompts for specialized AI agents that collaborate to deliver software projects.

## Agent Assignment via Labels

**Important**: Agents are not GitHub user accounts. To assign work to an agent role:

1. Apply a **role label** to the issue (e.g., `role:swe`, `role:spec`)
2. Automation assigns configured GitHub users (see `.github/automation/reviewers.json`)
3. Assigned users copy the agent prompt and execute it using their AI assistant

📖 **Full guide**: [Agent Assignment Pattern](../../docs/agent-assignment.md)

## Available Agents

### Project Workflow Agents

These agents execute the main workflow from specification to deployment:

| Agent | File | Primary Responsibility | Key Artifacts |
|-------|------|----------------------|---------------|
| **Spec Agent** | `role.spec.md` | Define project goals and acceptance criteria | spec.md, acceptance-tests.md |
| **Architect Agent** | `role.architect.md` | Design system and create implementation roadmap | architecture.md, plan.md, tasks.md, test-plan.md |
| **SWE Agent** | `role.swe.md` | Implement features with tests | Code, tests, linting config |
| **Testing Agent** | `role.testing.md` | Strengthen test coverage and reliability | Enhanced tests, test-plan.md updates |
| **Debugging Agent** | `role.debugging.md` | Investigate failures and fix bugs | Bug fixes, regression tests |
| **Deploy Agent** | `role.deployment.md` | Make projects production-ready | runbook.md, cost-plan.md, deployment pipelines |
| **Security Agent** | `role.security.md` | Identify and prevent security issues | Security notes in architecture.md and runbook.md |

### Meta Agent

| Agent | File | Primary Responsibility |
|-------|------|----------------------|
| **Kerrigan (Swarm Shaper)** | `kerrigan.swarm-shaper.md` | Maintain and improve the system itself (prompts, validators, playbooks) |

## How to Use Agent Prompts

### Manual Workflow (Recommended)

1. **Copy prompt**: Open the relevant `role.*.md` file
2. **Provide context**: Add project details (name, issue link, current state)
3. **Paste into AI tool**: Use GitHub Copilot, Claude, ChatGPT, or your preferred AI assistant
4. **Review output**: Agents produce files; you review and commit them
5. **Iterate**: If output needs refinement, provide feedback and re-run
6. **Add agent signature**: Include an agent signature in your PR description to verify you used the agent prompt (see [Agent Auditing](../../docs/agent-auditing.md))

### Agent Signature (Required for Auditing)

To help verify that agents are following their prompts, include a signature in your PR description:

```bash
# Generate a signature for your agent role
python tools/agent_audit.py create-signature role:swe

# Output: <!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->
# Copy this into your PR description
```

The signature is an HTML comment that won't be visible in rendered markdown but can be checked by reviewers and automation. See [docs/agent-auditing.md](../../docs/agent-auditing.md) for full details.

### Automated Workflow (Advanced)

Use orchestration tools that can:
- Read prompts from this directory
- Execute agents with repository access
- Create PRs automatically
- Coordinate handoffs between agents

## Typical Project Flow

```
1. Human creates issue with project idea
2. Spec Agent → writes spec.md and acceptance-tests.md
3. Architect Agent → reads spec, writes architecture and plans
4. Kerrigan Agent → validates constitution alignment
5. SWE Agent → implements first milestone with tests
6. Testing Agent → strengthens test coverage
7. Deploy Agent → creates operational runbooks
8. Human reviews and merges PR
9. [Repeat for subsequent milestones]
```

## Agent Design Principles

### Status Checking
All agents check `specs/projects/<project>/status.json` before starting:
- If status is "blocked" or "on-hold", agent stops and reports why
- This enables human pause/resume control

### Artifact-Driven
Agents communicate via repository files, not ephemeral messages:
- Each agent reads artifacts from previous phase
- Each agent produces artifacts for next phase
- Everything is version-controlled and reviewable

### Clear Contracts
Each prompt specifies:
- **Role**: What is this agent responsible for?
- **Deliverables**: What artifacts must be produced?
- **Guidelines**: How to approach the work?
- **Examples**: Concrete patterns to follow
- **Common mistakes**: Errors to avoid

### Validator Awareness
Agents know about validators and produce artifacts that pass:
- Exact heading names (case-sensitive)
- Required sections present
- File size limits respected
- Quality bar standards met

## Customizing Agents

These prompts are starting points. Feel free to:
- **Add new agents**: Create `role.yourname.md` for specialized needs
- **Modify existing prompts**: Adjust for your workflow or tech stack
- **Remove agents**: Not all projects need all roles
- **Combine roles**: For small projects, one agent can do multiple roles

## Agent Coordination

### Sequential Phases
Agents work sequentially, not in parallel:
1. Spec → Architecture → Implementation → Testing → Deployment
2. Each phase needs outputs from the previous phase
3. This ensures dependencies are met

### Handoffs
See `playbooks/handoffs.md` for detailed handoff process:
- What artifacts each phase produces
- What artifacts the next phase consumes
- Validation checkpoints between phases

### Status Tracking
Use `status.json` to coordinate:
```json
{
  "status": "active",
  "current_phase": "implementation",
  "last_updated": "2026-01-09T12:00:00Z"
}
```

## Quality Standards

All agents follow these standards:
- **Test-driven**: Tests written before or during implementation
- **Quality bar**: No files >800 lines without justification
- **Small diffs**: Incremental changes that keep CI green
- **Documentation**: Update docs when changing public APIs
- **Security-aware**: No secrets in code, validate inputs, use least privilege

## Agent Feedback

Agents can provide feedback to improve the system:
- **Purpose**: Report friction points, unclear instructions, or successful patterns
- **Format**: Structured YAML files in `feedback/agent-feedback/`
- **Process**: Kerrigan reviews feedback weekly and implements improvements
- **Template**: Use `feedback/agent-feedback/TEMPLATE.yaml` to submit feedback

See `specs/kerrigan/080-agent-feedback.md` for full specification.

## Getting Help

- **New to agents?** Read `docs/setup.md` for step-by-step guide
- **Questions?** Check `docs/FAQ.md`
- **Issues with prompts?** Submit feedback via `feedback/agent-feedback/`
- **Want to understand workflow?** See `docs/architecture.md` for visual diagram

## Examples

See `examples/` directory for complete project examples showing agent collaboration:
- `examples/hello-swarm/`: Minimal example
- `examples/hello-api/`: Full REST API with tests and deployment

---

**Remember**: Agents are tools to help you build faster and better. You remain in control via:
- Autonomy gates (label-based approval)
- Status tracking (pause/resume)
- PR reviews (approve or request changes)
- Direct file editing (override agent output when needed)
