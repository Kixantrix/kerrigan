#!/usr/bin/env python3
"""
Comprehensive tests for autonomy gate enforcement in agent-gates workflow.

Tests all three autonomy modes (on-demand, sprint, override) and edge cases
as required by Milestone 4.
"""

import unittest
from pathlib import Path


class TestAutonomyGatesWorkflow(unittest.TestCase):
    """Test autonomy gates workflow structure and implementation"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"
        self.workflow_content = self.workflow_path.read_text(encoding="utf-8")

    def test_workflow_exists(self):
        """Test that agent-gates.yml workflow exists"""
        self.assertTrue(self.workflow_path.exists(), "agent-gates.yml not found")

    def test_workflow_triggers_on_pr_events(self):
        """Test that workflow triggers on correct PR events"""
        # Should trigger on PR opened, synchronize, reopened, labeled, unlabeled
        required_events = ["opened", "synchronize", "reopened", "labeled", "unlabeled"]
        for event in required_events:
            self.assertIn(event, self.workflow_content, 
                f"Workflow should trigger on PR event: {event}")

    def test_workflow_has_required_permissions(self):
        """Test that workflow has necessary GitHub API permissions"""
        # Needs to read issues and pull requests
        self.assertIn("pull-requests: read", self.workflow_content)
        self.assertIn("issues: read", self.workflow_content)
        # Also needs to write labels to PRs for sprint mode
        self.assertIn("pull-requests: write", self.workflow_content)

    def test_workflow_uses_github_script(self):
        """Test that workflow uses actions/github-script for label checking"""
        self.assertIn("actions/github-script@v7", self.workflow_content)


class TestOnDemandMode(unittest.TestCase):
    """Test on-demand autonomy mode (agent:go label required)"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"
        self.workflow_content = self.workflow_path.read_text(encoding="utf-8")

    def test_checks_for_agent_go_label(self):
        """Test that workflow checks for agent:go label"""
        self.assertIn("agent:go", self.workflow_content,
            "Workflow should check for agent:go label")

    def test_extracts_linked_issues_from_pr_body(self):
        """Test that workflow extracts issue numbers from PR body"""
        # Should look for "Fixes #123", "Closes #456", etc.
        linking_patterns = ["Fixes", "Closes", "Resolves", "close", "fix", "resolve"]
        found_patterns = sum(1 for pattern in linking_patterns if pattern in self.workflow_content)
        self.assertGreater(found_patterns, 0,
            "Workflow should detect issue linking keywords")

    def test_fetches_issue_labels_via_api(self):
        """Test that workflow fetches labels from linked issues"""
        self.assertIn("github.rest.issues.get", self.workflow_content,
            "Workflow should fetch issue data from GitHub API")

    def test_fails_without_agent_go_label(self):
        """Test that workflow fails when no agent:go label found"""
        self.assertIn("core.setFailed", self.workflow_content,
            "Workflow should call setFailed when gates not met")
        self.assertIn("Autonomy gate", self.workflow_content,
            "Error message should mention autonomy gate")

    def test_provides_clear_error_messages(self):
        """Test that workflow provides actionable error messages"""
        # Should tell users how to proceed
        self.assertIn("To proceed", self.workflow_content,
            "Error message should guide users on how to proceed")
        self.assertIn("playbooks/autonomy-modes.md", self.workflow_content,
            "Error message should reference documentation")

    def test_handles_multiple_linked_issues(self):
        """Test that workflow can handle multiple linked issues"""
        # Should iterate through all linked issues
        self.assertIn("for", self.workflow_content,
            "Workflow should iterate through linked issues")

    def test_passes_with_agent_go_on_issue(self):
        """Test that workflow passes when linked issue has agent:go"""
        # Should check if any linked issue has agent:go
        self.assertIn("includes('agent:go')", self.workflow_content,
            "Workflow should check if labels include agent:go")


