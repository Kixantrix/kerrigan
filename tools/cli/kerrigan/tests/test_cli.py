"""Tests for CLI entry point."""

import pytest
from click.testing import CliRunner
from kerrigan_cli.cli import cli


def test_cli_help():
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Kerrigan CLI' in result.output
    assert 'init' in result.output
    assert 'status' in result.output
    assert 'validate' in result.output
    assert 'repos' in result.output
    assert 'agent' in result.output


def test_cli_version():
    """Test CLI version flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert '0.1.0' in result.output


def test_cli_no_command():
    """Test CLI with no command shows help."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert 'Kerrigan CLI' in result.output
