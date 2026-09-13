import unittest
from pathlib import Path
import re
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
        for profile in ("cloud", "kerrigan"):
            self.assertIn(f"  - {profile}", result.output)
        self.assertNotIn("Available agent roles:", result.output)

    def test_show_reads_profile_file(self):
        result = self.runner.invoke(
            agent,
            ["kerrigan", "--show"],
            catch_exceptions=False,
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Agent profile: kerrigan", result.output)
        relative_path = Path(".github") / "agents" / "kerrigan.md"
        self.assertIn(f"File: {relative_path}", result.output)
        self.assertIn((REPO_ROOT / relative_path).read_text(encoding="utf-8"), result.output)

    def test_help_and_documented_examples_resolve_real_profiles(self):
        help_result = self.runner.invoke(agent, ["--help"], catch_exceptions=False)
        self.assertEqual(help_result.exit_code, 0)
        self.assertIn("does not select a runtime agent", help_result.output)
        docs = (REPO_ROOT / "docs" / "operations" / "cli-reference.md").read_text(
            encoding="utf-8"
        )
        package_readme = (REPO_ROOT / "tools" / "cli" / "kerrigan" / "README.md").read_text(
            encoding="utf-8"
        )
        for source in (help_result.output, docs, package_readme):
            examples = re.findall(r"kerrigan agent (\w+) --(?:show|copy)", source)
            self.assertEqual(set(examples), {"kerrigan", "cloud"})
            for profile in examples:
                with self.subTest(profile=profile):
                    result = self.runner.invoke(
                        agent, [profile, "--show"], catch_exceptions=False
                    )
                    self.assertEqual(result.exit_code, 0)
                    self.assertIn(f"Agent profile: {profile}", result.output)
