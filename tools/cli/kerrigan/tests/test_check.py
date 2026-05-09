"""Tests for check command."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from kerrigan_cli.commands.check import REGISTERED_VALIDATORS, check
from kerrigan_cli.cli import cli


def _fake_completed_process(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """Return a completed-process-like mock object."""
    return MagicMock(returncode=returncode, stdout=stdout, stderr=stderr)


def _write_validator_tree(root: Path, names: list[str]) -> Path:
    """Create a fake validator directory tree."""
    validators = root / "tools" / "validators"
    validators.mkdir(parents=True)
    for name in names:
        (validators / name).write_text("# stub", encoding="utf-8")
    return validators


def test_check_help():
    """check --help exits 0 and mentions the command."""
    runner = CliRunner()
    result = runner.invoke(check, ["--help"])
    assert result.exit_code == 0
    assert "Run all registered validators" in result.output


def test_check_registered_in_cli():
    """kerrigan --help lists the check command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "check" in result.output


def test_check_runs_all_registered_validators(tmp_path):
    """check runs every validator script found in tools/validators."""
    validator_names = [spec.script_name for spec in REGISTERED_VALIDATORS]
    _write_validator_tree(tmp_path, validator_names)

    mock_run = MagicMock(return_value=_fake_completed_process(0))
    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", mock_run),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code == 0
    assert mock_run.call_count == len(REGISTERED_VALIDATORS)
    commands = [call.args[0] for call in mock_run.call_args_list]
    for validator_name in validator_names:
        assert any(validator_name in str(command) for command in commands)


def test_check_builds_pr_aware_validator_commands(tmp_path):
    """PR-aware validators receive PR body and comparison refs when available."""
    validator_names = [
        "show_status.py",
        "check_pr_documentation.py",
        "check_test_claims.py",
    ]
    _write_validator_tree(tmp_path, validator_names)

    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"pull_request": {"body": "## Testing\nRan 12 tests"}}),
        encoding="utf-8",
    )

    mock_run = MagicMock(return_value=_fake_completed_process(0))
    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", mock_run),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
        patch.dict(
            "os.environ",
            {"GITHUB_EVENT_PATH": str(event_path), "GITHUB_BASE_REF": "main"},
            clear=False,
        ),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code == 0
    commands = [call.args[0] for call in mock_run.call_args_list]

    pr_doc_command = next(
        (command for command in commands if "check_pr_documentation.py" in str(command)),
        None,
    )
    assert pr_doc_command is not None
    assert "--pr-body" in pr_doc_command
    assert "--repo-path" in pr_doc_command
    assert str(tmp_path) in pr_doc_command

    test_claims_command = next(
        (command for command in commands if "check_test_claims.py" in str(command)),
        None,
    )
    assert test_claims_command is not None
    assert "--pr-body" in test_claims_command
    assert "--base-ref" in test_claims_command
    assert "origin/main" in test_claims_command


def test_check_treats_advisory_validator_as_non_blocking(tmp_path):
    """Advisory validator failures do not fail the overall check."""
    _write_validator_tree(
        tmp_path,
        ["show_status.py", "check_pr_documentation.py"],
    )

    mock_run = MagicMock(
        side_effect=[
            _fake_completed_process(0),
            _fake_completed_process(1, stdout="warning"),
        ]
    )

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", mock_run),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code == 0
    assert "advisory validator returned non-zero; continuing" in result.output
    assert "1/2 validators passed, 1/2 advisory, 0/2 failed." in result.output


def test_check_fails_on_blocking_validator_error(tmp_path):
    """Blocking validator failures still fail the command."""
    _write_validator_tree(
        tmp_path,
        ["show_status.py", "check_artifacts.py"],
    )

    mock_run = MagicMock(
        side_effect=[
            _fake_completed_process(0),
            _fake_completed_process(1, stdout="artifact failure"),
        ]
    )

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", mock_run),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code != 0
    assert "1/2 validators passed, 0/2 advisory, 1/2 failed." in result.output


def test_check_fails_when_validator_script_is_unregistered(tmp_path):
    """Unknown validator scripts are reported as registration failures."""
    _write_validator_tree(tmp_path, ["show_status.py", "new_validator.py"])

    mock_run = MagicMock(return_value=_fake_completed_process(0))
    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", mock_run),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code != 0
    assert "new_validator.py is not registered in kerrigan check" in result.output
    assert "1/2 validators passed, 0/2 advisory, 1/2 failed." in result.output


def test_check_verbose_shows_output(tmp_path):
    """--verbose flag displays stdout from each validator."""
    _write_validator_tree(tmp_path, ["show_status.py"])

    mock_run = MagicMock(return_value=_fake_completed_process(0, stdout="all good\n"))

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", mock_run),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, ["--verbose"])

    assert result.exit_code == 0
    assert "all good" in result.output


def test_check_aborts_when_no_repo_root():
    """check exits with non-zero when repo root cannot be found."""
    runner = CliRunner()
    with patch("kerrigan_cli.commands.check._find_repo_root", return_value=None):
        result = runner.invoke(check, [])
    assert result.exit_code != 0
