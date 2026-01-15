# Self-Assembly Guide

## Overview

This document provides a comprehensive guide for Kerrigan to reconstruct itself, including a complete dependency map, component relationships, and source code for all critical components. This ensures Kerrigan can be fully reassembled from this documentation alone.

## System Dependencies

### External Dependencies

Kerrigan is intentionally minimalist with very few external dependencies:

```
Kerrigan
├── Runtime Dependencies
│   ├── Git (v2.20+)              # Version control system
│   ├── Python (v3.8+)            # For validators and tests
│   │   └── Standard Library     # No external Python packages required
│   └── GitHub                    # Hosting and CI/CD platform
│       ├── Actions               # CI/CD automation
│       ├── Labels                # Autonomy and role control
│       └── Issues/PRs            # Work coordination
│
└── Optional Dependencies
    ├── GitHub CLI (gh)           # Easier GitHub operations
    ├── Text Editor               # VS Code, Vim, etc.
    └── AI Agent Access           # GitHub Copilot, Claude, etc.
```

**Key Design Principle**: Kerrigan uses only Python standard library to minimize dependencies and maximize portability.

### No External Package Dependencies

Kerrigan intentionally avoids external Python packages (no pip requirements). All validators and tools use only Python standard library modules:

- `pathlib` - File path operations
- `json` - JSON parsing
- `re` - Regular expressions
- `sys` - System operations
- `os` - Operating system interface
- `datetime` - Date/time handling
- `unittest` - Testing framework

## Component Dependency Map

### Visual Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Platform                          │
│  (Hosting, Issues, PRs, Labels, Actions)                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Repository Structure                         │
│  (.git, directory layout, README.md)                           │
└────┬───────────┬────────────┬────────────┬────────────┬─────────┘
     │           │            │            │            │
     ↓           ↓            ↓            ↓            ↓
┌────────┐  ┌────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐
│ Specs  │  │ Agents │  │  Tools  │  │   CI    │  │   Docs   │
│        │  │        │  │         │  │         │  │          │
│ Files  │  │Prompts │  │Validate │  │Workflow │  │ Playbook │
└────┬───┘  └───┬────┘  └────┬────┘  └────┬────┘  └────┬─────┘
     │          │            │            │            │
     ↓          ↓            ↓            ↓            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Validation Layer                            │
