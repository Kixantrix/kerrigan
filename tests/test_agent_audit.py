#!/usr/bin/env python3
"""Tests for agent audit functionality."""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from agent_audit import (
    AgentSignature,
    AuditLog,
    validate_pr_signature,
    generate_agent_checklist,
    check_spec_references,
    validate_spec_compliance,
    check_quality_bar_compliance,
)


class TestAgentSignature(unittest.TestCase):
    """Test agent signature creation and validation."""

    def test_create_signature(self):
        """Test creating a new signature."""
        sig = AgentSignature.create("role:swe", "1.0")
        
        self.assertEqual(sig.role, "role:swe")
        self.assertEqual(sig.version, "1.0")
        self.assertIsNotNone(sig.timestamp)
        
        # Verify timestamp is valid ISO 8601
        datetime.fromisoformat(sig.timestamp.replace("Z", "+00:00"))

    def test_signature_to_markdown(self):
        """Test converting signature to markdown comment."""
        sig = AgentSignature("role:swe", "1.0", "2026-01-15T06:00:00Z")
        markdown = sig.to_markdown_comment()
        
        self.assertIn("AGENT_SIGNATURE", markdown)
        self.assertIn("role=role:swe", markdown)
        self.assertIn("version=1.0", markdown)
        self.assertIn("timestamp=2026-01-15T06:00:00Z", markdown)

    def test_signature_from_text(self):
        """Test extracting signature from text."""
        pr_body = """
# My PR

This PR adds a feature.

<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->

## Changes
- Added feature X
"""
        sig = AgentSignature.from_text(pr_body)
        
        self.assertIsNotNone(sig)
        self.assertEqual(sig.role, "role:swe")
        self.assertEqual(sig.version, "1.0")
        self.assertEqual(sig.timestamp, "2026-01-15T06:00:00Z")

    def test_signature_from_text_not_found(self):
        """Test extracting signature when none exists."""
        pr_body = "This PR has no signature."
        sig = AgentSignature.from_text(pr_body)
        
        self.assertIsNone(sig)

    def test_validate_valid_signature(self):
        """Test validation of a valid signature."""
        sig = AgentSignature("role:swe", "1.0", "2026-01-15T06:00:00Z")
        errors = sig.validate()
        
        self.assertEqual(len(errors), 0)

    def test_validate_invalid_role(self):
        """Test validation fails for invalid role format."""
        sig = AgentSignature("swe", "1.0", "2026-01-15T06:00:00Z")
        errors = sig.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("role:" in err or "agent:" in err for err in errors))

    def test_validate_invalid_version(self):
        """Test validation fails for invalid version format."""
        sig = AgentSignature("role:swe", "abc", "2026-01-15T06:00:00Z")
        errors = sig.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("version" in err.lower() for err in errors))

    def test_validate_invalid_timestamp(self):
        """Test validation fails for invalid timestamp format."""
        sig = AgentSignature("role:swe", "1.0", "not-a-timestamp")
        errors = sig.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("timestamp" in err.lower() for err in errors))


