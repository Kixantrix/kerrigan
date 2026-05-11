# Kerrigan Validators

All validators are run through the unified entry point:

```bash
kerrigan check           # run all validators
kerrigan check --fast    # skip heavy / PR-context validators
kerrigan check --verbose # show per-validator output
```

No validator should be called directly in CI workflows.
The single CI entry point is `kerrigan check` (see `.github/workflows/verify.yml`).

---

## Registered validators

### Always-run

| Validator | Description |
|---|---|
| `agents_md.py` | Validates `AGENTS.md` exists and every `.github/agents/*.md` profile has valid YAML frontmatter (`name`, `description`). |
| `check_artifacts.py` | Validates that required artifact files exist and contain required sections for each project in `specs/projects/`. |
| `check_dependencies.py` | Validates task dependency syntax in `tasks.md` files and detects circular dependencies. |
| `check_agent_signature.py` | Validates agent signatures on PRs in GitHub Actions context; skips gracefully when `GITHUB_EVENT_PATH` is not set. |
| `block_validator.py` | Validates block files in `.specify/blocks/` have correct YAML structure. |
| `test_capability_matrix.py` | Validates the agent capability matrix is well-formed. |
| `show_status.py` | Displays `status.json` information for all projects (informational; always passes). |

### Skipped with `--fast`

These validators scan all source files or require PR context and are skipped when
`kerrigan check --fast` is used to stay within the 30 s CI budget.

| Validator | Description |
|---|---|
| `check_quality_bar.py` | Warns when source files exceed 400 LOC and fails when they exceed 800 LOC. Supports `allow:large-file` PR label override. |
| `check_placeholders.py` | Detects placeholder/unimplemented code patterns in source files. Supports `placeholder:approved` PR label override. |
| `check_test_collateral.py` | Ensures source file changes in PRs have corresponding test updates (reads `.github/test-mapping.yml`). |
| `check_pr_documentation.py` | Detects potentially fabricated or misleading documentation in PR bodies and checks documentation-to-code ratios. |
| `check_test_claims.py` | Validates that test count claims in PR bodies match actual test files added or modified. |

---

## Adding a new validator

1. Place the script in `tools/validators/<name>.py`.
2. Ensure it exits `0` on success and non-zero on failure.
3. Register it in `tools/cli/kerrigan/kerrigan_cli/commands/check.py`:
   - Add it to the **always-run** block if it is fast (< 2 s).
   - Add it inside the `if not fast:` block if it scans many files or requires network/PR context.
4. Document it in this file.
