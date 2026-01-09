#!/usr/bin/env python3
"""Tests for automation configuration validation"""

import json
import unittest
from pathlib import Path


class TestReviewersConfig(unittest.TestCase):
    """Test reviewers.json configuration validation"""

    def setUp(self):
        """Load the reviewers config"""
        # Get to repo root from tests/test_automation.py
        repo_root = Path(__file__).resolve().parent.parent
        config_path = repo_root / ".github" / "automation" / "reviewers.json"
        
        try:
            self.config = json.loads(config_path.read_text())
        except FileNotFoundError:
            self.fail(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON in {config_path}: {e}")

    def test_config_has_required_fields(self):
        """Test that config has all required fields"""
        required_fields = ["role_mappings", "default_reviewers", "auto_assign_on_label", "comment_on_assignment"]
        for field in required_fields:
            self.assertIn(field, self.config, f"Missing required field: {field}")

    def test_role_mappings_is_dict(self):
        """Test that role_mappings is a dictionary"""
        self.assertIsInstance(self.config["role_mappings"], dict)

    def test_default_reviewers_is_list(self):
        """Test that default_reviewers is a list"""
        self.assertIsInstance(self.config["default_reviewers"], list)

    def test_auto_assign_on_label_is_bool(self):
        """Test that auto_assign_on_label is a boolean"""
        self.assertIsInstance(self.config["auto_assign_on_label"], bool)

    def test_comment_on_assignment_is_bool(self):
        """Test that comment_on_assignment is a boolean"""
        self.assertIsInstance(self.config["comment_on_assignment"], bool)

    def test_role_mappings_values_are_lists(self):
        """Test that all role_mappings values are lists"""
        for role, reviewers in self.config["role_mappings"].items():
            self.assertIsInstance(reviewers, list, f"Role {role} mapping is not a list")

    def test_expected_roles_present(self):
        """Test that expected roles are present in mappings"""
        expected_roles = ["role:spec", "role:architect", "role:swe", "role:testing", "role:security", "role:deployment"]
        for role in expected_roles:
            self.assertIn(role, self.config["role_mappings"], f"Missing expected role: {role}")

    def test_reviewer_names_are_strings(self):
        """Test that all reviewer names are strings"""
        for role, reviewers in self.config["role_mappings"].items():
            for reviewer in reviewers:
                self.assertIsInstance(reviewer, str, f"Reviewer in {role} is not a string: {reviewer}")

    def test_team_prefix_format(self):
        """Test that team mappings use team: prefix correctly"""
        for role, reviewers in self.config["role_mappings"].items():
            for reviewer in reviewers:
                if reviewer.startswith("team:"):
                    # Should have something after team:
                    self.assertGreater(len(reviewer), 5, f"Invalid team mapping in {role}: {reviewer}")


class TestTasksFormat(unittest.TestCase):
    """Test tasks.md format for AUTO-ISSUE feature"""

    def setUp(self):
        """Find tasks.md files in examples"""
        repo_root = Path(__file__).resolve().parent.parent
        self.tasks_files = list(repo_root.glob("examples/*/tasks.md"))

    def test_example_tasks_exist(self):
        """Test that example tasks.md files exist"""
        self.assertGreater(len(self.tasks_files), 0, "No example tasks.md files found")

    def test_auto_issue_marker_format(self):
        """Test that AUTO-ISSUE markers follow expected format"""
        import re
        pattern = re.compile(r'<!--\s*AUTO-ISSUE:\s*(.+?)\s*-->')
        
        for tasks_file in self.tasks_files:
            content = tasks_file.read_text()
            markers = pattern.findall(content)
            
            for marker in markers:
                # Should contain at least one label-like element
                self.assertRegex(marker, r'\w+:\w+', 
                    f"AUTO-ISSUE marker should contain labels like 'role:swe': {marker}")

    def test_task_structure(self):
        """Test that tasks with AUTO-ISSUE have required structure"""
        import re
        
        for tasks_file in self.tasks_files:
            content = tasks_file.read_text()
            
            # Find all tasks with AUTO-ISSUE markers
            # Matches task body until next task header, separator, or end of file
            task_pattern = re.compile(
                r'##\s+Task:\s+([^\r\n]+)\r?\n<!--\s*AUTO-ISSUE:\s*([^>]+?)\s*-->\s*\r?\n([\s\S]+?)(?=\n##\s+Task:|\n---\s*\n|$)'
            )
            
            matches = task_pattern.findall(content)
            
            for title, config, body in matches:
                # Should have a description
                self.assertIn("Description", body, 
                    f"Task '{title}' missing Description section")
                
                # Should have acceptance criteria (allow either "Criteria" or "Acceptance Criteria")
                has_acceptance = "Acceptance Criteria" in body or "Acceptance criteria" in body
                self.assertTrue(has_acceptance,
                    f"Task '{title}' missing Acceptance Criteria section")


class TestWorkflowsExist(unittest.TestCase):
    """Test that expected automation workflows exist"""

    def setUp(self):
        """Set up workflows directory path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflows_dir = repo_root / ".github" / "workflows"

    def test_auto_assign_reviewers_exists(self):
        """Test that auto-assign-reviewers workflow exists"""
        workflow_path = self.workflows_dir / "auto-assign-reviewers.yml"
        self.assertTrue(workflow_path.exists(), "auto-assign-reviewers.yml not found")

    def test_auto_assign_issues_exists(self):
        """Test that auto-assign-issues workflow exists"""
        workflow_path = self.workflows_dir / "auto-assign-issues.yml"
        self.assertTrue(workflow_path.exists(), "auto-assign-issues.yml not found")

    def test_auto_generate_issues_exists(self):
        """Test that auto-generate-issues workflow exists"""
        workflow_path = self.workflows_dir / "auto-generate-issues.yml"
        self.assertTrue(workflow_path.exists(), "auto-generate-issues.yml not found")

    def test_agent_gates_exists(self):
        """Test that agent-gates workflow exists"""
        workflow_path = self.workflows_dir / "agent-gates.yml"
        self.assertTrue(workflow_path.exists(), "agent-gates.yml not found")

    def test_workflows_are_valid_yaml(self):
        """Test that all workflow files are valid YAML"""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed, skipping YAML validation")
        
        for workflow_file in self.workflows_dir.glob("*.yml"):
            with self.subTest(workflow=workflow_file.name):
                content = workflow_file.read_text()
                try:
                    yaml.safe_load(content)
                except yaml.YAMLError as e:
                    self.fail(f"Invalid YAML in {workflow_file.name}: {e}")


class TestIssueTemplates(unittest.TestCase):
    """Test that agent role issue templates exist"""

    def setUp(self):
        """Set up issue templates directory path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.templates_dir = repo_root / ".github" / "ISSUE_TEMPLATE"

    def test_agent_task_templates_exist(self):
        """Test that agent task templates exist for key roles"""
        expected_templates = [
            "agent_task_spec.md",
            "agent_task_swe.md",
            "agent_task_testing.md",
            "agent_task_architect.md"
        ]
        
        for template_name in expected_templates:
            template_path = self.templates_dir / template_name
            self.assertTrue(template_path.exists(), f"Missing template: {template_name}")

    def test_templates_have_frontmatter(self):
        """Test that templates have valid frontmatter"""
        import re
        
        for template_file in self.templates_dir.glob("agent_task_*.md"):
            content = template_file.read_text()
            
            # Check for YAML frontmatter
            self.assertTrue(content.startswith("---"), 
                f"{template_file.name} missing frontmatter")
            
            # Check for required fields in frontmatter
            self.assertIn("name:", content, f"{template_file.name} missing 'name' in frontmatter")
            self.assertIn("labels:", content, f"{template_file.name} missing 'labels' in frontmatter")

    def test_templates_include_role_label(self):
        """Test that templates include appropriate role label"""
        role_label_map = {
            "agent_task_spec.md": "role:spec",
            "agent_task_swe.md": "role:swe",
            "agent_task_testing.md": "role:testing",
            "agent_task_architect.md": "role:architect"
        }
        
        for template_name, expected_label in role_label_map.items():
            template_path = self.templates_dir / template_name
            if template_path.exists():
                content = template_path.read_text()
                self.assertIn(expected_label, content, 
                    f"{template_name} missing {expected_label} label")


if __name__ == "__main__":
    unittest.main()
