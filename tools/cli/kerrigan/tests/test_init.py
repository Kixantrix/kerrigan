"""Tests for init command."""

from click.testing import CliRunner
from kerrigan_cli.commands.init import init


def test_init_help():
    """Test init command help."""
    runner = CliRunner()
    result = runner.invoke(init, ['--help'])
    assert result.exit_code == 0
    assert 'Initialize a new project' in result.output
    assert 'project_name' in result.output.lower()
