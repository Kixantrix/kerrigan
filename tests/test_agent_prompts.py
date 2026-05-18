#!/usr/bin/env python3
"""Tests for agent prompt validation.

This test suite validates that all v2 agent profiles follow expected structure,
include required frontmatter, and properly define their responsibilities.
"""

import re
import unittest
from pathlib import Path


class TestV2ProfileStructure(unittest.TestCase):
    """Test that v2 agent profiles have required structural elements"""

    def setUp(self):
        """Load all v2 agent profiles"""
        repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = repo_root / ".github" / "agents"
        self.profiles = {
            "cloud": self.agents_dir / "cloud.md",
            "kerrigan": self.agents_dir / "kerrigan.md",
        }
        for name, path in self.profiles.items():
            self.assertTrue(path.exists(), f"v2 profile not found: {name}.md")

    def test_all_profiles_have_yaml_frontmatter(self):
        """Test that all profiles have YAML frontmatter delimited by ---"""
        for name, path in self.profiles.items():
            with self.subTest(profile=name):
                content = path.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---"),
                    f"{name}.md must start with YAML frontmatter")
                second_marker = content.index("---", 3)
                self.assertGreater(second_marker, 3,
                    f"{name}.md must have closing --- for frontmatter")

    def test_all_profiles_have_name_field(self):
        """Test that all profiles declare a name in frontmatter"""
        for name, path in self.profiles.items():
            with self.subTest(profile=name):
                content = path.read_text(encoding="utf-8")
                self.assertRegex(content, f'name:\\s+{name}',
                    f"{name}.md must have name: {name} in frontmatter")

    def test_all_profiles_have_description(self):
        """Test that all profiles have a description in frontmatter"""
        for name, path in self.profiles.items():
            with self.subTest(profile=name):
                content = path.read_text(encoding="utf-8")
                self.assertIn("description:", content,
                    f"{name}.md must have a description in frontmatter")

    def test_all_profiles_are_markdown(self):
        """Test that all profiles use markdown format with headers"""
        for name, path in self.profiles.items():
            with self.subTest(profile=name):
                content = path.read_text(encoding="utf-8")
                self.assertRegex(content, r'#\s+\w+',
                    f"{name}.md should use markdown format with headers")

    def test_all_profiles_define_what_they_do(self):
        """Test that all profiles have a do/mission section"""
        for name, path in self.profiles.items():
            with self.subTest(profile=name):
                content = path.read_text(encoding="utf-8")
                has_do_section = any(term in content for term in [
                    "What you do",
                    "## Mission",
                ])
                self.assertTrue(has_do_section,
                    f"{name}.md must define what the agent does")

    def test_all_profiles_define_what_they_dont_do(self):
        """Test that all profiles have a don't-do section"""
        for name, path in self.profiles.items():
            with self.subTest(profile=name):
                content = path.read_text(encoding="utf-8")
                has_dont_section = "What you don" in content
                self.assertTrue(has_dont_section,
                    f"{name}.md must define what the agent doesn't do")

    def test_all_profiles_have_kerrigan_manifest(self):
        """Test that all profiles have a capability manifest"""
        for name, path in self.profiles.items():
            with self.subTest(profile=name):
                content = path.read_text(encoding="utf-8")
                self.assertIn("role:", content,
                    f"{name}.md must have a role in capability manifest")
                self.assertIn("blocks_on:", content,
                    f"{name}.md must declare what blocks it")


class TestCloudProfile(unittest.TestCase):
    """Test cloud (executor) profile specific requirements"""

    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.path = repo_root / ".github" / "agents" / "cloud.md"
        if not self.path.exists():
            self.fail("cloud.md not found")
        self.content = self.path.read_text(encoding="utf-8")

    def test_cloud_is_executor(self):
        self.assertIn("executor", self.content.lower())

    def test_cloud_emphasizes_testing(self):
        test_keywords = ["test", "Test", "TDD", "self-verify"]
        test_count = sum(self.content.count(kw) for kw in test_keywords)
        self.assertGreater(test_count, 5,
            "cloud.md must emphasize testing (multiple mentions)")

    def test_cloud_reads_briefing_first(self):
        self.assertIn("briefing", self.content.lower())

    def test_cloud_never_exceeds_scope(self):
        has_scope_guard = any(term in self.content for term in [
            "Never exceed scope",
            "scope-creep",
            "Scope-creep",
        ])
        self.assertTrue(has_scope_guard, "cloud.md must guard against scope creep")

    def test_cloud_opens_one_pr(self):
        self.assertIn("one PR", self.content)

    def test_cloud_self_verifies(self):
        self.assertIn("Self-verify", self.content)

    def test_cloud_has_pr_template(self):
        self.assertIn("PR body shape", self.content)

    def test_cloud_documents_verification_enforcement(self):
        self.assertIn("verifies_before_pr:", self.content)
        self.assertIn("enforce: block_on_unfixable_failure_before_pr", self.content)

    def test_cloud_has_self_verification_protocol_steps(self):
        self.assertIn("## Self-verification protocol", self.content)
        self.assertIn("Run unit + integration tests", self.content)
        self.assertIn("Run smoke test", self.content)
        self.assertIn("Run lint/type checks", self.content)
        self.assertIn("If still failing and unfixable in scope, emit a block and stop", self.content)

    def test_cloud_references_test_capability_matrix_rules(self):
        self.assertIn("cloud_ok | local_required | manual", self.content)
        self.assertIn("never `@skip` without a reason", self.content)

    def test_cloud_includes_self_test_failure_block_template(self):
        self.assertIn("### Self-test failure block template", self.content)
        self.assertIn("reason: test_infrastructure_failure", self.content)

    def test_cloud_pr_template_includes_verification_results(self):
        self.assertIn("## Self-verification results", self.content)
        self.assertIn("capability matrix declarations", self.content)


