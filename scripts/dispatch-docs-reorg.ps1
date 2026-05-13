# Dispatch docs-reorganization tasks to GitHub issues
# Run from repo root: pwsh scripts/dispatch-docs-reorg.ps1

$ErrorActionPreference = "Stop"

Write-Host "Creating GitHub issues for docs-reorganization project..." -ForegroundColor Cyan

# Wave 1: Parallel-safe foundation tasks

Write-Host ""
Write-Host "Wave 1: Parallel" -ForegroundColor Yellow

gh issue create `
  --title "docs-reorg-T1: Create docs subdirectories" `
  --label "agent:go" `
  --body @"
**Project**: docs-reorganization
**Wave**: 1 (parallel-safe)
**Priority**: High

## Objective
Create new documentation directory structure.

## Instructions
``````bash
mkdir -p docs/onboarding docs/architecture docs/operations docs/_archive
git add docs/
git commit -m "feat: create docs subdirectory structure"
``````

## Acceptance Criteria
- [ ] All 4 subdirectories exist
- [ ] Committed to branch

## Context
- [spec.md](../blob/main/specs/projects/docs-reorganization/spec.md)
- [tasks.md](../blob/main/specs/projects/docs-reorganization/tasks.md)
"@

gh issue create `
  --title "docs-reorg-T2: Update AGENTS.md v1 references" `
  --label "agent:go" `
  --body @"
**Project**: docs-reorganization  
**Wave**: 1 (parallel-safe)
**Priority**: High

## Objective
Remove "phasing out" language from AGENTS.md. State v2 as current.

## Instructions
Find lines ~90, ~136 with "v1 labels are being phased out in Phase 4".

Replace with: "v1 is archived in specs/kerrigan/_archive-v1/; v2 is current"

## Acceptance Criteria
- [ ] No "phasing out" or "transition" language
- [ ] Clear statement that v2 is current
- [ ] Reference to v1 archive location
- [ ] Commit message: docs: update AGENTS.md to reflect v2 as current

## Context
- [spec.md](../blob/main/specs/projects/docs-reorganization/spec.md)
"@

gh issue create `
  --title "docs-reorg-T3: Create specs/projects status legend" `
  --label "agent:go" `
  --body @"
**Project**: docs-reorganization
**Wave**: 1 (parallel-safe)
**Priority**: High

## Objective  
Create specs/projects/README.md with status legend for all 11+ projects.

## Instructions
Create README.md categorizing each project as Active/Reference/Archived.

Projects to categorize: _archive/, _template/, agent-frontmatter-upgrade/, copilot-sdk-integration/, design-system-playground/, docs-reorganization/, hello-api/, hello-cli/, hello-swarm/, kerrigan/, pause-resume-demo/, task-dashboard-example/, task-tracker-real/, validator-enhancement/

## Acceptance Criteria
- [ ] All projects categorized  
- [ ] Brief justification for each status
- [ ] Links to implementations (if in examples/)
- [ ] Commit message: docs: add specs/projects status legend

## Context
- [spec.md](../blob/main/specs/projects/docs-reorganization/spec.md)
- [tasks.md](../blob/main/specs/projects/docs-reorganization/tasks.md#task-3)
"@

gh issue create `
  --title "docs-reorg-T4: Clarify prompts vs agents distinction" `
  --label "agent:go" `
  --body @"
**Project**: docs-reorganization
**Wave**: 1 (parallel-safe)
**Priority**: Medium

## Objective
Add cross-references explaining prompts/ vs .github/agents/ distinction.

## Instructions  
Update prompts/README.md: Add section explaining prompts are reusable text templates.
Update .github/agents/README.md: Add section explaining agents are runtime configs.
Cross-reference between the two.

## Acceptance Criteria
- [ ] prompts/README.md clarifies difference from agent profiles
- [ ] .github/agents/README.md clarifies difference from prompt templates  
- [ ] Cross-references between both files
- [ ] Commit message: docs: clarify prompts vs agent profiles distinction

## Context
- [spec.md](../blob/main/specs/projects/docs-reorganization/spec.md)
"@

Write-Host "Wave 1: 4 issues created" -ForegroundColor Green

# Wave 2: File moves (must wait for Wave 1 dirs to exist)

Write-Host ""
Write-Host "Wave 2: Sequential - wait for Wave 1 merge" -ForegroundColor Yellow

