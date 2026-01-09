# Frequently Asked Questions (FAQ)

## General Questions

### What is Kerrigan?

Kerrigan is a repository template that enables teams to orchestrate a swarm of specialized AI agents to deliver software projects with high quality and minimal human intervention. It provides:
- Structured workflows for agent collaboration
- Artifact-driven communication between agents
- Quality enforcement through automated validation
- Human control via autonomy gates and status tracking

Think of it as a "project operating system" that coordinates AI agents while keeping humans in control of key decisions.

### How is Kerrigan different from GitHub Copilot?

| Aspect | GitHub Copilot | Kerrigan |
|--------|----------------|----------|
| **Scope** | Code completion and generation | Full project orchestration |
| **Agents** | Single AI assistant | Multiple specialized agents (Spec, Architect, SWE, Testing, Deploy, etc.) |
| **Workflow** | Developer-driven | Agent-driven with human checkpoints |
| **Artifacts** | Code only | Specs, architecture, plans, tests, runbooks, code |
| **Control** | Always on | Label-based autonomy gates |
| **Quality** | Suggestions | Enforced via CI validators |

**In short**: Copilot helps you write code faster. Kerrigan helps agents deliver complete projects independently.

You can use Copilot (or any AI coding assistant) **as** the agents in Kerrigan's workflow.

### Is Kerrigan a tool or a process?

Both! Kerrigan is:
- **A repository template** with structure and conventions
- **A set of agent prompts** for specialized roles
- **A workflow definition** for moving from spec to production
- **CI automation** for quality enforcement
- **A philosophy** about artifact-driven, human-in-loop collaboration

You can adopt all of it, or just the parts that fit your workflow.

### What languages and frameworks does Kerrigan support?

**All of them!** Kerrigan is intentionally stack-agnostic. It defines:
- What artifacts must exist (spec.md, architecture.md, tests, etc.)
- What quality bar must be met (test coverage, file size limits)
- What workflow phases happen (spec → architecture → implementation → deployment)

But it doesn't mandate Python vs JavaScript, REST vs GraphQL, Docker vs Kubernetes, etc. Teams choose their own stack, and Kerrigan provides the structure.

### Can I use Kerrigan for non-software projects?

Yes, with adaptation! The core principles (artifact-driven workflow, specialized roles, quality enforcement) apply to many domains:
- **Data Science**: Spec → Model Design → Training → Validation → Deployment
- **Documentation**: Outline → Content → Review → Publishing
- **Infrastructure**: Requirements → Architecture → Provisioning → Operations

You'd need to customize the agent prompts and artifact contracts for your domain, but the framework is flexible.

## Setup and Onboarding

### How long does it take to set up Kerrigan?

**Initial setup**: 15-30 minutes
- Fork/clone repository: 2 minutes
- Create GitHub labels: 5 minutes
- Read core documentation: 10-20 minutes

**First project**: 1-2 hours
- Create project folder: 5 minutes
- Invoke Spec and Architect agents: 30-60 minutes
- Implement first milestone: 30-60 minutes

After your first project, subsequent projects are much faster (often <30 minutes to reach implementation).

### Do I need to install any tools locally?

**Minimum (no local tools required)**:
- All validation happens in GitHub Actions CI
- You can work entirely through the GitHub web interface

**Recommended (for better experience)**:
- **Git**: For committing and pushing changes
- **Python 3.8+**: To run validators locally before pushing
- **Your preferred editor**: For editing specs and code

**Optional (for advanced usage)**:
- **GitHub CLI (`gh`)**: For creating labels and issues via command line
- **Docker**: If your project needs containerization
- **Language-specific tools**: Based on your project's stack

### Can I use this in a private repository?

Yes! Kerrigan works in both public and private repositories. The CI workflows use GitHub Actions, which is available for private repos with GitHub's standard usage limits.

Note: GitHub Actions usage is free for public repositories and has generous free tier for private repositories. See GitHub's pricing for details.

### How do I migrate an existing project to Kerrigan?

1. **Create project folder**: `specs/projects/<existing-project>/`
2. **Write spec retrospectively**: Document current state in spec.md
3. **Capture architecture**: Document existing design in architecture.md
4. **Create plan for future work**: Define milestones in plan.md
5. **Add status.json**: Set current phase (e.g., "maintenance" or "enhancement")
6. **Commit to Kerrigan repo**: Your existing code stays where it is

Kerrigan can manage projects that live in separate repositories. The `specs/projects/<name>/` folder is just the control plane.

## Agent Control and Autonomy

### How do I control when agents can work?

Kerrigan uses **autonomy gates** enforced by GitHub labels:

**On-Demand Mode (Recommended)**:
- Add `agent:go` label to an issue
- Agents may create PRs referencing that issue
- Remove label to stop agent work on that issue

**Sprint Mode**:
- Add `agent:sprint` label to a milestone/epic issue
- Agents may work on any issue linked to that milestone
- Remove label when sprint is complete

**Override**:
- Add `autonomy:override` label directly to a PR
- Bypasses all autonomy checks (human approval)

