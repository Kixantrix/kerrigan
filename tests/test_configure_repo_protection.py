#!/usr/bin/env python3
"""Tests for the repo-protection config, apply tool, and validator wiring."""

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_repo_protection_config_is_valid_and_declares_queue() -> None:
    config = json.loads(_read(".github/repo-protection.json"))
    assert config["branch"] == "main"
    assert config["protection_mode"] == "ruleset"
    assert config["strict_status_checks"] is False
    assert config["merge_queue"]["enabled"] is True
    for check in ("kerrigan check", "tests", "smoke", "check-attestation"):
        assert check in config["required_checks"]


def test_preset_default_matches_schema() -> None:
    # The satellite-facing default must be valid and declare the same shape.
    config = json.loads(_read("preset/kerrigan/repo-protection.json"))
    assert config["protection_mode"] == "ruleset"
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
    assert "required_status_checks" in content
    assert "merge_queue" in content
    assert "Kerrigan main protection" in content
    # Idempotent: it looks for an existing ruleset before creating.
    assert "PUT" in content and "POST" in content


def test_apply_tool_skips_when_no_config() -> None:
    content = _read("tools/configure-repo-protection.ps1")
    # Absent config => no-op (opt-in per repo).
    assert "Test-Path -LiteralPath $ConfigPath" in content


def test_merge_queue_validator_is_registered_in_check() -> None:
    content = _read("tools/cli/kerrigan/kerrigan_cli/commands/check.py")
    assert "check_merge_queue.py" in content


def test_apply_tool_uses_utf8_no_bom_not_ascii() -> None:
    # -Encoding ascii corrupts non-ASCII names; PS 5.1 -Encoding utf8 adds a BOM
    # gh rejects. The tool must write payloads as UTF-8 without BOM.
    content = _read("tools/configure-repo-protection.ps1")
    assert "Write-Utf8NoBom" in content
    assert "UTF8Encoding" in content
    # No ascii-encoded payload writes remain.
    assert "-Encoding ascii" not in content


def test_apply_tool_guards_empty_required_checks() -> None:
    # Refuse to PATCH an empty contexts list (which would clear required checks).
    content = _read("tools/configure-repo-protection.ps1")
    assert "refusing to clear required checks" in content


def test_apply_tool_dry_run_prints_single_ruleset_and_no_mutation(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        raise AssertionError("pwsh is required for this test")

    config_path = tmp_path / "repo-protection.json"
    config_path.write_text(
        json.dumps(
            {
                "branch": "main",
                "protection_mode": "ruleset",
                "required_checks": ["kerrigan check", "tests", "smoke", "check-attestation"],
                "strict_status_checks": True,
                "merge_queue": {
                    "enabled": True,
                    "merge_method": "squash",
                    "min_entries_to_merge": 1,
                    "max_entries_to_merge": 5,
                    "min_entries_to_merge_wait_minutes": 5,
                },
            }
        ),
        encoding="utf-8",
    )

    gh_log = tmp_path / "gh.log"
    gh_log.write_text("", encoding="utf-8")
    gh_stub = tmp_path / "gh"
    gh_stub.write_text(
        "#!/usr/bin/env sh\n"
        "echo \"$@\" >> \"$GH_LOG\"\n"
        "if [ \"$1\" = \"api\" ]; then\n"
        "  echo \"[]\"\n"
        "fi\n",
        encoding="utf-8",
    )
    gh_stub.chmod(gh_stub.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env.get('PATH', '')}"
    env["GH_LOG"] = str(gh_log)

    result = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-File",
            str(REPO_ROOT / "tools" / "configure-repo-protection.ps1"),
            "-Repo",
            "Kixantrix/kerrigan",
            "-ConfigPath",
            str(config_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Kerrigan main protection" in out
    assert '"type": "required_status_checks"' in out
    assert '"strict_required_status_checks_policy": false' in out
    assert '"context": "kerrigan check"' in out
    assert '"type": "merge_queue"' in out
    assert '"merge_method": "SQUASH"' in out
    assert '"max_entries_to_build": 5' in out
    assert '"check_response_timeout_minutes": 60' in out
    assert '"grouping_strategy": "ALLGREEN"' in out
    assert 'payload: {"strict":false,"contexts":[]}' in out

    # Dry-run must not call gh mutating endpoints.
    assert gh_log.read_text(encoding="utf-8").strip() == ""
