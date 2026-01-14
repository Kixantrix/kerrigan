"""Tests for CLI entry point."""

import unittest
from click.testing import CliRunner
from hello_cli.cli import cli


class TestCLI(unittest.TestCase):
    """Test cases for CLI entry point."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_without_command_shows_help(self):
        """Test CLI without subcommand shows help."""
        result = self.runner.invoke(cli, [])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Hello CLI', result.output)
        self.assertIn('--help', result.output)

    def test_cli_version_shows_version(self):
        """Test --version flag shows version number."""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('1.0.0', result.output)

    def test_cli_help_shows_commands(self):
        """Test --help flag shows available commands."""
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('greet', result.output)
        self.assertIn('echo', result.output)

    def test_cli_with_invalid_config_shows_error(self):
        """Test CLI with nonexistent config file shows error."""
        result = self.runner.invoke(
            cli,
            ['--config', '/nonexistent/config.yml',
             'greet', '--name', 'Test'])
        # Click returns 2 for usage errors
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Error', result.output)


if __name__ == '__main__':
    unittest.main()
