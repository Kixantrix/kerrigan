#!/usr/bin/env python3
"""Unit tests for tools/briefing_generator.py.

Achieves ≥80 % coverage of the module under test.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Ensure the tools directory is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from briefing_generator import (
    Task,
    PlanContext,
    parse_tasks,
    parse_plan,
    generate_briefings,
    _extract_task_id,
    _normalize_task_id,
    _render_briefing,
    main,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_TASKS_MD = """\
# Tasks: Demo

- [ ] T-001 Implement the widget factory
  - Done when: `widgets/factory.py` exists and all tests pass
  - Links: src/widgets/factory.py, tests/test_factory.py
- [ ] T-002 [P] Write unit tests for widget
  - Done when: coverage > 80 %
"""

PLAN_MD_WITH_SECTIONS = """\
# Plan: Demo Project

## Scope
- Touch: src/, tests/
- Read-only: docs/
- Out of scope: changing the public API

## Prior decisions
- Use stdlib only, no third-party deps — from plan.md §Tech Stack
- Single-module layout — from plan.md §Architecture

## Test commands
- unit: `pytest tests/ -x`
- integration: `pytest tests/integration/ -x`
- smoke: `scripts/smoke.sh`

## Relevant skills (preload)
- testing-with-pytest
- python-stdlib

## Routing
R-cloud-default — standard code change, no local-only capabilities.
"""

MINIMAL_PLAN_MD = "# Plan: Minimal\n\nNo sections.\n"

TASK_LABEL_TASKS_MD = """\
# Tasks: Old-style

- [x] Task: Create project structure
  - Done when: directory exists
  - Links: src/
- [ ] Task: Write README
"""

BARE_CHECKBOX_TASKS_MD = """\
# Tasks: Bare

- [ ] Set up package structure
- [x] Initialize git repository
"""

T001_NO_DASH = """\
# Tasks: NoDash

