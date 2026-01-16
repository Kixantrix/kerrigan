# CI Workflows

This document describes the continuous integration (CI) workflows that run automatically on pull requests and pushes to the main branch.

## Overview

Kerrigan uses GitHub Actions to automatically validate code quality, run tests, and check for potential issues. The main CI workflow is defined in `.github/workflows/ci.yml`.

## CI Validation Steps

The CI workflow runs the following checks:

### 1. Project Status Check
- **Tool**: `tools/validators/show_status.py`
- **Purpose**: Displays current project status and active tasks
- **When**: Always runs

### 2. Artifact Validation
- **Tool**: `tools/validators/check_artifacts.py`
- **Purpose**: Ensures required artifacts exist according to specs
- **When**: Always runs
- **Blocking**: Yes - PR will fail if artifacts are missing

### 3. Quality Bar Validation
- **Tool**: `tools/validators/check_quality_bar.py`
- **Purpose**: Enforces quality standards (e.g., max 800 LOC per file)
- **When**: Always runs
- **Blocking**: Yes - PR will fail if quality bar is not met
- **Override**: Can be bypassed with `allow:large-file` label

### 4. PR Documentation Validation (New!)
- **Tool**: `tools/validators/check_pr_documentation.py`
- **Purpose**: Detects potential fabricated or misleading documentation in PR descriptions
- **When**: Only on pull requests (not on push to main)
- **Blocking**: No - runs in warning-only mode
- **Configuration**: See [Configuration](#configuration) below

The validator checks for:
- Sequential PR references that might be simulated (#1, #2, #3, etc.)
- Phrases indicating simulated workflows
- Suspicious timeline claims that don't match git history
- Fabrication markers (agent signatures, elaborate phase descriptions)
- Disproportionate documentation-to-code ratios
- Fictional human review timing claims

See [PR Documentation Guidelines](pr-documentation-guidelines.md) for details on what the validator checks.

### 5. Unit Tests
- **Tool**: Python unittest framework
- **Purpose**: Runs all tests in the `tests/` directory
- **When**: Always runs
- **Blocking**: Yes - PR will fail if tests fail

## Configuration

### PR Documentation Validator

The PR documentation validator supports configuration via environment variables:

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `PR_DOC_LARGE_THRESHOLD_KB` | 15 | Files larger than this (in KB) are considered "large documentation" |
| `PR_DOC_RATIO_THRESHOLD` | 10 | Warn if documentation is this many times larger than code |

These can be adjusted in `.github/workflows/ci.yml`:

```yaml
- name: Validate PR documentation
  env:
    PR_DOC_LARGE_THRESHOLD_KB: 20  # Increase threshold
    PR_DOC_RATIO_THRESHOLD: 15     # Allow higher ratio
```

### Warning vs. Blocking

The PR documentation validator is configured as **warning-only** using `continue-on-error: true`. This means:
- ✅ The CI job will continue even if warnings are found
- ✅ PRs won't be blocked by documentation warnings
- ⚠️ Warnings will still be visible in the CI output
- 📋 Reviewers should check the warnings and verify accuracy

To make it blocking (fail CI on warnings), remove the `continue-on-error: true` line.

## Running Validators Locally

You can run any validator locally before pushing:

```bash
# Run all validators
python tools/validators/check_artifacts.py
python tools/validators/check_quality_bar.py

# Run PR documentation validator with custom thresholds
export PR_DOC_LARGE_THRESHOLD_KB=20
export PR_DOC_RATIO_THRESHOLD=15
python tools/validators/check_pr_documentation.py \
  --pr-body /path/to/pr_body.txt \
  --repo-path .

# Run tests
python -m unittest discover -s tests -p "test_*.py" -v
```

## Troubleshooting

### PR Documentation Validator Warnings

If you see warnings from the PR documentation validator:

1. **Review the flagged content**: Check if the PR description contains simulated workflows or fictional elements
2. **Verify claims**: Ensure timeline claims match git history and PR references are real
3. **Mark examples clearly**: If documenting examples or tutorials, use "Example:", "Tutorial:", or "Simulated:" prefixes
4. **Check ratios**: Ensure documentation size is proportional to code changes
5. **See guidelines**: Refer to [PR Documentation Guidelines](pr-documentation-guidelines.md)

### Quality Bar Failures

If a file exceeds 800 lines:
- Consider splitting into smaller, focused modules
- Or request human review and add `allow:large-file` label if truly necessary

### Test Failures

- Run tests locally: `python -m unittest discover -s tests -p "test_*.py" -v`
- Check test output for specific failures
- Ensure all dependencies are installed

## Related Documentation

- [PR Documentation Guidelines](pr-documentation-guidelines.md) - Standards for PR descriptions
- [Agent Auditing](agent-auditing.md) - Tracking which agents did what
- [Automation Configuration](.github/automation/README.md) - GitHub automation setup
- [Setup Guide](setup.md) - Initial repository setup
