#!/usr/bin/env python3
"""Integration tests for agent spec compliance workflow.

This test verifies that the workflow YAML is valid and the individual
compliance checks work correctly.
"""

import unittest
import yaml
from pathlib import Path


class TestAgentSpecComplianceWorkflow(unittest.TestCase):
    """Test the verify workflow for agent/profile compliance checks."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_root = Path(__file__).resolve().parents[1]
        self.workflow_path = self.repo_root / ".github" / "workflows" / "verify.yml"

    def test_workflow_file_exists(self):
        """Test that the workflow file exists."""
        self.assertTrue(
            self.workflow_path.exists(),
            "verify.yml workflow should exist"
        )

    def test_workflow_yaml_is_valid(self):
        """Test that the workflow YAML is valid."""
        try:
            with open(self.workflow_path, "r", encoding="utf-8") as f:
                workflow = yaml.safe_load(f)
            
            self.assertIsNotNone(workflow, "Workflow YAML should parse successfully")
            self.assertIn('name', workflow, "Workflow should have a name")
            # YAML parses 'on:' as boolean True, so check for True key
            self.assertTrue(
                'on' in workflow or True in workflow,
                "Workflow should have triggers (on: section)"
            )
            self.assertIn('jobs', workflow, "Workflow should have jobs")
        except yaml.YAMLError as e:
            self.fail(f"Workflow YAML is invalid: {e}")

    def test_workflow_has_required_jobs(self):
        """Test that the workflow has the required jobs."""
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            workflow = yaml.safe_load(f)
        
        jobs = workflow.get('jobs', {})
        
        # Check for validator job
        self.assertIn(
            'validators',
            jobs,
            "Workflow should have validators job"
        )
        
        # Check for tests job
        self.assertIn(
            'tests',
            jobs,
            "Workflow should have tests job"
        )

    def test_workflow_triggers_on_pr_events(self):
        """Test that the workflow triggers on pull request events."""
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            workflow = yaml.safe_load(f)
        
        # YAML parses 'on:' as boolean True
        on_config = workflow.get('on', workflow.get(True, {}))
        
        self.assertIn('pull_request', on_config, "Workflow should trigger on pull_request")
        
        pr_branches = on_config['pull_request'].get('branches', [])
        self.assertIn('main', pr_branches, "Workflow should trigger on pull requests to main")

    def test_workflow_triggers_on_relevant_paths(self):
        """Test that the workflow is not path-filtered (full PR verification)."""
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            workflow = yaml.safe_load(f)
        
        # YAML parses 'on:' as boolean True
        on_config = workflow.get('on', workflow.get(True, {}))
        pr_config = on_config.get('pull_request', {})
        self.assertNotIn('paths', pr_config, "Workflow should run for all pull request file changes")

    def test_spec_reference_job_uses_python(self):
        """Test that validators job uses Python."""
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            workflow = yaml.safe_load(f)
        
        job = workflow['jobs']['validators']
        steps = job.get('steps', [])
        
        # Check for Python setup step
        python_steps = [s for s in steps if 'Setup Python' in s.get('name', '')]
        self.assertEqual(len(python_steps), 1, "Job should have exactly one Python setup step")
        
        python_step = python_steps[0]
        self.assertEqual(
            python_step.get('uses', '').split('@')[0],
            'actions/setup-python',
            "Should use setup-python action"
        )

    def test_spec_reference_job_runs_check_command(self):
        """Test that validators job runs kerrigan check."""
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            workflow = yaml.safe_load(f)
        
        job = workflow['jobs']['validators']
        steps = job.get('steps', [])
        
        # Find the step that runs validators
        check_steps = [s for s in steps if 'Run validators' in s.get('name', '')]
        self.assertEqual(len(check_steps), 1, "Job should have validator run step")
        
        check_step = check_steps[0]
        run_command = check_step.get('run', '')
        
        self.assertIn(
            'kerrigan check',
            run_command,
            "Should run kerrigan check command"
        )


if __name__ == '__main__':
    unittest.main()