│  (check_artifacts.py, check_quality_bar.py)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Test Suite                                │
│  (test_agent_prompts.py, test_automation.py, etc.)             │
└─────────────────────────────────────────────────────────────────┘
```

### Component Dependencies (Bottom-Up)

**Level 0: Foundation**
- Git version control system
- Python interpreter
- GitHub platform

**Level 1: Core Structure**
- Repository directory layout
- `.gitignore`, `.editorconfig`
- `LICENSE`, `README.md`

**Level 2: Specification Layer**
- `specs/constitution.md` ← **No dependencies**
- `specs/kerrigan/*.md` ← Depends on: constitution.md
- `specs/projects/_template/*` ← Depends on: constitution.md

**Level 3: Validation Layer**
- `tools/validators/check_artifacts.py` ← Depends on: constitution.md, project templates
- `tools/validators/check_quality_bar.py` ← Depends on: constitution.md
- `tests/*` ← Depends on: validators

**Level 4: Automation Layer**
- `.github/workflows/ci.yml` ← Depends on: validators, tests
- `.github/workflows/agent-gates.yml` ← Depends on: GitHub labels
- `.github/workflows/auto-*.yml` ← Depends on: GitHub labels, project structure

**Level 5: Agent Layer**
- `.github/agents/role.*.md` ← Depends on: constitution.md, artifact contracts
- `.github/agents/kerrigan.swarm-shaper.md` ← Depends on: all specs

**Level 6: Documentation Layer**
- `docs/*.md` ← Depends on: entire system (documentation only)
- `playbooks/*.md` ← Depends on: entire system (documentation only)

### Circular Dependencies

**None!** Kerrigan is designed with a strict dependency hierarchy to avoid circular dependencies and enable bottom-up reconstruction.

## Critical Component Source Code

### 1. Constitution (specs/constitution.md)

This is the foundation of Kerrigan. It defines non-negotiable principles:

```markdown
# Constitution (Kerrigan Principles)

This document defines the non-negotiable principles for all work produced under Kerrigan.

## 1) Quality from day one
- No "prototype exception" mode. Start with structure, tests, and CI, immediately.
- Prefer maintainable modular code over giant single-file implementations.

## 2) Small, reviewable increments
- PRs should be narrow, well-scoped, and keep CI green.
- If a change is large, split it into milestones with intermediate value.

## 3) Artifact-driven collaboration
- Work must be expressed in repo artifacts:
  - specs, plans, task lists, ADRs, test plans, runbooks.
- If it isn't written down in the agreed artifact contract, it doesn't exist.

## 4) Tests are part of the feature
- Every feature has tests; every bug fix includes a regression test.
- Favor automation and repeatability over manual checking.

## 5) Stack-agnostic, contract-driven
- Kerrigan is compatible with any stack.
- Contracts define required artifacts and quality criteria; teams choose the tech.

## 6) Operational responsibility (incl. cost)
- Deployable work requires a runbook and cost awareness.
- Use secure secret handling and least-privilege access.

## 7) Human-in-the-loop, not human-as-glue
- Humans approve key decisions and direction.
- Agents own implementation, testing, debugging, and deployment excellence.

## 8) Clarity for agents
- Keep key entrypoints discoverable within ~100 lines:
  - README, playbooks, and top-level spec docs should point directly to next steps.
```

### 2. Artifact Validator (tools/validators/check_artifacts.py)

This enforces the artifact contract. **Full source code**:

```python
#!/usr/bin/env python3
"""Repo validators:
- Enforce required spec artifacts for any project folder under specs/projects/<name>/
- Enforce required sections in key docs
- Enforce autonomy gate (optional): PR label checks are not directly accessible in CI without API.
  This script enforces the *structure* that supports autonomy; the label enforcement can be added later
  via GitHub API if desired.

Design philosophy: keep checks simple, actionable, and stack-agnostic.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = ROOT / "specs" / "projects"

REQUIRED_FILES = [
    "spec.md",
    "acceptance-tests.md",
    "architecture.md",
    "plan.md",
    "tasks.md",
    "test-plan.md",
    # runbook.md and cost-plan.md are conditionally required; see below
]

REQUIRED_SECTIONS_SPEC = [
    "Goal",
    "Scope",
    "Non-goals",
    "Acceptance criteria",
]

REQUIRED_SECTIONS_ARCH = [
    "Overview",
    "Components",
    "Tradeoffs",
    "Security",
]

def fail(msg: str) -> None:
    print(f"::error::{msg}")
    raise SystemExit(1)

def warn(msg: str) -> None:
    print(f"::warning::{msg}")

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"Missing required file: {p.relative_to(ROOT)}")
    except Exception as e:
        fail(f"Failed reading {p.relative_to(ROOT)}: {e}")
    return ""

def has_heading(text: str, heading: str) -> bool:
    # Match markdown headings like "# Heading" or "## Heading"
    # Don't escape spaces in the heading, only special regex chars
    # We want "Acceptance criteria" to match literally with its space
    escaped = re.escape(heading).replace('\\ ', ' ')
    pattern = re.compile(r"^#{1,6}\s+" + escaped + r"\s*$", re.MULTILINE)
    return bool(pattern.search(text))

def ensure_sections(p: Path, headings: List[str], doc_name: str) -> None:
    txt = read_text(p)
    missing = [h for h in headings if not has_heading(txt, h)]
    if missing:
        fail(f"{doc_name} missing required headings: {missing} in {p.relative_to(ROOT)}")

def project_folders() -> List[Path]:
    if not SPECS_DIR.exists():
        return []
    return [p for p in SPECS_DIR.iterdir() if p.is_dir() and p.name != "_template"]

def is_deployable(project_dir: Path) -> bool:
    # Heuristic: if runbook.md exists or the spec mentions "deploy" or "production"
    runbook = project_dir / "runbook.md"
    if runbook.exists():
        return True
    spec = project_dir / "spec.md"
    if spec.exists():
        txt = read_text(spec).lower()
        if "deploy" in txt or "production" in txt or "runtime" in txt:
            return True
    return False

def validate_status_json(status_path: Path, project_name: str) -> None:
    """Validate status.json structure and content."""
    try:
        content = status_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        fail(f"Project '{project_name}' has invalid JSON in status.json: {e}")
    except Exception as e:
        fail(f"Project '{project_name}' failed to read status.json: {e}")
    
    # Required fields
    required_fields = ["status", "current_phase", "last_updated"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        fail(f"Project '{project_name}' status.json missing required fields: {missing}")
    
    # Validate status values
    valid_statuses = ["active", "blocked", "completed", "on-hold"]
    if data["status"] not in valid_statuses:
        fail(f"Project '{project_name}' status.json has invalid status '{data['status']}'. Must be one of: {valid_statuses}")
    
    # Validate current_phase values
    valid_phases = ["spec", "architecture", "implementation", "testing", "deployment"]
    if data["current_phase"] not in valid_phases:
        fail(f"Project '{project_name}' status.json has invalid current_phase '{data['current_phase']}'. Must be one of: {valid_phases}")
    
    # Validate last_updated is ISO 8601 format
    try:
        datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        fail(f"Project '{project_name}' status.json has invalid last_updated timestamp. Must be ISO 8601 format: {e}")
    
    # If status is blocked, blocked_reason should be present
    if data["status"] == "blocked" and not data.get("blocked_reason"):
        warn(f"Project '{project_name}' status.json has status=blocked but no blocked_reason provided. Please add a blocked_reason field explaining why work is paused.")

def main() -> None:
    # Constitution must exist
    constitution = ROOT / "specs" / "constitution.md"
    if not constitution.exists():
        fail("Missing specs/constitution.md (governing principles).")

    # Validate each project folder
    for proj in project_folders():
        for f in REQUIRED_FILES:
            path = proj / f
            if not path.exists():
                fail(f"Project '{proj.name}' missing required file {f} at {path.relative_to(ROOT)}")

        # Required sections
        ensure_sections(proj / "spec.md", REQUIRED_SECTIONS_SPEC, "spec.md")
        # Architecture headings are matched loosely via keywords
        arch_txt = read_text(proj / "architecture.md")
        # Require presence of these section headings (exact names from template)
        ensure_sections(proj / "architecture.md", ["Overview", "Components & interfaces", "Tradeoffs", "Security & privacy notes"], "architecture.md")

        # Conditional runbook/cost plan
        if is_deployable(proj):
            for f in ["runbook.md", "cost-plan.md"]:
                if not (proj / f).exists():
                    fail(f"Project '{proj.name}' appears deployable but is missing {f}.")
        
        # Optional status.json validation
        status_json = proj / "status.json"
        if status_json.exists():
            validate_status_json(status_json, proj.name)
    
    print("Artifact checks passed.")

if __name__ == "__main__":
    main()
```

### 3. Quality Bar Validator (tools/validators/check_quality_bar.py)

This enforces code quality standards. **Full source code**:

```python
#!/usr/bin/env python3
"""Quality bar validator:
- Enforce max lines-of-code per file (default: 800)
- Warn on large files in examples or tools
- Fail on large files in project implementation unless allow:large-file label

Design philosophy: prevent unmaintainable monoliths while allowing exceptions for generated code, examples, etc.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]

# Files matching these patterns are checked
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".swift", ".kt", ".cs",
    ".sh", ".bash", ".zsh"
}

# Exclude these paths from checks
EXCLUDE_PATTERNS = [
    ".git/",
    "node_modules/",
    "venv/",
    ".venv/",
    "__pycache__/",
    "dist/",
    "build/",
    ".github/",  # Exclude agent prompts and workflows
]

MAX_LINES = 800
WARN_THRESHOLD = 600

def should_check(path: Path) -> bool:
    """Determine if a file should be checked."""
    if path.suffix not in CODE_EXTENSIONS:
        return False
    
    path_str = str(path.relative_to(ROOT))
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return False
    
    return True

def count_lines(path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0

def check_file_size(path: Path) -> Tuple[bool, int]:
    """Check if file exceeds size limits. Returns (is_ok, line_count)."""
    lines = count_lines(path)
    return lines <= MAX_LINES, lines

def main() -> None:
    violations = []
    warnings = []
    
    # Walk through repository
    for root_dir, dirs, files in os.walk(ROOT):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if not any(ex.strip('/') == d for ex in EXCLUDE_PATTERNS)]
        
        for filename in files:
            filepath = Path(root_dir) / filename
            
            if not should_check(filepath):
                continue
            
            is_ok, lines = check_file_size(filepath)
            rel_path = filepath.relative_to(ROOT)
            
            if not is_ok:
                violations.append((rel_path, lines))
            elif lines > WARN_THRESHOLD:
                warnings.append((rel_path, lines))
    
    # Report warnings
    if warnings:
        print(f"::warning::Found {len(warnings)} files approaching size limit ({WARN_THRESHOLD}+ lines):")
        for path, lines in sorted(warnings, key=lambda x: x[1], reverse=True)[:5]:
            print(f"::warning::{path}: {lines} lines")
    
    # Report violations
    if violations:
        print(f"::error::Quality bar violation: {len(violations)} files exceed {MAX_LINES} lines")
        for path, lines in sorted(violations, key=lambda x: x[1], reverse=True):
            print(f"::error::{path}: {lines} lines (max: {MAX_LINES})")
        print("\nTo fix:")
        print("1. Refactor large files into smaller, focused modules")
        print("2. Or add 'allow:large-file' label to PR if necessary (e.g., generated code)")
        raise SystemExit(1)
    
    print(f"Quality bar checks passed. Checked files are under {MAX_LINES} lines.")

if __name__ == "__main__":
    main()
```

### 4. CI Workflow (.github/workflows/ci.yml)

This runs validators on every PR. **Full source code**:

```yaml
name: CI

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [ main ]

permissions:
  contents: read
  pull-requests: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run validators
        run: |
          python tools/validators/check_artifacts.py
          python tools/validators/check_quality_bar.py

      - name: Run tests
        run: |
          python -m unittest discover -s tests -p "test_*.py" -v
```

### 5. Project Template (specs/projects/_template/)

Every project needs these files:

**spec.md** - Project specification:
```markdown
# Spec: [Project Name]

## Goal
What is the project trying to achieve?

## Scope
What is included in this project?

## Non-goals
What is explicitly out of scope?

## Users & scenarios
Who will use this and how?

## Constraints
Technical, business, or other limitations

## Acceptance criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Risks & mitigations
What could go wrong and how do we handle it?

## Success metrics
How do we measure success?
```

**architecture.md** - System design:
```markdown
# Architecture: [Project Name]

## Overview
High-level description of the system design

## Components & interfaces
Describe each component and how they interact

### Component 1
- **Purpose**: What it does
- **Interface**: How to interact with it
- **Dependencies**: What it depends on

### Component 2
...

## Data flow
Describe how data moves through the system

## Tradeoffs
Document design decisions and alternatives considered

### Choice: [Design Decision]
- **Pro**: Benefits of this approach
- **Con**: Drawbacks
- **Rationale**: Why we chose this

## Security & privacy notes
Security considerations and privacy implications
```

**plan.md** - Implementation roadmap:
```markdown
# Plan: [Project Name]

## Milestones

### M1: [Milestone Name]
**Goal**: What this milestone delivers

**Tasks**:
- [ ] Task 1
- [ ] Task 2

**Success criteria**:
- [ ] Criterion 1

### M2: [Milestone Name]
...

## Dependencies
External dependencies or prerequisites

## Timeline
Estimated timeline or deadlines

## Resources
Required resources or team members
```

**tasks.md** - Detailed task list:
```markdown
# Tasks: [Project Name]

## Backlog
- [ ] Task description
- [ ] Another task

## In Progress
- [ ] Current task

## Done
- [x] Completed task
```

**test-plan.md** - Testing strategy:
```markdown
# Test Plan: [Project Name]

## Test strategy
Overall approach to testing

## Unit tests
Component-level tests

## Integration tests
System-level tests

## Acceptance tests
End-to-end validation

## Test environment
How to set up testing environment

## Coverage goals
Target coverage levels
```

**acceptance-tests.md** - Validation tests:
```markdown
# Acceptance Tests: [Project Name]

## Test scenarios

### Scenario 1: [Name]
**Given**: Initial conditions
**When**: Action performed
**Then**: Expected outcome

### Scenario 2: [Name]
...

## Manual validation
Steps for human validation

## Automated validation
Automated test commands
```

**runbook.md** - Operations guide (for deployable projects):
```markdown
# Runbook: [Project Name]

## Deployment
How to deploy the system

## Monitoring
What to monitor and how

## Common issues
Known issues and solutions

## Rollback
How to rollback if needed

## Emergency contacts
Who to contact for issues
```

**cost-plan.md** - Cost analysis (for deployable projects):
```markdown
# Cost Plan: [Project Name]

## Infrastructure costs
Estimated monthly costs for infrastructure

## Scaling costs
How costs scale with usage

## Cost optimization
Strategies to reduce costs

## Budget
Approved budget and limits
```

## Reconstruction Procedure

### From Scratch (No Backups)

**Time Required**: 4-8 hours for complete reconstruction

**Steps**:

1. **Create repository structure** (15 minutes)
   ```bash
   mkdir -p kerrigan/{.github/{agents,workflows,automation},docs,playbooks,specs/{kerrigan,projects/_template},tools/validators,tests/validators,examples}
   cd kerrigan
   git init
   ```

2. **Create constitution** (15 minutes)
   - Copy content from "Constitution" section above
   - Save to `specs/constitution.md`

3. **Create validators** (30 minutes)
   - Copy `check_artifacts.py` from source code above
   - Copy `check_quality_bar.py` from source code above
   - Save to `tools/validators/`
   - Make executable: `chmod +x tools/validators/*.py`

4. **Create CI workflow** (15 minutes)
   - Copy `ci.yml` from source code above
   - Save to `.github/workflows/ci.yml`

5. **Create project template** (30 minutes)
   - Copy all template files from above
   - Save to `specs/projects/_template/`

6. **Create agent prompts** (2 hours)
   - Create each agent prompt file in `.github/agents/`
   - Define role, responsibilities, inputs/outputs, success criteria
   - See [Agent Prompt Template](#agent-prompt-template) below

7. **Create documentation** (2 hours)
   - Setup guide (docs/setup.md)
   - Architecture (docs/architecture.md)
   - FAQ (docs/FAQ.md)
   - Playbooks (playbooks/*.md)

8. **Create README** (30 minutes)
   - Quickstart instructions
   - Architecture overview
   - Documentation links
   - Repository structure

9. **Validate** (30 minutes)
   ```bash
   python tools/validators/check_artifacts.py
   git add .
   git commit -m "Initial Kerrigan structure"
   ```

### From Partial Backup

**Time Required**: 1-2 hours

**Steps**:

1. **Restore available files**
2. **Identify missing components**
   ```bash
   python tools/validators/check_artifacts.py
   ```
3. **Recreate missing components** using this guide
4. **Validate**

### From Full Backup

**Time Required**: 15-30 minutes

**Steps**:

1. **Clone backup**
   ```bash
   git clone kerrigan-backup.git kerrigan
   cd kerrigan
   ```

2. **Validate**
   ```bash
   python tools/validators/check_artifacts.py
   python tools/validators/check_quality_bar.py
   ```

3. **Update remote**
   ```bash
   git remote set-url origin https://github.com/yourusername/kerrigan.git
   git push origin main
   ```

## Agent Prompt Template

Each agent prompt follows this structure:

```markdown
# Role: [Agent Name]

## Identity
You are a [role description] agent specialized in [domain].

## Responsibilities
- Responsibility 1
- Responsibility 2
- Responsibility 3

## Input Artifacts
What you read before starting work:
- constitution.md
- project spec.md
- other relevant artifacts

## Output Artifacts
What you produce:
- artifact 1 (path: specs/projects/<name>/artifact1.md)
- artifact 2 (path: specs/projects/<name>/artifact2.md)

## Success Criteria
How to know you've succeeded:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Handoff Protocol
What to do when done:
1. Create PR with your artifacts
2. Tag next role with label (e.g., role:architect)
3. Update status.json

## Quality Standards
Standards from constitution to uphold:
- Quality principle 1
- Quality principle 2

## Example Workflow
1. Read issue and gather context
2. Review input artifacts
3. Create output artifacts
4. Validate against success criteria
5. Submit PR for review
```

## Validation Checklist

After reconstruction, verify:

### Structure
- [ ] All directories present
- [ ] .gitignore configured
- [ ] LICENSE present
- [ ] README.md complete

### Core Artifacts
- [ ] specs/constitution.md exists and complete
- [ ] specs/projects/_template/ has all required files
- [ ] specs/kerrigan/ documented

### Tools
- [ ] tools/validators/check_artifacts.py exists and executable
- [ ] tools/validators/check_quality_bar.py exists and executable
- [ ] Validators run successfully

### CI/CD
- [ ] .github/workflows/ci.yml configured
- [ ] GitHub Actions enabled
- [ ] Test push triggers CI

### Agents
- [ ] All role prompts present in .github/agents/
- [ ] Agent prompts follow template structure
- [ ] Kerrigan meta-agent prompt exists

### Documentation
- [ ] docs/setup.md complete
- [ ] docs/architecture.md complete
- [ ] docs/FAQ.md exists
- [ ] playbooks/*.md present

### GitHub Configuration
- [ ] All labels created
- [ ] Repository settings configured
- [ ] Branch protection rules set (optional)

### Functional Test
- [ ] Can create test project
- [ ] Validators pass on test project
- [ ] CI runs on test PR
- [ ] Agent can complete test task

## Self-Assembly Test

To verify Kerrigan can self-assemble, run this test:

```bash
# 1. Create test branch
git checkout -b test-self-assembly

# 2. Create test project
mkdir -p specs/projects/self-assembly-test
cp specs/projects/_template/* specs/projects/self-assembly-test/

# 3. Validate
python tools/validators/check_artifacts.py
python tools/validators/check_quality_bar.py

# 4. Run tests
python -m unittest discover -s tests -p "test_*.py" -v

# 5. Clean up
git checkout main
git branch -D test-self-assembly
```

Expected result: All checks pass, indicating Kerrigan can validate itself.

## Maintenance

To keep self-assembly capability:

1. **Update this document** when adding new critical components
2. **Version control** all source code inline in this document
3. **Test reconstruction** periodically (quarterly recommended)
4. **Keep validators simple** - no external dependencies
5. **Document changes** in git commit messages

## Summary

Kerrigan's self-assembly capability relies on:
- **Minimal external dependencies** (Git, Python stdlib, GitHub)
- **Complete source code** for critical components embedded in documentation
- **Clear dependency hierarchy** with no circular dependencies
- **Comprehensive validation** to detect missing or broken components
- **Step-by-step procedures** for reconstruction from various states

This ensures Kerrigan can be fully reconstructed from this documentation alone, fulfilling the disaster recovery requirement.

---

**Last Updated**: 2026-01-15
**Tested**: Yes - validated reconstruction from clean environment
**Owner**: Kerrigan Core Team
