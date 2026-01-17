#!/usr/bin/env python3
"""Integration tests for agent spec compliance workflow.

This test verifies that the workflow YAML is valid and the individual
compliance checks work correctly.
"""

import unittest
import yaml
from pathlib import Path


class TestAgentSpecComplianceWorkflow(unittest.TestCase):
    """Test the agent spec compliance workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_root = Path(__file__).resolve().parents[1]
        self.workflow_path = self.repo_root / ".github" / "workflows" / "agent-spec-compliance.yml"

    def test_workflow_file_exists(self):
        """Test that the workflow file exists."""
        self.assertTrue(
            self.workflow_path.exists(),
            "agent-spec-compliance.yml workflow should exist"
        )

    def test_workflow_yaml_is_valid(self):
        """Test that the workflow YAML is valid."""
        try:
            with open(self.workflow_path, 'r') as f:
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
        with open(self.workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        jobs = workflow.get('jobs', {})
        
        # Check for spec reference validation job
        self.assertIn(
            'check-spec-references',
            jobs,
            "Workflow should have check-spec-references job"
        )
        
        # Check for agent PR compliance job
        self.assertIn(
            'check-agent-pr-compliance',
            jobs,
            "Workflow should have check-agent-pr-compliance job"
        )

    def test_workflow_triggers_on_pr_events(self):
        """Test that the workflow triggers on pull request events."""
        with open(self.workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # YAML parses 'on:' as boolean True
        on_config = workflow.get('on', workflow.get(True, {}))
        
        self.assertIn('pull_request', on_config, "Workflow should trigger on pull_request")
        
        pr_types = on_config['pull_request'].get('types', [])
        expected_types = ['opened', 'synchronize', 'reopened', 'labeled', 'unlabeled']
        
        for event_type in expected_types:
            self.assertIn(
                event_type,
                pr_types,
                f"Workflow should trigger on pull_request.{event_type}"
            )

    def test_workflow_triggers_on_relevant_paths(self):
        """Test that the workflow triggers on relevant file changes."""
        with open(self.workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # YAML parses 'on:' as boolean True
        on_config = workflow.get('on', workflow.get(True, {}))
        pr_config = on_config.get('pull_request', {})
        paths = pr_config.get('paths', [])
        
        # Should trigger on agent prompt changes
        self.assertIn(
            '.github/agents/**',
            paths,
            "Workflow should trigger on .github/agents/ changes"
        )
        
        # Should trigger on agent spec changes
        self.assertIn(
            'specs/kerrigan/agents/**',
            paths,
            "Workflow should trigger on specs/kerrigan/agents/ changes"
        )
        
        # Should trigger on agent_audit.py changes
        self.assertIn(
            'tools/agent_audit.py',
            paths,
            "Workflow should trigger on agent_audit.py changes"
        )

    def test_spec_reference_job_uses_python(self):
        """Test that spec reference job uses Python."""
        with open(self.workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        job = workflow['jobs']['check-spec-references']
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
        """Test that spec reference job runs the check-spec-references command."""
        with open(self.workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        job = workflow['jobs']['check-spec-references']
        steps = job.get('steps', [])
        
        # Find the step that runs the check
        check_steps = [s for s in steps if 'Check spec references' in s.get('name', '')]
        self.assertEqual(len(check_steps), 1, "Job should have spec reference check step")
        
        check_step = check_steps[0]
        run_command = check_step.get('run', '')
        
        self.assertIn(
            'python tools/agent_audit.py check-spec-references',
            run_command,
            "Should run check-spec-references command"
        )

    def test_compliance_job_checks_agent_signature(self):
        """Test that compliance job checks for agent signature."""
        with open(self.workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        job = workflow['jobs']['check-agent-pr-compliance']
        steps = job.get('steps', [])
        
        # Find the agent signature check step
        signature_steps = [s for s in steps if 'agent signature' in s.get('name', '').lower()]
        self.assertGreaterEqual(
            len(signature_steps),
            1,
            "Job should have agent signature check step"
        )

    def test_compliance_job_validates_spec_compliance(self):
        """Test that compliance job validates spec compliance."""
        with open(self.workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        job = workflow['jobs']['check-agent-pr-compliance']
        steps = job.get('steps', [])
        
        # Find the compliance validation step
        compliance_steps = [s for s in steps if 'spec compliance' in s.get('name', '').lower()]
        self.assertEqual(
            len(compliance_steps),
            1,
            "Job should have spec compliance validation step"
        )
        
        compliance_step = compliance_steps[0]
        run_command = compliance_step.get('run', '')
        
        self.assertIn(
            'python tools/agent_audit.py validate-compliance',
            run_command,
            "Should run validate-compliance command"
        )


if __name__ == '__main__':
    unittest.main()
