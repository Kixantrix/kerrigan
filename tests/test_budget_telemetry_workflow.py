#!/usr/bin/env python3
"""Tests for budget telemetry workflow configuration."""

import unittest
from pathlib import Path

import yaml


class TestBudgetTelemetryWorkflow(unittest.TestCase):
    """Validate budget telemetry workflow behavior and structure."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = self.repo_root / ".github" / "workflows" / "budget-telemetry.yml"

    def _get_trigger_key(self, content):
        return "on" if "on" in content else True

    def test_workflow_exists(self):
        self.assertTrue(self.workflow_path.exists(), "budget-telemetry.yml not found")

    def test_workflow_triggers_on_pull_request_events(self):
        workflow = yaml.safe_load(self.workflow_path.read_text(encoding="utf-8"))
        trigger_key = self._get_trigger_key(workflow)
        self.assertIn("pull_request", workflow[trigger_key])

    def test_workflow_has_configurable_threshold_defaults(self):
        workflow = yaml.safe_load(self.workflow_path.read_text(encoding="utf-8"))
        trigger_key = self._get_trigger_key(workflow)

        self.assertEqual(workflow["env"]["BUDGET_MINUTES_THRESHOLD"], "30")
        self.assertIn("workflow_dispatch", workflow[trigger_key])

        threshold_input = workflow[trigger_key]["workflow_dispatch"]["inputs"]["threshold_minutes"]
        self.assertEqual(str(threshold_input["default"]), "30")

    def test_workflow_collects_run_usage_and_job_breakdown(self):
        content = self.workflow_path.read_text(encoding="utf-8")
        self.assertIn("getWorkflowRunUsage", content)
        self.assertIn("listJobsForWorkflowRun", content)
        self.assertIn("Per-job breakdown", content)

    def test_workflow_uses_sticky_comment_actions(self):
        content = self.workflow_path.read_text(encoding="utf-8")
        self.assertIn("peter-evans/find-comment@v3", content)
        self.assertIn("peter-evans/create-or-update-comment@v4", content)
        self.assertIn("budget-telemetry-comment", content)

    def test_workflow_posts_budget_warning(self):
        content = self.workflow_path.read_text(encoding="utf-8")
        self.assertIn("Warning:", content)
        self.assertIn("exceed the threshold", content)


if __name__ == "__main__":
    unittest.main()
