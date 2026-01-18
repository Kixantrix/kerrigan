"""Tests for agent command."""

from click.testing import CliRunner
from kerrigan_cli.commands.agent import agent


def test_agent_help():
    """Test agent command help."""
    runner = CliRunner()
    result = runner.invoke(agent, ['--help'])
    assert result.exit_code == 0
    assert 'Invoke agent' in result.output
