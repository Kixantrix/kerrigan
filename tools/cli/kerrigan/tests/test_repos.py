"""Tests for repos command."""

from click.testing import CliRunner
from kerrigan_cli.commands.repos import repos


def test_repos_help():
    """Test repos command help."""
    runner = CliRunner()
    result = runner.invoke(repos, ['--help'])
    assert result.exit_code == 0
    assert 'Multi-repository operations' in result.output


def test_repos_list_help():
    """Test repos list subcommand help."""
    runner = CliRunner()
    result = runner.invoke(repos, ['list', '--help'])
    assert result.exit_code == 0
    assert 'List repositories' in result.output


def test_repos_sync_help():
    """Test repos sync subcommand help."""
    runner = CliRunner()
    result = runner.invoke(repos, ['sync', '--help'])
    assert result.exit_code == 0
    assert 'Sync status' in result.output
