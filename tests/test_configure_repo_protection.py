#!/usr/bin/env python3
"""Tests for the repo-protection config, apply tool, and validator wiring."""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_repo_protection_config_is_valid_and_declares_queue() -> None:
    config = json.loads(_read(".github/repo-protection.json"))
    assert config["branch"] == "main"
    assert config["strict_status_checks"] is False
    assert config["merge_queue"]["enabled"] is True
    for check in ("kerrigan check", "tests", "smoke", "check-attestation"):
        assert check in config["required_checks"]


def test_preset_default_matches_schema() -> None:
    # The satellite-facing default must be valid and declare the same shape.
    config = json.loads(_read("preset/kerrigan/repo-protection.json"))
    assert config["strict_status_checks"] is False
    assert config["merge_queue"]["enabled"] is True
    assert isinstance(config["required_checks"], list)


def test_apply_tool_has_help_and_is_dry_run_by_default() -> None:
    content = _read("tools/configure-repo-protection.ps1")
    for token in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER", ".EXAMPLE"):
        assert token in content
    # Mutations must be gated behind -Apply; dry-run is the default.
    assert "[switch]$Apply" in content
    assert "if ($Apply)" in content
    # The two managed surfaces.
    assert "branches/$branch/protection/required_status_checks" in content
    assert "rulesets" in content
    assert "merge_queue" in content
    # Idempotent: it looks for an existing ruleset before creating.
    assert "PUT" in content and "POST" in content


def test_apply_tool_skips_when_no_config() -> None:
    content = _read("tools/configure-repo-protection.ps1")
    # Absent config => no-op (opt-in per repo).
    assert "Test-Path -LiteralPath $ConfigPath" in content


def test_merge_queue_validator_is_registered_in_check() -> None:
    content = _read("tools/cli/kerrigan/kerrigan_cli/commands/check.py")
    assert "check_merge_queue.py" in content
