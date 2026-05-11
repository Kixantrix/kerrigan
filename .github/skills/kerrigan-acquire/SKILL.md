# Skill: kerrigan-acquire

**When:** Starting a new project or feature, or after a major architectural decision.
**Trigger:** Automatic when the agent recognizes a new project context. Also available as `/kerrigan.acquire`.
**Output:** `.specify/skills.yaml` — locked skill set for the project.
**Why:** Agents need domain knowledge before planning, and stack knowledge before implementing.

## Two-phase acquisition

### Phase 1: Pre-planning
Runs before planning starts. The agent scans the repo to understand the domain and proposes relevant skills.

**Scan targets:**
- File extensions and language distribution
- Package manifests (`package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, etc.)
- Framework markers (e.g., `next.config.js`, `django`, `FastAPI`, `Express`)
- Existing `.specify/skills.yaml` (if updating)
- Existing skills in `.github/skills/` and `skills/`

**Propose:** A list of skills with sources and trust levels. Present to the human for approval using the structured question UI.

### Phase 2: Post-architecture
Runs after the human makes a major architectural decision (e.g., "use WinML + Foundry", "deploy on Fly.io").

**Trigger:** The agent recognizes an architectural constraint and checks if new stack-specific skills are needed.

**Propose:** Additional skills mapped to the decided architecture. Append to `.specify/skills.yaml` after approval.

## Trust tiers

| Tier | Source | Approval |
|------|--------|----------|
| `trusted` | Repo skills (`.github/skills/`, `skills/`) or user config (`~/.claude/skills/`) | Auto-proposed, low friction |
| `registry` | Trusted registries (e.g., `agentskills` org) | Auto-proposed, trusted by default |
| `external` | Unknown GitHub repos, URLs | Proposed with source URL, requires explicit human approval |

## Skill proposal format

Present skills using the structured question UI, one batch:

```
For this project I'd recommend:
- python-patterns (your config) — Python idioms, PEP 8
- tdd-workflow (your config) — test-driven development
- docker-patterns (your config) — containerization
- fastapi-patterns (agentskills registry) — FastAPI conventions
- winml-guide (external: github.com/example/winml-skills) — UNVETTED
```

Human selects which to approve. Selected skills are written to `.specify/skills.yaml`.

## Downstream consumption

- **Briefing packets** include the `skills` list from `.specify/skills.yaml` in the "Relevant skills (preload)" section.
- **Cloud agents** load skills listed in their briefing before starting work.
- **Planning** uses locked skills to make informed architectural suggestions.

## Config format

Written to `.specify/skills.yaml`, validated against `.specify/schemas/skills.schema.json`.

```yaml
project: my-project
acquired_at: 2026-05-10T12:00:00Z
skills:
  - id: python-patterns
    source: user
    path: ~/.claude/skills/python-patterns/SKILL.md
    trust: trusted
    phase: both
  - id: fastapi-patterns
    source: registry
    path: agentskills/fastapi-patterns
    trust: trusted
    phase: implementation
  - id: winml-guide
    source: external
    path: https://github.com/example/winml-skills
    trust: approved
    phase: implementation
    approved_by: human
    notes: Needed for local NPU inference via WinML
```

## No ceremony mode

The agent does NOT require a slash command to trigger skill discovery. When the agent recognizes a new project context (new repo, new feature directory, conversation about a new goal), it should:

1. Silently scan the repo
2. Propose skills naturally in conversation
3. Record approvals in `.specify/skills.yaml`

The `/kerrigan.acquire` command exists as an explicit re-trigger for updating skills after architecture changes.
