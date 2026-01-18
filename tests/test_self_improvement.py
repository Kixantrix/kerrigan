"""
Tests for self-improvement analysis system.

This module validates the self-improvement analyzer including external research capabilities.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from self_improvement_analyzer import (
    FeedbackAnalyzer,
    RetrospectiveAnalyzer,
    ImprovementProposer,
)
from research import (
    WebSearchResearcher,
    GitHubAnalysisResearcher,
    PaperResearcher,
    FrameworkAnalysisResearcher,
)


class TestFeedbackAnalyzer(unittest.TestCase):
    """Test suite for FeedbackAnalyzer"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent
        self.feedback_dir = self.repo_root / "feedback" / "agent-feedback"

    def test_analyzer_initializes(self):
        """Test that FeedbackAnalyzer initializes properly"""
        analyzer = FeedbackAnalyzer(self.feedback_dir)
        self.assertEqual(analyzer.feedback_dir, self.feedback_dir)
        self.assertEqual(len(analyzer.feedback_items), 0)

    def test_load_feedback_skips_template(self):
        """Test that feedback loading skips template files"""
        analyzer = FeedbackAnalyzer(self.feedback_dir)
        items = analyzer.load_feedback()
        
        # Verify no template files are loaded
        for item in items:
            filename = item.get('_filename', '')
            self.assertNotIn('TEMPLATE', filename)