See `playbooks/autonomy-modes.md` for detailed configuration.

### What if I need to pause agent work?

Use `status.json` in your project folder:

```bash
# Pause work
echo '{"status":"blocked","current_phase":"implementation","blocked_reason":"Awaiting review","last_updated":"2026-01-09T12:00:00Z"}' > specs/projects/myproject/status.json

# Resume work  
echo '{"status":"active","current_phase":"implementation","last_updated":"2026-01-09T14:00:00Z"}' > specs/projects/myproject/status.json
```

All agent prompts include a status check at the start. If status is "blocked" or "on-hold", agents stop immediately and report the blocked reason.

### Can different agents work on the same project simultaneously?

No, by design. The workflow is **sequential**:
1. Spec Agent produces spec.md and acceptance-tests.md
2. Architect Agent reads those and produces architecture.md, plan.md, etc.
3. SWE Agent implements based on architecture
4. Testing Agent strengthens coverage
5. Deploy Agent creates operational docs

This ensures each agent has the artifacts it needs from the previous phase. Parallel agent work on different projects is fine and encouraged.

### What if an agent makes a mistake?

**Agents are fallible** — their PRs should always go through human review before merge. When a mistake happens:

1. **Reject the PR**: Add review comments explaining the issue
2. **Agent iterates**: The same agent (or Debugging Agent) can fix it
3. **Fallback to human**: If agent can't fix it, a human can step in

The artifact-driven approach means nothing is lost — all work is in Git, and you can revert or manually edit as needed.

## Costs and Infrastructure

### How much does it cost to run Kerrigan?

**Kerrigan itself**: Free and open source (MIT license)

**Costs you may incur**:
- **AI API calls**: If using OpenAI, Anthropic, etc. for agents
  - Cost depends on usage and model choice
  - Estimate: $5-50 per project depending on size and iterations
  - See `specs/projects/kerrigan/cost-plan.md` for Kerrigan's own costs
- **GitHub Actions**: Free for public repos, free tier for private repos
  - Paid plans if you exceed free tier minutes
- **Infrastructure**: If deploying services (AWS, Azure, GCP, etc.)
  - Depends entirely on your project's needs

**Cost control**:
- Use smaller models (GPT-4o-mini vs GPT-4) for routine tasks
- Limit agent retries with clear prompts
- Review and approve PRs before agents iterate further
- Use `status.json` to pause work if budgets are tight

### Can I use different LLM providers?

Yes! Kerrigan is LLM-agnostic. Agent prompts are just markdown files that you can:
- Copy into any AI assistant (Copilot, Claude, ChatGPT, etc.)
- Use with API-driven tools (langchain, semantic-kernel, etc.)
- Adapt for self-hosted models (llama, mistral, etc.)

The system doesn't care which LLM runs the agents, as long as the artifacts are produced correctly.

### Do agents need access to my repository?

Agents need to:
- **Read** repository files to understand context
- **Write** files to create specs, code, tests, etc.
- **Create PRs** to propose changes

How this works depends on your setup:
- **Manual workflow**: You copy agent prompts to your AI tool, which edits files locally, then you commit and push
- **Automated workflow**: An orchestration tool (like GitHub Copilot Workspace) has repository access and runs agents directly

Kerrigan supports both approaches. The default is manual workflow, which gives maximum human control.

## Quality and Validation

### What quality checks does Kerrigan enforce?

**Artifact Validation** (always run):
- Required files exist for each project
- Required sections present in key files
- Section headings match expected format (case-sensitive)

**Quality Bar** (always run):
- Files <400 LOC: No warning
- Files 400-800 LOC: Warning (still passes CI)
- Files >800 LOC: Fails CI (unless `allow:large-file` label present)

**Autonomy Gates** (always run):
- PRs must reference issues with autonomy labels
- Or PRs must have `autonomy:override` label

**Custom Checks** (optional):
- Add your own validators in `tools/validators/`
- Can enforce test coverage, linting, security scans, etc.

### How do I handle CI failures?

**Step 1: Identify the failure**
- Check GitHub Actions log
- Common failures: missing artifacts, wrong headings, large files, missing labels

**Step 2: Fix the issue**
- Artifact errors: Add missing files or fix section names
- Quality bar: Refactor large files or add `allow:large-file` label
- Autonomy gates: Add required label to issue or PR

**Step 3: Push again**
- CI reruns automatically on every push

**Step 4: If stuck**
- Read validator error messages carefully
- Check `playbooks/handoffs.md` for artifact requirements
- Review example projects in `examples/`

### Can I customize the validators?

Yes! Validators are Python scripts in `tools/validators/`:

**Modify existing validator**:
- Edit `check_artifacts.py` to change requirements
- Example: adjust file size limits, required sections, etc.

**Add new validator**:
- Create new script in `tools/validators/`
- Call it from `.github/workflows/ci.yml`
- Examples: test coverage check, linting enforcement, license verification

**Disable validator**:
- Comment out the check in `.github/workflows/ci.yml`
- Not recommended, but possible if a check doesn't fit your workflow

## Workflow and Processes

