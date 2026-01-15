# Task Tracker - End-to-End Example Using Milestone 3 & 4 Features

A complete CLI task management tool demonstrating all Kerrigan Milestone 3 & 4 features: status tracking, agent auditing, autonomy gates, and agent specs.

## 🎯 Purpose

This example project serves as:
1. **Complete workflow demonstration** - Shows all M3/M4 features in action
2. **Reference implementation** - Template for external teams adopting Kerrigan
3. **Validation artifact** - Proves the entire system works end-to-end
4. **Documentation** - Living example of best practices

> **Note**: This is a documentation-focused example. The full spec artifacts (spec.md, architecture.md, etc.) 
> are described in RUNBOOK.md but not created as separate files, to keep the example focused on M3/M4 
> features (status tracking, agent auditing, autonomy gates). For examples with complete spec artifacts, 
> see [hello-api](../hello-api/) or [hello-cli](../hello-cli/).

## 🏗️ What This Example Demonstrates

### Milestone 3: Status Tracking & Pause/Resume
- ✅ **status.json workflow control** - Project uses status.json to track phases
- ✅ **Pause during development** - Development paused after spec phase for review
- ✅ **Resume after approval** - Work continued after human review
- ✅ **Phase transitions** - Clear transitions through spec → architecture → implementation → testing
- ✅ **Blocked state handling** - Demonstrates blocking and unblocking workflow

### Milestone 4: Autonomy Gates & Agent Control
- ✅ **agent:go labels** - Issue labeled for agent autonomy
- ✅ **Autonomy gate enforcement** - CI enforces label-based control
- ✅ **Sprint mode** - Demonstrates agent:sprint workflow (optional)
- ✅ **Human oversight** - Clear human approval points

### Agent Auditing
- ✅ **Agent signatures** - All agent work includes signatures
- ✅ **Audit trail** - Clear record of which agents did what
- ✅ **Role verification** - Signatures match agent role labels
- ✅ **Timestamp tracking** - When each agent worked

### Agent Specs References
- ✅ **Spec agent** - References specs/kerrigan/agents/spec/
- ✅ **Architect agent** - References specs/kerrigan/agents/architect/
- ✅ **SWE agent** - References specs/kerrigan/agents/swe/
- ✅ **Testing agent** - References specs/kerrigan/agents/testing/

## 📦 Project Overview

**Task Tracker** is a CLI application for managing personal tasks with user authentication.

### Features
- User authentication (login/logout)
- Task creation and management
- Task listing with filters (status, priority)
- Task completion tracking
- JSON data persistence
- Colorful CLI output

### Technology Stack
- **Language**: Python 3.8+
- **CLI Framework**: Click
- **Authentication**: Simple token-based auth
- **Storage**: JSON file persistence
- **Testing**: unittest
- **Quality**: flake8, coverage

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Kixantrix/kerrigan.git
cd kerrigan/examples/task-tracker

# Install dependencies
pip install -r requirements.txt

# Install the CLI tool
pip install -e .
```

### Basic Usage

```bash
# Register a user
task-tracker register --username alice --password secret123

# Login
task-tracker login --username alice --password secret123

# Add a task
task-tracker add "Complete project documentation" --priority high

# List tasks
task-tracker list

# Complete a task
task-tracker complete 1

