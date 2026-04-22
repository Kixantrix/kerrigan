#!/usr/bin/env python3
"""Tests for the agents_md validator."""

import tempfile
import textwrap
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools" / "validators"))

from agents_md import parse_frontmatter, check_agent_profile, check_agents_md


class TestParseFrontmatter(unittest.TestCase):
    """Test frontmatter parsing."""

    def test_valid_frontmatter_lf(self):
        text = "---\nname: local\ndescription: A conductor\n---\n# Body"
        fm = parse_frontmatter(text)
        self.assertIsNotNone(fm)
        self.assertEqual(fm["name"], "local")
        self.assertEqual(fm["description"], "A conductor")

    def test_valid_frontmatter_crlf(self):
        text = "---\r\nname: cloud\r\ndescription: An executor\r\n---\r\n# Body"
        fm = parse_frontmatter(text)
        self.assertIsNotNone(fm)
        self.assertEqual(fm["name"], "cloud")

    def test_missing_frontmatter(self):
        text = "# No frontmatter here"
        fm = parse_frontmatter(text)
        self.assertIsNone(fm)

    def test_skips_comments_and_lists(self):
        text = "---\nname: test\n# a comment\n- list item\n  continuation: yes\ndescription: desc\n---\n"
        fm = parse_frontmatter(text)
        self.assertIsNotNone(fm)
        self.assertEqual(fm["name"], "test")
        self.assertEqual(fm["description"], "desc")
        self.assertNotIn("continuation", fm)


class TestCheckAgentProfile(unittest.TestCase):
    """Test profile validation."""

    def _write_profile(self, tmpdir: Path, name: str, content: str) -> Path:
        path = tmpdir / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_profile(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._write_profile(Path(td), "local.md",
                "---\nname: local\ndescription: Conductor\n---\n# local")
            errors = []
            # Monkey-patch REPO_ROOT for relative path display
            import agents_md
            old_root = agents_md.REPO_ROOT
            agents_md.REPO_ROOT = Path(td)
            try:
                check_agent_profile(p, errors)
            finally:
                agents_md.REPO_ROOT = old_root
            self.assertEqual(errors, [])

    def test_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._write_profile(Path(td), "bad.md", "# No frontmatter")
            errors = []
            import agents_md
            old_root = agents_md.REPO_ROOT
            agents_md.REPO_ROOT = Path(td)
            try:
                check_agent_profile(p, errors)
            finally:
                agents_md.REPO_ROOT = old_root
            self.assertEqual(len(errors), 1)
            self.assertIn("missing YAML frontmatter", errors[0])

    def test_missing_name_field(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._write_profile(Path(td), "test.md",
                "---\ndescription: Something\n---\n# test")
            errors = []
            import agents_md
            old_root = agents_md.REPO_ROOT
            agents_md.REPO_ROOT = Path(td)
            try:
                check_agent_profile(p, errors)
            finally:
                agents_md.REPO_ROOT = old_root
            self.assertTrue(any("name" in e for e in errors))

    def test_name_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._write_profile(Path(td), "cloud.md",
                "---\nname: local\ndescription: Wrong name\n---\n# cloud")
            errors = []
            import agents_md
            old_root = agents_md.REPO_ROOT
            agents_md.REPO_ROOT = Path(td)
            try:
                check_agent_profile(p, errors)
            finally:
                agents_md.REPO_ROOT = old_root
            self.assertTrue(any("does not match" in e for e in errors))

    def test_speckit_agent_only_requires_description(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._write_profile(Path(td), "speckit.git.commit.agent.md",
                "---\ndescription: Auto-commit\n---\n# commit")
            errors = []
            import agents_md
            old_root = agents_md.REPO_ROOT
            agents_md.REPO_ROOT = Path(td)
            try:
                check_agent_profile(p, errors)
            finally:
                agents_md.REPO_ROOT = old_root
            self.assertEqual(errors, [])


class TestCheckAgentsMd(unittest.TestCase):
    """Test AGENTS.md validation."""

    def test_missing_agents_md(self):
        with tempfile.TemporaryDirectory() as td:
            import agents_md
            old_md = agents_md.AGENTS_MD
            old_root = agents_md.REPO_ROOT
            agents_md.AGENTS_MD = Path(td) / "AGENTS.md"
            agents_md.REPO_ROOT = Path(td)
            try:
                errors = []
                check_agents_md(errors)
                self.assertTrue(any("missing" in e for e in errors))
            finally:
                agents_md.AGENTS_MD = old_md
                agents_md.REPO_ROOT = old_root

    def test_valid_agents_md(self):
        errors = []
        check_agents_md(errors)
        self.assertEqual(errors, [],
            "AGENTS.md in the real repo should pass validation")


if __name__ == "__main__":
    unittest.main()
