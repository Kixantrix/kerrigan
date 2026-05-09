#!/usr/bin/env python3
"""Unit tests for tools/route_task.py."""

import json
from io import StringIO
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from route_task import (  # noqa: E402
    TaskMetadata,
    apply_routing_to_briefing,
    decide_route,
    main,
    parse_task_metadata,
    route_task_file,
)


BRIEFING_TEMPLATE = """# Briefing: T-001

## Objective
{objective}

## Scope
- Touch: {touch}
- Read-only: {read_only}
- Out of scope: none

## Routing rule matched
R-cloud-default — standard code change, no local-only capabilities.
"""


class TestParseTaskMetadata(unittest.TestCase):
    def test_parses_description_scope_tags_and_override(self):
        content = BRIEFING_TEMPLATE.format(
            objective="Implement [P] workflow",
            touch="src/a.py, src/b.py",
            read_only="docs/",
        ) + "\n- Tags: backend, routing\nrouting_override: local\n"

        meta = parse_task_metadata(content)
        self.assertIn("Implement", meta.description)
        self.assertEqual(meta.touch_files, ["src/a.py", "src/b.py"])
        self.assertEqual(meta.read_only_files, ["docs/"])
        self.assertIn("backend", meta.tags)
        self.assertIn("P", meta.tags)
        self.assertEqual(meta.routing_override, "local")


class TestDecideRoute(unittest.TestCase):
    def test_default_cloud(self):
        meta = TaskMetadata("Implement utility", ["tools/x.py"], ["docs/"], [], "plain task body")
        self.assertEqual(decide_route(meta)["rule"], "R-cloud-default")

    def test_device_io_signal(self):
        meta = TaskMetadata("Capture microphone input", [], [], [], "")
        self.assertEqual(decide_route(meta)["rule"], "R-local.device-io")

    def test_os_specific_signal(self):
        meta = TaskMetadata("Use macOS keychain", [], [], [], "")
        self.assertEqual(decide_route(meta)["rule"], "R-local.os-specific")

    def test_paid_secret_signal(self):
        meta = TaskMetadata("Use personal API key", [], [], [], "")
        self.assertEqual(decide_route(meta)["rule"], "R-local.paid-secret")

    def test_human_judgment_signal(self):
        meta = TaskMetadata("Needs human-judgment", [], [], [], "")
        self.assertEqual(decide_route(meta)["rule"], "R-local.human-judgment")

    def test_local_required_marker_mapped(self):
        meta = TaskMetadata("", [], [], [], "# capability: local_required(os.windows)")
        self.assertEqual(decide_route(meta)["rule"], "R-local.os-specific")

    def test_multiple_signals_priority_order(self):
        meta = TaskMetadata("Needs os-specific and device-io camera", [], [], [], "")
        # R-local.device-io has highest priority in the local rule ordering
        self.assertEqual(decide_route(meta)["rule"], "R-local.device-io")

    def test_explicit_override_local_wins(self):
        meta = TaskMetadata("", [], [], [], "device-io", routing_override="local")
        decision = decide_route(meta)
        self.assertEqual(decision["route"], "local")
        self.assertEqual(decision["rule"], "R-local.human-judgment")


class TestApplyRoutingToBriefing(unittest.TestCase):
    def test_replaces_existing_routing_section(self):
        content = BRIEFING_TEMPLATE.format(
            objective="Do work",
            touch="src/a.py",
            read_only="docs/",
        )
        updated = apply_routing_to_briefing(
            content,
            {"rule": "R-local.device-io", "justification": "needs microphone", "route": "local"},
        )
        self.assertIn("R-local.device-io", updated)
        self.assertNotIn("R-cloud-default — standard code change", updated)

    def test_appends_missing_section(self):
        content = "# Briefing\n\n## Objective\nTask\n"
        updated = apply_routing_to_briefing(
            content,
            {"rule": "R-cloud-default", "justification": "none", "route": "cloud"},
        )
        self.assertIn("## Routing rule matched", updated)
        self.assertIn("R-cloud-default", updated)


class TestRouteTaskFileAndCli(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_route_task_file_writes_decision(self):
        task_file = self.tmpdir / "t-001.md"
        task_file.write_text(
            BRIEFING_TEMPLATE.format(
                objective="Use camera capture",
                touch="src/a.py",
                read_only="docs/",
            ),
            encoding="utf-8",
        )

        decision = route_task_file(task_file)
        self.assertEqual(decision["route"], "local")
        self.assertIn("R-local.device-io", task_file.read_text(encoding="utf-8"))

    def test_main_success(self):
        task_file = self.tmpdir / "t-001.md"
        task_file.write_text(
            BRIEFING_TEMPLATE.format(
                objective="Implement tool",
                touch="tools/route_task.py",
                read_only="tools/briefing_generator.py",
            ),
            encoding="utf-8",
        )

        with unittest.mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            rc = main(["--task-file", str(task_file)])
        self.assertEqual(rc, 0)

        payload = json.loads(mock_stdout.getvalue().strip())
        self.assertIn("rule", payload)
        self.assertIn("route", payload)

    def test_main_missing_file(self):
        rc = main(["--task-file", str(self.tmpdir / "missing.md")])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
