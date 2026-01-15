#!/usr/bin/env python3
"""Integration tests for pause/resume workflow using status.json.

These tests validate that the pause/resume workflow functions correctly
by simulating agent behavior when encountering different status states.
"""

import json
import tempfile
import unittest
from pathlib import Path
import sys

# Add parent directory to path to import check_artifacts
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "validators"))

from check_artifacts import validate_status_json


class TestPauseResumeWorkflow(unittest.TestCase):
    """Test full pause/resume workflow scenarios"""

    def setUp(self):
        """Create a temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.project_name = "test-project"

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def write_status_json(self, data: dict) -> Path:
        """Helper to write status.json with given data"""
        status_path = self.temp_path / "status.json"
        status_path.write_text(json.dumps(data, indent=2))
        return status_path

    def read_status_json(self) -> dict:
        """Helper to read current status.json"""
        status_path = self.temp_path / "status.json"
        with open(status_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def simulate_agent_check_status(self, status_path: Path) -> tuple[bool, str]:
        """
        Simulate agent checking status.json before starting work.
        
        Returns:
            (can_proceed: bool, message: str)
        """
        if not status_path.exists():
            return (True, "No status.json found, proceeding normally")
        
        try:
            data = self.read_status_json()
            status = data.get("status", "active")
            
            if status == "blocked":
                reason = data.get("blocked_reason", "No reason provided")
                return (False, f"Project blocked: {reason}")
            elif status == "on-hold":
                reason = data.get("notes", "No reason provided")
                return (False, f"Project on hold: {reason}")
            elif status == "completed":
                return (False, "Project already completed")
            elif status == "active":
                return (True, "Status is active, proceeding")
            else:
                return (False, f"Unknown status: {status}")
        except Exception as e:
            return (False, f"Error reading status: {e}")

    def test_workflow_no_status_file(self):
        """Test workflow when no status.json exists (default active behavior)"""
        # No status file = agent can proceed
        status_path = self.temp_path / "status.json"
        can_proceed, message = self.simulate_agent_check_status(status_path)
        
        self.assertTrue(can_proceed)
        self.assertIn("No status.json", message)

    def test_workflow_pause_with_blocked_status(self):
        """Test pausing agent work by setting blocked status"""
        # Human blocks the project
        blocked_data = {
            "status": "blocked",
            "current_phase": "implementation",
            "last_updated": "2026-01-15T10:00:00Z",
            "blocked_reason": "Awaiting security review"
        }
        status_path = self.write_status_json(blocked_data)
        
        # Validate status.json is valid
        validate_status_json(status_path, self.project_name)
        
        # Agent checks and should NOT proceed
        can_proceed, message = self.simulate_agent_check_status(status_path)
        
        self.assertFalse(can_proceed)
        self.assertIn("blocked", message.lower())
        self.assertIn("security review", message.lower())

    def test_workflow_resume_after_blocked(self):
        """Test resuming agent work after removing block"""
        # Start blocked
        blocked_data = {
            "status": "blocked",
            "current_phase": "implementation",
            "last_updated": "2026-01-15T10:00:00Z",
            "blocked_reason": "Awaiting security review"
        }
        status_path = self.write_status_json(blocked_data)
        
        # Agent checks - should not proceed
        can_proceed, _ = self.simulate_agent_check_status(status_path)
        self.assertFalse(can_proceed)
        
        # Human reviews and unblocks
        active_data = {
            "status": "active",
            "current_phase": "implementation",
            "last_updated": "2026-01-15T14:30:00Z",
            "notes": "Security review complete, cleared to proceed"
        }
        status_path = self.write_status_json(active_data)
        validate_status_json(status_path, self.project_name)
        
        # Agent checks again - should proceed
        can_proceed, message = self.simulate_agent_check_status(status_path)
        self.assertTrue(can_proceed)
        self.assertIn("active", message.lower())

    def test_workflow_on_hold_blocks_agent(self):
        """Test that on-hold status also prevents agent from proceeding"""
        # Human sets on-hold
        on_hold_data = {
            "status": "on-hold",
            "current_phase": "implementation",
            "last_updated": "2026-01-15T10:00:00Z",
            "notes": "Waiting for upstream API changes"
        }
        status_path = self.write_status_json(on_hold_data)
        validate_status_json(status_path, self.project_name)
        
        # Agent checks - should NOT proceed
        can_proceed, message = self.simulate_agent_check_status(status_path)
        
        self.assertFalse(can_proceed)
        self.assertIn("on hold", message.lower())

    def test_workflow_completed_prevents_further_work(self):
        """Test that completed status prevents agent from doing more work"""
        # Project is completed
        completed_data = {
            "status": "completed",
            "current_phase": "deployment",
            "last_updated": "2026-01-15T18:00:00Z",
            "notes": "All milestones finished"
        }
        status_path = self.write_status_json(completed_data)
        validate_status_json(status_path, self.project_name)
        
        # Agent checks - should NOT proceed
        can_proceed, message = self.simulate_agent_check_status(status_path)
        
        self.assertFalse(can_proceed)
        self.assertIn("completed", message.lower())

    def test_workflow_active_allows_work(self):
        """Test that active status allows agent to proceed"""
        # Status is active
        active_data = {
            "status": "active",
            "current_phase": "implementation",
            "last_updated": "2026-01-15T10:00:00Z"
        }
        status_path = self.write_status_json(active_data)
        validate_status_json(status_path, self.project_name)
        
        # Agent checks - should proceed
        can_proceed, message = self.simulate_agent_check_status(status_path)
        
        self.assertTrue(can_proceed)
        self.assertIn("active", message.lower())

    def test_workflow_multiple_pause_resume_cycles(self):
        """Test multiple pause/resume cycles work correctly"""
        status_path = self.temp_path / "status.json"
        
        # Cycle 1: Start active
        data = {
            "status": "active",
            "current_phase": "spec",
            "last_updated": "2026-01-15T09:00:00Z"
        }
        self.write_status_json(data)
        can_proceed, _ = self.simulate_agent_check_status(status_path)
        self.assertTrue(can_proceed)
        
        # Cycle 1: Block for review
        data["status"] = "blocked"
        data["blocked_reason"] = "Review spec before architecture"
        data["last_updated"] = "2026-01-15T10:00:00Z"
        self.write_status_json(data)
        can_proceed, _ = self.simulate_agent_check_status(status_path)
        self.assertFalse(can_proceed)
        
        # Cycle 1: Resume
        data["status"] = "active"
        data["current_phase"] = "architecture"
        data["last_updated"] = "2026-01-15T11:00:00Z"
        del data["blocked_reason"]
        self.write_status_json(data)
        can_proceed, _ = self.simulate_agent_check_status(status_path)
        self.assertTrue(can_proceed)
        
        # Cycle 2: Block again
        data["status"] = "blocked"
        data["blocked_reason"] = "Design review needed"
        data["last_updated"] = "2026-01-15T14:00:00Z"
        self.write_status_json(data)
        can_proceed, _ = self.simulate_agent_check_status(status_path)
        self.assertFalse(can_proceed)
        
        # Cycle 2: Resume
        data["status"] = "active"
        data["current_phase"] = "implementation"
        data["last_updated"] = "2026-01-15T15:00:00Z"
        del data["blocked_reason"]
        self.write_status_json(data)
        can_proceed, _ = self.simulate_agent_check_status(status_path)
        self.assertTrue(can_proceed)

    def test_workflow_phase_transitions(self):
        """Test that agents can update phase during workflow"""
        status_path = self.temp_path / "status.json"
        
        phases = ["spec", "architecture", "implementation", "testing", "deployment"]
        
        for phase in phases:
            data = {
                "status": "active",
                "current_phase": phase,
                "last_updated": "2026-01-15T10:00:00Z",
                "notes": f"Working on {phase} phase"
            }
            self.write_status_json(data)
            
            # Validate phase is valid
            validate_status_json(status_path, self.project_name)
            
            # Agent can proceed in any phase if active
            can_proceed, _ = self.simulate_agent_check_status(status_path)
            self.assertTrue(can_proceed, f"Should proceed in {phase} phase")

    def test_workflow_blocked_without_reason_still_blocks(self):
        """Test that blocked status works even without blocked_reason (though not recommended)"""
        # Blocked without reason (generates warning but still valid)
        blocked_data = {
            "status": "blocked",
            "current_phase": "implementation",
            "last_updated": "2026-01-15T10:00:00Z"
        }
        status_path = self.write_status_json(blocked_data)
        
        # Should still validate (with warning)
        validate_status_json(status_path, self.project_name)
        
        # Agent should still respect the block
        can_proceed, message = self.simulate_agent_check_status(status_path)
        self.assertFalse(can_proceed)
        self.assertIn("blocked", message.lower())


if __name__ == "__main__":
    unittest.main()
