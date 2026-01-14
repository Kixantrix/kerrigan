# Test Issue: Agent Workflow Validation

This document serves as a template for creating a GitHub issue to test the complete agent workflow for Milestone 2.

## Issue Title
Add color output to artifact validator

## Issue Body

### Goal
Enhance the artifact validator (`tools/validators/check_artifacts.py`) with color-coded output to improve readability and make errors more visible.

### Background
The current validator outputs plain text, which can be hard to scan quickly. Adding colors (green for success, yellow for warnings, red for errors) would improve the developer experience while maintaining full CI compatibility.

### Scope
- Add ANSI color support using Python standard library only
- Auto-detect TTY vs CI environments
- Add `--no-color` flag for explicit control
- Preserve GitHub Actions annotations (`::error::`, `::warning::`)

### Success Criteria
- Colors appear in terminal when running locally
- Colors are disabled automatically in CI
- All existing validation tests continue to pass
- No external dependencies added

### Project Artifacts
All specifications have been created in `specs/projects/validator-enhancement/`:
- ✅ spec.md
- ✅ acceptance-tests.md
- ✅ architecture.md
- ✅ plan.md
- ✅ tasks.md
- ✅ test-plan.md
- ✅ runbook.md
- ✅ cost-plan.md

### Implementation Plan
See `specs/projects/validator-enhancement/plan.md` for detailed milestones.

### Agent Assignment
This issue should be labeled with:
- `agent:go` - Grant agent permission to work
- `role:swe` - Assign to Software Engineering agent

### Acceptance Tests
See `specs/projects/validator-enhancement/acceptance-tests.md` for complete test scenarios.

### Dependencies
None - can start immediately

### Links
- Project folder: `specs/projects/validator-enhancement/`
- Architecture: `specs/projects/validator-enhancement/architecture.md`
- Tasks: `specs/projects/validator-enhancement/tasks.md`

---

## How to Create This Issue in GitHub

1. Navigate to your repository on GitHub
2. Click "Issues" tab
3. Click "New issue"
4. Copy the content above (from "Goal" to "Links")
5. Add labels:
   - `agent:go`
   - `role:swe`
6. Create the issue
7. Copy agent prompt from `.github/agents/role.swe.md`
8. Provide the agent with:
   - Link to the issue
   - Link to project folder: `specs/projects/validator-enhancement/`
   - Instructions to implement Milestone 1

## Expected Outcome

After the agent completes the work:
- New file: `tools/validators/colors.py` with color utilities
- Modified file: `tools/validators/check_artifacts.py` with color support
- New tests: `tests/validators/test_colors.py`
- All tests pass
- CI remains green
- PR opened and linked to this issue

## Validation Checklist

After agent completes work, verify:
- [ ] Colors appear when running validator locally
- [ ] Colors disabled in CI (check Actions logs)
- [ ] `--no-color` flag works
- [ ] GitHub Actions annotations still detected
- [ ] All tests pass
- [ ] No external dependencies added
- [ ] Code follows existing style
- [ ] Documentation updated

## Success Metrics for Milestone 2

This test issue validates:
- ✅ **Spec agent**: Produced valid spec.md and acceptance-tests.md
- ✅ **Architect agent**: Produced valid architecture.md and plan.md
- ⏳ **SWE agent**: Will implement feature with tests (pending)
- ⏳ **Kerrigan meta-agent**: Will validate constitution compliance (pending)
- ⏳ **CI validation**: Will remain green throughout (pending)

## Notes

This is a **test issue** for Milestone 2 validation. The goal is not just to implement the feature, but to **prove the agent workflow works end-to-end**.

Document any workflow gaps or friction points in `playbooks/handoffs.md`.
