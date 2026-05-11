import unittest
from pathlib import Path
import sys

from click.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "cli" / "kerrigan"))

from kerrigan_cli.commands.agent import agent


class TestAgentCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.repo_root = REPO_ROOT

    def test_list_shows_v2_profiles(self):
        result = self.runner.invoke(agent, ["--list"], catch_exceptions=False)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Available agent profiles:", result.output)
        for profile in ("local", "cloud", "kerrigan"):
            self.assertIn(f"  - {profile}", result.output)
        self.assertNotIn("Available agent roles:", result.output)

    def test_show_reads_profile_file(self):
        result = self.runner.invoke(
            agent,
            ["local", "--show"],
            catch_exceptions=False,
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Agent profile: local", result.output)
        self.assertIn("File: .github/agents/local.md", result.output)
