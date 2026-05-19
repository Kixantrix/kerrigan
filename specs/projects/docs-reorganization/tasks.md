# Tasks: Documentation Reorganization

## Wave 1: Foundation (Parallel-safe)

### Task 1: Create docs subdirectories
**Status**: Not started  
**Priority**: High  
**Dependencies**: None  

Create the new directory structure:
```bash
mkdir -p docs/onboarding docs/architecture docs/operations docs/_archive
```

**Acceptance Criteria**:
- [ ] `docs/onboarding/` exists
- [ ] `docs/architecture/` exists
- [ ] `docs/operations/` exists
- [ ] `docs/_archive/` exists

**Files modified**: None (new directories only)

---

### Task 2: Update AGENTS.md v1 references
**Status**: Not started  
**Priority**: High  
**Dependencies**: None  

Remove "phasing out" language from AGENTS.md. State clearly that v2 is current and v1 is archived.

**Target lines**: 90, 136 (mentions of "v1 labels are being phased out in Phase 4")

**Changes**:
- Replace "v1 labels are being phased out in Phase 4" → "v1 is archived in `specs/kerrigan/_archive-v1/`; v2 is current"
- Remove transition language; state v2 as the active system

**Acceptance Criteria**:
- [ ] No mentions of "phasing out" or "transition" related to v1
- [ ] Clear statement that v2 is current
- [ ] Reference to v1 archive location

**Files modified**: `AGENTS.md`

---

### Task 3: Create specs/projects status legend
**Status**: Not started  
**Priority**: High  
**Dependencies**: None  

Create `specs/projects/README.md` with a status legend for all 11 projects.

**Content structure**:
```markdown
# Kerrigan Projects

Status legend for all projects in this directory.

## Active Projects
Projects currently maintained and referenced in documentation.

| Project | Purpose | Status | Last Updated |
|---------|---------|--------|--------------|
| kerrigan | Meta-project for Kerrigan itself | Active | 2026-05-12 |
| task-tracker-real | Real workflow example with pause/resume | Reference | 2026-01-21 |
| hello-api | API scaffold example | Reference | 2026-01-15 |
| ... |

## Reference Projects
Complete examples maintained for educational purposes.

## Archived Projects
Specs without active implementation. Kept for historical context.

| Project | Reason | Archived Date |
|---------|--------|---------------|
| design-system-playground | Spec complete, code abandoned | 2026-05-12 |
| agent-frontmatter-upgrade | Completed in v2 rollout | 2026-05-12 |
| ... |
```

**Research needed**: Review each of 11 projects to determine status:
- `_archive/`, `_template/`, `agent-frontmatter-upgrade/`, `copilot-sdk-integration/`, `design-system-playground/`, `hello-api/`, `hello-cli/`, `hello-swarm/`, `kerrigan/`, `pause-resume-demo/`, `task-dashboard-example/`, `task-tracker-real/`, `validator-enhancement/`

**Acceptance Criteria**:
- [ ] All 11+ projects categorized as Active/Reference/Archived
- [ ] Brief justification for each status
- [ ] Links to implementations (if in `examples/`)

**Files modified**: `specs/projects/README.md` (new)

---

### Task 4: ~~Clarify prompts vs agents distinction~~ (obsolete)
**Status**: Cancelled — `prompts/` and `services/sdk-agent/` were retired (see PR retiring sdk-agent). `.github/agents/README.md` now explains agent profiles vs. briefing packets instead, which is the v2 mechanism.

---

## Wave 2: File Moves (Sequential)

### Task 5: Move docs to subdirectories
**Status**: Complete  
**Priority**: High  
**Dependencies**: Task 1 (directories must exist)  

Move files using `git mv` to preserve history:

**Onboarding**:
```bash
git mv docs/setup.md docs/onboarding/
git mv docs/fresh-user-test.md docs/onboarding/
git mv docs/FAQ.md docs/onboarding/
```

**Architecture**:
```bash
git mv docs/architecture.md docs/architecture/
git mv docs/project-directory.md docs/architecture/
```

