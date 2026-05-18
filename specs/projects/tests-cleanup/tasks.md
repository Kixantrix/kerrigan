# Tasks: tests-cleanup

## Task 1: Fix or remove `test_automation.py`
**Wave**: A · **Status**: Not started · **Files (touch)**: `tests/test_automation.py`, `.github/test-mapping.yml`

Audit 33 failures in `tests/test_automation.py`. Most assert on v1 auto-triage workflows (`.github/workflows/auto-triage-on-assign.yml`, `auto-generate-issues.yml`) and v1 role labels (`role:dev`, `role:reviewer`, etc.) that no longer exist in v2.

**Approach**:
- For each failing test, check whether the asserted file/label/workflow still exists.
- If the artifact is gone and no v2 equivalent exists → delete the test.
- If a v2 equivalent exists (e.g., `verify.yml` replacing `auto-triage`) → update the test to assert v2 reality.
- If the test depends on a tool that no longer exists (e.g., references `tools/auto_triage.py`) → delete.

**Acceptance Criteria**:
- [ ] `python -m pytest tests/test_automation.py -v` exits 0
- [ ] Any deleted tests have their rationale documented in commit message
- [ ] `.github/test-mapping.yml` updated if entire test files removed

---

## Task 2: Fix or remove `test_agent_prompts.py`
**Wave**: A · **Status**: Not started · **Files (touch)**: `tests/test_agent_prompts.py`

15 failures. Likely asserts on the v1 prompts/ directory structure that was reorganized.

**Acceptance Criteria**:
- [ ] `python -m pytest tests/test_agent_prompts.py -v` exits 0
- [ ] Tests now assert against current `prompts/` and `.github/agents/` reality

---

## Task 3: Fix or remove `test_agent_*` compliance tests
**Wave**: B · **Status**: Not started · **Files (touch)**: `tests/test_agent_spec_compliance_workflow.py`, `tests/test_agent_cli.py`, `tests/validators/test_agents_md.py`

12 failures. Includes references to the deleted `tools/agent_audit.py` (already removed from test_agent_audit.py — those imports are in test fixture strings, which is legitimate; do not remove those lines).

**Acceptance Criteria**:
- [ ] `python -m pytest tests/test_agent_spec_compliance_workflow.py tests/test_agent_cli.py tests/validators/test_agents_md.py -v` exits 0

---

## Task 4: Fix or remove remaining misc tests
**Wave**: C · **Status**: Not started · **Files (touch)**: `tests/test_test_collateral.py`, `tests/test_migrate_v1_to_v2_scripts.py`, `tests/test_budget_telemetry_workflow.py`, `tests/test_feedback.py`, `tests/validators/test_block_validator.py`

10 failures across 5 files.

**Acceptance Criteria**:
- [ ] `python -m pytest tests/test_test_collateral.py tests/test_migrate_v1_to_v2_scripts.py tests/test_budget_telemetry_workflow.py tests/test_feedback.py tests/validators/test_block_validator.py -v` exits 0

---

## Task 5: Add `tests` to required status checks
**Wave**: D (depends on T1+T2+T3+T4 merged) · **Status**: Not started · **Files (touch)**: `docs/operations/auto-merge-setup.md`

Update branch protection on `main` to require `tests` in addition to `kerrigan check`. Update the JSON in `docs/operations/auto-merge-setup.md` accordingly.

**Acceptance Criteria**:
- [ ] `gh api repos/Kixantrix/kerrigan/branches/main/protection --jq .required_status_checks.contexts` includes both `kerrigan check` and `tests`
- [ ] `docs/operations/auto-merge-setup.md` updated to reflect new required check list

---

## Dependencies

- T5 depends on T1, T2, T3, T4
- T1-T4 are mutually parallel-safe (no file overlap)

## Notes

- This project is `.tinyspec` (no architecture.md / test-plan.md required)
- The 5 commit-mapping references in `tests/test_test_collateral.py` to `tools/agent_audit.py` as a fixture string are intentional — they exercise the `matches_pattern` function with a known historical path. Do not "fix" those by deleting.
