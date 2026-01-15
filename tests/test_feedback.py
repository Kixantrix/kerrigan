"""
Tests for agent feedback system validation.

This module validates that the feedback backchannel system is properly configured
and that feedback files follow the required structure.
"""

import unittest
from pathlib import Path
import yaml
import re


class TestFeedbackStructure(unittest.TestCase):
    """Test suite for feedback system structure and configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent
        self.feedback_dir = self.repo_root / "feedback"
        self.agent_feedback_dir = self.feedback_dir / "agent-feedback"
        self.processed_dir = self.feedback_dir / "processed"

    def test_feedback_directories_exist(self):
        """Test that required feedback directories exist"""
        self.assertTrue(self.feedback_dir.exists(),
                       "feedback/ directory should exist")
        self.assertTrue(self.agent_feedback_dir.exists(),
                       "feedback/agent-feedback/ directory should exist")
        self.assertTrue(self.processed_dir.exists(),
                       "feedback/processed/ directory should exist")

    def test_template_exists(self):
        """Test that feedback template exists"""
        template = self.agent_feedback_dir / "TEMPLATE.yaml"
        self.assertTrue(template.exists(),
                       "feedback/agent-feedback/TEMPLATE.yaml should exist")

    def test_readme_files_exist(self):
        """Test that README files exist in feedback directories"""
        agent_readme = self.agent_feedback_dir / "README.md"
        processed_readme = self.processed_dir / "README.md"
        
        self.assertTrue(agent_readme.exists(),
                       "feedback/agent-feedback/README.md should exist")
        self.assertTrue(processed_readme.exists(),
                       "feedback/processed/README.md should exist")

    def test_feedback_spec_exists(self):
        """Test that feedback specification document exists"""
        spec = self.repo_root / "specs" / "kerrigan" / "080-agent-feedback.md"
        self.assertTrue(spec.exists(),
                       "specs/kerrigan/080-agent-feedback.md should exist")

    def test_feedback_playbook_exists(self):
        """Test that feedback review playbook exists"""
        playbook = self.repo_root / "playbooks" / "feedback-review.md"
        self.assertTrue(playbook.exists(),
                       "playbooks/feedback-review.md should exist")


class TestFeedbackTemplate(unittest.TestCase):
    """Test suite for feedback template validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent
        self.template_path = self.repo_root / "feedback" / "agent-feedback" / "TEMPLATE.yaml"

    def test_template_contains_required_fields(self):
        """Test that template documents all required fields"""
        with open(self.template_path, 'r') as f:
            content = f.read()

        required_fields = [
            "timestamp",
            "issue_number",
            "agent_role",
            "category",
            "severity",
            "title",
            "description"
        ]

        for field in required_fields:
            self.assertIn(field, content,
                         f"Template should document required field: {field}")

    def test_template_documents_categories(self):
        """Test that template documents all feedback categories"""
        with open(self.template_path, 'r') as f:
            content = f.read()

        categories = [
            "prompt_clarity",
            "missing_information",
            "artifact_conflict",
            "tool_limitation",
            "quality_bar",
            "workflow_friction",
            "success_pattern"
        ]

        for category in categories:
            self.assertIn(category, content,
                         f"Template should document category: {category}")

    def test_template_documents_severities(self):
        """Test that template documents all severity levels"""
        with open(self.template_path, 'r') as f:
            content = f.read()

        severities = ["low", "medium", "high"]

        for severity in severities:
            self.assertIn(severity, content,
                         f"Template should document severity: {severity}")

    def test_template_documents_statuses(self):
        """Test that template documents all status values"""
        with open(self.template_path, 'r') as f:
            content = f.read()

        statuses = ["new", "reviewed", "implemented", "wont_fix"]

        for status in statuses:
            self.assertIn(status, content,
                         f"Template should document status: {status}")


