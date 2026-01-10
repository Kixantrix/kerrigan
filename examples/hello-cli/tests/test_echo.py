"""Tests for the echo command."""

import unittest
from click.testing import CliRunner
from hello_cli.cli import cli


class TestEchoCommand(unittest.TestCase):
    """Test cases for echo command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_echo_returns_text(self):
        """Test echo returns the provided text."""
        result = self.runner.invoke(cli, ['echo', 'Hello World'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Hello World', result.output)

    def test_echo_with_upper_returns_uppercase(self):
        """Test echo with --upper flag returns uppercase text."""
        result = self.runner.invoke(cli, ['echo', '--upper', 'hello'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('HELLO', result.output)
        self.assertNotIn('hello', result.output)

    def test_echo_with_repeat_returns_multiple_lines(self):
        """Test echo with --repeat flag returns text multiple times."""
        result = self.runner.invoke(cli, ['echo', '--repeat', '3', 'Hi'])
        self.assertEqual(result.exit_code, 0)
        lines = result.output.strip().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertTrue(all('Hi' in line for line in lines))

    def test_echo_with_json_returns_json(self):
        """Test echo with --json flag returns JSON format."""
        result = self.runner.invoke(cli, ['echo', '--json', 'test'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"text"', result.output)
        self.assertIn('test', result.output)

    def test_echo_with_upper_and_repeat(self):
        """Test echo with both --upper and --repeat flags."""
        result = self.runner.invoke(cli, ['echo', '--upper', '--repeat', '2', 'hi'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('HI', result.output)
        lines = result.output.strip().split('\n')
        self.assertEqual(len(lines), 2)

    def test_echo_without_text_shows_error(self):
        """Test echo without text argument shows error."""
        result = self.runner.invoke(cli, ['echo'])
        self.assertEqual(result.exit_code, 2)  # Click usage error

    def test_echo_with_empty_string(self):
        """Test echo with empty string."""
        result = self.runner.invoke(cli, ['echo', ''])
        self.assertEqual(result.exit_code, 0)

    def test_echo_help_shows_usage(self):
        """Test echo --help shows usage information."""
        result = self.runner.invoke(cli, ['echo', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--upper', result.output)
        self.assertIn('--repeat', result.output)
        self.assertIn('Echo text', result.output)


if __name__ == '__main__':
    unittest.main()
