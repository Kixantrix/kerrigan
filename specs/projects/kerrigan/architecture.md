# Architecture: Kerrigan

## Overview
Kerrigan is a Git-repo-based coordination system for agent swarms. All state lives in files; CI enforces contracts; GitHub labels control autonomy.

**Core principle**: agents are stateless workers. The repo is the single source of truth.

## Components & interfaces

### 1. Artifact layer (`specs/`)
- **Constitution**: non-negotiable principles (quality, increments, tests)
- **Kerrigan meta-specs**: role definitions, artifact contracts, quality bar
- **Project specs**: per-project folders with standard artifact set

**Interface**: markdown files following defined section structure

### 2. Playbooks (`playbooks/`)
- Human-readable guides for:
  - kickoff (starting new projects)
  - autonomy modes (controlling agent behavior)
  - handoffs (role-to-role transitions)
  - PR review workflow

**Interface**: markdown with step-by-step instructions

### 3. Agent prompts (`.github/agents/`)
- Role-specific behavioral prompts
- Kerrigan meta-agent prompt (constitution enforcer)
- Output expectations and success criteria

**Interface**: markdown files designed for copy-paste into agent context

### 4. Validators (`tools/validators/`)
- `check_artifacts.py`: enforces required files and sections per project
- `check_quality_bar.py`: enforces file size limits and structure heuristics

**Interface**: Python scripts; exit code 0 = pass, non-zero = fail

### 5. CI workflows (`.github/workflows/`)
- `ci.yml`: runs validators on every PR
- `agent-gates.yml`: checks autonomy labels (future)

**Interface**: GitHub Actions; blocks merge on failure

### 6. Control plane (GitHub features)
- **Labels**: `agent:go`, `agent:sprint`, `autonomy:override`, role labels
- **Issues**: track work scope and agent authorization
- **PRs**: agents submit work; humans approve
- **Status checks**: CI gate for merge protection

## Data flow (conceptual)

```
Human creates issue + adds agent:go
    ↓
Agent reads: constitution, artifact contracts, project spec
    ↓
Agent produces: new/updated artifacts in specs/projects/<name>/
    ↓
Agent opens PR
    ↓
CI runs: check_artifacts.py, check_quality_bar.py
    ↓
Human reviews: scope/direction (not debugging)
    ↓
Merge → becomes new source of truth
    ↓
Next agent reads updated artifacts → continues work
```

## Tradeoffs

### Choice: Markdown files over database
- **Pro**: human-readable, Git-native, zero infrastructure
- **Con**: no structured queries, manual parsing
- **Rationale**: simplicity and transparency matter more than query power

### Choice: CI validation over runtime checks
- **Pro**: enforces contracts before merge; no broken states
- **Con**: slower feedback than real-time
- **Rationale**: correctness over speed; agents can iterate in draft PRs

### Choice: Label-based autonomy over config file
- **Pro**: visible in GitHub UI; easy to toggle per-issue
- **Con**: requires manual label management
- **Rationale**: explicit human control is more important than automation

### Choice: Stack-agnostic
- **Pro**: works with any language/framework
- **Con**: validators can't check language-specific quality
- **Rationale**: reusability across teams/projects

## Security & privacy notes
- **No secrets in repo**: constitution mandates secure secret handling
- **No credential commits**: .gitignore should cover common secret files
- **Least privilege**: deployment runbooks must specify minimal access
- **Agent access**: agents read public repo content; no special GitHub API access required (labels/approvals are human-only)
- **Autonomy override**: humans can always bypass via `autonomy:override` label