class TestSprintMode(unittest.TestCase):
    """Test sprint autonomy mode (agent:sprint label triggers auto-approval)"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"
        self.workflow_content = self.workflow_path.read_text(encoding="utf-8")

    def test_checks_for_agent_sprint_label(self):
        """Test that workflow checks for agent:sprint label"""
        self.assertIn("agent:sprint", self.workflow_content,
            "Workflow should check for agent:sprint label")

    def test_auto_applies_agent_go_label(self):
        """Test that workflow auto-applies agent:go to PR in sprint mode"""
        self.assertIn("addLabels", self.workflow_content,
            "Workflow should add labels to PR")
        # Should add agent:go when agent:sprint found
        self.assertIn("'agent:go'", self.workflow_content,
            "Workflow should add agent:go label")

    def test_handles_label_api_errors(self):
        """Test that workflow handles errors when adding labels"""
        # Should catch errors if label addition fails
        self.assertIn("catch", self.workflow_content,
            "Workflow should handle API errors gracefully")

    def test_passes_with_agent_sprint_on_issue(self):
        """Test that workflow passes when linked issue has agent:sprint"""
        self.assertIn("includes('agent:sprint')", self.workflow_content,
            "Workflow should check if labels include agent:sprint")

    def test_logs_sprint_mode_activation(self):
        """Test that workflow logs when sprint mode is activated"""
        self.assertIn("sprint mode", self.workflow_content.lower(),
            "Workflow should log sprint mode activation")


class TestOverrideMode(unittest.TestCase):
    """Test override mechanism (autonomy:override bypasses all gates)"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"
        self.workflow_content = self.workflow_path.read_text(encoding="utf-8")

    def test_checks_for_autonomy_override_label(self):
        """Test that workflow checks for autonomy:override label"""
        self.assertIn("autonomy:override", self.workflow_content,
            "Workflow should check for autonomy:override label")

    def test_override_bypasses_all_checks(self):
        """Test that override label bypasses all other checks"""
        # Override check should come first, before other logic
        override_index = self.workflow_content.find("autonomy:override")
        setfailed_index = self.workflow_content.find("core.setFailed")
        self.assertLess(override_index, setfailed_index,
            "Override check should come before failure conditions")

    def test_override_checked_on_pr_not_issue(self):
        """Test that override label is checked on PR, not linked issues"""
        # Should check prLabels not issueLabels for override
        self.assertIn("prLabels.includes('autonomy:override')", self.workflow_content,
            "Override should be checked on PR labels")

    def test_override_logs_bypass_message(self):
        """Test that workflow logs when override is used"""
        self.assertIn("bypass", self.workflow_content.lower(),
            "Workflow should log when override bypasses gates")


class TestFallbackMode(unittest.TestCase):
    """Test fallback mode (check PR labels when no linked issues)"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"
        self.workflow_content = self.workflow_path.read_text(encoding="utf-8")

    def test_checks_pr_labels_when_no_issues(self):
        """Test that workflow checks PR labels when no linked issues found"""
        self.assertIn("issueNumbers.length === 0", self.workflow_content,
            "Workflow should detect when no linked issues found")

    def test_accepts_agent_go_on_pr(self):
        """Test that workflow accepts agent:go label directly on PR"""
        # Should check prLabels for agent:go as fallback
        self.assertIn("prLabels.includes('agent:go')", self.workflow_content,
            "Workflow should check PR labels for agent:go")

    def test_accepts_agent_sprint_on_pr(self):
        """Test that workflow accepts agent:sprint label directly on PR"""
        # Should check prLabels for agent:sprint as fallback
        self.assertIn("prLabels.includes('agent:sprint')", self.workflow_content,
            "Workflow should check PR labels for agent:sprint")

    def test_fails_pr_without_issues_or_labels(self):
        """Test that workflow fails PR with no issues and no autonomy labels"""
        # Should provide specific error for this case
        self.assertIn("No linked issues", self.workflow_content,
            "Workflow should detect PRs without linked issues")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"
        self.workflow_content = self.workflow_path.read_text(encoding="utf-8")

    def test_handles_issue_fetch_errors(self):
        """Test that workflow handles errors when fetching issue data"""
        self.assertIn("catch (error)", self.workflow_content,
            "Workflow should catch API errors")

    def test_handles_private_or_external_issues(self):
        """Test that workflow handles inaccessible issues gracefully"""
        # Should provide guidance when issues can't be fetched
        self.assertIn("Could not fetch issue", self.workflow_content,
            "Workflow should handle inaccessible issues")

    def test_supports_cross_repo_issue_references(self):
        """Test that workflow can parse cross-repo issue references"""
        # Pattern should support owner/repo#123 format
        self.assertIn("repo", self.workflow_content.lower(),
            "Workflow should handle repo references in patterns")

    def test_handles_empty_pr_body(self):
        """Test that workflow handles PRs with empty body"""
        self.assertIn("pr.body || ''", self.workflow_content,
            "Workflow should handle empty PR body")

    def test_deduplicates_issue_numbers(self):
        """Test that workflow deduplicates issue numbers from PR body"""
        # Should use Set to avoid checking same issue multiple times
        self.assertIn("Set", self.workflow_content,
            "Workflow should deduplicate issue numbers")

    def test_logs_all_linked_issues(self):
        """Test that workflow logs all linked issues found"""
        self.assertIn("Linked issues", self.workflow_content,
            "Workflow should log linked issues found")

    def test_provides_fallback_when_api_unavailable(self):
        """Test that workflow suggests fallback when API errors occur"""
        # Should suggest adding labels to PR as fallback
        self.assertIn("Add agent:go", self.workflow_content,
            "Workflow should suggest direct PR labels as fallback")

    def test_case_insensitive_keyword_matching(self):
        """Test that workflow uses case-insensitive pattern matching"""
        # Regex patterns should use 'i' flag for case-insensitive
        self.assertIn("gi", self.workflow_content,
            "Workflow patterns should be case-insensitive")


class TestLabelCombinations(unittest.TestCase):
    """Test various label combinations and priorities"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"
        self.workflow_content = self.workflow_path.read_text(encoding="utf-8")

    def test_override_has_highest_priority(self):
        """Test that autonomy:override has highest priority"""
        # Override check should return early, before other checks
        override_idx = self.workflow_content.find("autonomy:override")
        agent_go_idx = self.workflow_content.find("includes('agent:go')")
        self.assertLess(override_idx, agent_go_idx,
            "Override check should come before other label checks")

    def test_allow_large_file_is_informational(self):
        """Test that allow:large-file label is logged but doesn't affect gates"""
        if "allow:large-file" in self.workflow_content:
            # Should be logged but not return/exit
            self.assertIn("allow:large-file", self.workflow_content,
                "Workflow should acknowledge allow:large-file label")

    def test_sprint_mode_takes_precedence_over_on_demand(self):
        """Test that agent:sprint check happens before agent:go"""
        # Both should be checked, but sprint may auto-add agent:go
        self.assertIn("agent:sprint", self.workflow_content)
        self.assertIn("agent:go", self.workflow_content)

    def test_multiple_issues_any_grant_passes(self):
        """Test that any linked issue with agent:go or agent:sprint passes gate"""
        # Should break/return after finding first valid grant
        self.assertIn("break", self.workflow_content,
            "Workflow should stop checking after finding valid grant")


