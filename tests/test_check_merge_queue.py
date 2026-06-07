#!/usr/bin/env python3
"""Tests for the merge-queue readiness validator."""

import json
import sys
from pathlib import Path

# Import the validator the same way the other validator tests do: add
# tools/validators to sys.path and import the module directly. Importing via
# `from tools.validators...` trips check_python_deps (it reads `tools` as an
# undeclared third-party package).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "validators"))
from check_merge_queue import validate  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _config(**overrides) -> str:
    config = {
        "branch": "main",
        "required_checks": ["kerrigan check", "tests", "check-attestation"],
        "merge_queue": {"enabled": True},
    }
    config.update(overrides)
    return json.dumps(config)


# A workflow whose jobs produce "kerrigan check" and "tests" on merge_group.
_VERIFY_WF = """
name: verify
on:
  pull_request:
    branches: [main]
  merge_group:
    branches: [main]
jobs:
  validators:
    name: kerrigan check
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
  tests:
    name: tests
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
"""

# The attestation check uses the job id as its context (no explicit name).
_ATTESTATION_WF = """
name: attestation-check
on:
  pull_request:
    types: [opened]
  merge_group:
    branches: [main]
jobs:
  check-attestation:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
"""


def test_no_config_is_noop(tmp_path: Path) -> None:
    (tmp_path / ".github").mkdir()
    assert validate(tmp_path) == []


def test_queue_disabled_is_noop_even_without_merge_group(tmp_path: Path) -> None:
    _write(tmp_path / ".github" / "repo-protection.json", _config(merge_queue={"enabled": False}))
    _write(tmp_path / ".github" / "workflows" / "verify.yml", "name: verify\non:\n  pull_request:\njobs:\n  tests:\n    name: tests\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n")
    assert validate(tmp_path) == []


def test_all_required_checks_on_merge_group_passes(tmp_path: Path) -> None:
    _write(tmp_path / ".github" / "repo-protection.json", _config())
    _write(tmp_path / ".github" / "workflows" / "verify.yml", _VERIFY_WF)
    _write(tmp_path / ".github" / "workflows" / "attestation-check.yml", _ATTESTATION_WF)
    assert validate(tmp_path) == []


def test_missing_merge_group_trigger_fails(tmp_path: Path) -> None:
    # attestation workflow only triggers on pull_request -> check-attestation is
    # not produced on merge_group -> queued PRs would hang.
    pr_only_attestation = _ATTESTATION_WF.replace(
        "  merge_group:\n    branches: [main]\n", ""
    )
    _write(tmp_path / ".github" / "repo-protection.json", _config())
    _write(tmp_path / ".github" / "workflows" / "verify.yml", _VERIFY_WF)
    _write(tmp_path / ".github" / "workflows" / "attestation-check.yml", pr_only_attestation)
    problems = validate(tmp_path)
    assert len(problems) == 1
    assert "check-attestation" in problems[0]
    assert "merge_group" in problems[0]


def test_repo_protection_file_matches_actual_workflows() -> None:
    # The real repo must satisfy its own declared invariant.
    repo_root = Path(__file__).resolve().parents[1]
    assert validate(repo_root) == []