gh issue create `
  --title "docs-reorg-T5: Move docs to subdirectories" `
  --label "agent:wait" `
  --body @"
**Project**: docs-reorganization
**Wave**: 2 (sequential - depends on T1)
**Priority**: High

## Objective
Move 19 docs files to new subdirectories using git mv.

## Instructions
Use git mv to preserve history:

Onboarding:
``````bash
git mv docs/setup.md docs/onboarding/
git mv docs/fresh-user-test.md docs/onboarding/
git mv docs/FAQ.md docs/onboarding/
``````

Architecture:
``````bash  
git mv docs/architecture.md docs/architecture/
git mv docs/project-directory.md docs/architecture/
``````

Operations: (13 files - see tasks.md)

Archive: (4 files - see tasks.md)

## Acceptance Criteria
- [ ] All 19 files moved with git mv
- [ ] Git history preserved
- [ ] Only self-assembly.md remains in docs/ root
- [ ] Commit message: refactor: move docs to subdirectories

## Dependencies
- **Blocks on**: T1 (directories must exist)
- **Change label to agent:go** when T1 is merged

## Context
- [tasks.md](../blob/main/specs/projects/docs-reorganization/tasks.md#task-5) (full file list)
"@

gh issue create `
  --title "docs-reorg-T6: Move playbook setup guides to docs/operations" `
  --label "agent:wait" `
  --body @"
**Project**: docs-reorganization
**Wave**: 2 (sequential - depends on T1)
**Priority**: Medium

## Objective
Move autonomy-modes.md and copilot-review-setup.md from playbooks/ to docs/operations/.

## Instructions
``````bash
git mv playbooks/autonomy-modes.md docs/operations/
git mv playbooks/copilot-review-setup.md docs/operations/
git commit -m "refactor: move playbook setup guides to docs/operations"
``````

## Acceptance Criteria  
- [ ] Both files moved with git mv
- [ ] Git history preserved

## Dependencies
- **Blocks on**: T1 (directories must exist)
- **Change label to agent:go** when T1 is merged

## Context
- [spec.md](../blob/main/specs/projects/docs-reorganization/spec.md)
"@

Write-Host "Wave 2: 2 issues created with agent:wait label" -ForegroundColor Green

# Wave 3: Link fixes and validation (must wait for Wave 2 moves)

Write-Host ""
Write-Host "Wave 3: Sequential - wait for Wave 2 merge" -ForegroundColor Yellow

gh issue create `
  --title "docs-reorg-T7: Fix broken links after reorganization" `
  --label "agent:wait" `
  --body @"
**Project**: docs-reorganization
**Wave**: 3 (sequential - depends on T5, T6)
**Priority**: High

## Objective
Update all internal links to reflect new file paths.

## Instructions
Search and replace common patterns:
- docs/setup.md → docs/onboarding/setup.md
- docs/architecture.md → docs/architecture/architecture.md
- docs/ci-workflows.md → docs/operations/ci-workflows.md
- playbooks/autonomy-modes.md → docs/operations/autonomy-modes.md

Search in: all .md files in repo root, docs/, playbooks/, examples/, specs/, .github/

## Acceptance Criteria
- [ ] All links updated
- [ ] python tools/validators/check_hygiene.py passes
- [ ] Commit message: fix: update links after docs reorganization

## Dependencies
- **Blocks on**: T5, T6 (files must be moved first)
- **Change label to agent:go** when T5 and T6 are merged

## Context
- [tasks.md](../blob/main/specs/projects/docs-reorganization/tasks.md#task-7)
"@

gh issue create `
  --title "docs-reorg-T8: Verify and commit final state" `
  --label "agent:wait" `
  --body @"
**Project**: docs-reorganization
**Wave**: 3 (sequential - depends on T7)
**Priority**: High

## Objective
Run final validation and commit all changes.

## Instructions
``````bash
# Run hygiene validator
python tools/validators/check_hygiene.py

# If clean, stage and commit
git add -A
git commit -m "refactor: reorganize documentation structure

- Create docs subdirs: onboarding, architecture, operations, _archive
- Move 19 docs to appropriate subdirs  
- Move playbook setup guides to docs/operations
- Update AGENTS.md v1 references
- Add specs/projects status legend
- Clarify prompts vs agents distinction
- Fix all internal links"
``````

## Acceptance Criteria
- [ ] Hygiene validator passes (0 errors, 0 warnings)
- [ ] All changes committed
- [ ] Commit message follows conventional commits

## Dependencies
- **Blocks on**: T7 (links must be fixed first)
- **Change label to agent:go** when T7 is merged

## Context
- [spec.md](../blob/main/specs/projects/docs-reorganization/spec.md)
"@

Write-Host "Wave 3: 2 issues created with agent:wait label" -ForegroundColor Green

Write-Host ""
Write-Host "All 8 tasks dispatched to GitHub" -ForegroundColor Cyan
Write-Host "Wave 1 - 4 tasks ready for cloud agents with agent:go label" -ForegroundColor Cyan  
Write-Host "Waves 2-3 will auto-activate as earlier waves merge" -ForegroundColor Cyan
