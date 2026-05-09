"""Tests for check command."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from kerrigan_cli.commands.check import check
from kerrigan_cli.cli import cli


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_run(returncode: int = 0):
    """Return a mock for subprocess.run that yields the given returncode."""
    mock_result = MagicMock()
    mock_result.returncode = returncode
    mock_result.stdout = ""
    mock_result.stderr = ""
    return MagicMock(return_value=mock_result)


# ---------------------------------------------------------------------------
# Help / registration
# ---------------------------------------------------------------------------


def test_check_help():
    """check --help exits 0 and mentions the command."""
    runner = CliRunner()
    result = runner.invoke(check, ["--help"])
    assert result.exit_code == 0
    assert "Run all validators" in result.output


def test_check_registered_in_cli():
    """kerrigan --help lists the check command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "check" in result.output


# ---------------------------------------------------------------------------
# AC-2 / AC-3: validators run
# ---------------------------------------------------------------------------


def test_check_runs_agents_md_and_check_artifacts(tmp_path):
    """check calls agents_md.py and check_artifacts.py when both are present."""
    # Create fake validator tree
    validators = tmp_path / "tools" / "validators"
    validators.mkdir(parents=True)
    (validators / "agents_md.py").write_text("# stub")
    (validators / "check_artifacts.py").write_text("# stub")

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", _fake_run(0)) as mock_run,
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code == 0
    # Two subprocess calls (agents_md + check_artifacts)
    assert mock_run.call_count == 2
    calls = [c.args[0] for c in mock_run.call_args_list]
    assert any("agents_md.py" in str(c) for c in calls)
    assert any("check_artifacts.py" in str(c) for c in calls)


def test_check_skips_check_artifacts_when_absent(tmp_path):
    """check skips check_artifacts.py when the file is not present."""
    validators = tmp_path / "tools" / "validators"
    validators.mkdir(parents=True)
    (validators / "agents_md.py").write_text("# stub")
    # check_artifacts.py intentionally NOT created

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", _fake_run(0)) as mock_run,
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code == 0
    assert mock_run.call_count == 1
    assert "agents_md.py" in str(mock_run.call_args_list[0].args[0])


# ---------------------------------------------------------------------------
# AC-4: specify check optional
# ---------------------------------------------------------------------------


def test_check_runs_specify_when_on_path(tmp_path):
    """check includes specify check when specify is on PATH."""
    validators = tmp_path / "tools" / "validators"
    validators.mkdir(parents=True)
    (validators / "agents_md.py").write_text("# stub")

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", _fake_run(0)) as mock_run,
        patch("kerrigan_cli.commands.check.shutil.which", return_value="/usr/bin/specify"),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code == 0
    calls = [c.args[0] for c in mock_run.call_args_list]
    assert any(c == ["specify", "check"] for c in calls)


def test_check_skips_specify_when_not_on_path(tmp_path):
    """check skips specify check when specify is not installed."""
    validators = tmp_path / "tools" / "validators"
    validators.mkdir(parents=True)
    (validators / "agents_md.py").write_text("# stub")

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", _fake_run(0)) as mock_run,
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code == 0
    calls = [c.args[0] for c in mock_run.call_args_list]
    assert not any(c == ["specify", "check"] for c in calls)
    assert "skipping" in result.output


# ---------------------------------------------------------------------------
# AC-5: summary output
# ---------------------------------------------------------------------------


def test_check_summary_all_pass(tmp_path):
    """Summary reports N/N validators passed when all succeed."""
    validators = tmp_path / "tools" / "validators"
    validators.mkdir(parents=True)
    (validators / "agents_md.py").write_text("# stub")
    (validators / "check_artifacts.py").write_text("# stub")

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", _fake_run(0)),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert "2/2 validators passed" in result.output
    assert "0/2 failed" in result.output


def test_check_summary_one_fail(tmp_path):
    """Summary reports failed count and exits non-zero when a validator fails."""
    validators = tmp_path / "tools" / "validators"
    validators.mkdir(parents=True)
    (validators / "agents_md.py").write_text("# stub")
    (validators / "check_artifacts.py").write_text("# stub")

    # agents_md passes (call 0), check_artifacts fails (call 1)
    results = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=1, stdout="fail output", stderr=""),
    ]
    mock_run = MagicMock(side_effect=results)

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", mock_run),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code != 0
    assert "1/2 validators passed" in result.output
    assert "1/2 failed" in result.output


# ---------------------------------------------------------------------------
# AC-6: --verbose flag
# ---------------------------------------------------------------------------


def test_check_verbose_shows_output(tmp_path):
    """--verbose flag displays stdout from each validator."""
    validators = tmp_path / "tools" / "validators"
    validators.mkdir(parents=True)
    (validators / "agents_md.py").write_text("# stub")

    mock_result = MagicMock(returncode=0, stdout="all good\n", stderr="")
    mock_run = MagicMock(return_value=mock_result)

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", mock_run),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, ["--verbose"])

    assert result.exit_code == 0
    assert "all good" in result.output


def test_check_no_verbose_hides_passing_output(tmp_path):
    """Without --verbose, stdout from passing validators is suppressed."""
    validators = tmp_path / "tools" / "validators"
    validators.mkdir(parents=True)
    (validators / "agents_md.py").write_text("# stub")

    mock_result = MagicMock(returncode=0, stdout="quiet output\n", stderr="")
    mock_run = MagicMock(return_value=mock_result)

    runner = CliRunner()
    with (
        patch("kerrigan_cli.commands.check._find_repo_root", return_value=tmp_path),
        patch("kerrigan_cli.commands.check.subprocess.run", mock_run),
        patch("kerrigan_cli.commands.check.shutil.which", return_value=None),
    ):
        result = runner.invoke(check, [])

    assert result.exit_code == 0
    assert "quiet output" not in result.output


# ---------------------------------------------------------------------------
# Repo root not found
# ---------------------------------------------------------------------------


def test_check_aborts_when_no_repo_root():
    """check exits with non-zero when repo root cannot be found."""
    runner = CliRunner()
    with patch("kerrigan_cli.commands.check._find_repo_root", return_value=None):
        result = runner.invoke(check, [])
    assert result.exit_code != 0
