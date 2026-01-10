"""Integration tests for Hello CLI."""

import unittest
import subprocess
import sys
import os


class TestIntegration(unittest.TestCase):
    """Integration tests for full command execution."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment - install package in development mode."""
        # Get the hello-cli directory
        cls.hello_cli_dir = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))

        # Install in development mode
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-e', cls.hello_cli_dir],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to install package: {result.stderr}")

    def run_hello(self, *args):
        """Run hello command and return result."""
        result = subprocess.run(
            [sys.executable, '-m', 'hello_cli.cli'] + list(args),
            capture_output=True,
            text=True
        )
        return result

    def test_version_command(self):
        """Test --version flag displays version."""
        result = self.run_hello('--version')
        self.assertEqual(result.returncode, 0)
        self.assertIn('1.0.0', result.stdout)

    def test_help_command(self):
        """Test --help flag displays help."""
        result = self.run_hello('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Hello CLI', result.stdout)
        self.assertIn('greet', result.stdout)
        self.assertIn('echo', result.stdout)

    def test_greet_command_integration(self):
        """Test greet command end-to-end."""
        result = self.run_hello('greet', '--name', 'Integration')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Hello, Integration!', result.stdout)

    def test_greet_json_output_integration(self):
        """Test greet command with JSON output."""
        result = self.run_hello('greet', '--name', 'Test', '--json')
        self.assertEqual(result.returncode, 0)
        self.assertIn('"message"', result.stdout)
        self.assertIn('Hello, Test!', result.stdout)

    def test_echo_command_integration(self):
        """Test echo command end-to-end."""
        result = self.run_hello('echo', 'Integration test')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Integration test', result.stdout)

    def test_echo_with_upper_integration(self):
        """Test echo with uppercase transformation."""
        result = self.run_hello('echo', '--upper', 'lowercase')
        self.assertEqual(result.returncode, 0)
        self.assertIn('LOWERCASE', result.stdout)

    def test_echo_with_repeat_integration(self):
        """Test echo with repeat option."""
        result = self.run_hello('echo', '--repeat', '3', 'repeat')
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.strip().split('\n')
        self.assertEqual(len(lines), 3)

    def test_invalid_command_shows_error(self):
        """Test invalid command shows error."""
        result = self.run_hello('invalid-command')
        self.assertNotEqual(result.returncode, 0)

    def test_greet_without_name_shows_error(self):
        """Test greet without required --name shows error."""
        result = self.run_hello('greet')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--name', result.stderr.lower() or result.stdout.lower())


if __name__ == '__main__':
    unittest.main()