class TestFeedbackFiles(unittest.TestCase):
    """Test suite for validating feedback YAML files"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent
        self.agent_feedback_dir = self.repo_root / "feedback" / "agent-feedback"
        self.processed_dir = self.repo_root / "feedback" / "processed"
        
        # Define valid values for validation
        self.valid_roles = ["spec", "architect", "swe", "testing", "deployment", "debugging", "security", "kerrigan"]
        self.valid_categories = ["prompt_clarity", "missing_information", "artifact_conflict", 
                                "tool_limitation", "quality_bar", "workflow_friction", "success_pattern"]
        self.valid_severities = ["low", "medium", "high"]
        self.valid_statuses = ["new", "reviewed", "implemented", "wont_fix"]

    def get_feedback_files(self, directory):
        """Get all YAML feedback files from directory (excluding template)"""
        if not directory.exists():
            return []
        
        yaml_files = []
        for file in directory.glob("*.yaml"):
            if file.name != "TEMPLATE.yaml":
                yaml_files.append(file)
        return yaml_files

    def test_feedback_files_are_valid_yaml(self):
        """Test that all feedback files are valid YAML"""
        all_files = (self.get_feedback_files(self.agent_feedback_dir) + 
                    self.get_feedback_files(self.processed_dir))
        
        for feedback_file in all_files:
            with self.subTest(file=feedback_file.name):
                with open(feedback_file, 'r') as f:
                    try:
                        yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        self.fail(f"Invalid YAML in {feedback_file.name}: {e}")

    def test_feedback_files_have_required_fields(self):
        """Test that feedback files contain all required fields"""
        all_files = (self.get_feedback_files(self.agent_feedback_dir) + 
                    self.get_feedback_files(self.processed_dir))
        
        required_fields = ["timestamp", "issue_number", "agent_role", 
                          "category", "severity", "title", "description"]

        for feedback_file in all_files:
            with self.subTest(file=feedback_file.name):
                with open(feedback_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                for field in required_fields:
                    self.assertIn(field, data,
                                f"{feedback_file.name} should have field: {field}")

    def test_feedback_files_have_valid_roles(self):
        """Test that feedback files use valid agent roles"""
        all_files = (self.get_feedback_files(self.agent_feedback_dir) + 
                    self.get_feedback_files(self.processed_dir))
        
        for feedback_file in all_files:
            with self.subTest(file=feedback_file.name):
                with open(feedback_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                if "agent_role" in data:
                    self.assertIn(data["agent_role"], self.valid_roles,
                                f"{feedback_file.name} has invalid agent_role: {data['agent_role']}")

    def test_feedback_files_have_valid_categories(self):
        """Test that feedback files use valid categories"""
        all_files = (self.get_feedback_files(self.agent_feedback_dir) + 
                    self.get_feedback_files(self.processed_dir))
        
        for feedback_file in all_files:
            with self.subTest(file=feedback_file.name):
                with open(feedback_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                if "category" in data:
                    self.assertIn(data["category"], self.valid_categories,
                                f"{feedback_file.name} has invalid category: {data['category']}")

    def test_feedback_files_have_valid_severities(self):
        """Test that feedback files use valid severity levels"""
        all_files = (self.get_feedback_files(self.agent_feedback_dir) + 
                    self.get_feedback_files(self.processed_dir))
        
        for feedback_file in all_files:
            with self.subTest(file=feedback_file.name):
                with open(feedback_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                if "severity" in data:
                    self.assertIn(data["severity"], self.valid_severities,
                                f"{feedback_file.name} has invalid severity: {data['severity']}")

    def test_processed_files_have_status(self):
        """Test that processed feedback files have status field"""
        processed_files = self.get_feedback_files(self.processed_dir)
        
        for feedback_file in processed_files:
            with self.subTest(file=feedback_file.name):
                with open(feedback_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                self.assertIn("status", data,
                            f"Processed file {feedback_file.name} should have status field")
                self.assertIn(data["status"], self.valid_statuses,
                            f"{feedback_file.name} has invalid status: {data.get('status')}")

    def test_feedback_filename_format(self):
        """Test that feedback files follow naming convention"""
        all_files = (self.get_feedback_files(self.agent_feedback_dir) + 
                    self.get_feedback_files(self.processed_dir))
        
        # Expected format: YYYY-MM-DD-<issue-number>-<short-slug>.yaml
        # Slug should start and end with word character, no consecutive dashes
        pattern = re.compile(r'^\d{4}-\d{2}-\d{2}-\d+-[\w][\w-]*[\w]\.yaml$')
        
        for feedback_file in all_files:
            with self.subTest(file=feedback_file.name):
                self.assertIsNotNone(pattern.match(feedback_file.name),
                                   f"{feedback_file.name} doesn't follow naming convention: "
                                   f"YYYY-MM-DD-<issue-number>-<short-slug>.yaml")


class TestAgentPromptFeedbackSections(unittest.TestCase):
    """Test suite for validating that agent prompts mention feedback mechanism"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent
        self.agents_dir = self.repo_root / ".github" / "agents"

    def test_agent_prompts_mention_feedback(self):
        """Test that agent role prompts mention the feedback mechanism"""
        role_prompts = list(self.agents_dir.glob("role.*.md"))
        
        self.assertGreater(len(role_prompts), 0, 
                          "Should find role prompt files")

        for prompt_file in role_prompts:
            with self.subTest(file=prompt_file.name):
                with open(prompt_file, 'r') as f:
                    content = f.read()
                
                # Check for feedback mention (case-insensitive)
                self.assertIn("feedback", content.lower(),
                            f"{prompt_file.name} should mention feedback mechanism")
                # Check for Agent Feedback section (case-sensitive)
                self.assertIn("Agent Feedback", content,
                            f"{prompt_file.name} should have 'Agent Feedback' section")

    def test_kerrigan_prompt_mentions_feedback_processing(self):
        """Test that Kerrigan prompt mentions feedback processing responsibility"""
        kerrigan_prompt = self.agents_dir / "kerrigan.swarm-shaper.md"
        
        with open(kerrigan_prompt, 'r') as f:
            content = f.read().lower()
        
        self.assertIn("feedback", content,
                     "Kerrigan prompt should mention feedback")
        self.assertIn("feedback/agent-feedback", content,
                     "Kerrigan prompt should mention feedback directory")


class TestDocumentationReferences(unittest.TestCase):
    """Test suite for validating that key documents reference feedback system"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_readme_mentions_feedback(self):
        """Test that README mentions agent feedback"""
        readme = self.repo_root / "README.md"
        
        with open(readme, 'r') as f:
            content = f.read()
        
        self.assertIn("080-agent-feedback.md", content,
                     "README should link to feedback specification")

    def test_agents_readme_mentions_feedback(self):
        """Test that agents README mentions feedback"""
        agents_readme = self.repo_root / ".github" / "agents" / "README.md"
        
        with open(agents_readme, 'r') as f:
            content = f.read()
        
        self.assertIn("Agent Feedback", content,
                     "Agents README should have Agent Feedback section")
        self.assertIn("080-agent-feedback.md", content,
                     "Agents README should link to feedback specification")

    def test_handoffs_playbook_mentions_feedback(self):
        """Test that handoffs playbook mentions feedback"""
        handoffs = self.repo_root / "playbooks" / "handoffs.md"
        
        with open(handoffs, 'r') as f:
            content = f.read()
        
        self.assertIn("feedback", content.lower(),
                     "Handoffs playbook should mention feedback")
        self.assertIn("080-agent-feedback.md", content,
                     "Handoffs playbook should link to feedback specification")


if __name__ == "__main__":
    unittest.main()
