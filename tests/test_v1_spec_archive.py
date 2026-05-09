"""Tests for the archived Kerrigan v1 meta-spec layout."""

from pathlib import Path
import unittest


class TestV1SpecArchive(unittest.TestCase):
    """Validate that retired v1 meta-specs are archived in one place."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent
        self.specs_dir = self.repo_root / "specs" / "kerrigan"
        self.archive_dir = self.specs_dir / "_archive-v1"
        self.archived_specs = [
            "000-kerrigan-meta-spec.md",
            "010-agent-archetypes.md",
            "020-artifact-contracts.md",
            "030-quality-bar.md",
            "040-toolchain-and-ops.md",
            "050-cost-guardrails.md",
            "060-self-chaining-issues.md",
            "070-automation-contracts.md",
            "080-agent-feedback.md",
        ]

    def test_archive_directory_and_readme_exist(self):
        self.assertTrue(self.archive_dir.exists(), "specs/kerrigan/_archive-v1/ should exist")
        readme = self.archive_dir / "README.md"
        self.assertTrue(readme.exists(), "specs/kerrigan/_archive-v1/README.md should exist")
        content = readme.read_text(encoding="utf-8")
        self.assertIn("historical reference", content.lower())
        self.assertIn("kerrigan-v2", content)

    def test_all_v1_specs_were_moved_into_archive(self):
        for filename in self.archived_specs:
            with self.subTest(filename=filename):
                self.assertTrue((self.archive_dir / filename).exists(), f"{filename} should be archived")
                self.assertFalse((self.specs_dir / filename).exists(), f"{filename} should not remain at specs/kerrigan/")

    def test_active_docs_point_to_v2_and_archive(self):
        agents_md = (self.repo_root / "AGENTS.md").read_text(encoding="utf-8")
        legacy_index = (self.specs_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn("specs/kerrigan-v2/", agents_md)
        self.assertIn("specs/kerrigan/_archive-v1/", agents_md)
        self.assertIn("source of truth", legacy_index.lower())
        self.assertIn("_archive-v1", legacy_index)


if __name__ == "__main__":
    unittest.main()
