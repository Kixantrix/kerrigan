#!/usr/bin/env python3
"""Unit tests for block_validator.py."""

import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "validators"))

from block_validator import validate_blocks


class TestBlockValidator(unittest.TestCase):
    """Test block schema and lifecycle validation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.blocks_dir = Path(self.temp_dir.name) / "blocks"
        self.blocks_dir.mkdir(parents=True, exist_ok=True)
        self.schema_path = (
            Path(__file__).resolve().parents[2]
            / ".specify"
            / "schemas"
            / "block.schema.json"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _base_block(self, emitted_at: str | None = None) -> dict:
        return {
            "task_id": "T-P3-003",
            "emitted_by": "kerrigan",
            "emitted_at": emitted_at or "2026-05-09T00:00:00Z",
            "reason": "prereq-missing",
            "severity": "high",
            "summary": "Missing prerequisite artifact.",
            "details": "A required file is missing on base branch.",
            "decision_needed": "Merge prerequisite PR before dispatch.",
            "options": [
                {
                    "id": "A",
                    "description": "Merge prerequisite PR",
                    "implication": "Unblocks dispatch",
                }
            ],
            "recommendation": "A",
            "minimum_human_input": "Merge prerequisite PR.",
        }

    def _write_block(self, name: str, data: dict) -> Path:
        path = self.blocks_dir / name
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        return path

    def test_unresolved_block_with_ack_label_passes(self):
        block = self._base_block()
        block["labels"] = ["block:acknowledged"]
        self._write_block("t-001.yaml", block)

        errors, warnings = validate_blocks(
            self.blocks_dir,
            schema_path=self.schema_path,
            now=datetime(2026, 5, 9, 1, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_unresolved_block_without_ack_label_fails(self):
        self._write_block("t-001.yaml", self._base_block())

        errors, warnings = validate_blocks(
            self.blocks_dir,
            schema_path=self.schema_path,
            now=datetime(2026, 5, 9, 1, 0, tzinfo=timezone.utc),
        )

        self.assertTrue(
            any("block:acknowledged" in error for error in errors),
            f"Expected missing ack label error in: {errors}",
        )
        self.assertEqual(warnings, [])

    def test_unresolved_block_older_than_24h_warns(self):
        old_timestamp = (
            datetime(2026, 5, 9, 1, 0, tzinfo=timezone.utc) - timedelta(hours=25)
        ).isoformat().replace("+00:00", "Z")
        block = self._base_block(emitted_at=old_timestamp)
        block["labels"] = ["block:acknowledged"]
        self._write_block("t-001.yaml", block)

        errors, warnings = validate_blocks(
            self.blocks_dir,
            schema_path=self.schema_path,
            now=datetime(2026, 5, 9, 1, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(errors, [])
        self.assertTrue(any("older than 24 hours" in warning for warning in warnings))

    def test_resolved_block_without_ack_label_passes(self):
        block = self._base_block()
        block["resolution"] = {
            "resolved_by": "human",
            "resolved_at": "2026-05-09T01:00:00Z",
            "chosen_option": "A",
        }
        self._write_block("t-001.yaml", block)

        errors, _warnings = validate_blocks(self.blocks_dir, schema_path=self.schema_path)
        self.assertEqual(errors, [])

    def test_invalid_reason_fails_schema(self):
        block = self._base_block()
        block["reason"] = "ambiguous_ac"
        block["labels"] = ["block:acknowledged"]
        self._write_block("t-001.yaml", block)

        errors, _warnings = validate_blocks(self.blocks_dir, schema_path=self.schema_path)
        self.assertTrue(any("must be one of" in error for error in errors))

    def test_non_object_yaml_fails(self):
        path = self.blocks_dir / "t-001.yaml"
        path.write_text("- not\n- an\n- object\n", encoding="utf-8")

        errors, _warnings = validate_blocks(self.blocks_dir, schema_path=self.schema_path)
        self.assertTrue(any("YAML object" in error for error in errors))

    def test_cli_blocks_dir_option(self):
        script_path = (
            Path(__file__).resolve().parents[2]
            / "tools"
            / "validators"
            / "block_validator.py"
        )
        self._write_block("t-001.yaml", self._base_block())

        result = subprocess.run(
            [sys.executable, str(script_path), "--blocks-dir", str(self.blocks_dir)],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("block:acknowledged", result.stdout)

    def test_missing_blocks_dir_is_valid(self):
        missing_dir = Path(self.temp_dir.name) / "does-not-exist"
        errors, warnings = validate_blocks(missing_dir, schema_path=self.schema_path)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
