#!/usr/bin/env python3
"""Tests for current (v2) automation configuration."""

import unittest
from pathlib import Path

import yaml


class TestTasksFormat(unittest.TestCase):
    """Test tasks.md format for AUTO-ISSUE examples."""

    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.tasks_files = list(repo_root.glob("examples/*/tasks.md"))

    def test_example_tasks_exist(self):
        self.assertGreater(len(self.tasks_files), 0, "No example tasks.md files found")

    def test_auto_issue_marker_format(self):
        import re

        pattern = re.compile(r"<!--\s*AUTO-ISSUE:\s*(.+?)\s*-->")
        for tasks_file in self.tasks_files:
            content = tasks_file.read_text(encoding="utf-8")
            markers = pattern.findall(content)
            for marker in markers:
                self.assertRegex(
                    marker,
                    r"\w+:\w+",
                    f"AUTO-ISSUE marker should contain labels like 'agent:go': {marker}",
                )

    def test_task_structure(self):
        import re

        task_pattern = re.compile(
            r"##\s+Task:\s+([^\r\n]+)\r?\n<!--\s*AUTO-ISSUE:\s*([^>]+?)\s*-->\s*\r?\n([\s\S]+?)(?=\n##\s+Task:|\n---\s*\n|$)"
        )

        for tasks_file in self.tasks_files:
            content = tasks_file.read_text(encoding="utf-8")
            matches = task_pattern.findall(content)
            for title, _, body in matches:
                self.assertIn("Description", body, f"Task '{title}' missing Description section")
                has_acceptance = "Acceptance Criteria" in body or "Acceptance criteria" in body
                self.assertTrue(has_acceptance, f"Task '{title}' missing Acceptance Criteria section")


class TestV2Workflows(unittest.TestCase):
    """Test that v2 automation workflows exist and are well-formed."""

    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.workflows_dir = repo_root / ".github" / "workflows"
        self.expected_workflows = {
            "verify.yml",
            "budget-telemetry.yml",
            "sdk-agent-service.yml",
            "sync-template-branches.yml",
        }

    def test_expected_v2_workflows_exist(self):
        for workflow_name in self.expected_workflows:
            workflow_path = self.workflows_dir / workflow_name
            self.assertTrue(workflow_path.exists(), f"{workflow_name} not found")

    def test_workflows_are_valid_yaml(self):
        for workflow_file in self.workflows_dir.glob("*.yml"):
            with self.subTest(workflow=workflow_file.name):
                content = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))
                self.assertIsInstance(content, dict, f"{workflow_file.name} should parse as YAML object")

    def test_verify_workflow_has_core_jobs(self):
        workflow_path = self.workflows_dir / "verify.yml"
        content = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        jobs = content.get("jobs", {})
        for job_name in ("validators", "smoke", "tests"):
            self.assertIn(job_name, jobs, f"verify.yml missing '{job_name}' job")

    def test_workflows_declare_permissions(self):
        for workflow_name in self.expected_workflows:
            workflow_path = self.workflows_dir / workflow_name
            content = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
            self.assertIn("permissions", content, f"{workflow_name} should declare permissions")


class TestIssueTemplates(unittest.TestCase):
    """Test issue templates that are part of v2 automation flow."""

    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.templates_dir = repo_root / ".github" / "ISSUE_TEMPLATE"

    def test_agent_task_template_exists(self):
        self.assertTrue((self.templates_dir / "agent_task.md").exists(), "agent_task.md not found")

    def test_agent_task_template_uses_agent_go_label(self):
        content = (self.templates_dir / "agent_task.md").read_text(encoding="utf-8")
        self.assertIn('labels: ["agent:go"]', content)


class TestLabelsDocumentation(unittest.TestCase):
    """Test the v2 labels documentation."""

    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.labels_doc = repo_root / "docs" / "operations" / "github-labels.md"
        self.content = self.labels_doc.read_text(encoding="utf-8")

    def test_labels_doc_exists(self):
        self.assertTrue(self.labels_doc.exists(), "docs/operations/github-labels.md not found")

    def test_required_v2_labels_are_documented(self):
        required_labels = ["agent:go", "agent:wait", "agent:local", "autonomy:override"]
        for label in required_labels:
            self.assertIn(f"`{label}`", self.content, f"{label} should be documented")

    def test_v2_label_count_is_documented(self):
        self.assertIn("uses **4 labels**", self.content)


if __name__ == "__main__":
    unittest.main()
