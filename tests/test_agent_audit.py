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


if __name__ == "__main__":
    unittest.main()