- [ ] T001 First task
- [ ] T002 Second task
"""


# ---------------------------------------------------------------------------
# _extract_task_id
# ---------------------------------------------------------------------------

class TestExtractTaskId(unittest.TestCase):

    def test_standard_t_dash_format(self):
        self.assertEqual(_extract_task_id("T-001 Do something"), "T-001")

    def test_standard_t_no_dash(self):
        self.assertEqual(_extract_task_id("T001 Do something"), "T-001")

    def test_t_large_number(self):
        self.assertEqual(_extract_task_id("T-42 Some task"), "T-042")

    def test_no_id_returns_none(self):
        self.assertIsNone(_extract_task_id("No ID here"))

    def test_id_inside_brackets_skipped(self):
        # "[P]" should not match as a task id
        self.assertIsNone(_extract_task_id("[P] Do something"))

    def test_id_with_parallel_marker(self):
        # e.g. "T-003 [P] Some task" — only the T-003 portion should match
        self.assertEqual(_extract_task_id("T-003 [P] Some task"), "T-003")


# ---------------------------------------------------------------------------
# _normalise_task_id
# ---------------------------------------------------------------------------

class TestNormaliseTaskId(unittest.TestCase):

    def test_strips_leading_zeros(self):
        self.assertEqual(_normalize_task_id("T-001"), "T-1")

    def test_handles_no_dash(self):
        self.assertEqual(_normalize_task_id("T001"), "T-1")

    def test_uppercase(self):
        self.assertEqual(_normalize_task_id("t-005"), "T-5")

    def test_unknown_format(self):
        self.assertEqual(_normalize_task_id("TASK-XYZ"), "TASK-XYZ")


# ---------------------------------------------------------------------------
# parse_tasks
# ---------------------------------------------------------------------------

class TestParseTasks(unittest.TestCase):

    def test_parses_explicit_ids(self):
        tasks = parse_tasks(MINIMAL_TASKS_MD)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].task_id, "T-001")
        self.assertEqual(tasks[1].task_id, "T-002")

    def test_description_stripped_of_parallel_markers(self):
        tasks = parse_tasks(MINIMAL_TASKS_MD)
        self.assertNotIn("[P]", tasks[1].description)

    def test_done_when_extracted(self):
        tasks = parse_tasks(MINIMAL_TASKS_MD)
        self.assertIn("widgets/factory.py", tasks[0].done_when)

    def test_links_extracted(self):
        tasks = parse_tasks(MINIMAL_TASKS_MD)
        self.assertIn("src/widgets/factory.py", tasks[0].links)
        self.assertIn("tests/test_factory.py", tasks[0].links)

    def test_task_label_format(self):
        tasks = parse_tasks(TASK_LABEL_TASKS_MD)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].description, "Create project structure")

    def test_bare_checkbox_format(self):
        tasks = parse_tasks(BARE_CHECKBOX_TASKS_MD)
        self.assertEqual(len(tasks), 2)
        # IDs are auto-generated
        self.assertTrue(tasks[0].task_id.startswith("T-"))

    def test_no_dash_id_format(self):
        tasks = parse_tasks(T001_NO_DASH)
        self.assertEqual(tasks[0].task_id, "T-001")
        self.assertEqual(tasks[1].task_id, "T-002")

    def test_empty_content_returns_empty_list(self):
        tasks = parse_tasks("")
        self.assertEqual(tasks, [])

    def test_only_headings_returns_empty_list(self):
        tasks = parse_tasks("# Tasks\n\n## Phase 1\n\n## Phase 2\n")
        self.assertEqual(tasks, [])

    def test_completed_tasks_are_included(self):
        content = "- [x] T-010 Already done task\n"
        tasks = parse_tasks(content)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task_id, "T-010")


# ---------------------------------------------------------------------------
# parse_plan
# ---------------------------------------------------------------------------

class TestParsePlan(unittest.TestCase):

    def test_title_extracted(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertEqual(ctx.title, "Plan: Demo Project")

    def test_scope_touch(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertIn("src/", ctx.scope_touch)
        self.assertIn("tests/", ctx.scope_touch)

    def test_scope_read_only(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertIn("docs/", ctx.scope_read_only)

    def test_scope_out_of(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertTrue(any("public API" in s for s in ctx.scope_out_of))

    def test_decisions_extracted(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertGreater(len(ctx.decisions), 0)
        self.assertTrue(any("stdlib" in d for d in ctx.decisions))

    def test_test_commands_extracted(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertIn("unit", ctx.test_commands)
        self.assertIn("pytest tests/ -x", ctx.test_commands["unit"])

    def test_smoke_command_extracted(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertIn("smoke", ctx.test_commands)

    def test_skills_extracted(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertIn("testing-with-pytest", ctx.skills)

    def test_routing_rule_extracted(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertEqual(ctx.routing_rule, "R-cloud-default")

    def test_routing_justification_extracted(self):
        ctx = parse_plan(PLAN_MD_WITH_SECTIONS)
        self.assertIn("standard code change", ctx.routing_justification)

    def test_minimal_plan_has_defaults(self):
        ctx = parse_plan(MINIMAL_PLAN_MD)
        self.assertEqual(ctx.decisions, [])
        self.assertEqual(ctx.test_commands, {})
        self.assertEqual(ctx.routing_rule, "R-cloud-default")


# ---------------------------------------------------------------------------
# _render_briefing
# ---------------------------------------------------------------------------

class TestRenderBriefing(unittest.TestCase):

    def setUp(self):
        self.task = Task(
            task_id="T-001",
            description="Implement the widget factory",
            done_when="factory.py exists and tests pass",
            links=["src/widgets/factory.py"],
        )
        self.plan_ctx = parse_plan(PLAN_MD_WITH_SECTIONS)

    def test_heading_contains_task_id(self):
        result = _render_briefing(self.task, self.plan_ctx)
        self.assertIn("# Briefing: T-001", result)

    def test_objective_present(self):
        result = _render_briefing(self.task, self.plan_ctx)
        self.assertIn("## Objective", result)
        self.assertIn("Implement the widget factory", result)

    def test_acceptance_criteria_present(self):
        result = _render_briefing(self.task, self.plan_ctx)
        self.assertIn("## Acceptance criteria", result)
        self.assertIn("AC-T-001-a", result)
        self.assertIn("factory.py exists and tests pass", result)

    def test_scope_section_present(self):
        result = _render_briefing(self.task, self.plan_ctx)
        self.assertIn("## Scope", result)
        self.assertIn("Touch:", result)
        self.assertIn("Read-only:", result)
        self.assertIn("Out of scope:", result)

    def test_prior_decisions_present(self):
        result = _render_briefing(self.task, self.plan_ctx)
        self.assertIn("## Prior decisions", result)
        self.assertIn("from plan.md", result)

    def test_skills_section_present(self):
        result = _render_briefing(self.task, self.plan_ctx)
        self.assertIn("## Relevant skills (preload)", result)
        self.assertIn("testing-with-pytest", result)

    def test_test_commands_present(self):
        result = _render_briefing(self.task, self.plan_ctx)
        self.assertIn("## Test commands", result)
        self.assertIn("pytest tests/ -x", result)

    def test_routing_rule_present(self):
        result = _render_briefing(self.task, self.plan_ctx)
        self.assertIn("## Routing rule matched", result)
        self.assertIn("R-cloud-default", result)

    def test_budget_present(self):
        result = _render_briefing(self.task, self.plan_ctx)
        self.assertIn("## Budget", result)
        self.assertIn("max_turns: 40", result)
        self.assertIn("max_premium_requests: 25", result)

    def test_custom_budget(self):
        result = _render_briefing(self.task, self.plan_ctx, budget_turns=10, budget_premium=5)
        self.assertIn("max_turns: 10", result)
        self.assertIn("max_premium_requests: 5", result)

    def test_no_done_when_falls_back_to_description(self):
        task = Task(task_id="T-002", description="Write tests", done_when="")
        ctx = PlanContext()
        result = _render_briefing(task, ctx)
        self.assertIn("Write tests", result)

    def test_minimal_plan_context_uses_defaults(self):
        task = Task(task_id="T-003", description="Do something")
        ctx = PlanContext()
        result = _render_briefing(task, ctx)
        self.assertIn("tbd", result)


# ---------------------------------------------------------------------------
# generate_briefings
# ---------------------------------------------------------------------------

class TestGenerateBriefings(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.output_dir = self.tmpdir / ".specify" / "briefings"

    def test_generates_files_for_all_tasks(self):
        paths = generate_briefings(
            plan_content=PLAN_MD_WITH_SECTIONS,
            tasks_content=MINIMAL_TASKS_MD,
            output_dir=self.output_dir,
        )
        self.assertEqual(len(paths), 2)
        for p in paths:
            self.assertTrue(p.exists())

    def test_output_directory_created(self):
        generate_briefings(
            plan_content=MINIMAL_PLAN_MD,
            tasks_content=MINIMAL_TASKS_MD,
            output_dir=self.output_dir,
        )
        self.assertTrue(self.output_dir.exists())

    def test_file_named_after_task_id(self):
        paths = generate_briefings(
            plan_content=MINIMAL_PLAN_MD,
            tasks_content=MINIMAL_TASKS_MD,
            output_dir=self.output_dir,
        )
        names = [p.name for p in paths]
        self.assertIn("t-001.md", names)
        self.assertIn("t-002.md", names)

    def test_briefing_content_is_correct(self):
        paths = generate_briefings(
            plan_content=PLAN_MD_WITH_SECTIONS,
            tasks_content=MINIMAL_TASKS_MD,
            output_dir=self.output_dir,
        )
        content = paths[0].read_text(encoding="utf-8")
        self.assertIn("# Briefing: T-001", content)

    def test_task_filter_single_task(self):
        paths = generate_briefings(
            plan_content=MINIMAL_PLAN_MD,
            tasks_content=MINIMAL_TASKS_MD,
            output_dir=self.output_dir,
            task_filter="T-001",
        )
        self.assertEqual(len(paths), 1)
        self.assertIn("t-001.md", paths[0].name)

    def test_task_filter_no_dash(self):
        paths = generate_briefings(
            plan_content=MINIMAL_PLAN_MD,
            tasks_content=MINIMAL_TASKS_MD,
            output_dir=self.output_dir,
            task_filter="T001",
        )
        self.assertEqual(len(paths), 1)

    def test_task_filter_not_found_returns_empty(self):
        paths = generate_briefings(
            plan_content=MINIMAL_PLAN_MD,
            tasks_content=MINIMAL_TASKS_MD,
            output_dir=self.output_dir,
            task_filter="T-999",
        )
        self.assertEqual(paths, [])

    def test_empty_tasks_returns_empty(self):
        paths = generate_briefings(
            plan_content=MINIMAL_PLAN_MD,
            tasks_content="# Tasks\n\n",
            output_dir=self.output_dir,
        )
        self.assertEqual(paths, [])

    def test_custom_budget_propagated(self):
        paths = generate_briefings(
            plan_content=MINIMAL_PLAN_MD,
            tasks_content="- [ ] T-005 Build something\n",
            output_dir=self.output_dir,
            budget_turns=20,
            budget_premium=10,
        )
        content = paths[0].read_text(encoding="utf-8")
        self.assertIn("max_turns: 20", content)
        self.assertIn("max_premium_requests: 10", content)

    def test_existing_output_dir_does_not_error(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        paths = generate_briefings(
            plan_content=MINIMAL_PLAN_MD,
            tasks_content=MINIMAL_TASKS_MD,
            output_dir=self.output_dir,
        )
        self.assertGreater(len(paths), 0)


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------

class TestMain(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def _write(self, name: str, content: str) -> Path:
        p = self.tmpdir / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_generates_briefings_and_returns_zero(self):
        plan = self._write("plan.md", PLAN_MD_WITH_SECTIONS)
        tasks = self._write("tasks.md", MINIMAL_TASKS_MD)
        out = self.tmpdir / "briefings"

        rc = main([
            "--plan", str(plan),
            "--tasks", str(tasks),
            "--output-dir", str(out),
        ])
        self.assertEqual(rc, 0)
        self.assertTrue((out / "t-001.md").exists())

    def test_single_task_flag(self):
        plan = self._write("plan.md", MINIMAL_PLAN_MD)
        tasks = self._write("tasks.md", MINIMAL_TASKS_MD)
        out = self.tmpdir / "briefings"

        rc = main([
            "--plan", str(plan),
            "--tasks", str(tasks),
            "--output-dir", str(out),
            "--task", "T-002",
        ])
        self.assertEqual(rc, 0)
        self.assertFalse((out / "t-001.md").exists())
        self.assertTrue((out / "t-002.md").exists())

    def test_missing_plan_returns_nonzero(self):
        tasks = self._write("tasks.md", MINIMAL_TASKS_MD)
        rc = main([
            "--plan", str(self.tmpdir / "nonexistent.md"),
            "--tasks", str(tasks),
            "--output-dir", str(self.tmpdir / "out"),
        ])
        self.assertNotEqual(rc, 0)

    def test_missing_tasks_returns_nonzero(self):
        plan = self._write("plan.md", MINIMAL_PLAN_MD)
        rc = main([
            "--plan", str(plan),
            "--tasks", str(self.tmpdir / "nonexistent.md"),
            "--output-dir", str(self.tmpdir / "out"),
        ])
        self.assertNotEqual(rc, 0)

    def test_no_tasks_found_returns_zero(self):
        plan = self._write("plan.md", MINIMAL_PLAN_MD)
        tasks = self._write("tasks.md", "# No tasks here\n")
        rc = main([
            "--plan", str(plan),
            "--tasks", str(tasks),
            "--output-dir", str(self.tmpdir / "out"),
        ])
        self.assertEqual(rc, 0)

    def test_task_filter_not_found_returns_nonzero(self):
        plan = self._write("plan.md", MINIMAL_PLAN_MD)
        tasks = self._write("tasks.md", MINIMAL_TASKS_MD)
        rc = main([
            "--plan", str(plan),
            "--tasks", str(tasks),
            "--output-dir", str(self.tmpdir / "out"),
            "--task", "T-999",
        ])
        self.assertNotEqual(rc, 0)

    def test_custom_budget_flags(self):
        plan = self._write("plan.md", MINIMAL_PLAN_MD)
        tasks = self._write("tasks.md", "- [ ] T-001 Something\n")
        out = self.tmpdir / "briefings"

        rc = main([
            "--plan", str(plan),
            "--tasks", str(tasks),
            "--output-dir", str(out),
            "--budget-turns", "15",
            "--budget-premium", "8",
        ])
        self.assertEqual(rc, 0)
        content = (out / "t-001.md").read_text()
        self.assertIn("max_turns: 15", content)
        self.assertIn("max_premium_requests: 8", content)


# ---------------------------------------------------------------------------
# Task repr
# ---------------------------------------------------------------------------

class TestTaskRepr(unittest.TestCase):

    def test_task_repr(self):
        t = Task(task_id="T-001", description="Do something")
        r = repr(t)
        self.assertIn("T-001", r)
        self.assertIn("Do something", r)


if __name__ == "__main__":
    unittest.main()
