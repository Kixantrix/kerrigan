# Validator registry

Run the validator suite through the CLI entry point:

```bash
kerrigan check
```

Registered validators in `kerrigan check`:

- `show_status.py`
- `agents_md.py`
- `block_validator.py`
- `check_agent_signature.py`
- `check_artifacts.py`
- `check_dependencies.py`
- `check_placeholders.py`
- `check_pr_documentation.py` *(advisory)*
- `check_quality_bar.py`
- `check_test_claims.py`
- `check_test_collateral.py` *(advisory)*
- `test_capability_matrix.py`

`kerrigan check` also runs `specify check` when `specify` is available on `PATH`.