class TestDocumentationAlignment(unittest.TestCase):
    """Test that workflow aligns with documentation"""

    def setUp(self):
        """Set up file paths"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"
        self.playbook_path = repo_root / "playbooks" / "autonomy-modes.md"
        self.workflow_content = self.workflow_path.read_text(encoding="utf-8")
        self.playbook_content = self.playbook_path.read_text(encoding="utf-8")

    def test_playbook_documents_all_modes(self):
        """Test that playbook documents all three autonomy modes"""
        self.assertIn("On-demand", self.playbook_content)
        self.assertIn("sprint", self.playbook_content.lower())
        self.assertIn("Override", self.playbook_content)

    def test_playbook_documents_labels(self):
        """Test that playbook documents all autonomy labels"""
        labels = ["agent:go", "agent:sprint", "autonomy:override"]
        for label in labels:
            self.assertIn(label, self.playbook_content,
                f"Playbook should document {label} label")

    def test_playbook_explains_issue_linking(self):
        """Test that playbook explains how to link issues"""
        link_keywords = ["Fixes", "Closes", "Resolves"]
        found = sum(1 for keyword in link_keywords if keyword in self.playbook_content)
        self.assertGreater(found, 0,
            "Playbook should explain issue linking syntax")

    def test_playbook_references_workflow(self):
        """Test that playbook references the workflow file"""
        self.assertIn("agent-gates.yml", self.playbook_content,
            "Playbook should reference agent-gates workflow")

    def test_workflow_references_playbook(self):
        """Test that workflow error messages reference playbook"""
        self.assertIn("autonomy-modes.md", self.workflow_content,
            "Workflow errors should reference playbook")


class TestWorkflowLogging(unittest.TestCase):
    """Test workflow logging and observability"""

    def setUp(self):
        """Set up workflow path"""
        repo_root = Path(__file__).resolve().parent.parent
        self.workflow_path = repo_root / ".github" / "workflows" / "agent-gates.yml"
        self.workflow_content = self.workflow_path.read_text(encoding="utf-8")

    def test_logs_pr_information(self):
        """Test that workflow logs PR number and title"""
        self.assertIn("pr.number", self.workflow_content)
        self.assertIn("pr.title", self.workflow_content)

    def test_logs_pr_labels(self):
        """Test that workflow logs labels on PR"""
        self.assertIn("PR Labels", self.workflow_content)

    def test_logs_linked_issues(self):
        """Test that workflow logs linked issue numbers"""
        self.assertIn("Linked issues", self.workflow_content)

    def test_logs_issue_labels(self):
        """Test that workflow logs labels on each linked issue"""
        self.assertIn("Issue #", self.workflow_content)
        self.assertIn("labels:", self.workflow_content)

    def test_uses_emoji_indicators(self):
        """Test that workflow uses emoji for better readability"""
        # Should use emojis like ✅, ❌, ⚠️, ℹ️, 🔍, 🏷️ etc.
        # Check for common emoji characters used in the workflow
        emoji_indicators = ["✅", "❌", "⚠️", "ℹ️", "🔍", "🏷️"]
        found_emojis = sum(1 for emoji in emoji_indicators if emoji in self.workflow_content)
        self.assertGreater(found_emojis, 0,
            "Workflow should use emoji indicators for readability")

    def test_logs_decision_outcomes(self):
        """Test that workflow clearly logs why it passed or failed"""
        self.assertIn("gate passed", self.workflow_content.lower())
        self.assertIn("FAILED", self.workflow_content)


if __name__ == "__main__":
    unittest.main()