**Operations**:
```bash
git mv docs/ci-workflows.md docs/operations/
git mv docs/auto-merge-setup.md docs/operations/
git mv docs/github-labels.md docs/operations/
git mv docs/github-security-setup.md docs/operations/
git mv docs/git-best-practices.md docs/operations/
git mv docs/powershell-style-guide.md docs/operations/
git mv docs/cli-reference.md docs/operations/
git mv docs/pr-documentation-guidelines.md docs/operations/
git mv docs/skills-implementation-summary.md docs/operations/
```

**Archive**:
```bash
git mv docs/milestone-6-retrospective.md docs/_archive/
git mv docs/self-improvement-system.md docs/_archive/
git mv docs/external-research-workflow.md docs/_archive/
git mv docs/skills-sh-investigation.md docs/_archive/
git mv docs/playground-infrastructure.md docs/_archive/
```

**Keep in root**: `docs/self-assembly.md` (validator reference)

**Acceptance Criteria**:
- [x] All listed files moved to appropriate subdirectories
- [x] Git history preserved (use `git mv`)
- [x] No files left in `docs/` root except `self-assembly.md`

**Files modified**: 19 files moved

---

### Task 6: Move playbook setup guides to docs/operations
**Status**: Not started  
**Priority**: Medium  
**Dependencies**: Task 1 (directories must exist)  

Move setup/configuration guides from `playbooks/` to `docs/operations/`:

```bash
git mv playbooks/autonomy-modes.md docs/operations/
git mv playbooks/copilot-review-setup.md docs/operations/
```

Playbooks should contain operational workflows (kickoff, pr-review, triage), not infrastructure setup.

**Acceptance Criteria**:
- [ ] `autonomy-modes.md` moved to `docs/operations/`
- [ ] `copilot-review-setup.md` moved to `docs/operations/`
- [ ] Git history preserved

**Files modified**: 2 files moved

---

## Wave 3: Cleanup (Depends on moves)

### Task 7: Fix broken links after reorganization
**Status**: Not started  
**Priority**: High  
**Dependencies**: Tasks 5, 6 (files must be moved first)  

Update all internal links to reflect new paths. Common patterns:

- `docs/setup.md` → `docs/onboarding/setup.md`
- `docs/architecture.md` → `docs/architecture/architecture.md`
- `docs/ci-workflows.md` → `docs/operations/ci-workflows.md`
- `playbooks/autonomy-modes.md` → `docs/operations/autonomy-modes.md`

**Search for references in**:
- All markdown files in repo root (README.md, AGENTS.md, CLAUDE.md)
- All files in `docs/`, `playbooks/`, `examples/`, `specs/`, `.github/`
- Agent profiles in `.github/agents/`

**Acceptance Criteria**:
- [ ] All links updated to new paths
- [ ] No broken internal links
- [ ] Hygiene validator passes

**Files modified**: TBD (search results will determine)

---

### Task 8: Verify and commit
**Status**: Not started  
**Priority**: High  
**Dependencies**: Tasks 1-7 (all changes complete)  

Run final validation and commit:

```bash
# Run hygiene validator
python tools/validators/check_hygiene.py

# Commit if clean
git add -A
git commit -m "refactor: reorganize documentation structure

- Create docs subdirs: onboarding, architecture, operations, _archive
- Move 19 docs to appropriate subdirs
- Move playbook setup guides to docs/operations
- Update AGENTS.md v1 references
- Add specs/projects status legend
- Clarify prompts vs agents distinction
- Fix all internal links"
```

**Acceptance Criteria**:
- [ ] Hygiene validator passes (0 errors, 0 warnings)
- [ ] All changes committed
- [ ] Commit message follows conventional commits format

**Files modified**: N/A (validation only)

---

## Summary

- **Wave 1**: 4 tasks (parallel)
- **Wave 2**: 2 tasks (sequential, depends on Wave 1)
- **Wave 3**: 2 tasks (sequential, depends on Wave 2)
- **Total estimated effort**: 2-3 hours for cloud agents
- **Files affected**: ~40+ files (19 moves + link updates)
