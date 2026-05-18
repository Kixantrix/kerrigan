# Plan: tests-cleanup

## Approach

Group failures by topic, dispatch each as a parallel-safe wave (no file overlap between waves).

## Failure inventory (as of dispatch)

70 failures across 10 files:

| File | Failures | Wave |
|---|---:|---|
| `tests/test_automation.py` | 33 | A |
| `tests/test_agent_prompts.py` | 15 | A |
| `tests/test_agent_spec_compliance_workflow.py` | 9 | B |
| `tests/test_agent_cli.py` | 2 | B |
| `tests/validators/test_agents_md.py` | 1 | B |
| `tests/test_test_collateral.py` | 5 | C |
| `tests/test_migrate_v1_to_v2_scripts.py` | 2 | C |
| `tests/test_budget_telemetry_workflow.py` | 1 | C |
| `tests/test_feedback.py` | 1 | C |
| `tests/validators/test_block_validator.py` | 1 | C |

## Waves

- **Wave A — automation & prompts debt** (`T1`, `T2`)
- **Wave B — agent compliance debt** (`T3`)
- **Wave C — misc & validators** (`T4`)
- **Wave D — enforce** (`T5`): add `tests` to required checks

File touch boundaries are non-overlapping across A/B/C → safe to parallel-dispatch.

D depends on A+B+C merged.
