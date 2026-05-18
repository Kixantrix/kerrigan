# Spec: tests-cleanup

## Goal

Restore the `tests/` suite to green so the `tests` job in the `verify` workflow can become a required status check. Currently 70 test failures span 10 files, all from v1→v2 migration debt — assertions about workflows, labels, agent formats, and tools that no longer exist.

## Scope

1. **Audit each failing test**: determine whether it asserts something v2 still cares about (fix the test) or something that's been removed (delete the test).
2. **Update fixture data** where tests reference v1 artifact strings as test inputs (e.g., `tools/agent_audit.py` as a path string is legitimate even though the file is gone — leave those).
3. **Drop tests** for removed workflows: `auto-triage`, `auto-generate-issues`, `auto-ready-pr`, and the old role-label automation.
4. **Keep the test count high**: dropping tests is fine when they validate dead code; rewriting them is preferred when the system v2 still has the underlying behavior.
5. After all waves merge, **make the `tests` job a required status check** in branch protection.

## Acceptance criteria

- [ ] `python -m pytest tests/` passes with 0 failures on `main`
- [ ] No test is renamed/moved without justification in commit body
- [ ] Removed test files have their entries removed from `.github/test-mapping.yml`
- [ ] `tests` is added to `required_status_checks` in branch protection (see `docs/operations/auto-merge-setup.md`)
- [ ] Constitution check (`tests/__init__.py` no orphan imports, no skipped suites)

## Non-goals

- Adding new tests beyond what's needed to keep coverage of v2 features
- Refactoring the validator code under `tools/validators/`
- Changing CI infrastructure beyond making `tests` required at the end
