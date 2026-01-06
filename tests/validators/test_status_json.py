#!/usr/bin/env python3
"""Unit tests for status.json validation in check_artifacts.py"""

import json
import tempfile
import unittest
from pathlib import Path
import sys

# Add parent directory to path to import check_artifacts
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "validators"))

from check_artifacts import validate_status_json


class TestStatusJsonValidation(unittest.TestCase):
    """Test status.json validation logic"""

    def setUp(self):
        """Create a temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def write_status_json(self, data: dict) -> Path:
        """Helper to write status.json with given data"""
        status_path = self.temp_path / "status.json"
        status_path.write_text(json.dumps(data))
        return status_path

    def test_valid_status_active(self):
        """Test valid status.json with active status"""
        data = {
            "status": "active",
            "current_phase": "implementation",
            "last_updated": "2026-01-06T21:00:00Z"
        }
        status_path = self.write_status_json(data)
        # Should not raise any exception
        validate_status_json(status_path, "test-project")

    def test_valid_status_blocked_with_reason(self):
        """Test valid status.json with blocked status and reason"""
        data = {
            "status": "blocked",
            "current_phase": "architecture",
            "last_updated": "2026-01-06T21:00:00Z",
            "blocked_reason": "Awaiting security review"
        }
        status_path = self.write_status_json(data)
        validate_status_json(status_path, "test-project")

    def test_valid_status_completed(self):
        """Test valid status.json with completed status"""
        data = {
            "status": "completed",
            "current_phase": "deployment",
            "last_updated": "2026-01-06T21:00:00Z",
            "notes": "Project successfully deployed"
        }
        status_path = self.write_status_json(data)
        validate_status_json(status_path, "test-project")

    def test_valid_status_on_hold(self):
        """Test valid status.json with on-hold status"""
        data = {
            "status": "on-hold",
            "current_phase": "testing",
            "last_updated": "2026-01-06T21:00:00Z"
        }
        status_path = self.write_status_json(data)
        validate_status_json(status_path, "test-project")

    def test_valid_all_phases(self):
        """Test all valid phase values"""
        phases = ["spec", "architecture", "implementation", "testing", "deployment"]
        for phase in phases:
            data = {
                "status": "active",
                "current_phase": phase,
                "last_updated": "2026-01-06T21:00:00Z"
            }
            status_path = self.write_status_json(data)
            validate_status_json(status_path, "test-project")

    def test_invalid_json(self):
        """Test invalid JSON format"""
        status_path = self.temp_path / "status.json"
        status_path.write_text("{invalid json")
        with self.assertRaises(SystemExit):
            validate_status_json(status_path, "test-project")

    def test_missing_required_field_status(self):
        """Test missing status field"""
        data = {
            "current_phase": "implementation",
            "last_updated": "2026-01-06T21:00:00Z"
        }
        status_path = self.write_status_json(data)
        with self.assertRaises(SystemExit):
            validate_status_json(status_path, "test-project")

    def test_missing_required_field_current_phase(self):
        """Test missing current_phase field"""
        data = {
            "status": "active",
            "last_updated": "2026-01-06T21:00:00Z"
        }
        status_path = self.write_status_json(data)
        with self.assertRaises(SystemExit):
            validate_status_json(status_path, "test-project")

    def test_missing_required_field_last_updated(self):
        """Test missing last_updated field"""
        data = {
            "status": "active",
            "current_phase": "implementation"
        }
        status_path = self.write_status_json(data)
        with self.assertRaises(SystemExit):
            validate_status_json(status_path, "test-project")

    def test_invalid_status_value(self):
        """Test invalid status value"""
        data = {
            "status": "invalid-status",
            "current_phase": "implementation",
            "last_updated": "2026-01-06T21:00:00Z"
        }
        status_path = self.write_status_json(data)
        with self.assertRaises(SystemExit):
            validate_status_json(status_path, "test-project")

    def test_invalid_phase_value(self):
        """Test invalid current_phase value"""
        data = {
            "status": "active",
            "current_phase": "invalid-phase",
            "last_updated": "2026-01-06T21:00:00Z"
        }
        status_path = self.write_status_json(data)
        with self.assertRaises(SystemExit):
            validate_status_json(status_path, "test-project")

    def test_invalid_timestamp_format(self):
        """Test invalid timestamp format"""
        data = {
            "status": "active",
            "current_phase": "implementation",
            "last_updated": "not-a-timestamp"
        }
        status_path = self.write_status_json(data)
        with self.assertRaises(SystemExit):
            validate_status_json(status_path, "test-project")

    def test_valid_timestamp_without_z(self):
        """Test valid ISO 8601 timestamp without Z suffix"""
        data = {
            "status": "active",
            "current_phase": "implementation",
            "last_updated": "2026-01-06T21:00:00+00:00"
        }
        status_path = self.write_status_json(data)
        validate_status_json(status_path, "test-project")

    def test_optional_notes_field(self):
        """Test optional notes field is accepted"""
        data = {
            "status": "active",
            "current_phase": "implementation",
            "last_updated": "2026-01-06T21:00:00Z",
            "notes": "Making good progress"
        }
        status_path = self.write_status_json(data)
        validate_status_json(status_path, "test-project")

    def test_optional_blocked_reason_field(self):
        """Test optional blocked_reason field is accepted"""
        data = {
            "status": "active",
            "current_phase": "implementation",
            "last_updated": "2026-01-06T21:00:00Z",
            "blocked_reason": "Previously blocked, now resolved"
        }
        status_path = self.write_status_json(data)
        validate_status_json(status_path, "test-project")


if __name__ == "__main__":
    unittest.main()