class TestValidatePRSignature(unittest.TestCase):
    """Test PR signature validation function."""

    def test_validate_pr_with_signature(self):
        """Test validation passes for PR with valid signature."""
        pr_body = """
# Feature Implementation

<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->

This PR implements feature X.
"""
        is_valid, errors = validate_pr_signature(pr_body)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_pr_without_signature(self):
        """Test validation fails for PR without signature."""
        pr_body = "This PR has no signature."
        is_valid, errors = validate_pr_signature(pr_body)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("signature" in err.lower() for err in errors))

    def test_validate_empty_pr_body(self):
        """Test validation fails for empty PR body."""
        is_valid, errors = validate_pr_signature("")
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestAuditLog(unittest.TestCase):
    """Test audit log functionality."""

    def setUp(self):
        """Create temporary audit log file."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = Path(self.temp_dir) / "audit.json"
        self.audit_log = AuditLog(self.log_path)

    def test_create_empty_log(self):
        """Test creating a new audit log."""
        self.assertEqual(len(self.audit_log.entries), 0)

    def test_add_entry(self):
        """Test adding an entry to audit log."""
        self.audit_log.add_entry(
            agent_role="role:swe",
            pr_number=123,
            issue_number=456
        )
        
        self.assertEqual(len(self.audit_log.entries), 1)
        entry = self.audit_log.entries[0]
        
        self.assertEqual(entry["agent_role"], "role:swe")
        self.assertEqual(entry["pr_number"], 123)
        self.assertEqual(entry["issue_number"], 456)
        self.assertIn("timestamp", entry)

    def test_add_entry_with_signature(self):
        """Test adding an entry with signature."""
        sig = AgentSignature("role:swe", "1.0", "2026-01-15T06:00:00Z")
        
        self.audit_log.add_entry(
            agent_role="role:swe",
            pr_number=123,
            signature=sig
        )
        
        entry = self.audit_log.entries[0]
        self.assertIn("signature", entry)
        self.assertEqual(entry["signature"]["role"], "role:swe")

    def test_get_entries_for_agent(self):
        """Test filtering entries by agent role."""
        self.audit_log.add_entry("role:swe", pr_number=1)
        self.audit_log.add_entry("role:spec", pr_number=2)
        self.audit_log.add_entry("role:swe", pr_number=3)
        
        swe_entries = self.audit_log.get_entries_for_agent("role:swe")
        self.assertEqual(len(swe_entries), 2)
        
        spec_entries = self.audit_log.get_entries_for_agent("role:spec")
        self.assertEqual(len(spec_entries), 1)

    def test_get_entries_for_pr(self):
        """Test filtering entries by PR number."""
        self.audit_log.add_entry("role:swe", pr_number=123)
        self.audit_log.add_entry("role:spec", pr_number=456)
        
        entries = self.audit_log.get_entries_for_pr(123)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["pr_number"], 123)

    def test_persist_and_load(self):
        """Test that audit log persists to disk and can be loaded."""
        self.audit_log.add_entry("role:swe", pr_number=123)
        
        # Create new instance from same path
        new_log = AuditLog(self.log_path)
        
        self.assertEqual(len(new_log.entries), 1)
        self.assertEqual(new_log.entries[0]["agent_role"], "role:swe")


class TestGenerateAgentChecklist(unittest.TestCase):
    """Test agent checklist generation."""

    def test_generate_swe_checklist(self):
        """Test generating checklist for SWE agent."""
        checklist = generate_agent_checklist("role:swe")
        
        self.assertIn("Agent Checklist", checklist)
        self.assertIn("SWE Agent", checklist)
        self.assertIn("status.json", checklist)
        self.assertIn("linting", checklist.lower())

    def test_generate_spec_checklist(self):
        """Test generating checklist for Spec agent."""
        checklist = generate_agent_checklist("role:spec")
        
        self.assertIn("Spec Agent", checklist)
        self.assertIn("spec.md", checklist)
        self.assertIn("acceptance", checklist.lower())

    def test_generate_unknown_role_checklist(self):
        """Test generating checklist for unknown role."""
        checklist = generate_agent_checklist("role:unknown")
        
        self.assertIn("Agent Checklist", checklist)
        self.assertIn("role:unknown", checklist)


class TestCheckSpecReferences(unittest.TestCase):
    """Test spec reference checking."""

    def test_check_spec_references_in_actual_repo(self):
        """Test checking spec references in actual repository."""
        # Get the repository root (3 levels up from tests/)
        repo_root = Path(__file__).resolve().parent.parent
        
        is_valid, issues = check_spec_references(repo_root)
        
        # Should be valid since we just added the references
        self.assertTrue(is_valid, f"Spec references validation failed: {issues}")
        self.assertEqual(len(issues), 0)

    def test_check_spec_references_missing_directory(self):
        """Test behavior when directories are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            is_valid, issues = check_spec_references(temp_path)
            
            self.assertFalse(is_valid)
            self.assertGreater(len(issues), 0)
            self.assertTrue(any("not found" in issue.lower() for issue in issues))


