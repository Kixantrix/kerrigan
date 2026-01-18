"""Tests for status command."""

from click.testing import CliRunner
from kerrigan_cli.commands.status import status


def test_status_help():
    """Test status command help."""
    runner = CliRunner()
    result = runner.invoke(status, ['--help'])
    assert result.exit_code == 0
    assert 'Show project status' in result.output
