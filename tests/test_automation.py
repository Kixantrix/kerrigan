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


class TestAutoTriageConfig(unittest.TestCase):
    """Test auto-triage configuration validation"""

    def setUp(self):
        """Load the reviewers config"""
        repo_root = Path(__file__).resolve().parent.parent
        config_path = repo_root / ".github" / "automation" / "reviewers.json"
        
        try:
            self.config = json.loads(config_path.read_text())
        except FileNotFoundError:
            self.fail(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON in {config_path}: {e}")

    def test_triage_mappings_exist(self):
        """Test that triage_mappings field exists"""
        self.assertIn("triage_mappings", self.config, "Missing triage_mappings field")

    def test_auto_triage_on_assign_is_bool(self):
        """Test that auto_triage_on_assign is a boolean"""
        self.assertIn("auto_triage_on_assign", self.config, "Missing auto_triage_on_assign field")
        self.assertIsInstance(self.config["auto_triage_on_assign"], bool)

    def test_comment_on_triage_is_bool(self):
        """Test that comment_on_triage is a boolean"""
        self.assertIn("comment_on_triage", self.config, "Missing comment_on_triage field")
        self.assertIsInstance(self.config["comment_on_triage"], bool)

    def test_triage_mappings_is_dict(self):
        """Test that triage_mappings is a dictionary"""
        self.assertIsInstance(self.config["triage_mappings"], dict)

    def test_triage_mappings_values_are_lists(self):
        """Test that all triage_mappings values are lists"""
        triage_mappings = self.config.get("triage_mappings", {})
        for user, labels in triage_mappings.items():
            if user.startswith("_"):  # Skip comment keys
                continue
            self.assertIsInstance(labels, list, f"Triage mapping for {user} is not a list")

    def test_triage_labels_are_valid_role_labels(self):
        """Test that triage mappings use valid role labels"""
        triage_mappings = self.config.get("triage_mappings", {})
        valid_role_labels = list(self.config["role_mappings"].keys())
        
        for user, labels in triage_mappings.items():
            if user.startswith("_"):  # Skip comment keys
                continue
            for label in labels:
                self.assertIn(label, valid_role_labels, 
                    f"Triage label '{label}' for user '{user}' is not a valid role label")

    def test_copilot_triage_configured(self):
        """Test that copilot user has triage configuration"""
        triage_mappings = self.config.get("triage_mappings", {})
        self.assertIn("copilot", triage_mappings, "copilot should have triage configuration")
        
        copilot_labels = triage_mappings["copilot"]
        self.assertGreater(len(copilot_labels), 0, "copilot should have at least one role label")


class TestAutoTriageWorkflow(unittest.TestCase):
    """Test auto-triage-on-assign workflow"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "auto-triage-on-assign.yml"

    def test_workflow_exists(self):
        """Test that auto-triage-on-assign workflow exists"""
        self.assertTrue(self.workflow_path.exists(), "auto-triage-on-assign.yml not found")

    def test_workflow_triggers_on_assigned(self):
        """Test that workflow triggers on issues assigned event"""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed, skipping YAML validation")
        
        content = yaml.safe_load(self.workflow_path.read_text())
        # 'on' is a YAML keyword and may be parsed as True, check for it
        trigger_key = "on" if "on" in content else True
        self.assertIn(trigger_key, content)
        self.assertIn("issues", content[trigger_key])
        self.assertIn("assigned", content[trigger_key]["issues"]["types"])

    def test_workflow_has_required_permissions(self):
        """Test that workflow has required permissions"""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed, skipping YAML validation")
        
        content = yaml.safe_load(self.workflow_path.read_text())
        job = content["jobs"]["auto_triage"]
        
        self.assertIn("permissions", job)
        self.assertEqual(job["permissions"]["issues"], "write")
        self.assertEqual(job["permissions"]["contents"], "read")


class TestSprintModeAutomation(unittest.TestCase):
    """Test sprint mode automation in agent-gates workflow"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"

    def test_workflow_exists(self):
        """Test that agent-gates workflow exists"""
        self.assertTrue(self.workflow_path.exists(), "agent-gates.yml not found")

    def test_workflow_checks_sprint_label(self):
        """Test that workflow checks for agent:sprint label"""
        content = self.workflow_path.read_text()
        self.assertIn("agent:sprint", content, "Workflow should check for agent:sprint label")

    def test_workflow_auto_applies_agent_go(self):
        """Test that workflow auto-applies agent:go label in sprint mode"""
        content = self.workflow_path.read_text()
        self.assertIn("agent:go", content, "Workflow should handle agent:go label")
        self.assertIn("addLabels", content, "Workflow should add labels")

    def test_workflow_handles_linked_issues(self):
        """Test that workflow detects linked issues from PR body"""
        content = self.workflow_path.read_text()
        # Check for common linking keywords
        linking_keywords = ["Fixes", "Closes", "Resolves", "close", "fix", "resolve"]
        found_keywords = sum(1 for keyword in linking_keywords if keyword in content)
        self.assertGreater(found_keywords, 0, "Workflow should detect linked issues")


class TestIssueGenerationWorkflow(unittest.TestCase):
    """Test auto-generate-issues workflow"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "auto-generate-issues.yml"

    def test_workflow_exists(self):
        """Test that auto-generate-issues workflow exists"""
        self.assertTrue(self.workflow_path.exists(), "auto-generate-issues.yml not found")

    def test_workflow_triggers_on_tasks_push(self):
        """Test that workflow triggers on push to tasks.md"""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed, skipping YAML validation")
        
        content = yaml.safe_load(self.workflow_path.read_text())
        # 'on' is a YAML keyword and may be parsed as True, check for it
        trigger_key = "on" if "on" in content else True
        self.assertIn(trigger_key, content)
        self.assertIn("push", content[trigger_key])
        self.assertIn("paths", content[trigger_key]["push"])
        
        paths = content[trigger_key]["push"]["paths"]
        self.assertTrue(any("tasks.md" in path for path in paths), 
            "Workflow should trigger on tasks.md changes")

    def test_workflow_has_manual_dispatch(self):
        """Test that workflow supports manual dispatch"""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed, skipping YAML validation")
        
        content = yaml.safe_load(self.workflow_path.read_text())
        # 'on' is a YAML keyword and may be parsed as True, check for it
        trigger_key = "on" if "on" in content else True
        self.assertIn("workflow_dispatch", content[trigger_key])

    def test_workflow_has_dry_run_option(self):
        """Test that workflow has dry run option"""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed, skipping YAML validation")
        
        content = yaml.safe_load(self.workflow_path.read_text())
        # 'on' is a YAML keyword and may be parsed as True, check for it
        trigger_key = "on" if "on" in content else True
        if "workflow_dispatch" in content[trigger_key] and "inputs" in content[trigger_key]["workflow_dispatch"]:
            inputs = content[trigger_key]["workflow_dispatch"]["inputs"]
            self.assertIn("dry_run", inputs, "Workflow should have dry_run input")

    def test_workflow_parses_auto_issue_markers(self):
        """Test that workflow logic parses AUTO-ISSUE markers"""
        content = self.workflow_path.read_text()
        self.assertIn("AUTO-ISSUE", content, "Workflow should parse AUTO-ISSUE markers")

    def test_workflow_checks_for_duplicates(self):
        """Test that workflow checks for duplicate issues"""
        content = self.workflow_path.read_text()
        self.assertIn("alreadyExists", content, "Workflow should check for duplicate issues")


class TestWorkflowIntegration(unittest.TestCase):
    """Test integration between different workflows"""

    def setUp(self):
        """Load all workflow files"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflows_dir = repo_root / ".github" / "workflows"

    def test_consistent_config_usage(self):
        """Test that all workflows use consistent config path"""
        config_path_pattern = ".github/automation/reviewers.json"
        
        workflow_files = [
            "auto-assign-issues.yml",
            "auto-assign-reviewers.yml",
            "auto-triage-on-assign.yml"
        ]
        
        for workflow_name in workflow_files:
            workflow_path = self.workflows_dir / workflow_name
            if workflow_path.exists():
                content = workflow_path.read_text()
                self.assertIn(config_path_pattern, content, 
                    f"{workflow_name} should use consistent config path")

    def test_all_workflows_have_permissions(self):
        """Test that all automation workflows declare required permissions"""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed, skipping YAML validation")
        
        automation_workflows = [
            "auto-assign-issues.yml",
            "auto-assign-reviewers.yml",
            "auto-triage-on-assign.yml",
            "auto-generate-issues.yml",
            "agent-gates.yml"
        ]
        
        for workflow_name in automation_workflows:
            workflow_path = self.workflows_dir / workflow_name
            if workflow_path.exists():
                with self.subTest(workflow=workflow_name):
                    content = yaml.safe_load(workflow_path.read_text())
                    # Check that at least one job has permissions
                    has_permissions = False
                    for job in content["jobs"].values():
                        if "permissions" in job:
                            has_permissions = True
                            break
                    self.assertTrue(has_permissions, 
                        f"{workflow_name} should declare permissions")

    def test_workflows_handle_config_errors(self):
        """Test that workflows have error handling for config loading"""
        workflow_files = [
            "auto-assign-issues.yml",
            "auto-assign-reviewers.yml",
            "auto-triage-on-assign.yml"
        ]
        
        for workflow_name in workflow_files:
            workflow_path = self.workflows_dir / workflow_name
            if workflow_path.exists():
                with self.subTest(workflow=workflow_name):
                    content = workflow_path.read_text()
                    # Check for error handling
                    self.assertIn("catch", content, 
                        f"{workflow_name} should have error handling")
                    self.assertIn("error", content.lower(), 
                        f"{workflow_name} should handle errors")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios"""

    def setUp(self):
        """Load configuration"""
        repo_root = Path(__file__).resolve().parent.parent
        config_path = repo_root / ".github" / "automation" / "reviewers.json"
        self.config = json.loads(config_path.read_text())

    def test_empty_role_mappings_handled(self):
        """Test that empty role mappings are valid"""
        # Empty arrays should be allowed to disable auto-assignment for specific roles
        for role, reviewers in self.config["role_mappings"].items():
            self.assertIsInstance(reviewers, list)
            # No requirement that lists be non-empty

    def test_team_mappings_format(self):
        """Test that team mappings follow team: prefix convention"""
        all_reviewers = []
        all_reviewers.extend(self.config.get("default_reviewers", []))
        for reviewers in self.config["role_mappings"].values():
            all_reviewers.extend(reviewers)
        
        for reviewer in all_reviewers:
            if "team" in reviewer.lower():
                # If it looks like a team, it should use team: prefix
                self.assertTrue(reviewer.startswith("team:"), 
                    f"Team mapping should use 'team:' prefix: {reviewer}")

    def test_no_duplicate_role_mappings(self):
        """Test that role mappings don't have duplicate entries"""
        for role, reviewers in self.config["role_mappings"].items():
            unique_reviewers = set(reviewers)
            self.assertEqual(len(reviewers), len(unique_reviewers), 
                f"Role {role} has duplicate reviewers")

    def test_config_has_usage_notes(self):
        """Test that config has helpful usage notes or comments"""
        # Config should be self-documenting
        config_str = json.dumps(self.config)
        has_documentation = "_comment" in self.config or "_usage_notes" in self.config
        self.assertTrue(has_documentation, 
            "Config should have usage notes or comments for maintainability")


if __name__ == "__main__":
    unittest.main()