class TestValidateSpecCompliance(unittest.TestCase):
    """Test spec compliance validation."""

    def test_validate_compliance_without_pr_body(self):
        """Test validation without PR body."""
        repo_root = Path(__file__).resolve().parent.parent
        
        is_compliant, issues = validate_spec_compliance("role:swe", repo_root=repo_root)
        
        # Should pass basic checks
        self.assertTrue(is_compliant, f"Compliance validation failed: {issues}")

    def test_validate_compliance_with_valid_pr_body(self):
        """Test validation with valid PR body."""
        repo_root = Path(__file__).resolve().parent.parent
        pr_body = """
# Feature Implementation

<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->

This PR implements feature X.
"""
        
        is_compliant, issues = validate_spec_compliance("role:swe", pr_body, repo_root)
        
        self.assertTrue(is_compliant, f"Compliance validation failed: {issues}")

    def test_validate_compliance_with_mismatched_role(self):
        """Test validation with mismatched role in signature."""
        repo_root = Path(__file__).resolve().parent.parent
        pr_body = """
<!-- AGENT_SIGNATURE: role=role:architect, version=1.0, timestamp=2026-01-15T06:00:00Z -->
"""
        
        is_compliant, issues = validate_spec_compliance("role:swe", pr_body, repo_root)
        
        self.assertFalse(is_compliant)
        self.assertTrue(any("does not match" in issue for issue in issues))


class TestCheckQualityBarCompliance(unittest.TestCase):
    """Test quality bar compliance checking."""

    def test_check_quality_bar_empty_list(self):
        """Test quality bar check with empty file list."""
        meets_standards, issues = check_quality_bar_compliance("role:swe", [])
        
        self.assertTrue(meets_standards)
        self.assertEqual(len(issues), 0)

    def test_check_quality_bar_with_nonexistent_file(self):
        """Test quality bar check with nonexistent file."""
        fake_path = Path("/tmp/nonexistent_file_12345.py")
        meets_standards, issues = check_quality_bar_compliance("role:swe", [fake_path])
        
        self.assertFalse(meets_standards)
        self.assertTrue(any("not found" in issue for issue in issues))

    def test_check_quality_bar_with_small_file(self):
        """Test quality bar check with small file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Write a small file (under 800 lines)
            for i in range(100):
                f.write(f"# Line {i}\n")
            temp_path = Path(f.name)
        
        try:
            meets_standards, issues = check_quality_bar_compliance("role:swe", [temp_path])
            
            self.assertTrue(meets_standards)
            self.assertEqual(len(issues), 0)
        finally:
            temp_path.unlink()

    def test_check_quality_bar_with_oversized_file(self):
        """Test quality bar check with oversized file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Write a large file (over 800 lines)
            for i in range(850):
                f.write(f"# Line {i}\n")
            temp_path = Path(f.name)
        
        try:
            meets_standards, issues = check_quality_bar_compliance("role:swe", [temp_path])
            
            self.assertFalse(meets_standards)
            self.assertTrue(any("exceeds 800 line" in issue for issue in issues))
        finally:
            temp_path.unlink()

    def test_check_quality_bar_ignores_markdown_files(self):
        """Test quality bar check ignores markdown files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            # Write a large markdown file (over 800 lines)
            for i in range(1000):
                f.write(f"# Line {i}\n")
            temp_path = Path(f.name)
        
        try:
            meets_standards, issues = check_quality_bar_compliance("role:swe", [temp_path])
            
            # Markdown files should be ignored
            self.assertTrue(meets_standards)
            self.assertEqual(len(issues), 0)
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
