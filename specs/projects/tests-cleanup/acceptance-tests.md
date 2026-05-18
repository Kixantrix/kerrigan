# Acceptance tests: tests-cleanup

## AC1: T1 — `test_automation.py` green
- [ ] **Given** `main` after T1 merge **When** running `python -m pytest tests/test_automation.py` **Then** exit code is 0

## AC2: T2 — `test_agent_prompts.py` green
- [ ] **Given** `main` after T2 merge **When** running `python -m pytest tests/test_agent_prompts.py` **Then** exit code is 0

## AC3: T3 — agent compliance tests green
- [ ] **Given** `main` after T3 merge **When** running `python -m pytest tests/test_agent_spec_compliance_workflow.py tests/test_agent_cli.py tests/validators/test_agents_md.py` **Then** exit code is 0

## AC4: T4 — misc tests green
- [ ] **Given** `main` after T4 merge **When** running `python -m pytest tests/test_test_collateral.py tests/test_migrate_v1_to_v2_scripts.py tests/test_budget_telemetry_workflow.py tests/test_feedback.py tests/validators/test_block_validator.py` **Then** exit code is 0

## AC5: T5 — full suite green and required
- [ ] **Given** `main` after T5 merge **When** running `python -m pytest tests/` **Then** exit code is 0
- [ ] **Given** branch protection on `main` **When** querying `required_status_checks.contexts` **Then** it includes both `kerrigan check` and `tests`
