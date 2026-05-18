#!/usr/bin/env python3
"""Tests for budget telemetry workflow configuration."""

import unittest
from pathlib import Path

import yaml


class TestBudgetTelemetryWorkflow(unittest.TestCase):
    """Validate budget telemetry workflow behavior and structure."""

    EXPECTED_DEFAULT_THRESHOLD = "30"

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = self.repo_root / ".github" / "workflows" / "budget-telemetry.yml"

    def _get_trigger_key(self, content):
        # PyYAML can parse top-level `on:` as boolean True in GitHub workflow files.
        if "on" in content:
            return "on"
        if True in content:
            return True
        self.fail("Workflow should define an 'on' trigger block")

    def test_get_trigger_key_supports_yaml_boolean_on(self):
        self.assertEqual(self._get_trigger_key({"on": {}}), "on")
        self.assertEqual(self._get_trigger_key({True: {}}), True)

    def test_workflow_exists(self):
        self.assertTrue(self.workflow_path.exists(), "budget-telemetry.yml not found")

    def test_workflow_triggers_on_pull_request_events(self):
        workflow = yaml.safe_load(self.workflow_path.read_text(encoding="utf-8"))
        trigger_key = self._get_trigger_key(workflow)
        self.assertIn("pull_request", workflow[trigger_key])

    def test_workflow_has_configurable_threshold_defaults(self):
        workflow = yaml.safe_load(self.workflow_path.read_text(encoding="utf-8"))
        trigger_key = self._get_trigger_key(workflow)

        self.assertEqual(
            workflow["env"]["BUDGET_MINUTES_THRESHOLD"],
            self.EXPECTED_DEFAULT_THRESHOLD,
        )
        self.assertIn("workflow_dispatch", workflow[trigger_key])
        self.assertIn("threshold_minutes", workflow[trigger_key]["workflow_dispatch"]["inputs"])

    def test_workflow_uses_pr_branch_for_run_query(self):
        content = self.workflow_path.read_text(encoding="utf-8")
        self.assertIn("github.rest.pulls.get", content)
        self.assertIn("branch: pullRequest.data.head.ref", content)

    def test_workflow_collects_run_usage_and_job_breakdown(self):
        content = self.workflow_path.read_text(encoding="utf-8")
        self.assertIn("getWorkflowRunUsage", content)
        self.assertIn("listJobsForWorkflowRun", content)
        self.assertIn("Per-job breakdown", content)

    def test_workflow_uses_sticky_comment_actions(self):
        import re
        content = self.workflow_path.read_text(encoding="utf-8")
        # The repo convention pins third-party Actions to a full 40-hex commit SHA
        # with a # vN comment, e.g. peter-evans/find-comment@<sha>  # v3
        sha_or_pin = re.compile(r"peter-evans/find-comment@[0-9a-f]{40}")
        self.assertRegex(content, sha_or_pin,
                         "peter-evans/find-comment should be pinned to a full commit SHA")
        sha_or_pin2 = re.compile(r"peter-evans/create-or-update-comment@[0-9a-f]{40}")
        self.assertRegex(content, sha_or_pin2,
                         "peter-evans/create-or-update-comment should be pinned to a full commit SHA")
        self.assertIn("budget-telemetry-comment", content)

    def test_workflow_posts_budget_warning(self):
        content = self.workflow_path.read_text(encoding="utf-8")
        self.assertIn("Warning:", content)
        self.assertIn("exceed the threshold", content)


if __name__ == "__main__":
    unittest.main()