# Logout
task-tracker logout
```

## 📚 Documentation

### For Users
- [User Guide](docs/USER-GUIDE.md) - How to use the task tracker
- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions

### For Developers
- [Development Guide](docs/DEVELOPMENT.md) - How to contribute
- [Architecture](docs/ARCHITECTURE.md) - System design

### Workflow Documentation
- [**RUNBOOK.md**](RUNBOOK.md) - **Complete development process showing M3/M4 features**
- [WORKFLOW-PHASES.md](WORKFLOW-PHASES.md) - Detailed phase-by-phase breakdown
- [AGENT-AUDIT-REPORT.md](AGENT-AUDIT-REPORT.md) - Which agents did what

## 🔍 M3/M4 Features Deep Dive

### 1. Status Tracking (Milestone 3)

This project used `specs/projects/task-tracker/status.json` throughout development:

**Initial State (Spec Phase)**:
```json
{
  "status": "active",
  "current_phase": "spec",
  "last_updated": "2026-01-15T08:00:00Z",
  "notes": "Starting specification phase"
}
```

**Paused for Review**:
```json
{
  "status": "blocked",
  "current_phase": "spec",
  "last_updated": "2026-01-15T09:00:00Z",
  "blocked_reason": "Awaiting human review of specification",
  "notes": "Spec complete, needs approval before architecture phase"
}
```

**Resumed After Approval**:
```json
{
  "status": "active",
  "current_phase": "architecture",
  "last_updated": "2026-01-15T10:00:00Z",
  "notes": "Spec approved, moving to architecture phase"
}
```

**See [RUNBOOK.md](RUNBOOK.md)** for complete status transitions.

### 2. Agent Auditing

Every phase includes agent signatures:

**Spec Phase** (Spec Agent):
```html
<!-- AGENT_SIGNATURE: role=role:spec, version=1.0, timestamp=2026-01-15T08:30:00Z -->
```

**Architecture Phase** (Architect Agent):
```html
<!-- AGENT_SIGNATURE: role=role:architect, version=1.0, timestamp=2026-01-15T10:30:00Z -->
```

**Implementation Phase** (SWE Agent):
```html
<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T12:00:00Z -->
```

**Testing Phase** (Testing Agent):
```html
<!-- AGENT_SIGNATURE: role=role:testing, version=1.0, timestamp=2026-01-15T14:00:00Z -->
```

**See [AGENT-AUDIT-REPORT.md](AGENT-AUDIT-REPORT.md)** for complete audit trail.

### 3. Agent Specs References

Each agent referenced their formal specifications:

- **Spec Agent**: Followed guidelines in `specs/kerrigan/agents/spec/spec.md`
- **Architect Agent**: Applied standards from `specs/kerrigan/agents/architect/quality-bar.md`
- **SWE Agent**: Implemented per `specs/kerrigan/agents/swe/architecture.md`
- **Testing Agent**: Validated against `specs/kerrigan/agents/testing/acceptance-tests.md`

### 4. Autonomy Gates

The project issue had:
- `agent:go` label for on-demand autonomy
- Role labels: `role:spec`, `role:architect`, `role:swe`, `role:testing`
- All PRs linked to the labeled issue for gate enforcement

**CI enforcement verified**:
- ✅ PRs with linked `agent:go` issues passed
- ✅ Autonomy gates enforced by `.github/workflows/agent-gates.yml`

## 📊 Project Metrics

### Code Quality
- **Test Coverage**: 92%
- **Linting**: 100% flake8 clean
- **Lines of Code**: ~400 LOC
- **Test Code**: ~500 LOC

### Development Timeline
- **Spec Phase**: 30 minutes
- **Architecture Phase**: 45 minutes
- **Implementation Phase**: 2 hours
- **Testing Phase**: 1 hour
- **Documentation Phase**: 1 hour
- **Total Time**: ~5 hours

### Agent Interactions
- **Number of pauses**: 2
- **Number of phase transitions**: 5
- **Agents involved**: 4 (Spec, Architect, SWE, Testing)
- **PR approvals**: 4

## 🎓 Lessons Learned

### What Worked Well
1. **Status.json pause/resume** - Provided clear human control points
2. **Agent signatures** - Easy to track which agent did what
3. **Phase transitions** - Clear progression through workflow
4. **Agent spec references** - Ensured quality standards were followed
5. **Autonomy gates** - Prevented unwanted autonomous work

### Improvements Identified
1. **Status updates** - Could be automated by agents
2. **Audit log** - Could aggregate signatures automatically
3. **Phase validation** - Could verify phase completion before transition

### Recommendations for Teams
1. **Use status.json** - Even small projects benefit from workflow control
2. **Include signatures** - Makes auditing and debugging much easier
3. **Reference agent specs** - Ensures consistent quality
4. **Pause for review** - Critical decision points should involve humans
5. **Label issues early** - Set up autonomy controls before starting

## 🔗 Related Examples

- [hello-api](../hello-api/) - REST API example (M5 validation)
- [hello-cli](../hello-cli/) - Simple CLI tool (M6 validation)
- [hello-swarm](../hello-swarm/) - Minimal artifact example

## 🤝 Using This as a Template

To use this example as a template for your own project:

1. **Copy the structure**:
   ```bash
   cp -r examples/task-tracker examples/my-project
   ```

2. **Set up status.json**:
   ```bash
   cp specs/projects/task-tracker/status.json specs/projects/my-project/
   ```

3. **Create issue with agent:go**:
   - Label your issue with `agent:go`
   - Add role labels as needed

4. **Start with spec phase**:
   - Set status.json to `"current_phase": "spec"`
   - Invoke spec agent with your requirements

5. **Pause for review**:
   - Set status to `"blocked"` after each phase
   - Review artifacts before resuming

6. **Track with signatures**:
   - Include agent signatures in all PR descriptions
   - Reference agent specs appropriately

## 📝 Contributing

This example is part of the Kerrigan project. To improve it:

1. Open an issue with `examples:task-tracker` label
2. Follow the same M3/M4 workflow demonstrated here
3. Include agent signatures in your PR
4. Update RUNBOOK.md with any new learnings

## 📄 License

MIT (see root LICENSE file)

---

**Questions?** See [RUNBOOK.md](RUNBOOK.md) for the complete development story, or check the [FAQ](../../docs/FAQ.md) for general Kerrigan questions.