### What are the autonomy modes and which should I use?

**Mode A: On-Demand** (Recommended for starting)
- Agents only work when you label an issue `agent:go`
- Maximum human control
- Best for: learning, high-stakes projects, uncertain scope

**Mode B: Sprint Mode** (Good for focused work)
- Label a milestone with `agent:sprint`
- Agents can work on any issue in that milestone
- Best for: time-boxed development, clear scope, trusted agents

**Mode C: Hybrid** (Advanced)
- Spec and Architect agents can always propose
- SWE/Testing/Deploy agents need explicit approval
- Best for: balancing exploration and execution control

Start with Mode A, then graduate to Mode B or C as you gain confidence.

### How do I know what phase my project is in?

Check the `status.json` file if it exists:
```bash
cat specs/projects/myproject/status.json
```

Or review the most recent artifacts:
- Only spec.md exists → **Specification phase**
- architecture.md exists → **Architecture phase**
- Code and tests exist → **Implementation phase**
- runbook.md exists → **Deployment phase**

The `tasks.md` file also tracks completion status for each milestone.

### What if I want to change the workflow?

Kerrigan is customizable! You can:

**Add/remove agent roles**:
- Create new role prompts in `.github/agents/`
- Example: Add "Documentation Agent" or "Security Audit Agent"

**Change phase order**:
- Edit `playbooks/kickoff.md` to redefine workflow
- Example: Add "design review" phase between Architect and SWE

**Modify artifact requirements**:
- Edit `specs/kerrigan/020-artifact-contracts.md`
- Update validators to match new requirements

**Adjust quality bar**:
- Modify line-of-code limits in `tools/validators/check_artifacts.py`
- Add custom quality metrics

The key: keep the workflow **artifact-driven** so agents can discover what to do next.

## Troubleshooting

### Agent prompts are too long for my AI tool

**Solution 1**: Use prompt compression
- Keep only the essential instructions
- Reference full docs via links instead of copying

**Solution 2**: Break prompts into steps
- Run Spec Agent prompt first, commit artifacts
- Then run Architect Agent prompt with updated context

**Solution 3**: Use a tool with larger context
- Claude 3.5 Sonnet: 200K tokens
- GPT-4 Turbo: 128K tokens
- o1: 200K tokens

### Agents aren't producing the right artifacts

**Common causes**:
1. **Prompt unclear**: Add more specific instructions
2. **Missing context**: Ensure agent sees relevant existing files
3. **Wrong heading format**: Check agent prompts for exact headings
4. **Validator too strict**: Adjust requirements if needed

**Solution**: Iterate on agent prompts in `.github/agents/` to improve clarity.

### CI passes but the code is still wrong

CI validates **structure**, not **correctness**:
- Files exist ✅
- Headings match ✅
- Quality bar met ✅

But CI doesn't verify:
- Logic is correct ❌
- Tests are meaningful ❌
- Architecture is sound ❌

**Solution**: Human review is essential! CI catches structural issues, humans catch semantic issues.

## Advanced Topics

### Can Kerrigan manage multiple repositories?

Not directly in v1, but you can:
- Create a "meta-repo" with Kerrigan
- Have project folders reference other repos
- Use runbooks to orchestrate cross-repo work

**Future**: Multi-repo orchestration is planned for v2.

### How do I integrate with external tools?

**CI integration**:
- Add checks to `.github/workflows/ci.yml`
- Examples: Snyk security scanning, SonarQube analysis, deployment gates

**Issue tracking integration**:
- Use GitHub Projects for visualization
- Add custom labels for your workflow
- Link issues to external systems via comments/links

**Notification integration**:
- GitHub Actions can post to Slack, Discord, email, etc.
- Add notification steps to workflows

### Can I use this for open source projects?

Absolutely! Kerrigan is MIT licensed and designed for transparency. Benefits for OSS:
- Clear contribution process (artifact-driven)
- Automated quality checks (consistent standards)
- Documented architecture and decisions (easy onboarding)
- Agent-assisted maintenance (reduce maintainer burden)

Consider adding `CONTRIBUTING.md` that references your Kerrigan workflow.

## Getting More Help

### Where can I see examples?

- `examples/hello-swarm/`: Minimal example project
- `examples/hello-api/`: Complete REST API example
- `specs/projects/kerrigan/`: Kerrigan managing itself (meta-example)

### Documentation structure

- **Getting started**: `README.md`, `docs/setup.md`
- **Architecture**: `docs/architecture.md`
- **Process**: `playbooks/*.md`
- **Specifications**: `specs/constitution.md`, `specs/kerrigan/*.md`
- **Agent roles**: `.github/agents/*.md`

### I have a question not covered here

1. **Check existing docs**: Search README, playbooks, and specs
2. **Review examples**: See how example projects work
3. **Open an issue**: Use the GitHub issue tracker
4. **Contribute**: PRs welcome to improve documentation!

---

**Still confused?** That's okay! Kerrigan has a learning curve. Start with the [setup guide](setup.md), run your first project, and iterate. You'll get the hang of it quickly.
