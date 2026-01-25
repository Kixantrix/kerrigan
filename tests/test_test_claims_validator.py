#!/usr/bin/env python3
"""Tests for check_test_claims validator."""

import unittest
import tempfile
from pathlib import Path
import sys
import os

# Add tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools', 'validators'))

from check_test_claims import check_test_claims, check_honest_reporting_section


class TestCheckTestClaims(unittest.TestCase):
    """Test the test claims validator."""
    
    def test_detects_vague_test_claims(self):
        """Test that vague claims are detected."""
        pr_body = """
        ## Changes
        Made some updates to the code.
        
        All tests passing.
        """
        
        warnings, errors = check_test_claims(pr_body, [])
        
        # Should warn about vague claim
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any('vague' in w.lower() for w in warnings))
    
    def test_detects_fabricated_39_tests(self):
        """Test that the known fabricated '39 tests' is caught."""
        pr_body = """
        ## Changes
        Updated authentication.
        
        All tests passing (39 tests).
        """
        
        warnings, errors = check_test_claims(pr_body, [])
        
        # Should error on this specific fabricated number
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any('39 tests' in e for e in errors))
    
    def test_detects_test_claims_without_file_changes(self):
        """Test detection of test claims when no test files changed."""
        pr_body = """
        ## Changes
        Added new feature.
        
        Added 5 new tests. All tests passing.
        """
        
        # No test files changed
        changed_files = []
        
        warnings, errors = check_test_claims(pr_body, changed_files)
        
        # Should error because claims tests but no test files
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any('no test files' in e.lower() for e in errors))
    
    def test_accepts_honest_reporting_no_tests(self):
        """Test that honest 'no tests added' statements are accepted."""
        pr_body = """
        ## Changes
        Updated documentation.
        
        ## Testing
        No new tests added - changes are documentation only.
        Existing 226 tests still pass.
        """
        
        # No test files changed (which is correct)
        changed_files = []
        
        warnings, errors = check_test_claims(pr_body, changed_files)
        
        # Should have minimal or no issues
        self.assertEqual(len(errors), 0)
    
    def test_accepts_specific_test_file_references(self):
        """Test that specific test file references are accepted."""
        pr_body = """
        ## Changes
        Added authentication feature.
        
        ## Testing
        Added 5 new tests in tests/test_auth.py (lines 45-89)
        All 231 tests pass (226 existing + 5 new)
        Test run: Ran 231 tests in 0.5s - OK
        """
        
        # Test file was actually changed
        changed_files = ['tests/test_auth.py']
        
        warnings, errors = check_test_claims(pr_body, changed_files)
        
        # Should have no errors (warnings might exist about details)
        self.assertEqual(len(errors), 0)
    
    def test_warns_without_test_runner_output(self):
        """Test warning when test runner output is missing."""
        pr_body = """
        ## Testing
        Added 3 tests in tests/test_api.py
        All tests pass.
        """
        
        changed_files = ['tests/test_api.py']
        
        warnings, errors = check_test_claims(pr_body, changed_files)
        
        # Should warn about missing test runner output
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any('runner output' in w.lower() for w in warnings))
    
    def test_recognizes_testing_section(self):
        """Test recognition of Testing section in PR."""
        pr_body = """
        ## Changes
        Updated code.
        
        ## Testing
        Added tests and verified.
        """
        
        info = check_honest_reporting_section(pr_body)
        
        # Should find the Testing section
        self.assertTrue(any('Testing' in i for i in info))
    
    def test_handles_empty_pr_body(self):
        """Test that empty PR body doesn't crash."""
        pr_body = ""
        
        warnings, errors = check_test_claims(pr_body, None)
        
        # Should not crash, might have warnings
        self.assertIsInstance(warnings, list)
        self.assertIsInstance(errors, list)


class TestHonestReportingDetection(unittest.TestCase):
    """Test honest reporting detection."""
    
    def test_detects_no_tests_statement(self):
        """Test detection of 'no tests added' statements."""
        pr_body = """
        ## Testing
        No new tests added - documentation only.
        """
        
        info = check_honest_reporting_section(pr_body)
        
        # Should recognize honest reporting
        self.assertTrue(any('no new tests' in i.lower() for i in info))
    
    def test_suggests_testing_section(self):
        """Test suggestion to use Testing section."""
        pr_body = """
        ## Changes
        Some changes here.
        """
        
        info = check_honest_reporting_section(pr_body)
        
        # Should suggest adding Testing section
        self.assertTrue(any('testing' in i.lower() for i in info))


if __name__ == '__main__':
    unittest.main()