class TestRetrospectiveAnalyzer(unittest.TestCase):
    """Test suite for RetrospectiveAnalyzer"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent
        self.docs_dir = self.repo_root / "docs"

    def test_analyzer_initializes(self):
        """Test that RetrospectiveAnalyzer initializes properly"""
        analyzer = RetrospectiveAnalyzer(self.docs_dir)
        self.assertEqual(analyzer.docs_dir, self.docs_dir)
        self.assertEqual(len(analyzer.retrospectives), 0)

    def test_load_retrospectives(self):
        """Test that retrospectives are loaded"""
        analyzer = RetrospectiveAnalyzer(self.docs_dir)
        retros = analyzer.load_retrospectives()
        
        # Should find at least the milestone retrospectives if they exist
        self.assertIsInstance(retros, list)


class TestImprovementProposer(unittest.TestCase):
    """Test suite for ImprovementProposer"""

    def test_proposer_initializes(self):
        """Test that ImprovementProposer initializes properly"""
        proposer = ImprovementProposer()
        self.assertEqual(len(proposer.proposals), 0)

    def test_generate_proposals_empty_input(self):
        """Test proposal generation with empty input"""
        proposer = ImprovementProposer()
        proposals = proposer.generate_proposals(
            feedback_analysis={},
            retro_patterns=[],
            feedback_items=[]
        )
        self.assertEqual(len(proposals), 0)

    def test_generate_proposals_with_external_findings(self):
        """Test proposal generation with external findings"""
        proposer = ImprovementProposer()
        
        external_findings = [
            {
                'type': 'test_finding',
                'title': 'Test Finding',
                'summary': 'Test summary',
                'relevance': 0.8,
                'evidence': 'Test evidence',
                'potential_application': 'Test application'
            }
        ]
        
        proposals = proposer.generate_proposals(
            feedback_analysis={},
            retro_patterns=[],
            feedback_items=[],
            external_findings=external_findings
        )
        
        # Should have at least one external proposal
        external_proposals = [p for p in proposals if p.get('source') == 'external']
        self.assertGreater(len(external_proposals), 0)
        
        # Verify proposal structure
        for proposal in external_proposals:
            self.assertIn('type', proposal)
            self.assertIn('priority', proposal)
            self.assertIn('title', proposal)
            self.assertIn('source', proposal)
            self.assertEqual(proposal['source'], 'external')

    def test_quality_filter_rejects_low_relevance(self):
        """Test that low-relevance findings are filtered out"""
        proposer = ImprovementProposer()
        
        external_findings = [
            {
                'type': 'test_finding',
                'title': 'Low Relevance Finding',
                'summary': 'Test summary',
                'relevance': 0.5,  # Below threshold
                'evidence': 'Test evidence',
                'potential_application': 'Test application'
            }
        ]
        
        proposals = proposer.generate_proposals(
            feedback_analysis={},
            retro_patterns=[],
            feedback_items=[],
            external_findings=external_findings
        )
        
        # Should not generate proposals for low-relevance findings
        external_proposals = [p for p in proposals if p.get('source') == 'external']
        self.assertEqual(len(external_proposals), 0)


class TestWebSearchResearcher(unittest.TestCase):
    """Test suite for WebSearchResearcher"""

    def test_researcher_initializes(self):
        """Test that WebSearchResearcher initializes properly"""
        researcher = WebSearchResearcher(enabled=True)
        self.assertTrue(researcher.enabled)
        self.assertEqual(len(researcher.findings), 0)

    def test_disabled_researcher_returns_empty(self):
        """Test that disabled researcher returns no findings"""
        researcher = WebSearchResearcher(enabled=False)
        findings = researcher.search_best_practices()
        self.assertEqual(len(findings), 0)

    def test_evaluate_relevance(self):
        """Test relevance evaluation"""
        researcher = WebSearchResearcher(enabled=True)
        
        # High relevance finding
        finding = {
            'title': 'AI Agent Orchestration Best Practices',
            'summary': 'Autonomous agent workflows with LLM integration'
        }
        score = researcher.evaluate_relevance(finding)
        self.assertGreater(score, 0.5)
        
        # Low relevance finding
        finding2 = {
            'title': 'Unrelated Topic',
            'summary': 'Nothing about agents here'
        }
        score2 = researcher.evaluate_relevance(finding2)
        self.assertLess(score2, 0.3)


class TestGitHubAnalysisResearcher(unittest.TestCase):
    """Test suite for GitHubAnalysisResearcher"""

    def test_researcher_initializes(self):
        """Test that GitHubAnalysisResearcher initializes properly"""
        researcher = GitHubAnalysisResearcher(
            "test-owner", "test-repo", "test-token", enabled=True
        )
        self.assertEqual(researcher.repo_owner, "test-owner")
        self.assertEqual(researcher.repo_name, "test-repo")
        self.assertEqual(researcher.github_token, "test-token")
        self.assertTrue(researcher.enabled)

    def test_disabled_researcher_returns_empty(self):
        """Test that disabled researcher returns no findings"""
        researcher = GitHubAnalysisResearcher(
            "test-owner", "test-repo", None, enabled=False
        )
        findings = researcher.analyze_patterns()
        self.assertEqual(len(findings), 0)

    def test_no_token_returns_empty(self):
        """Test that researcher without token returns no findings"""
        researcher = GitHubAnalysisResearcher(
            "test-owner", "test-repo", None, enabled=True
        )
        findings = researcher.analyze_patterns()
        self.assertEqual(len(findings), 0)


class TestPaperResearcher(unittest.TestCase):
    """Test suite for PaperResearcher"""

    def test_researcher_initializes(self):
        """Test that PaperResearcher initializes properly"""
        researcher = PaperResearcher(enabled=False)
        self.assertFalse(researcher.enabled)
        self.assertEqual(len(researcher.findings), 0)

    def test_disabled_researcher_returns_empty(self):
        """Test that disabled researcher returns no findings"""
        researcher = PaperResearcher(enabled=False)
        findings = researcher.search_arxiv()
        self.assertEqual(len(findings), 0)


class TestFrameworkAnalysisResearcher(unittest.TestCase):
    """Test suite for FrameworkAnalysisResearcher"""

    def test_researcher_initializes(self):
        """Test that FrameworkAnalysisResearcher initializes properly"""
        researcher = FrameworkAnalysisResearcher(enabled=True)
        self.assertTrue(researcher.enabled)
        self.assertEqual(len(researcher.findings), 0)

    def test_disabled_researcher_returns_empty(self):
        """Test that disabled researcher returns no findings"""
        researcher = FrameworkAnalysisResearcher(enabled=False)
        findings = researcher.analyze_frameworks()
        self.assertEqual(len(findings), 0)


class TestSafetyGates(unittest.TestCase):
    """Test suite for safety gates - ensure no automatic implementation"""

    def test_proposals_are_output_only(self):
        """Test that proposals are generated but not automatically implemented"""
        proposer = ImprovementProposer()
        
        # High severity feedback should generate proposals
        feedback_items = [
            {
                'severity': 'high',
                'status': 'new',
                'title': 'Test Issue',
                'description': 'Test description',
                'category': 'test_category',
                'agent_role': 'test_agent',
                '_filename': 'test.yaml'
            }
        ]
        
        feedback_analysis = {
            'high_severity_count': 1,
            'by_category': {'test_category': 1}
        }
        
        proposals = proposer.generate_proposals(
            feedback_analysis=feedback_analysis,
            retro_patterns=[],
            feedback_items=feedback_items
        )
        
        # Should generate proposals
        self.assertGreater(len(proposals), 0)
        
        # But they should all have required fields for manual review
        for proposal in proposals:
            self.assertIn('type', proposal)
            self.assertIn('priority', proposal)
            self.assertIn('title', proposal)
            self.assertIn('description', proposal)
            self.assertIn('evidence', proposal)
            self.assertIn('proposed_solution', proposal)
            # No 'auto_implement' or similar field should exist
            self.assertNotIn('auto_implement', proposal)
            self.assertNotIn('auto_create_issue', proposal)

    def test_external_proposals_marked_for_review(self):
        """Test that external proposals are clearly marked for human review"""
        proposer = ImprovementProposer()
        
        external_findings = [
            {
                'type': 'external_test',
                'title': 'External Finding',
                'summary': 'From external source',
                'relevance': 0.9,
                'evidence': 'External evidence',
                'potential_application': 'Apply externally'
            }
        ]
        
        proposals = proposer.generate_proposals(
            feedback_analysis={},
            retro_patterns=[],
            feedback_items=[],
            external_findings=external_findings
        )
        
        external_proposals = [p for p in proposals if p.get('source') == 'external']
        
        # All external proposals should be marked as external
        for proposal in external_proposals:
            self.assertEqual(proposal.get('source'), 'external')
            # Should have low priority by default
            self.assertEqual(proposal.get('priority'), 'low')


if __name__ == "__main__":
    unittest.main()