class TestKerriganProfile(unittest.TestCase):
    """Test kerrigan (swarm shaper) profile specific requirements"""

    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.path = repo_root / ".github" / "agents" / "kerrigan.md"
        if not self.path.exists():
            self.fail("kerrigan.md not found")
        self.content = self.path.read_text(encoding="utf-8")

    def test_kerrigan_is_conductor(self):
        self.assertIn("role: conductor", self.content)

    def test_kerrigan_mentions_validators(self):
        self.assertIn("validator", self.content.lower())

    def test_kerrigan_mentions_feedback(self):
        self.assertIn("feedback", self.content.lower())

    def test_kerrigan_mentions_constitution(self):
        self.assertIn("constitution", self.content.lower())

    def test_kerrigan_doesnt_implement_features(self):
        self.assertIn("implement feature code", self.content.lower())


class TestAgentPromptCompleteness(unittest.TestCase):
    """Test that all expected agents have prompts"""

    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = repo_root / ".github" / "agents"

    def test_v2_profiles_exist(self):
        for profile in ["cloud.md", "kerrigan.md"]:
            path = self.agents_dir / profile
            self.assertTrue(path.exists(), f"v2 profile not found: {profile}")

    def test_adapters_directory_exists(self):
        adapters_dir = self.agents_dir / "adapters"
        self.assertTrue(adapters_dir.exists(), "adapters/ directory must exist")
        expected = ["explore.md", "plan.md", "copilot-review.md", "copilot-coding.md"]
        for adapter in expected:
            path = adapters_dir / adapter
            self.assertTrue(path.exists(), f"adapter not found: {adapter}")

    def test_agents_readme_exists(self):
        readme = self.agents_dir / "README.md"
        self.assertTrue(readme.exists(), "Agents directory must have a README.md")

    def test_agents_readme_documents_profiles(self):
        readme = self.agents_dir / "README.md"
        if not readme.exists():
            self.skipTest("README not found")
        content = readme.read_text(encoding="utf-8")
        for profile in ["cloud", "kerrigan"]:
            self.assertIn(profile, content.lower(),
                f"README should document the {profile} profile")


class TestTriageAgentRoleBoundaries(unittest.TestCase):
    """Test that triage analysis prompt enforces strict role boundaries"""

    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.triage_prompt_path = repo_root / "prompts" / "triage-analysis.md"
        if not self.triage_prompt_path.exists():
            self.skipTest("Triage analysis prompt not found")
        self.triage_content = self.triage_prompt_path.read_text(encoding="utf-8")

    def test_triage_forbids_direct_implementation(self):
        self.assertIn("Do NOT implement", self.triage_content)
        self.assertIn("Do NOT make code changes", self.triage_content)

    def test_triage_forbids_committing_code(self):
        self.assertIn("Do NOT commit code", self.triage_content)

    def test_triage_emphasizes_delegation(self):
        delegate_count = self.triage_content.lower().count("delegate")
        self.assertGreaterEqual(delegate_count, 5)

    def test_triage_has_role_boundary_section(self):
        self.assertIn("Role Boundary", self.triage_content)
        self.assertIn("CRITICAL", self.triage_content)

    def test_triage_defines_analysis_only_role(self):
        self.assertIn("analysis", self.triage_content.lower())

    def test_triage_uses_anti_pattern_markers(self):
        has_markers = chr(10060) in self.triage_content or chr(9940) in self.triage_content
        self.assertTrue(has_markers)


if __name__ == "__main__":
    unittest.main()
