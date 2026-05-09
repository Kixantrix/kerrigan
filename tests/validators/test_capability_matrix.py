#!/usr/bin/env python3
"""Unit tests for test capability matrix validator."""

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "validators"))

from test_capability_matrix import (
    parse_capability_marker,
    is_allowed_local_capability,
    validate_test_capability_matrix,
)


class TestCapabilityMarkerParsing(unittest.TestCase):
    def test_parse_cloud_ok_marker(self):
        marker = parse_capability_marker("# capability: cloud_ok\n")
        self.assertEqual(marker, ("cloud_ok", None))

    def test_parse_local_required_marker(self):
        marker = parse_capability_marker("# capability: local_required(device-io.usb)\n")
        self.assertEqual(marker, ("local_required", "device-io.usb"))

    def test_parse_manual_marker(self):
        marker = parse_capability_marker("# capability: manual(human-judgment)\n")
        self.assertEqual(marker, ("manual", "human-judgment"))

    def test_parse_invalid_marker(self):
        marker = parse_capability_marker("# capability: local_required\n")
        self.assertEqual(marker, ("invalid", "local_required"))

    def test_parse_missing_marker(self):
        marker = parse_capability_marker("def test_x():\n    assert True\n")
        self.assertIsNone(marker)


class TestCapabilityAllowlist(unittest.TestCase):
    def test_allowlisted_capabilities(self):
        self.assertTrue(is_allowed_local_capability("device-io.usb"))
        self.assertTrue(is_allowed_local_capability("os.windows"))
        self.assertTrue(is_allowed_local_capability("paid-service.github-actions"))
        self.assertTrue(is_allowed_local_capability("human-judgment"))

    def test_unlisted_capabilities(self):
        self.assertFalse(is_allowed_local_capability("network.socket"))
        self.assertFalse(is_allowed_local_capability("device-io"))
        self.assertFalse(is_allowed_local_capability("human"))


class TestCapabilityMatrixValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_test(self, name: str, content: str) -> Path:
        path = self.test_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_missing_marker_defaults_to_cloud_ok(self):
        self.write_test("test_default.py", "def test_default():\n    assert True\n")
        errors = validate_test_capability_matrix(self.test_dir)
        self.assertEqual(errors, [])

    def test_valid_local_required_allowlisted_capability(self):
        self.write_test(
            "test_usb.py",
            "# capability: local_required(device-io.usb)\ndef test_usb():\n    assert True\n",
        )
        errors = validate_test_capability_matrix(self.test_dir)
        self.assertEqual(errors, [])

    def test_local_required_unlisted_capability_fails(self):
        test_file = self.write_test(
            "test_bad_cap.py",
            "# capability: local_required(network.bluetooth)\ndef test_bad():\n    assert True\n",
        )
        errors = validate_test_capability_matrix(self.test_dir)
        self.assertEqual(len(errors), 1)
        self.assertIn(str(test_file), errors[0])
        self.assertIn("not allowlisted", errors[0])

    def test_local_required_without_capability_fails(self):
        test_file = self.write_test(
            "test_missing_cap.py",
            "# capability: local_required()\ndef test_bad():\n    assert True\n",
        )
        errors = validate_test_capability_matrix(self.test_dir)
        self.assertEqual(len(errors), 1)
        self.assertIn(str(test_file), errors[0])
        self.assertIn("must include a capability", errors[0])

    def test_manual_marker_with_reason_passes(self):
        self.write_test(
            "test_manual.py",
            "# capability: manual(human-judgment)\ndef test_manual():\n    assert True\n",
        )
        errors = validate_test_capability_matrix(self.test_dir)
        self.assertEqual(errors, [])

    def test_invalid_marker_format_fails(self):
        test_file = self.write_test(
            "test_invalid.py",
            "# capability: unknown(value)\ndef test_invalid():\n    assert True\n",
        )
        errors = validate_test_capability_matrix(self.test_dir)
        self.assertEqual(len(errors), 1)
        self.assertIn(str(test_file), errors[0])
        self.assertIn("invalid capability marker", errors[0])


if __name__ == "__main__":
    unittest.main()
