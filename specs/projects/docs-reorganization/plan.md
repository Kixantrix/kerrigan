# Plan: Documentation Reorganization

## Objective

Reorganize Kerrigan's documentation from a flat 20-file structure to a hierarchical system that improves navigability and clarifies ownership.

## Phases

### Phase 1: Foundation Setup (Wave 1 - Parallel)
Create directory structure and update core references. These tasks have no file conflicts.

- **Create docs subdirectories** — new dirs only, no conflicts
- **Update AGENTS.md v1 references** — single file edit
- **Create specs/projects status legend** — new file
- **Clarify prompts vs agents distinction** — two README edits, no overlap

**Duration**: 30-45 minutes  
**Risk**: Low (no file moves yet)

### Phase 2: File Reorganization (Wave 2 - Sequential)
Move files to new locations. Must complete after Phase 1.

- **Move docs to subdirectories** — 19 files moved  
- **Move playbook setup guides** — 2 files moved

**Duration**: 15-20 minutes  
**Risk**: Medium (breaking links until Wave 3 completes)

### Phase 3: Link Repair & Validation (Wave 3 - Sequential)
Fix all broken links and validate. Must complete after Phase 2.

- **Fix broken links after reorganization** — update all references
- **Verify and commit** — final validation

**Duration**: 30-45 minutes  
**Risk**: Low (hygiene validator catches errors)

## Success Metrics

- [ ] `docs/` has 4 subdirectories with files organized by purpose
- [ ] AGENTS.md states v2 as current (no "phasing out" language)
- [ ] All 11+ projects in `specs/projects/` have documented status
- [ ] `prompts/` vs `.github/agents/` distinction is clear
- [ ] Hygiene validator passes with 0 errors
- [ ] All changes committed in single atomic commit

## Dependencies

- **Wave 1** → **Wave 2**: Directories must exist before moving files
- **Wave 2** → **Wave 3**: Files must be moved before fixing links
- **Within waves**: Tasks are parallel-safe (no file conflicts)

## Rollback Plan

If validation fails:
1. `git reset --hard HEAD` to undo uncommitted changes
2. Review hygiene validator errors
3. Fix issues and retry Wave 3

## Out of Scope

- Content rewrites (only moves and clarifications)
- File deletions (archive instead)
- Changing `.specify/` or spec-kit artifacts
- Updating CI workflows (links auto-resolve)
