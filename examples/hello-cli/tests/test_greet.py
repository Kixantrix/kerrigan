"""Tests for the greet command."""

import unittest
from click.testing import CliRunner
from hello_cli.cli import cli


class TestGreetCommand(unittest.TestCase):
    """Test cases for greet command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_greet_with_name_returns_message(self):
        """Test greet with name returns personalized message."""
        result = self.runner.invoke(cli, ['greet', '--name', 'Alice'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Hello, Alice!', result.output)

    def test_greet_with_name_json_returns_json(self):
        """Test greet with --json flag returns JSON format."""
        result = self.runner.invoke(cli, ['greet', '--name', 'Bob', '--json'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"message"', result.output)
        self.assertIn('Hello, Bob!', result.output)

    def test_greet_without_name_shows_error(self):
        """Test greet without --name shows error."""
        result = self.runner.invoke(cli, ['greet'])
        self.assertEqual(result.exit_code, 2)  # Click usage error
        self.assertIn('--name', result.output.lower())

    def test_greet_with_unicode_name(self):
        """Test greet with unicode characters in name."""
        result = self.runner.invoke(cli, ['greet', '--name', '李明'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Hello, 李明!', result.output)

    def test_greet_help_shows_usage(self):
        """Test greet --help shows usage information."""
        result = self.runner.invoke(cli, ['greet', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--name', result.output)
        self.assertIn('Greet a person by name', result.output)


if __name__ == '__main__':
    unittest.main()
