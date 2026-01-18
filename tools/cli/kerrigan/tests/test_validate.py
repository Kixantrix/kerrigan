"""Tests for validate command."""

from click.testing import CliRunner
from kerrigan_cli.commands.validate import validate


def test_validate_help():
    """Test validate command help."""
    runner = CliRunner()
    result = runner.invoke(validate, ['--help'])
    assert result.exit_code == 0
    assert 'Run artifact validators' in result.output
